# AI_LOG.md — Session Journal

Track what was AI-generated vs manually rewritten each session.

---

## Phase 1 — 2026-06-05

### AI-generated (unmodified)
- `pyproject.toml` — all dependencies, build config, tool settings
- `.env.example` — all required env vars with placeholders
- `docker-compose.yml` — app, postgres, redis, minio services with healthchecks
- `config/settings.py` — django-tenants config, SHARED_APPS/TENANT_APPS split, Celery, S3/MinIO, logging
- `config/urls.py` — NinjaAPI mount, evals router registration
- `config/celery.py` — Celery app init with autodiscover
- `config/wsgi.py` — standard WSGI application
- `apps/core/models.py` — Tenant, Domain (django-tenants mixins)
- `apps/core/admin.py` — TenantAdmin, DomainAdmin
- `apps/users/models.py` — custom User extending AbstractUser, email as USERNAME_FIELD
- `apps/evals/models.py` — EvalSuite, PromptCase, EvalRun, ModelRun, ScoreResult with full status choices
- `scripts/preflight.py` — DB, Redis, MinIO connectivity checks; exits 1 on failure
- `scripts/seed.py` — demo tenant + EvalSuite + 2 PromptCases
- `docs/AI_LOG.md` (this file)
- `docs/architecture.md`
- `docs/interview_prep.md`

### Manually rewritten
- None yet.

---

## Phase 2 — 2026-06-06

### AI-generated (scaffold — review before shipping)
- `apps/evals/models.py` — updated: added `baseline_run` FK to `EvalSuite`
- `apps/evals/schemas.py` — all Pydantic schemas (In/Out/Patch per resource)
- `apps/evals/router.py` — all 13 endpoints; `_get_or_404` helper; `SUPPORTED_MODELS` list
- `apps/evals/adapters/base.py` — `AdapterResult` dataclass, `ModelAdapter` ABC, `from_model_id` factory
- `apps/evals/adapters/anthropic.py` — Anthropic SDK, retry on 429, latency + token_count
- `apps/evals/adapters/openai.py` — OpenAI SDK, `OpenAICompatAdapter` subclass for Ollama/vLLM
- `apps/evals/adapters/gemini.py` — google-generativeai SDK, rate-limit detection via string matching + `ResourceExhausted`
- `apps/evals/scoring/exact_match.py` — difflib ratio ≥ 0.95
- `apps/evals/scoring/rubric.py` — Claude judge call, JSON parse, weighted overall (0–1)
- `apps/evals/scoring/llm_judge.py` — delegates to rubric; fallback single-criterion path
- `apps/evals/scoring/regression.py` — calls llm_judge, diffs against baseline ScoreResult
- `apps/evals/tasks/dispatch.py` — chord fan-out, schema_context propagation
- `apps/evals/tasks/run_model.py` — adapter call, S3 raw output upload, never raises
- `apps/evals/tasks/score.py` — per-mode dispatch, bulk_create, S3 report upload
- `apps/evals/prompts/judge_score.txt` — rubric scoring prompt with escaped JSON shape
- `apps/evals/prompts/judge_regression.txt` — regression comparison prompt
- `config/urls.py` — added health router

### Paths requiring manual review before production
- **Error handling in scoring** — `score_rubric` falls back to `overall=0.0` on any Claude API failure; verify this default is acceptable or surface it as a distinct error state.
- **S3 key construction** — `evals/{schema_name}/{eval_run_id}/{model_run_id}.txt` — confirm bucket policy allows worker IAM role writes.
- **Chord callback** — `score_all_results.si()` ignores `run_model` return values. If a Celery broker restart happens mid-chord, inflight tasks may replay; ensure idempotency (`bulk_create(ignore_conflicts=True)` covers ScoreResult).
- **Gemini rate-limit detection** — string-matching on exception message; replace with explicit `google.api_core.exceptions.ResourceExhausted` catch once confirmed the import is available in your environment.
- **`regression_threshold` default** — currently 0.3 (any drop > 0.3 fails). Tune per suite before enabling regression alerting.

### Manually rewritten
- None yet.

---

## Phase 1.5 -- 2026-06-06

Phase 1.5 -- bin/ restructure and tests/ scaffold. All .ps1 rewritten to fix string terminator bug.

- Moved `start_stack.ps1`, `stop_stack.ps1`, `dev.ps1` from project root into `bin/`
- Root cause of parse error: em dash in UTF-8 encodes as bytes E2 80 94; byte 0x94 is RIGHT DOUBLE QUOTATION MARK in Windows-1252 (PS5.1 default), terminating strings mid-line
- Fix: all strings in .ps1 files now use single quotes or concatenation; zero non-ASCII characters remain
- `$PSScriptRoot` in `bin/` scripts resolves to the `bin/` dir; `Split-Path $PSScriptRoot -Parent` reaches project root
- Created `tests/conftest.py` with `django_db_setup` (session-scoped), `tenant_schema`, and `client` fixtures
- Created `tests/evals/.gitkeep` placeholder

---

## Phase 2.5 -- 2026-06-06

Three runtime bug fixes (all confirmed by audit) + admin registration.

- `tasks/score.py`: `round(overall_avg, 4)` now guards against `None` when all judge calls fail
- `scoring/regression.py`: `delta = current - baseline` guarded against `None` on either side; passes with `delta=None` instead of crashing
- `apps/evals/models.py`: `ScoreResult.__str__` no longer crashes when `self.overall is None`
- `apps/evals/admin.py`: created; registers EvalSuite, PromptCase, EvalRun, ModelRun, ScoreResult

`manage.py check` and `scripts/preflight.py` both pass after these changes.

---
