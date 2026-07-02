import logging
import os
import re
import time
import uuid
from pathlib import Path

from apps.evidence.adapters.openai import OpenAICompatAdapter
from apps.evidence.agent.tools import TOOL_REGISTRY
from apps.evidence.models import AgentTrace, AnalysisJob

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 5
PLANNER_PROMPT = (
    Path(__file__).parent.parent / "prompts" / "react_planner.txt"
).read_text(encoding="utf-8")


def _get_adapter() -> OpenAICompatAdapter:
    model = os.environ.get("NAVIGATOR_MODEL", "llama-3.3-70b-instruct")
    return OpenAICompatAdapter(model_id=model)


def _parse_action(text: str) -> tuple[str, list]:
    """
    Parse <action>tool_name(arg1, arg2)</action> from LLM output.
    Returns (tool_name, args_list) or ("", []) if not found.
    """
    match = re.search(
        r'<action>\s*(\w+)\(([^)]*)\)\s*</action>',
        text, re.IGNORECASE
    )
    if not match:
        return "", []
    tool_name = match.group(1).strip()
    raw_args = match.group(2).strip()
    args = [a.strip().strip('"\'') for a in raw_args.split(",") if a.strip()]
    return tool_name, args


def _parse_answer(text: str) -> tuple[str, float]:
    """
    Parse <answer confidence="X">yes|no|maybe</answer>.
    Returns (answer, confidence) or ("maybe", 0.5) if not found.
    """
    match = re.search(
        r'<answer(?:\s+confidence=["\']?([\d.]+)["\']?)?\s*>(yes|no|maybe)</answer>',
        text, re.IGNORECASE
    )
    if not match:
        return "maybe", 0.5
    confidence = float(match.group(1)) if match.group(1) else 0.5
    answer = match.group(2).lower()
    confidence = max(0.0, min(1.0, confidence))
    return answer, confidence


def _parse_thought(text: str) -> str:
    match = re.search(r'<thought>(.*?)</thought>', text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else text[:300]


def _parse_reasoning(text: str) -> str:
    match = re.search(r'<reasoning>(.*?)</reasoning>', text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _call_tool(tool_name: str, args: list, job_id: int) -> dict:
    """
    Dispatch a tool call. job_id is injected as first arg for retrieve tools.
    """
    tool_fn = TOOL_REGISTRY.get(tool_name)
    if not tool_fn:
        return {"error": f"unknown tool: {tool_name}"}

    if tool_name in ("retrieve_answers", "retrieve_claims"):
        return tool_fn(job_id)
    if tool_name == "nli_score" and len(args) >= 2:
        return tool_fn(args[0], args[1])
    return {"error": f"bad args for {tool_name}: {args}"}


def run_agent(job: AnalysisJob, question: str) -> dict:
    """
    Run bounded ReAct loop for a question over job evidence.
    Saves AgentTrace per step. Returns final answer dict.
    """
    session_id = str(uuid.uuid4())
    adapter = _get_adapter()
    model_name = os.environ.get("NAVIGATOR_MODEL", "llama-3.3-70b-instruct")
    conversation = []
    final_answer = "maybe"
    final_conf = 0.5
    final_reason = ""

    system_prompt = PLANNER_PROMPT.format(question=question)

    def _log(iteration: int, role: str, tool_name: str,
             tool_input: dict, tool_output: dict,
             latency_ms: int = 0, final: bool = False,
             answer: str = "", confidence: float = None):
        AgentTrace.objects.create(
            job=job,
            session_id=session_id,
            iteration=iteration,
            role=role,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            model_version=model_name,
            latency_ms=latency_ms,
            final_answer=answer if final else "",
            confidence=confidence if final else None,
        )

    for iteration in range(MAX_ITERATIONS):
        if iteration == 0:
            user_msg = f"Research question: {question}\n\nBegin reasoning."
        else:
            user_msg = "Continue reasoning based on the observation above."

        conversation.append({"role": "user", "content": user_msg})

        t0 = time.time()
        try:
            result = adapter.complete(
                system_prompt=system_prompt,
                user_prompt="\n".join(
                    f"{m['role'].upper()}: {m['content']}"
                    for m in conversation[-6:]
                ),
                max_tokens=1024,
            )
            llm_output = result.output or ""
            latency = int((time.time() - t0) * 1000)
        except Exception as e:
            logger.error(f"Agent LLM call failed at iter {iteration}: {e}")
            _log(iteration, AgentTrace.Role.ERROR, AgentTrace.ToolName.LLM,
                 {"question": question}, {"error": str(e)}, 0)
            break

        thought = _parse_thought(llm_output)
        conversation.append({"role": "assistant", "content": llm_output})

        if "<answer" in llm_output.lower():
            final_answer, final_conf = _parse_answer(llm_output)
            final_reason = _parse_reasoning(llm_output)
            _log(iteration, AgentTrace.Role.ANSWER, AgentTrace.ToolName.NONE,
                 {"question": question, "thought": thought},
                 {"answer": final_answer, "confidence": final_conf,
                  "reasoning": final_reason},
                 latency, final=True,
                 answer=final_answer, confidence=final_conf)
            break

        tool_name, args = _parse_action(llm_output)

        _log(iteration, AgentTrace.Role.THOUGHT, AgentTrace.ToolName.NONE,
             {"thought": thought}, {}, latency)

        if not tool_name:
            conversation.append({
                "role": "user",
                "content": "No action detected. Please provide your final <answer>."
            })
            continue

        _log(iteration, AgentTrace.Role.ACTION,
             tool_name, {"args": args}, {}, 0)

        t1 = time.time()
        observation = _call_tool(tool_name, args, job.id)
        tool_latency = int((time.time() - t1) * 1000)

        _log(iteration, AgentTrace.Role.OBSERVATION, tool_name,
             {"args": args}, observation, tool_latency)

        obs_text = str(observation)[:1000]
        conversation.append({
            "role": "user",
            "content": f"OBSERVATION from {tool_name}:\n{obs_text}"
        })

    else:
        _log(MAX_ITERATIONS, AgentTrace.Role.ANSWER, AgentTrace.ToolName.NONE,
             {"question": question},
             {"answer": "maybe", "confidence": 0.3,
              "reasoning": "Exceeded maximum iterations without reaching a conclusion."},
             0, final=True, answer="maybe", confidence=0.3)
        final_answer = "maybe"
        final_conf = 0.3
        final_reason = "Exceeded maximum iterations without reaching a conclusion."

    return {
        "session_id": session_id,
        "question": question,
        "answer": final_answer,
        "confidence": final_conf,
        "reasoning": final_reason,
        "iterations": len([
            t for t in AgentTrace.objects.filter(
                session_id=session_id, role=AgentTrace.Role.ACTION
            )
        ]),
        "model": model_name,
    }
