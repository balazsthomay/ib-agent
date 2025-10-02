"""Tests for project API routes."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app




@pytest.mark.asyncio
async def test_create_project_success(mock_current_user, test_db):
    """Test successful project creation."""
    from app.db.database import get_db
    from app.middleware.auth import get_current_user

    # Create a proper async generator wrapper for the test_db session
    async def override_get_db():
        try:
            yield test_db
        finally:
            pass  # Session cleanup handled by the fixture

    async def override_get_current_user():
        return mock_current_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/projects",
                json={
                    "name": "Test Project",
                    "description": "Test Description",
                    "target_company": "Company A",
                },
                headers={"Authorization": "Bearer fake_token"},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Test Project"
            assert data["firm_id"] == "org_789"
            assert data["status"] == "draft"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_project_no_org():
    """Test project creation fails without organization."""
    from app.middleware.auth import get_current_user

    user_without_org = {
        "user_id": "user_123",
        "session_id": "session_456",
        "email": "test@example.com",
        "org_id": None,
        "org_role": None,
    }

    async def override_get_current_user():
        return user_without_org

    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/projects",
                json={"name": "Test Project"},
                headers={"Authorization": "Bearer fake_token"},
            )

            assert response.status_code == 403
            assert "must belong to an organization" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_projects(mock_current_user):
    """Test listing projects."""
    from app.middleware.auth import get_current_user

    async def override_get_current_user():
        return mock_current_user

    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/projects",
                headers={"Authorization": "Bearer fake_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_unauthorized_access():
    """Test unauthorized access to projects."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/projects")

        assert response.status_code == 401
