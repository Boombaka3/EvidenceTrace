# llm_eval_harness/scripts/create_admin.py
"""
Idempotent admin + demo-tenant bootstrap.
Run after migrate_schemas --shared and seed.py.
"""
import os
import sys

import django
from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django_tenants.utils import schema_context  # noqa: E402


def main() -> None:
    password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
    if not password:
        print("ERROR: DJANGO_SUPERUSER_PASSWORD is not set.")
        sys.exit(1)

    username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
    email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@gauntlet.local")
    tenant_schema = os.environ.get("GAUNTLET_TENANT_SCHEMA", "demo")
    tenant_domain = os.environ.get("GAUNTLET_TENANT_DOMAIN", "demo.localhost")

    User = get_user_model()

    # ── Create or fetch superuser (lives in public schema) ────────────────────
    with schema_context("public"):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            user.set_password(password)
            user.save()
            print(f"Superuser '{username}' created.")
        else:
            print(f"Superuser '{username}' already exists.")

        api_key = user.api_key

    # ── Create demo tenant + domain if missing ────────────────────────────────
    with schema_context("public"):
        from apps.core.models import Domain, Tenant

        tenant, t_created = Tenant.objects.get_or_create(
            schema_name=tenant_schema,
            defaults={"name": "Demo Tenant"},
        )
        if t_created:
            print(f"Tenant '{tenant_schema}' created.")
        else:
            print(f"Tenant '{tenant_schema}' already exists.")

        _, d_created = Domain.objects.get_or_create(
            domain=tenant_domain,
            defaults={"tenant": tenant, "is_primary": True},
        )
        if d_created:
            print(f"Domain '{tenant_domain}' created.")
        else:
            print(f"Domain '{tenant_domain}' already exists.")

    print(f"Admin setup complete. API key: {api_key}")


if __name__ == "__main__":
    main()
