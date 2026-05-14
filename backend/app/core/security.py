from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt
import secrets

from app.config import settings

password_hasher = PasswordHasher()


def hash_value(value: str) -> str:
    """
    Hashes sensitive values using Argon2id.
    """

    return password_hasher.hash(value)


def verify_hash(value: str, hashed_value: str) -> bool:
    """
    Verifies Argon2id hash.
    """

    try:
        return password_hasher.verify(
            hashed_value,
            value,
        )

    except VerifyMismatchError:
        return False


def create_access_token(data: dict) -> str:
    """
    Creates JWT access token.
    """

    payload = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    payload.update(
        {
            "exp": expire,
        }
    )

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    """
    Decodes JWT token.
    """

    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )

    except JWTError as exception:
        raise ValueError("Invalid or expired token") from exception


def generate_secure_token(length: int = 32) -> str:
    """
    Generates cryptographically secure token.
    """

    return secrets.token_urlsafe(length)