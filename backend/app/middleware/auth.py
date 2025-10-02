"""Authentication middleware for Clerk JWT verification."""

import logging
from typing import Annotated

import httpx
import jwt
from fastapi import Depends, Header, HTTPException, Request, status
from jwt import PyJWKClient

from app.config import settings

logger = logging.getLogger(__name__)

# Clerk JWKS URL for token verification
CLERK_JWKS_URL = f"https://{settings.clerk_publishable_key.split('_')[1]}.clerk.accounts.dev/.well-known/jwks.json"


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
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                },
            )

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
            logger.error(f"Token verification error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed",
            )


clerk_auth = ClerkAuth()


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> dict:
    """
    FastAPI dependency to get current authenticated user.

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

    return {
        "user_id": payload.get("sub"),
        "session_id": payload.get("sid"),
        "email": payload.get("email"),
        "org_id": payload.get("org_id"),
        "org_role": payload.get("org_role"),
    }


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
