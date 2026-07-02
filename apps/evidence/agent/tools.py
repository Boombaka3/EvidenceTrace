import logging
import time

from apps.evidence.models import AnswerRecord, Claim

logger = logging.getLogger(__name__)


def retrieve_answers(job_id: int) -> dict:
    """
    Tool: retrieve stored AnswerRecords for this job.
    Returns top 10 by final_confidence.
    """
    start = time.time()
    try:
        records = list(
            AnswerRecord.objects.filter(paper__job_id=job_id)
            .select_related("paper", "reward")
            .order_by("-reward__final_confidence")[:10]
        )
        result = {
            "count": len(records),
            "answers": [
                {
                    "question": ar.question,
                    "answer": ar.answer,
                    "confidence": ar.reward.final_confidence if hasattr(ar, "reward") and ar.reward else None,
                    "reasoning": ar.reasoning,
                    "source": ar.source_sentence,
                    "paper": ar.paper.title,
                }
                for ar in records
            ]
        }
    except Exception as e:
        logger.error(f"retrieve_answers failed: {e}")
        result = {"count": 0, "answers": [], "error": str(e)}
    latency = int((time.time() - start) * 1000)
    result["latency_ms"] = latency
    return result


def retrieve_claims(job_id: int) -> dict:
    """
    Tool: retrieve raw extracted claims for this job.
    Returns up to 20 claims.
    """
    start = time.time()
    try:
        claims = list(
            Claim.objects.filter(paper__job_id=job_id)
            .select_related("paper")[:20]
        )
        result = {
            "count": len(claims),
            "claims": [
                {
                    "text": c.text,
                    "type": c.claim_type,
                    "section": c.section,
                    "paper": c.paper.title,
                }
                for c in claims
            ]
        }
    except Exception as e:
        logger.error(f"retrieve_claims failed: {e}")
        result = {"count": 0, "claims": [], "error": str(e)}
    latency = int((time.time() - start) * 1000)
    result["latency_ms"] = latency
    return result


def nli_score_tool(text_a: str, text_b: str) -> dict:
    """
    Tool: compute NLI entailment probability between two texts.
    """
    start = time.time()
    try:
        from apps.evidence.scoring.nli_grounding import score_nli_grounding

        score = score_nli_grounding(text_a[:500], text_b[:500])
        result = {"entailment": score, "available": score is not None}
    except Exception as e:
        logger.error(f"nli_score_tool failed: {e}")
        result = {"entailment": None, "available": False, "error": str(e)}
    latency = int((time.time() - start) * 1000)
    result["latency_ms"] = latency
    return result


TOOL_REGISTRY = {
    "retrieve_answers": retrieve_answers,
    "retrieve_claims": retrieve_claims,
    "nli_score": nli_score_tool,
}
