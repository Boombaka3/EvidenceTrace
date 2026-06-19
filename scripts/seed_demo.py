#!/usr/bin/env python
"""
Seed EvidenceTrace with 3 completed demo analysis jobs.
Uses real SciFact abstract text for credible biomedical content.
Safe to run multiple times (idempotent).

Usage: uv run python scripts/seed_demo.py
"""
import os
import sys
import django
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
from dotenv import load_dotenv
load_dotenv()
django.setup()

from django.utils import timezone
from django_tenants.utils import schema_context

DEMO_JOBS = [
    {
        "title": "Hypothalamic glutamate and energy regulation",
        "n_samples": 3,
        "papers": [
            {
                "title": "Glutamate mediates MC4R function in body weight regulation",
                "abstract": (
                    "The melanocortin receptor 4 (MC4R) is a well-established "
                    "mediator of body weight homeostasis. We conditionally restored "
                    "MC4R expression in Sim1 neurons in Mc4r-null mice. The "
                    "restoration dramatically reduced obesity. Glutamatergic "
                    "neurotransmission from PVH Sim1 neurons is required for "
                    "MC4R-mediated control of energy balance and body weight."
                ),
                "claims": [
                    {
                        "text": "Hypothalamic glutamate neurotransmission mediates energy balance.",
                        "claim_type": "causal",
                        "section": "results",
                        "source_sentence": (
                            "Glutamatergic neurotransmission from PVH Sim1 neurons "
                            "is required for MC4R-mediated control of energy balance."
                        ),
                        "confidence": 0.91,
                    },
                    {
                        "text": "MC4R restoration in Sim1 neurons reduces obesity in Mc4r-null mice.",
                        "claim_type": "causal",
                        "section": "results",
                        "source_sentence": (
                            "The restoration dramatically reduced obesity in Mc4r-null mice."
                        ),
                        "confidence": 0.95,
                    },
                ],
                "answers": [
                    {
                        "question": "Does the evidence support that hypothalamic glutamate neurotransmission mediates energy balance?",
                        "answer": "yes",
                        "reasoning": "The abstract states that glutamatergic neurotransmission from PVH Sim1 neurons is required for MC4R-mediated control of energy balance.",
                        "source_sentence": "Glutamatergic neurotransmission from PVH Sim1 neurons is required for MC4R-mediated control of energy balance.",
                        "error_types": [],
                        "consistency_score": 1.0,
                        "faithfulness_score": 0.91,
                        "final_confidence": 0.97,
                        "n_samples": 3,
                    },
                    {
                        "question": "Does the evidence support that MC4R restoration in Sim1 neurons reduces obesity?",
                        "answer": "yes",
                        "reasoning": "The abstract explicitly states the restoration dramatically reduced obesity in Mc4r-null mice.",
                        "source_sentence": "The restoration dramatically reduced obesity in Mc4r-null mice.",
                        "error_types": [],
                        "consistency_score": 1.0,
                        "faithfulness_score": 0.95,
                        "final_confidence": 0.98,
                        "n_samples": 3,
                    },
                ],
            },
            {
                "title": "VMH glutamate release prevents hypoglycemia",
                "abstract": (
                    "Ventromedial hypothalamic (VMH) neurons are predominantly "
                    "glutamatergic and express VGLUT2. To evaluate the role of "
                    "glutamate release from VMH neurons, we generated mice lacking "
                    "VGLUT2 selectively in SF1 neurons. These mice showed impaired "
                    "counterregulatory responses to hypoglycemia, demonstrating that "
                    "VMH glutamate release is part of the neurocircuitry that prevents "
                    "hypoglycemia."
                ),
                "claims": [
                    {
                        "text": "VMH glutamate release is required for counterregulatory responses to hypoglycemia.",
                        "claim_type": "causal",
                        "section": "results",
                        "source_sentence": (
                            "VMH glutamate release is part of the neurocircuitry "
                            "that prevents hypoglycemia."
                        ),
                        "confidence": 0.88,
                    },
                    {
                        "text": "Hypothalamic glutamate neurotransmission serves multiple distinct physiological roles.",
                        "claim_type": "descriptive",
                        "section": "discussion",
                        "source_sentence": (
                            "VMH neurons are predominantly glutamatergic and express VGLUT2."
                        ),
                        "confidence": 0.72,
                    },
                ],
                "answers": [
                    {
                        "question": "Does the evidence support that VMH glutamate release prevents hypoglycemia?",
                        "answer": "yes",
                        "reasoning": "The abstract demonstrates that mice lacking VGLUT2 in SF1 neurons showed impaired counterregulatory responses, confirming VMH glutamate release is necessary.",
                        "source_sentence": "VMH glutamate release is part of the neurocircuitry that prevents hypoglycemia.",
                        "error_types": [],
                        "consistency_score": 1.0,
                        "faithfulness_score": 0.93,
                        "final_confidence": 0.98,
                        "n_samples": 3,
                    },
                    {
                        "question": "Does the evidence support that hypothalamic glutamate serves multiple distinct physiological roles?",
                        "answer": "maybe",
                        "reasoning": "The abstract confirms a role in hypoglycemia prevention but does not explicitly claim multiple distinct roles.",
                        "source_sentence": "VMH neurons are predominantly glutamatergic and express VGLUT2.",
                        "error_types": ["overgeneralization"],
                        "consistency_score": 0.67,
                        "faithfulness_score": 0.71,
                        "final_confidence": 0.68,
                        "n_samples": 3,
                    },
                ],
            },
        ],
    },
    {
        "title": "HPV screening vs conventional cytology",
        "n_samples": 3,
        "papers": [
            {
                "title": "HPV and Pap co-testing in cervical cancer screening",
                "abstract": (
                    "We evaluated HPV testing combined with conventional cytology "
                    "for cervical cancer screening. HPV co-testing identified "
                    "significantly more CIN2+ lesions at baseline compared to "
                    "cytology alone. At 5-year follow-up, women with negative "
                    "co-test results had fewer incident lesions than those with "
                    "negative cytology results alone, supporting co-testing as "
                    "the preferred primary screening strategy."
                ),
                "claims": [
                    {
                        "text": "HPV co-testing detects more CIN2+ lesions than cytology alone.",
                        "claim_type": "comparative",
                        "section": "results",
                        "source_sentence": (
                            "HPV co-testing identified significantly more CIN2+ "
                            "lesions at baseline compared to cytology alone."
                        ),
                        "confidence": 0.93,
                    },
                    {
                        "text": "Co-testing provides superior long-term protection against cervical lesions.",
                        "claim_type": "comparative",
                        "section": "conclusion",
                        "source_sentence": (
                            "Women with negative co-test results had fewer incident "
                            "lesions than those with negative cytology results alone."
                        ),
                        "confidence": 0.85,
                    },
                ],
                "answers": [
                    {
                        "question": "Does the evidence support that HPV co-testing detects more CIN2+ lesions than cytology alone?",
                        "answer": "yes",
                        "reasoning": "The abstract explicitly states HPV co-testing identified significantly more CIN2+ lesions at baseline.",
                        "source_sentence": "HPV co-testing identified significantly more CIN2+ lesions at baseline compared to cytology alone.",
                        "error_types": [],
                        "consistency_score": 1.0,
                        "faithfulness_score": 0.94,
                        "final_confidence": 0.98,
                        "n_samples": 3,
                    },
                    {
                        "question": "Does the evidence support that co-testing provides superior long-term protection?",
                        "answer": "yes",
                        "reasoning": "The 5-year follow-up data shows fewer incident lesions in the co-test group.",
                        "source_sentence": "Women with negative co-test results had fewer incident lesions than those with negative cytology results alone.",
                        "error_types": [],
                        "consistency_score": 1.0,
                        "faithfulness_score": 0.87,
                        "final_confidence": 0.96,
                        "n_samples": 3,
                    },
                ],
            },
            {
                "title": "HPV primary screening without cytology triage",
                "abstract": (
                    "Primary HPV screening without routine cytology triage was "
                    "evaluated in a large randomized trial. HPV-only screening "
                    "detected CIN3+ with sensitivity equivalent to co-testing "
                    "while reducing unnecessary colposcopies. Addition of cytology "
                    "to HPV testing did not significantly improve detection of "
                    "high-grade lesions and increased false-positive rates, "
                    "suggesting cytology adds limited value to HPV-based screening."
                ),
                "claims": [
                    {
                        "text": "Adding cytology to HPV testing does not significantly improve CIN3+ detection.",
                        "claim_type": "comparative",
                        "section": "results",
                        "source_sentence": (
                            "Addition of cytology to HPV testing did not significantly "
                            "improve detection of high-grade lesions."
                        ),
                        "confidence": 0.89,
                    },
                    {
                        "text": "HPV-only screening reduces unnecessary colposcopies.",
                        "claim_type": "comparative",
                        "section": "results",
                        "source_sentence": (
                            "HPV-only screening detected CIN3+ with sensitivity "
                            "equivalent to co-testing while reducing unnecessary colposcopies."
                        ),
                        "confidence": 0.91,
                    },
                ],
                "answers": [
                    {
                        "question": "Does the evidence support that adding cytology to HPV testing does not improve detection?",
                        "answer": "yes",
                        "reasoning": "The abstract states addition of cytology did not significantly improve detection and increased false-positive rates.",
                        "source_sentence": "Addition of cytology to HPV testing did not significantly improve detection of high-grade lesions.",
                        "error_types": [],
                        "consistency_score": 1.0,
                        "faithfulness_score": 0.92,
                        "final_confidence": 0.98,
                        "n_samples": 3,
                    },
                    {
                        "question": "Does the evidence support that HPV-only screening is sufficient without cytology?",
                        "answer": "yes",
                        "reasoning": "The abstract concludes cytology adds limited value and HPV-only achieves equivalent sensitivity with fewer colposcopies.",
                        "source_sentence": "Cytology adds limited value to HPV-based screening.",
                        "error_types": [],
                        "consistency_score": 0.67,
                        "faithfulness_score": 0.83,
                        "final_confidence": 0.72,
                        "n_samples": 3,
                    },
                ],
            },
        ],
    },
    {
        "title": "IFN-gamma in autoimmune myocarditis",
        "n_samples": 3,
        "papers": [
            {
                "title": "IFN-gamma receptor deficiency causes severe myocarditis",
                "abstract": (
                    "Mice lacking the IFN-gamma receptor develop severe and "
                    "persistent experimental autoimmune myocarditis (EAM) compared "
                    "to wild-type controls. Histological analysis revealed extensive "
                    "myocardial inflammation and fibrosis persisting beyond the "
                    "acute phase. These findings suggest IFN-gamma signaling "
                    "provides a protective role in limiting cardiac inflammation "
                    "during autoimmune myocarditis."
                ),
                "claims": [
                    {
                        "text": "IFN-gamma receptor signaling limits cardiac inflammation in autoimmune myocarditis.",
                        "claim_type": "causal",
                        "section": "results",
                        "source_sentence": (
                            "IFN-gamma signaling provides a protective role in "
                            "limiting cardiac inflammation during autoimmune myocarditis."
                        ),
                        "confidence": 0.87,
                    },
                    {
                        "text": "IFN-gamma receptor deficiency leads to persistent myocardial fibrosis.",
                        "claim_type": "factual",
                        "section": "results",
                        "source_sentence": (
                            "Histological analysis revealed extensive myocardial "
                            "inflammation and fibrosis persisting beyond the acute phase."
                        ),
                        "confidence": 0.92,
                    },
                ],
                "answers": [
                    {
                        "question": "Does the evidence support that IFN-gamma receptor signaling limits cardiac inflammation?",
                        "answer": "yes",
                        "reasoning": "The abstract directly states IFN-gamma signaling provides a protective role in limiting cardiac inflammation.",
                        "source_sentence": "IFN-gamma signaling provides a protective role in limiting cardiac inflammation during autoimmune myocarditis.",
                        "error_types": [],
                        "consistency_score": 1.0,
                        "faithfulness_score": 0.93,
                        "final_confidence": 0.98,
                        "n_samples": 3,
                    },
                    {
                        "question": "Does the evidence support that IFN-gamma deficiency causes persistent myocardial fibrosis?",
                        "answer": "yes",
                        "reasoning": "Histological analysis confirmed extensive myocardial inflammation and fibrosis persisting beyond the acute phase in receptor-deficient mice.",
                        "source_sentence": "Histological analysis revealed extensive myocardial inflammation and fibrosis persisting beyond the acute phase.",
                        "error_types": [],
                        "consistency_score": 1.0,
                        "faithfulness_score": 0.91,
                        "final_confidence": 0.97,
                        "n_samples": 3,
                    },
                ],
            },
            {
                "title": "Recombinant IFN-gamma suppresses experimental myocarditis",
                "abstract": (
                    "IFN-gamma deficient mice develop more severe EAM than "
                    "wild-type controls. Administration of recombinant IFN-gamma "
                    "to IFN-gamma deficient mice significantly suppressed myocarditis "
                    "severity. IFN-gamma treatment reduced CD4+ T cell infiltration "
                    "and inflammatory cytokine production in cardiac tissue, "
                    "demonstrating a direct anti-inflammatory role for IFN-gamma "
                    "in autoimmune cardiac disease."
                ),
                "claims": [
                    {
                        "text": "Recombinant IFN-gamma directly suppresses autoimmune myocarditis severity.",
                        "claim_type": "causal",
                        "section": "results",
                        "source_sentence": (
                            "Administration of recombinant IFN-gamma to IFN-gamma "
                            "deficient mice significantly suppressed myocarditis severity."
                        ),
                        "confidence": 0.94,
                    },
                    {
                        "text": "IFN-gamma reduces CD4+ T cell infiltration in cardiac tissue.",
                        "claim_type": "factual",
                        "section": "results",
                        "source_sentence": (
                            "IFN-gamma treatment reduced CD4+ T cell infiltration "
                            "and inflammatory cytokine production in cardiac tissue."
                        ),
                        "confidence": 0.90,
                    },
                ],
                "answers": [
                    {
                        "question": "Does the evidence support that recombinant IFN-gamma suppresses myocarditis?",
                        "answer": "yes",
                        "reasoning": "The abstract states recombinant IFN-gamma administration significantly suppressed myocarditis severity in deficient mice.",
                        "source_sentence": "Administration of recombinant IFN-gamma to IFN-gamma deficient mice significantly suppressed myocarditis severity.",
                        "error_types": [],
                        "consistency_score": 1.0,
                        "faithfulness_score": 0.94,
                        "final_confidence": 0.98,
                        "n_samples": 3,
                    },
                    {
                        "question": "Does the evidence support that IFN-gamma reduces T cell infiltration in cardiac tissue?",
                        "answer": "yes",
                        "reasoning": "The abstract explicitly states IFN-gamma treatment reduced CD4+ T cell infiltration and inflammatory cytokine production.",
                        "source_sentence": "IFN-gamma treatment reduced CD4+ T cell infiltration and inflammatory cytokine production in cardiac tissue.",
                        "error_types": [],
                        "consistency_score": 1.0,
                        "faithfulness_score": 0.96,
                        "final_confidence": 0.99,
                        "n_samples": 3,
                    },
                ],
            },
        ],
    },
]


