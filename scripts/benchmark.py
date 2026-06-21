# scripts/benchmark.py
"""
Offline benchmark for EvidenceTrace evidence QA scoring.

Evaluates compute_reward_text() against ground-truth datasets:
  - scripts/test_data/benchmark_records.jsonl  (SciFact/PubMedQA/QASPER records)
  - scripts/test_data/conflict_pairs_ground_truth.jsonl  (5 manual cross-doc pairs)

Reward components reported:
  - Outcome reward (binary, from gold label)
  - NLI grounding score (cross-encoder/nli-deberta-v3-base)
  - Consistency score (N-sample voting)
  - Format score (1.0 if <think>/<answer> tags used)
  - Final confidence (weighted composite)
  - Overall QA accuracy (predicted answer vs gold)

Usage:
  uv run python scripts/benchmark.py
  uv run python scripts/benchmark.py --limit 50
  uv run python scripts/benchmark.py --dataset scifact
  uv run python scripts/benchmark.py --out docs/benchmark_results_v2.jsonl

Requires OPENAI_API_KEY (NaviGator Toolkit) in .env.
Exit 0 on completion (regardless of score), 1 on setup failure.
"""
import argparse
import json
import os
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

import django
django.setup()

from apps.evidence.scoring.reward_voting import compute_reward_text
from apps.evidence.utils.dataset_loader import (
    load_benchmark_records,
    load_conflict_pairs,
)


# ── Gold-label normalisation ──────────────────────────────────────────────────

def _gold_to_answer(gold: str) -> str:
    """Map SUPPORTS/CONTRADICTS/NEI (or yes/no/maybe) to yes/no/maybe."""
    g = str(gold).lower().strip()
    if g in ("support", "supports", "supported", "yes", "true"):
        return "yes"
    if g in ("contradict", "contradicts", "contradicted", "conflict",
             "conflict_or_conditionally_supported", "no", "false", "refutes"):
        return "no"
    return "maybe"


# ── Record normalisation ──────────────────────────────────────────────────────

def _sentences_text(doc: dict) -> str:
    if not doc:
        return ""
    sents = doc.get("sentences") or []
    if sents:
        return " ".join(s.strip() for s in sents if s.strip())
    return (doc.get("abstract") or "").strip()


def _flatten_records(records: list[dict]) -> list[dict]:
    """Return a normalised list with consistent keys for benchmarking."""
    out = []
    for r in records:
        doc_a = r.get("document_a") or {}
        doc_b = r.get("document_b") or {}
        text_a = _sentences_text(doc_a)
        text_b = _sentences_text(doc_b)

        # For claim-verification records (document_b is null):
        # treat input_claim_or_question as the question, document_a as the abstract.
        if not text_b:
            text_a = r.get("input_claim_or_question", "")
            text_b = _sentences_text(doc_a)

        raw_gold = r.get("gold_answer") or r.get("gold_label", "")
        gold_answer = _gold_to_answer(raw_gold) if raw_gold else ""

        out.append({
            "id":             r.get("id", ""),
            "source_dataset": r.get("source_dataset", ""),
            "task_type":      r.get("task_type", ""),
            "question":       text_a,     # claim or question
            "abstract":       text_b,     # supporting document
            "gold_answer":    gold_answer,
        })
    return out


