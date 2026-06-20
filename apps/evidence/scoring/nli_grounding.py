# apps/evidence/scoring/nli_grounding.py
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

NLI_MODEL_NAME = "cross-encoder/nli-deberta-v3-base"


@lru_cache(maxsize=1)
def _get_nli_model():
    """
    Lazy singleton. Downloads on first call (~450 MB).
    Cached for the lifetime of the process.
    """
    try:
        from sentence_transformers import CrossEncoder
        model = CrossEncoder(NLI_MODEL_NAME)
        logger.info(f"NLI model loaded: {NLI_MODEL_NAME}")
        return model
    except Exception as e:
        logger.error(f"Failed to load NLI model: {e}")
        return None


def score_nli_grounding(reasoning: str, abstract: str) -> float | None:
    """
    Score whether the reasoning is entailed by the abstract.

    Uses cross-encoder NLI model. Returns entailment probability [0, 1].
    Returns None if model unavailable or inputs are empty.

    Labels order for cross-encoder/nli-deberta-v3-base:
    [contradiction=0, entailment=1, neutral=2]
    """
    if not reasoning or not abstract:
        return None

    model = _get_nli_model()
    if model is None:
        return None

    try:
        premise    = abstract[:1000]
        hypothesis = reasoning[:500]
        scores = model.predict(
            [(premise, hypothesis)],
            apply_softmax=True,
        )
        entailment_score = float(scores[0][1])
        return max(0.0, min(1.0, entailment_score))
    except Exception as e:
        logger.error(f"NLI grounding failed: {e}")
        return None


def score_nli_grounding_batch(
    pairs: list[tuple[str, str]]
) -> list[float | None]:
    """
    Batch version for efficiency when scoring multiple pairs.
    pairs: list of (reasoning, abstract) tuples
    """
    if not pairs:
        return []

    model = _get_nli_model()
    if model is None:
        return [None] * len(pairs)

    try:
        inputs = [
            (abstract[:1000], reasoning[:500])
            for reasoning, abstract in pairs
        ]
        scores = model.predict(inputs, apply_softmax=True)
        return [
            max(0.0, min(1.0, float(s[1])))
            for s in scores
        ]
    except Exception as e:
        logger.error(f"NLI batch grounding failed: {e}")
        return [None] * len(pairs)
