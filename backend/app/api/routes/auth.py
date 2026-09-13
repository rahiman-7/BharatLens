import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserRegisterRequest, UserLoginRequest, UserResponse, TokenResponse
from app.core.security import hash_password, verify_password, create_access_token
from app.api.deps import get_current_user

logger = logging.getLogger("bharatlens.api.auth")

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User",
)
def register(
    req: UserRegisterRequest,
    db: Session = Depends(get_db),
):
    """Register a new BharatLens user account.
    
    Zero-questionnaire onboarding: No category preference questionnaire during signup.
    """
    clean_email = req.email.strip().lower()
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == clean_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    # Securely hash password using Argon2/Bcrypt
    pw_hash = hash_password(req.password)

    new_user = User(
        email=clean_email,
        password_hash=pw_hash,
        created_at=utc_now(),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"Registered new user ID {new_user.id} ({new_user.email})")
    return new_user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User Login",
)
def login(
    req: UserLoginRequest,
    db: Session = Depends(get_db),
):
    """Authenticate user credentials and issue an RFC 7519 JWT access token."""
    clean_email = req.email.strip().lower()
    user = db.query(User).filter(User.email == clean_email).first()

    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Issue JWT token
    access_token = create_access_token(subject=user.id)
    logger.info(f"User ID {user.id} logged in successfully.")

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current Authenticated User",
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    """Retrieve profile metadata for the authenticated user session."""
    return current_user
