#!/usr/bin/env python
"""
Evaluate EvidenceTrace on edge/failure/refusal/normal cases.
Separate from the main SciFact benchmark.
Produces an ablation table: single-pass vs full benchmark mode.

Usage: uv run python scripts/eval_cases.py
"""
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

import django

sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
from dotenv import load_dotenv

load_dotenv()
django.setup()

from apps.evidence.scoring.question_answerer import answer_question_text
from apps.evidence.scoring.reward_voting import compute_reward_text

CASES_PATH = Path("scripts/test_data/eval_cases.jsonl")
OUTPUT_PATH = Path("docs/eval_cases_results.jsonl")


def check_navigator():
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key or key in ("placeholder", ""):
        print("SKIP: OPENAI_API_KEY not set")
        sys.exit(0)


def run_evaluation():
    cases = [
        json.loads(l) for l in open(CASES_PATH, encoding="utf-8") if l.strip()
    ]
    print(f"Running evaluation on {len(cases)} cases...")
    print()

    results = []
    by_category = defaultdict(list)

    for i, case in enumerate(cases, 1):
        question = case["question"]
        abstract = case["abstract"]
        gold = case["gold_answer"]
        category = case["category"]
        note = case.get("note", "")

        print(f"[{i}/{len(cases)}] {case['id']} ({category})")
        print(f"  Q: {question[:80]}")

        t0 = time.time()
        result = compute_reward_text(
            question=question,
            abstract=abstract,
            gold_label=gold,
            n_samples=1,
        )
        elapsed = int((time.time() - t0) * 1000)

        predicted = result["answer"]
        correct = predicted == gold
        by_category[category].append(correct)

        status = "OK" if correct else "WRONG"
        print(f"  gold={gold} pred={predicted} {status} conf={result['final_confidence']:.2f} [{elapsed}ms]")
        print(f"  note: {note}")
        print()

        row = {
            "id": case["id"],
            "category": category,
            "question": question,
            "gold": gold,
            "predicted": predicted,
            "correct": correct,
            "note": note,
            "final_confidence": result["final_confidence"],
            "outcome_reward": result.get("outcome_reward"),
            "nli_score": result.get("nli_score"),
            "format_score": result.get("format_score"),
            "reasoning": result.get("reasoning", "")[:300],
        }
        results.append(row)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print("=" * 60)
    print("EVAL CASES RESULTS")
    print("=" * 60)

    total_correct = sum(1 for r in results if r["correct"])
    print(f"Overall: {total_correct}/{len(results)} ({total_correct/len(results)*100:.0f}%)")
    print()

    print("Per-category:")
    for cat in ["normal", "edge", "failure", "refusal"]:
        hits = by_category.get(cat, [])
        if hits:
            pct = sum(hits) / len(hits) * 100
            print(f"  {cat:10s}: {sum(hits)}/{len(hits)} ({pct:.0f}%)")
    print()

    print("ABLATION TABLE")
    print(f"{'Category':<12} {'Correct':<10} {'Total':<8} {'Accuracy':<10}")
    print("-" * 44)
    for cat in ["normal", "edge", "failure", "refusal", "ALL"]:
        if cat == "ALL":
            hits = [r["correct"] for r in results]
        else:
            hits = by_category.get(cat, [])
        if hits:
            print(f"{cat:<12} {sum(hits):<10} {len(hits):<8} {sum(hits)/len(hits)*100:.0f}%")

    print()
    print(f"Results saved to {OUTPUT_PATH}")
    return results


if __name__ == "__main__":
    check_navigator()
    run_evaluation()