def seed_demo_data():
    from apps.evidence.models import (
        AnalysisJob, Paper, Claim, AnswerRecord, RewardScore
    )

    print("Seeding demo data...")
    created = 0

    for job_data in DEMO_JOBS:
        with schema_context("demo"):
            if AnalysisJob.objects.filter(
                result_s3_key=f"demo/{job_data['title'][:40]}"
            ).exists():
                print(f"  Already exists: {job_data['title'][:50]}")
                continue

            job = AnalysisJob.objects.create(
                status=AnalysisJob.Status.DONE,
                n_samples=job_data["n_samples"],
                result_s3_key=f"demo/{job_data['title'][:40]}",
                started_at=timezone.now(),
                finished_at=timezone.now(),
            )

            for p_idx, paper_data in enumerate(job_data["papers"]):
                paper = Paper.objects.create(
                    job=job,
                    title=paper_data["title"],
                    abstract=paper_data["abstract"],
                    s3_key=f"demo/job_{job.id}/paper_{p_idx}.pdf",
                    parsed_sections={"abstract": paper_data["abstract"]},
                )

                for claim_data in paper_data["claims"]:
                    Claim.objects.create(
                        paper=paper,
                        text=claim_data["text"],
                        claim_type=claim_data["claim_type"],
                        section=claim_data["section"],
                        source_sentence=claim_data["source_sentence"],
                        confidence=claim_data["confidence"],
                        entities=[],
                    )

                for ans_data in paper_data["answers"]:
                    ar = AnswerRecord.objects.create(
                        paper=paper,
                        question=ans_data["question"],
                        answer=ans_data["answer"],
                        reasoning=ans_data["reasoning"],
                        source_sentence=ans_data["source_sentence"],
                        error_types=ans_data["error_types"],
                    )
                    RewardScore.objects.create(
                        answer_record=ar,
                        consistency_score=ans_data["consistency_score"],
                        faithfulness_score=ans_data["faithfulness_score"],
                        final_confidence=ans_data["final_confidence"],
                        n_samples=ans_data["n_samples"],
                    )

            paper_count  = len(job_data["papers"])
            claim_count  = sum(len(p["claims"])  for p in job_data["papers"])
            answer_count = sum(len(p["answers"]) for p in job_data["papers"])
            print(f"  Created: {job_data['title'][:50]}")
            print(f"    Papers:{paper_count} Claims:{claim_count} Answers:{answer_count}")
            created += 1

    print(f"\nSeed complete. Created {created} new jobs.")


def verify():
    from apps.evidence.models import AnalysisJob, AnswerRecord, RewardScore
    with schema_context("demo"):
        jobs    = AnalysisJob.objects.filter(status="DONE")
        answers = AnswerRecord.objects.all()
        rewards = RewardScore.objects.all()
        print(f"\nDatabase after seed:")
        print(f"  DONE jobs:     {jobs.count()}")
        print(f"  AnswerRecords: {answers.count()}")
        print(f"  RewardScores:  {rewards.count()}")
        for job in jobs:
            a_count = AnswerRecord.objects.filter(paper__job=job).count()
            print(f"  Job {job.id}: {job.papers.count()} papers, "
                  f"{a_count} answers -- {job.result_s3_key[:40]}")


if __name__ == "__main__":
    seed_demo_data()
    verify()
