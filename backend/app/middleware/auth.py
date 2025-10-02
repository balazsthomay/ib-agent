"""Authentication middleware for Clerk JWT verification."""

import base64
import logging
from typing import Annotated

import httpx
import jwt
from fastapi import Depends, Header, HTTPException, Request, status
from jwt import PyJWKClient

from app.config import settings

logger = logging.getLogger(__name__)


def get_clerk_jwks_url() -> str:
    """Extract Clerk domain from publishable key and construct JWKS URL."""
    try:
        # Get the base64 part after pk_test_ or pk_live_
        key_parts = settings.clerk_publishable_key.split("_")
        if len(key_parts) >= 3:
            # Decode base64 domain
            encoded_domain = key_parts[2]
            # Add padding if needed
            padding = 4 - len(encoded_domain) % 4
            if padding != 4:
                encoded_domain += "=" * padding
            domain = base64.b64decode(encoded_domain).decode("utf-8").rstrip("$")
            return f"https://{domain}/.well-known/jwks.json"
    except Exception as e:
        logger.error(f"Failed to extract Clerk domain: {e}")

    # Fallback - this should be replaced with actual domain
    raise ValueError("Invalid Clerk publishable key format")


# Clerk JWKS URL for token verification
CLERK_JWKS_URL = get_clerk_jwks_url()


class ClerkAuth:
    """Clerk authentication handler."""

    def __init__(self):
        self.jwks_client = PyJWKClient(CLERK_JWKS_URL)

    def verify_token(self, token: str) -> dict:
        """
        Verify Clerk session token.

        Args:
            token: JWT token from Authorization header

        Returns:
            Decoded token payload

        Raises:
            HTTPException: If token is invalid
        """
        try:
            # Get signing key from JWKS
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)

            # Verify and decode token
            # Don't verify audience/issuer for now - Clerk handles this differently
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_aud": False,  # Clerk doesn't always include aud claim
                },
            )

            logger.debug(f"Token verified successfully for user: {payload.get('sub')}")
            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
            )
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed",
            )


clerk_auth = ClerkAuth()


async def fetch_clerk_user(user_id: str) -> dict | None:
    """
    Fetch full user details from Clerk API.

    Returns user data with email, first_name, last_name, etc.
    """
    import httpx
    from app.config import settings

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.clerk.com/v1/users/{user_id}",
                headers={
                    "Authorization": f"Bearer {settings.clerk_secret_key}",
                },
                timeout=5.0,
            )

            if response.status_code == 200:
                user_data = response.json()
                return {
                    "id": user_data.get("id"),
                    "email": user_data.get("email_addresses", [{}])[0].get("email_address"),
                    "first_name": user_data.get("first_name"),
                    "last_name": user_data.get("last_name"),
                    "image_url": user_data.get("image_url"),
                }
    except Exception as e:
        logger.error(f"Failed to fetch Clerk user: {e}")

    return None


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> dict:
    """
    FastAPI dependency to get current authenticated user.

    Also ensures user exists in database (auto-provisions on first request).

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        User payload from token

    Raises:
        HTTPException: If authentication fails
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token from "Bearer <token>"
    scheme, _, token = authorization.partition(" ")

    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token and return user data
    payload = clerk_auth.verify_token(token)

    user_data = {
        "user_id": payload.get("sub"),
        "session_id": payload.get("sid"),
        "email": payload.get("email"),
        "org_id": payload.get("org_id"),
        "org_role": payload.get("org_role"),
    }

    # Ensure user exists in database (async background task)
    # This runs without blocking the request
    import asyncio
    asyncio.create_task(_ensure_user_exists(user_data))

    return user_data


async def _ensure_user_exists(user_data: dict) -> None:
    """
    Background task to ensure user exists in database.
    Creates user and firm if they don't exist.
    """
    from app.db.database import get_db
    from app.db.models import Firm, User
    from sqlalchemy import select

    try:
        # Get a new DB session for this background task
        async for db in get_db():
            user_id = user_data["user_id"]
            firm_id = user_data.get("org_id") or user_id

            # Check if user exists
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if not user:
                # Fetch full user details from Clerk
                clerk_user = await fetch_clerk_user(user_id)

                # Ensure firm exists first (for FK constraint)
                result = await db.execute(select(Firm).where(Firm.id == firm_id))
                firm = result.scalar_one_or_none()

                if not firm:
                    firm = Firm(
                        id=firm_id,
                        name=f"Personal - {clerk_user.get('email') if clerk_user else 'User'}",
                    )
                    db.add(firm)
                    await db.flush()

                # Create user
                user = User(
                    id=user_id,
                    email=clerk_user.get("email") if clerk_user else f"{user_id}@unknown.com",
                    first_name=clerk_user.get("first_name") if clerk_user else None,
                    last_name=clerk_user.get("last_name") if clerk_user else None,
                    image_url=clerk_user.get("image_url") if clerk_user else None,
                    firm_id=firm_id if user_data.get("org_id") else None,
                )
                db.add(user)
                await db.commit()
                logger.info(f"Auto-provisioned user: {user_id}")

            break  # Exit the async generator loop
    except Exception as e:
        logger.error(f"Failed to ensure user exists: {e}")


async def get_optional_user(
    authorization: Annotated[str | None, Header()] = None,
) -> dict | None:
    """
    Optional authentication - returns user if authenticated, None otherwise.

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        User payload or None
    """
    if not authorization:
        return None

    try:
        return await get_current_user(authorization=authorization)
    except HTTPException:
        return None


# Type alias for dependency injection
CurrentUser = Annotated[dict, Depends(get_current_user)]
OptionalUser = Annotated[dict | None, Depends(get_optional_user)]
