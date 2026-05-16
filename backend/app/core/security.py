import secrets

from datetime import (
    datetime, 
    timedelta, 
    timezone
)

from jose import (
    JWTError, 
    jwt
)

from cryptography.fernet import Fernet

from app.config import settings


# Global Fernet instance for symmetric encryption.
# Uses a 128-bit AES key for encrypting sensitive data at rest.
fernet = Fernet(key=settings.FERNET_SECRET_KEY.encode())


def create_access_token(data: dict) -> str:
    """
    Generates a signed JWT access token for user authentication.

    The token includes a standard 'exp' (expiration) claim based on the 
    application settings.

    Args:
        data: The payload dictionary to encode (e.g., {"sub": user_id}).

    Returns:
        str: An encoded JWT string.
    """

    payload = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    payload.update({"exp": expire,})

    return jwt.encode(
        claims=payload,
        key=settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    """
    Decodes and validates a JWT access token.

    Verifies the signature using the configured secret and checks 
    if the token has expired.

    Args:
        token: The JWT string provided by the client.

    Returns:
        dict: The decoded payload.

    Raises:
        ValueError: If the token is malformed, has an invalid signature, or is expired.
    """

    try:
        return jwt.decode(
            token=token,
            key=settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )

    except JWTError as exception:
        # We wrap the library error to avoid leaking internal implementation details
        raise ValueError("Invalid or expired token") from exception


def generate_secure_token(length: int = 32) -> str:
    """
    Generates a cryptographically secure URL-safe string.

    Used for sensitive identifiers like password reset tokens or session IDs.

    Args:
        length: The number of bytes of randomness to use.
    """

    return secrets.token_urlsafe(length)


def generate_invite_key(prefix: str = "SBR") -> str:
    """
    Produces a human-readable but highly random invite key.

    Format: PREFIX-XXXX-XXXX-XXXX
    Uses a custom alphabet (excluding ambiguous characters like 0, O, 1, I) 
    to ensure high entropy and ease of typing.

    Args:
        prefix: A short string identifying the key type or organization.
    """

    # Excludes ambiguous characters for better UX
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ23456789"
    parts = []

    for _ in range(3):
        segment = "".join(secrets.choice(alphabet) for _ in range(4))
        parts.append(segment)
    
    return f"{prefix}-{'-'.join(parts)}"



def encrypt_invite_key(invite_key: str) -> str:
    """
    Encrypts an invite key using Fernet symmetric encryption.

    This ensures that keys stored in the database cannot be used 
    if the database is compromised, provided the application secret is safe.

    Args:
        invite_key: The plain text invite key.

    Returns:
        str: The encrypted, URL-safe base64 encoded string.
    """
    encrypted = fernet.encrypt(data=invite_key.encode())
    return encrypted.decode()


def decrypt_invite_key(encrypted_invite_key: str) -> str:
    """
    Decrypts an encrypted invite key back to plain text.

    Args:
        encrypted_invite_key: The encrypted string retrieved from storage.

    Returns:
        str: The original plain text invite key.
    """
    decrypted = fernet.decrypt(token=encrypted_invite_key.encode())
    return decrypted.decode()
