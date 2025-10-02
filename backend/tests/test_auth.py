"""Tests for authentication middleware."""

from unittest.mock import MagicMock, patch

import jwt
import pytest
from fastapi import HTTPException

from app.middleware.auth import get_current_user, get_optional_user


@pytest.mark.asyncio
async def test_get_current_user_success():
    """Test successful user authentication."""
    # Mock JWT payload
    mock_payload = {
        "sub": "user_123",
        "sid": "session_456",
        "email": "test@example.com",
        "org_id": "org_789",
        "org_role": "admin",
    }

    with patch("app.middleware.auth.clerk_auth.verify_token", return_value=mock_payload):
        user = await get_current_user(authorization="Bearer valid_token_here")

        assert user["user_id"] == "user_123"
        assert user["session_id"] == "session_456"
        assert user["email"] == "test@example.com"
        assert user["org_id"] == "org_789"
        assert user["org_role"] == "admin"


@pytest.mark.asyncio
async def test_get_current_user_missing_header():
    """Test authentication with missing Authorization header."""
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(authorization=None)

    assert exc_info.value.status_code == 401
    assert "Missing authorization header" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_current_user_invalid_scheme():
    """Test authentication with invalid scheme."""
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(authorization="Basic invalid_scheme")

    assert exc_info.value.status_code == 401
    assert "Invalid authentication scheme" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_current_user_missing_token():
    """Test authentication with missing token."""
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(authorization="Bearer ")

    assert exc_info.value.status_code == 401
    assert "Missing authentication token" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_current_user_expired_token():
    """Test authentication with expired token."""
    with patch(
        "app.middleware.auth.clerk_auth.verify_token",
        side_effect=HTTPException(status_code=401, detail="Token has expired"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization="Bearer expired_token")

        assert exc_info.value.status_code == 401
        assert "Token has expired" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    """Test authentication with invalid token."""
    with patch(
        "app.middleware.auth.clerk_auth.verify_token",
        side_effect=HTTPException(status_code=401, detail="Invalid authentication token"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization="Bearer invalid_token")

        assert exc_info.value.status_code == 401
        assert "Invalid authentication token" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_optional_user_success():
    """Test optional authentication with valid token."""
    mock_payload = {
        "sub": "user_123",
        "sid": "session_456",
        "email": "test@example.com",
        "org_id": "org_789",
        "org_role": "admin",
    }

    with patch("app.middleware.auth.clerk_auth.verify_token", return_value=mock_payload):
        user = await get_optional_user(authorization="Bearer valid_token")

        assert user is not None
        assert user["user_id"] == "user_123"


@pytest.mark.asyncio
async def test_get_optional_user_no_token():
    """Test optional authentication with no token."""
    user = await get_optional_user(authorization=None)
    assert user is None


@pytest.mark.asyncio
async def test_get_optional_user_invalid_token():
    """Test optional authentication with invalid token returns None."""
    with patch(
        "app.middleware.auth.clerk_auth.verify_token",
        side_effect=HTTPException(status_code=401, detail="Invalid token"),
    ):
        user = await get_optional_user(authorization="Bearer invalid_token")

        assert user is None
