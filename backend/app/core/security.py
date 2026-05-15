import secrets

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from cryptography.fernet import Fernet

from app.config import settings


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


def generate_invite_key(prefix: str = "SBR") -> str:
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ23456789"

    parts = []

    for _ in range(3):
        segment = "".join(secrets.choice(alphabet) for _ in range(4))
        parts.append(segment)
    
    return f"{prefix}-{'-'.join(parts)}"


fernet = Fernet(key=settings.FERNET_SECRET_KEY.encode())

def encrypt_invite_key(invite_key: str) -> str:
    encrypted = fernet.encrypt(data=invite_key.encode())

    return encrypted.decode()


def decrypt_invite_key(encrypted_invite_key: str) -> str:
    decrypted = fernet.decrypt(token=encrypted_invite_key.encode())

    return decrypted.decode()
