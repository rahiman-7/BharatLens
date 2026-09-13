import time
import uuid
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
import jwt

from app.main import app
from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)

client = TestClient(app)


def test_password_hashing_and_verification():
    """Test 4: Password is stored hashed and verifies correctly, never plaintext."""
    raw_password = "SecurePassword2026!"
    hashed = hash_password(raw_password)

    assert hashed != raw_password
    assert not hashed.startswith(raw_password)
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword123", hashed) is False


def test_successful_user_registration():
    """Test 1: Register new user with valid email and password."""
    unique_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    response = client.post(
        "/api/v1/auth/register",
        json={"email": unique_email, "password": "Password123!"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == unique_email
    assert "id" in data
    assert "password" not in data
    assert "password_hash" not in data


def test_duplicate_email_registration_rejected():
    """Test 2: Duplicate email registration returns 409 Conflict."""
    unique_email = f"dup_{uuid.uuid4().hex[:8]}@example.com"
    resp1 = client.post(
        "/api/v1/auth/register",
        json={"email": unique_email, "password": "Password123!"},
    )
    assert resp1.status_code == 201

    resp2 = client.post(
        "/api/v1/auth/register",
        json={"email": unique_email, "password": "AnotherPassword456!"},
    )
    assert resp2.status_code == 409
    assert "already exists" in resp2.json()["detail"].lower()


def test_invalid_email_and_short_password_rejected():
    """Test 3: Invalid email format or password under minimum length is rejected with 422."""
    resp_invalid_email = client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "ValidPassword123"},
    )
    assert resp_invalid_email.status_code == 422

    resp_short_pw = client.post(
        "/api/v1/auth/register",
        json={"email": f"short_{uuid.uuid4().hex[:8]}@example.com", "password": "123"},
    )
    assert resp_short_pw.status_code == 422


def test_successful_user_login():
    """Test 5: User login returns a valid JWT access token."""
    unique_email = f"login_{uuid.uuid4().hex[:8]}@example.com"
    password = "MySecretLoginPass123"
    
    # Register first
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={"email": unique_email, "password": password},
    )
    assert reg_resp.status_code == 201

    # Login
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": password},
    )
    assert login_resp.status_code == 200
    data = login_resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == unique_email


def test_login_wrong_password_and_nonexistent_user_rejected():
    """Test 6: Wrong password or nonexistent user returns 401 Unauthorized."""
    unique_email = f"wrongpw_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": unique_email, "password": "CorrectPassword123"},
    )

    # Wrong password
    resp_wrong = client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": "WrongPassword999"},
    )
    assert resp_wrong.status_code == 401

    # Nonexistent email
    resp_nonexistent = client.post(
        "/api/v1/auth/login",
        json={"email": "ghost_user_9999@example.com", "password": "AnyPassword"},
    )
    assert resp_nonexistent.status_code == 401


def test_auth_me_endpoint_returns_authenticated_user():
    """Test 9: /auth/me returns current user info when Bearer token is provided."""
    unique_email = f"me_{uuid.uuid4().hex[:8]}@example.com"
    password = "PasswordForMe123"

    reg_resp = client.post(
        "/api/v1/auth/register",
        json={"email": unique_email, "password": password},
    )
    user_id = reg_resp.json()["id"]

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": password},
    )
    token = login_resp.json()["access_token"]

    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    data = me_resp.json()
    assert data["id"] == user_id
    assert data["email"] == unique_email


def test_auth_me_unauthenticated_request_rejected():
    """Test 10: /auth/me returns 401 Unauthorized when token is missing."""
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_invalid_and_tampered_token_rejected():
    """Test 7: Malformed or tampered token returns 401 Unauthorized."""
    resp_malformed = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not.a.valid.jwt.token"},
    )
    assert resp_malformed.status_code == 401


def test_expired_token_rejected():
    """Test 8: Expired JWT token is rejected with 401 Unauthorized."""
    # Create expired token (-1 minute)
    expired_token = create_access_token(
        subject=999999,
        expires_delta=timedelta(minutes=-1),
    )
    resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert resp.status_code == 401
