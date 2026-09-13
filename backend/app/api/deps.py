import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.core.security import decode_access_token

logger = logging.getLogger("bharatlens.auth")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=True)
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """Validate Bearer JWT token and return the authenticated User instance."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or session has expired.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except (jwt.PyJWTError, ValueError) as e:
        logger.warning(f"JWT validation failed: {e}")
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        logger.warning(f"Authenticated user ID {user_id} not found in database.")
        raise credentials_exception

    return user


def get_current_user_optional(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme_optional),
) -> Optional[User]:
    """Optional authentication dependency: returns User if token valid, otherwise None."""
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        user_id_str = payload.get("sub")
        if user_id_str is None:
            return None
        return db.query(User).filter(User.id == int(user_id_str)).first()
    except Exception:
        return None
