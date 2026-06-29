"""Password hashing and JWT token utilities."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

ALGORITHM = "HS256"

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenType(str, Enum):
    ACCESS = "access"
    RESET = "reset"


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def create_token(
    subject: str,
    token_type: TokenType = TokenType.ACCESS,
    expires_delta: timedelta | None = None,
) -> str:
    if expires_delta is None:
        minutes = (
            settings.access_token_expire_minutes
            if token_type == TokenType.ACCESS
            else 30
        )
        expires_delta = timedelta(minutes=minutes)
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type.value,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str, expected_type: TokenType = TokenType.ACCESS) -> str:
    """Return the subject (user id) if the token is valid and of the right type.

    Raises ValueError on any problem.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError as exc:  # invalid signature / expired
        raise ValueError("invalid token") from exc

    if payload.get("type") != expected_type.value:
        raise ValueError("wrong token type")
    subject = payload.get("sub")
    if not subject:
        raise ValueError("missing subject")
    return subject
