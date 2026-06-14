# apps/evidence/adapters/openai.py
import logging
import os
import time

from apps.evidence.adapters.base import AdapterResult, ModelAdapter

logger = logging.getLogger(__name__)


class OpenAICompatAdapter(ModelAdapter):
    """OpenAI-compatible adapter. Works with NaviGator Toolkit, Ollama, vLLM, etc."""

    def __init__(self, model_id: str | None = None) -> None:
        import openai as _openai
        self._openai = _openai
        self.model_id = model_id or os.environ.get("NAVIGATOR_MODEL", "llama-3.3-70b-instruct")
        base_url = os.environ.get("OPENAI_COMPAT_BASE_URL", "https://api.ai.it.ufl.edu/v1")
        api_key = os.environ.get("OPENAI_API_KEY", "")
        self._client = _openai.OpenAI(base_url=base_url, api_key=api_key)

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1024,
        timeout: int = 60,
    ) -> AdapterResult:
        for attempt in range(2):
            try:
                start = time.monotonic()
                response = self._client.chat.completions.create(
                    model=self.model_id,
                    max_tokens=max_tokens,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    timeout=timeout,
                )
                latency_ms = int((time.monotonic() - start) * 1000)
                output = ""
                if response.choices:
                    output = response.choices[0].message.content or ""
                token_count = None
                if response.usage:
                    token_count = response.usage.prompt_tokens + response.usage.completion_tokens
                return AdapterResult(output=output, latency_ms=latency_ms, token_count=token_count)

            except self._openai.RateLimitError:
                if attempt == 0:
                    logger.warning("NaviGator rate limit on %s, retrying after 2s", self.model_id)
                    time.sleep(2)
                    continue
                return AdapterResult(output="", latency_ms=0, error="NaviGator rate limit exceeded after retry")
            except Exception as exc:
                logger.error("OpenAICompatAdapter.complete failed [%s]: %s", self.model_id, exc)
                return AdapterResult(output="", latency_ms=0, error=str(exc))

        return AdapterResult(output="", latency_ms=0, error="Unknown error in OpenAICompatAdapter")
