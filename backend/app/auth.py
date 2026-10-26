"""Demo login: one hard-coded user and stateless signed tokens (JWT).

Showcases the login flow only. A real system would keep users in a database with
hashed passwords. Env vars override the defaults so a deployment can change them.
"""

import hmac
import os
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas import LoginRequest, Token

DEMO_EMAIL = os.environ.get("DEMO_EMAIL", "trader@example.com")
DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD", "windpower2026")
# HS256 needs a secret of at least 32 bytes.
SECRET = os.environ.get("JWT_SECRET", "dev-only-secret-set-JWT_SECRET-in-production")
ALGORITHM = "HS256"
TOKEN_TTL = timedelta(hours=8)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=False)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(401, detail, headers={"WWW-Authenticate": "Bearer"})


@router.post("/login")
def login(body: LoginRequest) -> Token:
    # compare_digest takes the same time whether or not the strings match.
    email_ok = hmac.compare_digest(body.email.strip().lower(), DEMO_EMAIL)
    password_ok = hmac.compare_digest(body.password, DEMO_PASSWORD)
    if not (email_ok and password_ok):
        raise _unauthorized("Wrong email or password")
    expires_at = datetime.now(UTC) + TOKEN_TTL
    token = jwt.encode({"sub": DEMO_EMAIL, "exp": expires_at}, SECRET, algorithm=ALGORITHM)
    return Token(access_token=token, expires_at=expires_at)


def require_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> str:
    """Dependency guarding protected routes. Returns the logged-in user's email."""
    if credentials is None:
        raise _unauthorized("Not logged in")
    try:
        payload = jwt.decode(credentials.credentials, SECRET, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise _unauthorized("Session expired, please log in again") from None
    except jwt.InvalidTokenError:
        raise _unauthorized("Invalid token") from None
    return payload["sub"]
