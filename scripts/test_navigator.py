# scripts/test_navigator.py
"""
Quick connection test for the UF NaviGator Toolkit (OpenAI-compatible API).

Sends a minimal conflict-detection prompt and verifies the adapter returns
a parseable JSON verdict. Exit 0 on PASS, 1 on FAIL.

Usage:
  uv run python scripts/test_navigator.py
"""
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

api_key = os.environ.get("OPENAI_API_KEY", "")
if not api_key or api_key in ("<your-navigator-api-key>", "placeholder", ""):
    print("FAIL: OPENAI_API_KEY not set — add your NaviGator key to .env")
    sys.exit(1)

base_url = os.environ.get("OPENAI_COMPAT_BASE_URL", "https://api.ai.it.ufl.edu/v1")
model = os.environ.get("NAVIGATOR_MODEL", "llama-3.3-70b-instruct")

print(f"NaviGator connection test")
print(f"  base_url : {base_url}")
print(f"  model    : {model}")
print()

import django
django.setup()

from apps.evidence.adapters.openai import OpenAICompatAdapter

adapter = OpenAICompatAdapter(model_id=model)

TEST_PROMPT = """\
Paper A (Mouse Study): Drug X reduces tumor size by 40 percent in mouse models.
Paper B (Clinical Trial): Drug X shows no significant effect on tumor size in clinical trials.

Return ONLY valid JSON:
{"verdict": "SUPPORTS|CONTRADICTS|NEI", "conflict_type": "population|methodology|measurement|outcome|none", "severity": 1, "reasoning": "one sentence", "error_types": []}"""

result = adapter.complete(
    system_prompt="You are a scientific conflict detection expert. Return only valid JSON.",
    user_prompt=TEST_PROMPT,
    max_tokens=256,
)

if result.error:
    print(f"FAIL: adapter returned error: {result.error}")
    sys.exit(1)

print(f"Raw output ({result.latency_ms}ms):")
print(f"  {result.output[:300]}")
print()

try:
    data = json.loads(result.output.strip())
    verdict = data.get("verdict", "")
    if verdict not in ("SUPPORTS", "CONTRADICTS", "NEI"):
        print(f"FAIL: unexpected verdict value '{verdict}'")
        sys.exit(1)
    print(f"PASS  verdict={verdict}  latency={result.latency_ms}ms")
    if result.token_count:
        print(f"      tokens={result.token_count}")
except json.JSONDecodeError as e:
    print(f"FAIL: could not parse JSON response: {e}")
    print(f"      raw output: {result.output!r}")
    sys.exit(1)
