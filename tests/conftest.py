"""Shared pytest isolation so a developer's local .env never affects offline tests."""
import pytest

AUTH_ENV_KEYS = (
    "AUTH_REQUIRED",
    "VERCEL",
    "CLERK_ISSUER",
    "CLERK_JWKS_URL",
    "CLERK_AUTHORIZED_PARTIES",
    "CLERK_SECRET_KEY",
    "CLERK_WEBHOOK_SECRET",
    "SUPABASE_URL",
    "SUPABASE_PUBLISHABLE_KEY",
    "SUPABASE_ANON_KEY",
    "SUPABASE_SECRET_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
)


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch):
    for key in AUTH_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
