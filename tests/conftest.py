# tests/conftest.py
import pytest
from django_tenants.utils import schema_context

DEMO_SCHEMA = "demo"
DEMO_DOMAIN = "demo.localhost"


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Extends pytest-django's DB setup to create the demo tenant once per
    test session.  Uses django_db_blocker so the write is committed and
    visible to all subsequent tests.
    """
    with django_db_blocker.unblock():
        with schema_context("public"):
            from apps.core.models import Domain, Tenant

            tenant, _ = Tenant.objects.get_or_create(
                schema_name=DEMO_SCHEMA,
                defaults={"name": "Demo Tenant"},
            )
            Domain.objects.get_or_create(
                domain=DEMO_DOMAIN,
                tenant=tenant,
                defaults={"is_primary": True},
            )


@pytest.fixture
def tenant_schema(db):
    """
    Activate the demo tenant schema for the duration of one test.
    All ORM queries inside the test run against the 'demo' PostgreSQL schema.
    """
    with schema_context(DEMO_SCHEMA):
        yield DEMO_SCHEMA


@pytest.fixture
def client(tenant_schema):
    """
    Django test client pre-configured with the Host header and a test-user
    API key so all protected endpoints pass authentication.
    """
    from django.contrib.auth import get_user_model
    from django.test import Client

    with schema_context("public"):
        User = get_user_model()
        user, _ = User.objects.get_or_create(
            username="testuser",
            defaults={"email": "test@gauntlet.local", "is_active": True},
        )
        api_key = user.api_key

    return Client(HTTP_HOST=DEMO_DOMAIN, HTTP_X_API_KEY=api_key)
