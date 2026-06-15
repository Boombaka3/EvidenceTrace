# EvidenceTrace -- Interview and Application Prep

## Project in one sentence

Multi-tenant NLP backend that extracts structured claims from biomedical research PDFs,
builds a cross-paper conflict graph, and detects contradictions using an RL-refined
reward model (consistency voting + faithfulness scoring).

---

## Backend interview anchors

### Q: Walk me through POST /api/evidence/jobs/{id}/dispatch/

A: The endpoint marks the job RUNNING and calls dispatch_analysis_job.delay(job_id).
   In the Celery task:
   1. A group of extract_claims.si(paper_id) tasks fires -- one per uploaded PDF.
   2. A chord callback (build_conflict_graph) fires when ALL extraction tasks complete.
   extract_claims calls llama-3.3-70b-instruct via NaviGator Toolkit (UF HiPerGator),
   parses structured claim JSON per section, stores Claim objects in PostgreSQL.
   build_conflict_graph generates all cross-paper claim pairs (O(n x m)),
   runs judge_conflict N times per pair (RL consistency voting),
   stores ConflictPair + RewardScore, marks job DONE.

### Q: How does multi-tenancy work at the database level?

A: django-tenants creates a separate PostgreSQL schema per tenant.
   The demo tenant's tables (evidence_analysisjob, evidence_paper, etc.)
   live in the demo schema, isolated from other tenants.
   The middleware reads the Host header on every request,
   looks up the tenant in the public.core_tenant table,
   and executes SET search_path = demo before any query.
   No row-level tenant_id filtering -- true schema isolation.
   Cross-tenant data access is impossible at the database level.

### Q: What is the RL component?

A: Level 1 RL: run the conflict judge N times on the same claim pair.
   Majority verdict wins. consistency_score = majority_count / N.
   A second LLM call audits claim faithfulness against the source sentence.
   faithfulness_score = how well the claim is grounded in the original text.
   final_confidence = 0.7 * consistency + 0.3 * faithfulness.
   This addresses the self-verification problem in LLM-as-judge:
   a single verdict has unknown reliability; N samples give a distribution.

### Q: How do you handle a model API failure mid-pipeline?

A: extract_claims and build_graph tasks catch all exceptions at the per-item level.
   A failed section extraction is logged and skipped; the task continues.
   A failed conflict pair judgment falls back to NEI verdict.
   Celery chord still fires build_conflict_graph after all extract_claims tasks complete,
   even if individual tasks had partial failures.
   AnalysisJob.status reflects the terminal state (DONE or FAILED).

### Q: Why NaviGator Toolkit?

A: NaviGator Toolkit is UF's OpenAI-compatible API running on HiPerGator.
   The OpenAICompatAdapter handles any OpenAI-compatible endpoint.
   Switching models is a one-line change: NAVIGATOR_MODEL=medgemma-27b-it.
   For biomedical domain tasks, medgemma-27b-it is locally available at zero cost.
   The adapter pattern makes the backend model-agnostic.

### Q: What does the Celery chord pattern buy you?

A: The chord pattern (group + callback) decouples extraction from graph building.
   All N extract_claims tasks run in parallel -- one per paper.
   build_conflict_graph fires exactly once, after all extractions complete.
   If one paper fails extraction, the chord still fires with partial claims.
   This is a proper fan-out/join pattern -- not polling or sleep loops.

### Q: How is the API authenticated?

A: Every protected endpoint requires X-API-Key in the request header.
   ApiKeyAuth (Django Ninja) looks up the key in the users.User table (public schema).
   Keys are auto-generated via secrets.token_urlsafe(32) on User.save().
   The demo admin key is printed by scripts/create_admin.py after first run.

---

## PhD application anchors

### Research contribution

EvidenceLens established baseline: 24.5% error rate, 5/5 conflict pairs detected.
EvidenceTrace extends it with:
1. Production-grade backend (Django 5, Celery, multi-tenant PostgreSQL)
2. RL reward scoring (N-sample consistency + faithfulness blend)
3. 10-type error taxonomy from EvidenceLens applied per claim
4. 4,960-record benchmark across SciFact, PubMedQA, QASPER

### Open problem addressed

Cross-paper claim conflict detection at scale.
LLM-as-judge has no independent verification layer.
Single verdicts have unknown reliability.
Consistency voting + faithfulness scoring provides calibrated confidence.

### Publishable roadmap

Level 2: DeBERTa NLI reward model fine-tuned on SciFact + FEVER-NLI
  -- acts as a verifiable secondary signal independent of the judge LLM
Level 3: RLVR fine-tuning on SciFact ground truth
  -- directly relevant to AVeriTeC 2025, SciClaimEval, CONFACT benchmarks

---

## API endpoints for live demo

```
POST /api/evidence/jobs/                   Create job (n_samples=3)
POST /api/evidence/jobs/{id}/papers/       Upload PDF (multipart/form-data)
POST /api/evidence/jobs/{id}/dispatch/     Start pipeline (Celery chord)
GET  /api/evidence/jobs/{id}/              Poll: claims_count grows, then conflicts_count
GET  /api/evidence/jobs/{id}/conflicts/    Conflict pairs with RL confidence scores
GET  /api/evidence/jobs/{id}/report/       Summary: contradictions, avg confidence
```

Swagger UI: http://localhost:8000/api/docs

---

## What to say about each conflict field

```
verdict:           CONTRADICTS/SUPPORTS/PARTIAL/NEI -- LLM majority vote
conflict_type:     direct/methodological/temporal/population/none
severity:          1-5 scale of disagreement magnitude
consistency_score: RL signal -- agreement across N independent judgments
faithfulness_score: claim is grounded in source sentence (0.0 to 1.0)
final_confidence:  0.7 * consistency + 0.3 * faithfulness
error_types:       EvidenceLens taxonomy applied per claim pair
```

Error types: overgeneralization, condition_dropping, false_certainty,
missing_evidence, unsupported_claim, wrong_evidence,
missing_limitation, contradiction_with_source,
conflict_ignored, paper_section_misread

---

## ASCII pipeline to draw on whiteboard

```
POST /api/evidence/jobs/{id}/dispatch/
  --> AnalysisJob.status = RUNNING
  --> dispatch_analysis_job.delay(job_id)      [Celery task]
      --> group([
            extract_claims.si(paper_1_id),
            extract_claims.si(paper_2_id),
            ...
          ])
          each extract_claims:
            - download PDF from MinIO
            - parse sections (pdfplumber)
            - LLM --> JSON claims per section
            - store Claim objects in PostgreSQL
      --> chord callback fires when all done:
          build_conflict_graph.si(job_id)
            - for each paper pair: O(n x m) claim pairs
            - compute_reward(claim_a, claim_b, n_samples=3):
                - judge_conflict x 3 (LLM-as-judge)
                - majority vote --> consistency_score
                - score_faithfulness x 2 (one per claim)
                - final_confidence = 0.7*consistency + 0.3*faithfulness
            - store ConflictPair + RewardScore
  --> AnalysisJob.status = DONE
```

---

## Key numbers for interviews

- 4,960 benchmark records (SciFact + PubMedQA + QASPER)
- 5 hand-curated cross-document conflict pairs (ground truth)
- 10-type error taxonomy (EvidenceLens)
- 24.5% baseline error rate (EvidenceLens 200-record study)
- 38 pytest tests (models, API, scoring, RL pipeline)
- Level 1 RL: majority vote over N samples, n=1/3/5 configurable
- final_confidence formula: 0.7 * consistency + 0.3 * faithfulness
