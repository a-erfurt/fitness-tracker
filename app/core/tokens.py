from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings
from typing import Any
from jwt import ExpiredSignatureError, InvalidTokenError


def create_access_token(subject: str) -> str:
    expire = datetime.now(tz=timezone.utc) + timedelta(
        minutes=settings.access_token_exp_minutes
    )

    payload = {
        "sub": subject,
        "exp": expire,
        "type": "access",
    }

    token = jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    return token

def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != "access":
            raise InvalidTokenError("Invalid token type")
        return payload
    except ExpiredSignatureError as exc:
        raise InvalidTokenError("Token expired") from exc