import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Union, Dict

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher

from app.core.config import settings

logger = logging.getLogger("bharatlens.security")

# Modern password hashing context with Argon2 primary and Bcrypt fallback
password_hash_context = PasswordHash((Argon2Hasher(), BcryptHasher()))


def hash_password(password: str) -> str:
    """Hash a plaintext password securely using Argon2/Bcrypt."""
    return password_hash_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored secure hash."""
    try:
        return password_hash_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Error during password verification: {e}")
        return False


def create_access_token(
    subject: Union[str, int],
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Create an RFC 7519 compliant JWT access token with user identifier and expiration."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)

    encoded_jwt = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT access token.
    
    Raises:
        jwt.ExpiredSignatureError: if token is expired.
        jwt.InvalidTokenError: if signature is invalid or token malformed.
    """
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
    return payload
