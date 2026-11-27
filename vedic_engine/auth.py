"""Clerk JWT authentication and webhook signature verification.

When Clerk / Supabase env vars (or VERCEL) are configured, protected routes require
a valid `Authorization: Bearer <clerk_session_jwt>` header verified via Clerk's JWKS.
When running locally with no auth/cloud env vars set, falls back to a local anonymous
user (`user_id="local"`) so offline single-user desktop runs keep working.
"""
from __future__ import annotations

import functools
import os
import pathlib
from dataclasses import dataclass, field
from typing import Any

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional fallback if not installed
    load_dotenv = None

_ROOT_ENV = pathlib.Path(__file__).resolve().parent.parent / ".env"
if load_dotenv and _ROOT_ENV.exists():
    load_dotenv(_ROOT_ENV, override=False)

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthUser:
    """Authenticated caller resolved from a verified Clerk JWT (or local offline mode)."""

    user_id: str
    token: str | None = None
    claims: dict[str, Any] = field(default_factory=dict)


def _norm_url(raw: str) -> str:
    val = raw.strip().rstrip("/")
    if val and not val.startswith(("http://", "https://")):
        val = f"https://{val}"
    return val


def clerk_issuer() -> str:
    return _norm_url(os.environ.get("CLERK_ISSUER", ""))


def clerk_jwks_url() -> str:
    explicit = os.environ.get("CLERK_JWKS_URL", "").strip()
    if explicit:
        return explicit if explicit.startswith(("http://", "https://")) else f"https://{explicit}"
    iss = clerk_issuer()
    return f"{iss}/.well-known/jwks.json" if iss else ""


def auth_enabled() -> bool:
    """True whenever Clerk/Supabase/Vercel is active unless explicitly disabled locally."""
    if os.environ.get("VERCEL"):
        return True
    explicit = os.environ.get("AUTH_REQUIRED", "").strip().lower()
    if explicit in ("0", "false", "no", "off"):
        return False
    if explicit in ("1", "true", "yes", "on"):
        return True
    return bool(
        clerk_jwks_url()
        or os.environ.get("SUPABASE_URL", "").strip()
    )


@functools.lru_cache(maxsize=4)
def _jwk_client(jwks_url: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(jwks_url, cache_jwk_set=True, lifespan=300)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def verify_clerk_token(token: str) -> AuthUser:
    """Verify a Clerk session JWT against JWKS and return an AuthUser."""
    jwks_url = clerk_jwks_url()
    if not jwks_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is enabled, but CLERK_ISSUER / CLERK_JWKS_URL is not configured.",
        )
    issuer = clerk_issuer()
    try:
        signing_key = _jwk_client(jwks_url).get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=issuer or None,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iss": bool(issuer),
                "verify_aud": False,
            },
        )
    except jwt.PyJWTError as exc:
        raise _unauthorized(f"Invalid or expired token: {exc}") from exc

    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub:
        raise _unauthorized("Token missing 'sub' claim")

    azp_raw = os.environ.get("CLERK_AUTHORIZED_PARTIES", "").strip()
    if azp_raw:
        allowed = {x.strip() for x in azp_raw.split(",") if x.strip()}
        azp = payload.get("azp")
        if azp not in allowed:
            raise _unauthorized("Token 'azp' is not an authorized party")

    return AuthUser(user_id=sub, token=token, claims=payload)


def require_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AuthUser:
    """FastAPI dependency that enforces authentication when auth is enabled."""
    if not auth_enabled():
        return AuthUser(user_id="local", token=None, claims={})
    if creds is None or creds.scheme.lower() != "bearer" or not creds.credentials:
        raise _unauthorized("Missing bearer token")
    return verify_clerk_token(creds.credentials)


def optional_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AuthUser | None:
    """Verify Bearer token if supplied; allow anonymous access otherwise."""
    if creds is None:
        return None if auth_enabled() else AuthUser(user_id="local", token=None, claims={})
    if creds.scheme.lower() != "bearer" or not creds.credentials:
        raise _unauthorized("Invalid authorization header")
    return verify_clerk_token(creds.credentials)


async def verify_clerk_webhook(request: Request) -> dict[str, Any]:
    """Verify Svix signature headers on an incoming Clerk webhook request."""
    secret = os.environ.get("CLERK_WEBHOOK_SECRET", "").strip()
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CLERK_WEBHOOK_SECRET is not configured.",
        )
    try:
        from svix.webhooks import Webhook, WebhookVerificationError
    except ImportError as exc:  # pragma: no cover
        raise HTTPException(status_code=503, detail="svix package not installed") from exc

    body = await request.body()
    headers = {k.lower(): v for k, v in request.headers.items()}
    try:
        payload = Webhook(secret).verify(body, headers)
    except WebhookVerificationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid webhook signature: {exc}") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unexpected webhook payload")
    return payload