def stratified_sample(records: list[dict], limit: int, seed: int = 42) -> list[dict]:
    """Sample as equally as possible from each gold-label class."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        gold = record.get("gold_answer") or record.get("gold_label", "unknown")
        groups[str(gold).lower().strip()].append(record)

    if not groups:
        return records[:limit]

    rng = random.Random(seed)
    pools = {label: rng.sample(group, len(group)) for label, group in groups.items()}
    positions = {label: 0 for label in groups}
    sampled: list[dict] = []
    remaining = min(limit, len(records))
    active = sorted(groups)

    # Reallocate unused quotas when a small class cannot supply its share.
    while remaining and active:
        per_group = max(1, remaining // len(active))
        next_active = []
        for label in active:
            available = len(pools[label]) - positions[label]
            take = min(per_group, available, remaining)
            start = positions[label]
            sampled.extend(pools[label][start:start + take])
            positions[label] += take
            remaining -= take
            if positions[label] < len(pools[label]) and remaining:
                next_active.append(label)
        active = next_active

    rng.shuffle(sampled)
    return sampled[:limit]


# ── Metrics ───────────────────────────────────────────────────────────────────

def _accuracy(preds: list[str], golds: list[str]) -> float:
    if not preds:
        return 0.0
    return sum(p == g for p, g in zip(preds, golds)) / len(preds)


def _avg(vals: list) -> float:
    filtered = [v for v in vals if v is not None]
    return sum(filtered) / len(filtered) if filtered else 0.0


def _confusion(preds: list[str], golds: list[str]) -> dict:
    matrix: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for p, g in zip(preds, golds):
        matrix[g][p] += 1
    return {k: dict(v) for k, v in matrix.items()}


def _print_confusion(matrix: dict) -> None:
    all_labels = sorted({k for row in matrix.values() for k in row} | set(matrix.keys()))
    col_w = max(len(l) for l in all_labels) + 2
    row_label = "Gold \\ Pred"
    header = f"{row_label:<16}" + "".join(f"{l:>{col_w}}" for l in all_labels)
    print(header)
    print("-" * len(header))
    for gold in all_labels:
        row = matrix.get(gold, {})
        line = f"{gold:<16}" + "".join(f"{row.get(pred, 0):>{col_w}}" for pred in all_labels)
        print(line)


# ── Main ──────────────────────────────────────────────────────────────────────

def run_benchmark(
    records: list[dict],
    limit: int | None,
    out_path: Path | None,
) -> list[dict]:
    if limit:
        records = records[:limit]

    results = []
    for i, rec in enumerate(records, 1):
        print(
            f"  [{i}/{len(records)}] {rec['id']}  "
            f"({rec['source_dataset']})  gold={rec['gold_answer']}",
            end=" ... ",
            flush=True,
        )
        try:
            result = compute_reward_text(
                question=rec["question"],
                abstract=rec["abstract"],
                gold_label=rec["gold_answer"],
                n_samples=1,
            )
            predicted  = result["answer"]
            correct    = result["correct"]
            confidence = result["final_confidence"]
            nli_score  = result["nli_score"]
            format_ok  = result["format_score"] > 0.5

            print(f"pred={predicted}  {'OK' if correct else 'WRONG'}")
            if nli_score is not None:
                print(f"    nli_score={nli_score:.3f}  format={'OK' if format_ok else 'FAIL'}"
                      f"  confidence={confidence:.3f}")
            else:
                print(f"    nli_score=None  format={'OK' if format_ok else 'FAIL'}"
                      f"  confidence={confidence:.3f}")

        except Exception as e:
            predicted  = "maybe"
            correct    = bool(rec["gold_answer"]) and predicted == rec["gold_answer"]
            confidence = 0.0
            nli_score  = None
            format_ok  = False
            result     = {}
            print(f"ERROR: {e}")

        results.append({
            "id":             rec["id"],
            "source_dataset": rec["source_dataset"],
            "task_type":      rec["task_type"],
            "gold_answer":    rec["gold_answer"],
            "pred_answer":    predicted,
            "correct":        correct,
            "outcome_reward": result.get("outcome_reward"),
            "nli_score":      nli_score,
            "consistency":    result.get("consistency", 1.0),
            "format_score":   result.get("format_score", 0.0),
            "final_confidence": confidence,
            "reasoning":      result.get("reasoning", ""),
        })

    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            for row in results:
                f.write(json.dumps(row) + "\n")
        print(f"\nResults written to {out_path}")

    return results


def print_report(results: list[dict]) -> None:
    if not results:
        print("No results.")
        return

    preds = [r["pred_answer"]  for r in results]
    golds = [r["gold_answer"]  for r in results]

    overall_acc = _accuracy(preds, golds)
    n_correct   = sum(r["correct"] for r in results)

    print(f"\n{'=' * 60}")
    print(f"BENCHMARK RESULTS  ({len(results)} records)")
    print(f"{'=' * 60}")
    print(f"  Overall accuracy : {overall_acc:.3f} ({n_correct}/{len(results)})")

    # Per-dataset breakdown
    by_dataset: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        by_dataset[r["source_dataset"]].append(r)

    print(f"\n  Per-dataset accuracy:")
    for ds, recs in sorted(by_dataset.items()):
        ds_preds = [r["pred_answer"] for r in recs]
        ds_golds = [r["gold_answer"] for r in recs]
        ds_acc   = _accuracy(ds_preds, ds_golds)
        ds_correct = sum(r["correct"] for r in recs)
        print(f"    {ds:<35} {ds_acc:.3f}  ({ds_correct}/{len(recs)})")

    # Answer distribution
    print(f"\n  Predicted answer distribution:")
    for ans, count in sorted(Counter(preds).items()):
        print(f"    {ans:<10} {count}")

    print(f"\n  Confusion matrix (rows=gold, cols=pred):")
    matrix = _confusion(preds, golds)
    _print_confusion(matrix)

    # Four-component breakdown
    outcome_vals    = [r["outcome_reward"]   for r in results]
    nli_vals        = [r["nli_score"]        for r in results]
    consistency_vals = [r["consistency"]     for r in results]
    format_vals     = [r["format_score"]     for r in results]
    confidence_vals = [r["final_confidence"] for r in results]

    print(f"\n{'=' * 60}")
    print(f"  === Four-Component Reward Breakdown ===")
    print(f"  Outcome reward (when gold available):  {_avg(outcome_vals):.3f} avg")
    print(f"  NLI grounding score:                   {_avg(nli_vals):.3f} avg"
          f"  ({sum(1 for v in nli_vals if v is not None)}/{len(nli_vals)} available)")
    print(f"  Consistency score:                     {_avg(consistency_vals):.3f} avg")
    print(f"  Format score:                          {_avg(format_vals):.3f} avg")
    print(f"  Final confidence:                      {_avg(confidence_vals):.3f} avg")
    print(f"{'=' * 60}")


def main() -> None:
    parser = argparse.ArgumentParser(description="EvidenceTrace evidence QA benchmark")
    parser.add_argument("--limit", type=int, default=None, help="Max records to evaluate")
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Filter by source_dataset (case-insensitive substring match)",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Path to write per-record JSONL results",
    )
    parser.add_argument(
        "--stratify",
        action="store_true",
        help="Sample equally from each gold label class",
    )
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key or api_key in ("<your-navigator-api-key>", "placeholder", ""):
        print("ERROR: OPENAI_API_KEY not set in .env — benchmark requires NaviGator Toolkit API key.")
        print("  Set OPENAI_COMPAT_BASE_URL=https://api.ai.it.ufl.edu/v1 and your NaviGator key.")
        sys.exit(1)

    print("Loading benchmark records...")
    benchmark     = _flatten_records(load_benchmark_records())
    conflict_pairs = _flatten_records(load_conflict_pairs())
    all_records   = benchmark + conflict_pairs
    print(f"  benchmark_records.jsonl  : {len(benchmark)} records")
    print(f"  conflict_pairs.jsonl     : {len(conflict_pairs)} records")
    print(f"  Total                    : {len(all_records)} records")

    if args.dataset:
        ds_filter   = args.dataset.lower()
        all_records = [r for r in all_records if ds_filter in r["source_dataset"].lower()]
        print(f"  After --dataset filter   : {len(all_records)} records")

    if not all_records:
        print("No records to evaluate after filtering.")
        sys.exit(0)

    limit = args.limit or len(all_records)
    if args.stratify:
        all_records = stratified_sample(all_records, limit)
        print(f"Stratified sample: {len(all_records)} records")
        dist = Counter(
            (r.get("gold_answer") or r.get("gold_label", "")).lower()
            for r in all_records
        )
        print(f"Gold distribution: {dict(dist)}")
    else:
        all_records = all_records[:limit]

    out_path = Path(args.out) if args.out else None

    print(f"\nRunning benchmark (n={len(all_records)})...\n")
    results = run_benchmark(all_records, limit=None, out_path=out_path)
    print_report(results)


if __name__ == "__main__":
    main()
