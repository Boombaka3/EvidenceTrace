# apps/evidence/scoring/reward_voting.py
import logging
from collections import Counter
from apps.evidence.models import Paper, AnswerRecord, RewardScore
from apps.evidence.scoring.question_answerer import answer_question
from apps.evidence.scoring.nli_grounding import score_nli_grounding

logger = logging.getLogger(__name__)

VALID_ANSWERS = {"yes", "no", "maybe"}


def _compute_format_score(record: AnswerRecord) -> float:
    """
    1.0 if the response used <think>/<answer> format correctly.
    0.0 if it fell back to JSON or had parse errors.
    From Med-RLVR: format reward prevents skipping reasoning.
    """
    return 1.0 if getattr(record, '_format_ok', False) else 0.0


def _compute_outcome_reward(answer: str, gold_label: str) -> float | None:
    """
    Binary verifiable reward: 1.0 if correct, 0.0 if wrong.
    None if no gold label available.
    From Med-RLVR: this is the core RLVR signal.
    """
    if not gold_label:
        return None
    gold = gold_label.lower().strip()
    pred = answer.lower().strip()
    gold = "yes"   if gold in ("yes", "true", "supports") else \
           "no"    if gold in ("no", "false", "contradicts", "refutes") else \
           "maybe"
    return 1.0 if pred == gold else 0.0


def compute_reward(
    paper: Paper,
    question: str,
    n_samples: int = 3,
    gold_label: str = "",
) -> tuple[AnswerRecord, RewardScore]:
    """
    Four-component reward signal.

    Component 1 -- Format reward (Med-RLVR)
      Did the model use <think>/<answer> structure?
      1.0 = yes (reasoning present), 0.0 = no

    Component 2 -- Outcome reward (Med-RLVR, RLVR signal)
      Is the majority answer correct?
      Binary, verifiable against gold label.
      None when no gold label available.

    Component 3 -- NLI grounding (MedRAGChecker)
      Is the reasoning entailed by the abstract?
      Cross-encoder NLI, not circular self-judgment.

    Component 4 -- Consistency (N-sample voting)
      Do N independent runs agree?
      Majority count / N.

    final_confidence formula:
      With gold label:    0.4*outcome + 0.3*grounding + 0.2*consistency + 0.1*format
      Without gold label: 0.5*grounding + 0.3*consistency + 0.2*format
    """
    answers    = []
    format_oks = []
    last_record = None

    for _ in range(n_samples):
        try:
            record = answer_question(paper, question)
            answers.append(record.answer)
            format_oks.append(getattr(record, '_format_ok', False))
            last_record = record
        except Exception as e:
            logger.error(f"answer_question failed in voting loop: {e}")
            answers.append("maybe")
            format_oks.append(False)

    counts = Counter(answers)
    majority_answer, majority_count = counts.most_common(1)[0]
    consistency = majority_count / n_samples
    format_score = sum(format_oks) / n_samples if format_oks else 0.0

    if last_record is None:
        last_record = AnswerRecord(
            paper=paper,
            question=question,
            answer="maybe",
            reasoning="all runs failed",
            source_sentence="",
            error_types=[],
        )
    last_record.answer = majority_answer

    outcome_reward = _compute_outcome_reward(majority_answer, gold_label)
    if gold_label:
        last_record.gold_label = gold_label

    abstract = paper.abstract or " ".join(
        paper.parsed_sections.get(k, "")
        for k in ("abstract", "body")
        if paper.parsed_sections.get(k)
    )
    nli_score = score_nli_grounding(last_record.reasoning, abstract)

    grounding = nli_score if nli_score is not None else consistency

    if outcome_reward is not None:
        # Full four-component reward (benchmark mode)
        final_confidence = (
            0.4 * outcome_reward +
            0.3 * grounding +
            0.2 * consistency +
            0.1 * format_score
        )
    else:
        # Inference mode (no gold label)
        final_confidence = (
            0.5 * grounding +
            0.3 * consistency +
            0.2 * format_score
        )

    reward = RewardScore(
        consistency_score  = consistency,
        nli_score          = nli_score,
        faithfulness_score = format_score,   # repurposed field: stores format score
        final_confidence   = final_confidence,
        n_samples          = n_samples,
    )

    return last_record, reward


def compute_reward_text(
    question: str,
    abstract: str,
    gold_label: str = "",
    n_samples: int = 1,
) -> dict:
    """
    Text-only version for benchmarking. No ORM objects.
    Used by scripts/benchmark.py.
    """
    from apps.evidence.scoring.question_answerer import answer_question_text

    answers    = []
    format_oks = []
    last_parsed = None

    for _ in range(n_samples):
        try:
            parsed = answer_question_text(question, abstract, gold_label)
            answers.append(parsed.get("answer", "maybe"))
            format_oks.append(parsed.get("format_ok", False))
            last_parsed = parsed
        except Exception as e:
            logger.error(f"answer_question_text failed: {e}")
            answers.append("maybe")
            format_oks.append(False)

    counts = Counter(answers)
    majority_answer, majority_count = counts.most_common(1)[0]
    consistency = majority_count / n_samples
    format_score = sum(format_oks) / n_samples

    outcome_reward = _compute_outcome_reward(majority_answer, gold_label)

    nli_score = score_nli_grounding(
        (last_parsed or {}).get("reasoning", ""),
        abstract,
    )

    grounding = nli_score if nli_score is not None else consistency

    if outcome_reward is not None:
        final_confidence = (
            0.4 * outcome_reward +
            0.3 * grounding +
            0.2 * consistency +
            0.1 * format_score
        )
    else:
        final_confidence = (
            0.5 * grounding +
            0.3 * consistency +
            0.2 * format_score
        )

    return {
        "answer":           majority_answer,
        "consistency":      consistency,
        "format_score":     format_score,
        "nli_score":        nli_score,
        "outcome_reward":   outcome_reward,
        "final_confidence": final_confidence,
        "reasoning":        (last_parsed or {}).get("reasoning", ""),
        "gold_label":       gold_label,
        "correct":          outcome_reward == 1.0 if outcome_reward is not None else None,
    }
