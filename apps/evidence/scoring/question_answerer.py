# apps/evidence/scoring/question_answerer.py
import os
import re
import json
import logging
from pathlib import Path
from apps.evidence.models import Paper, AnswerRecord
from apps.evidence.adapters.openai import OpenAICompatAdapter

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "question_answerer.txt"
PROMPT_TEMPLATE = PROMPT_PATH.read_text(encoding="utf-8")

VALID_ANSWERS = {"yes", "no", "maybe"}


def _get_adapter() -> OpenAICompatAdapter:
    model = os.environ.get("NAVIGATOR_MODEL", "llama-3.3-70b-instruct")
    return OpenAICompatAdapter(model_id=model)


def _clamp(v) -> float | None:
    if v is None:
        return None
    try:
        return max(0.0, min(1.0, float(v)))
    except (TypeError, ValueError):
        return None


def _extract_source_sentence(reasoning: str) -> str:
    """
    Heuristic: extract the most evidence-grounded sentence from reasoning.
    Look for sentences with quotation marks or specific citation patterns.
    """
    if not reasoning:
        return ""
    sentences = [s.strip() for s in reasoning.split('.') if len(s.strip()) > 20]
    for s in sentences:
        if '"' in s or 'abstract' in s.lower() or 'states' in s.lower():
            return s[:300]
    return sentences[0][:300] if sentences else ""


def _parse_response(raw: str) -> dict:
    """
    Parse <think>...</think><answer>yes|no|maybe</answer> format.
    Falls back to JSON parsing if tags not found (backward compat).
    """
    raw = raw.strip()

    # Extract <think> content
    think_match = re.search(
        r'<think>(.*?)</think>', raw, re.DOTALL | re.IGNORECASE
    )
    reasoning = think_match.group(1).strip() if think_match else ""

    # Extract <answer> content
    answer_match = re.search(
        r'<answer>\s*(yes|no|maybe)\s*</answer>',
        raw, re.IGNORECASE
    )

    if answer_match:
        answer = answer_match.group(1).lower().strip()
        format_ok = bool(think_match) and bool(answer_match)
        return {
            "answer": answer,
            "reasoning": reasoning,
            "source_sentence": _extract_source_sentence(reasoning),
            "confidence": None,
            "error_types": [],
            "format_ok": format_ok,
        }

    # Fallback: try JSON parsing (backward compat)
    try:
        stripped = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
        stripped = re.sub(r'```\s*$', '', stripped, flags=re.MULTILINE).strip()
        data = json.loads(stripped)
        answer = str(data.get("answer", "maybe")).lower().strip()
        if answer not in VALID_ANSWERS:
            answer = "maybe"
        return {
            "answer": answer,
            "reasoning": str(data.get("reasoning", ""))[:500],
            "source_sentence": str(data.get("source_sentence", ""))[:500],
            "confidence": _clamp(data.get("confidence")),
            "error_types": [e for e in data.get("error_types", [])
                            if isinstance(e, str)],
            "format_ok": False,  # JSON fallback = old format
        }
    except Exception:
        pass

    # Complete fallback
    return {
        "answer": "maybe",
        "reasoning": "parse error",
        "source_sentence": "",
        "confidence": None,
        "error_types": [],
        "format_ok": False,
    }


def answer_question(paper: Paper, question: str) -> AnswerRecord:
    """
    Ask a yes/no/maybe question about a paper using its abstract.
    Returns an unsaved AnswerRecord with _format_ok set as a non-model attribute.
    """
    abstract = paper.abstract or " ".join(
        paper.parsed_sections.get(k, "")
        for k in ("abstract", "body")
        if paper.parsed_sections.get(k)
    )
    prompt = (
        PROMPT_TEMPLATE
        .replace("{question}", question.strip())
        .replace("{abstract}", abstract[:3000])
    )
    try:
        adapter = _get_adapter()
        result = adapter.complete(
            system_prompt=(
                "You are a biomedical research question answerer. "
                "Use <think>...</think><answer>yes|no|maybe</answer> format."
            ),
            user_prompt=prompt,
            max_tokens=512,
        )
        if result.error:
            logger.error(f"Adapter error: {result.error}")
            parsed = _parse_response("")
        else:
            parsed = _parse_response(result.output or "")
    except Exception as e:
        logger.error(f"answer_question failed: {e}")
        parsed = _parse_response("")

    record = AnswerRecord(
        paper=paper,
        question=question.strip(),
        answer=parsed["answer"],
        reasoning=parsed["reasoning"],
        source_sentence=parsed["source_sentence"],
        error_types=parsed["error_types"],
    )
    # Attach format_ok as a non-model attribute for reward_voting
    record._format_ok = parsed.get("format_ok", False)
    return record


def answer_question_text(question: str,
                         abstract: str,
                         gold_label: str = "") -> dict:
    """
    Text-only version for benchmarking. No ORM objects created.
    Returns dict with answer, reasoning, source_sentence, confidence, error_types, format_ok.
    """
    prompt = (
        PROMPT_TEMPLATE
        .replace("{question}", question.strip())
        .replace("{abstract}", abstract[:3000])
    )
    try:
        adapter = _get_adapter()
        result = adapter.complete(
            system_prompt=(
                "You are a biomedical research question answerer. "
                "Use <think>...</think><answer>yes|no|maybe</answer> format."
            ),
            user_prompt=prompt,
            max_tokens=512,
        )
        parsed = _parse_response(result.output or "" if not result.error else "")
    except Exception as e:
        logger.error(f"answer_question_text failed: {e}")
        parsed = _parse_response("")
    parsed["format_ok"] = parsed.get("format_ok", False)
    return parsed
