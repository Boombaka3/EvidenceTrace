#!/usr/bin/env python
"""
Seed EvidenceTrace demo data.
Creates demo tenant, domains, and verifies schema health.
Run after: uv run python manage.py migrate_schemas
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from dotenv import load_dotenv
load_dotenv()

import django
django.setup()


def seed_tenant():
    from apps.core.models import Tenant, Domain
    tenant, created = Tenant.objects.get_or_create(
        schema_name="demo",
        defaults={"name": "Demo Organization"}
    )
    if created:
        print("Created tenant: demo")
    else:
        print("Tenant demo: already exists")

    for domain_name in ["demo.localhost", "localhost", "127.0.0.1"]:
        domain, created = Domain.objects.get_or_create(
            domain=domain_name,
            defaults={"tenant": tenant, "is_primary": domain_name == "demo.localhost"}
        )
        if created:
            print(f"  Created domain: {domain_name}")
        else:
            print(f"  Domain {domain_name}: already exists")

    return tenant


def verify_evidence_schema():
    from django_tenants.utils import schema_context
    with schema_context("demo"):
        from apps.evidence.models import AnalysisJob, AnswerRecord, Claim, Paper, RewardScore
        counts = {
            "AnalysisJob":  AnalysisJob.objects.count(),
            "Paper":        Paper.objects.count(),
            "Claim":        Claim.objects.count(),
            "AnswerRecord": AnswerRecord.objects.count(),
            "RewardScore":  RewardScore.objects.count(),
        }
        for model, count in counts.items():
            print(f"  {model}: {count} records")


def main():
    print("=== EvidenceTrace seed ===")
    seed_tenant()
    print("\nEvidence schema:")
    verify_evidence_schema()
    print("\nSeed complete.")
    print("Next steps:")
    print("  uv run python scripts/create_admin.py")
    print("  uv run python scripts/smoke_test.py")


if __name__ == "__main__":
    main()
