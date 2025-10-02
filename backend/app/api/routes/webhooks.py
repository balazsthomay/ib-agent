"""Webhook endpoints for external service integrations."""

import json
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from svix.webhooks import Webhook, WebhookVerificationError

from app.config import settings
from app.db.database import async_session_maker
from app.db.models import Firm, User

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/clerk")
async def clerk_webhook(
    request: Request,
    svix_id: str = Header(None, alias="svix-id"),
    svix_timestamp: str = Header(None, alias="svix-timestamp"),
    svix_signature: str = Header(None, alias="svix-signature"),
) -> dict[str, str]:
    """
    Handle Clerk webhook events for user synchronization.

    Supports:
    - user.created: Create user and personal firm in database
    - user.updated: Update user details (email, name, image)
    - user.deleted: Soft delete or handle cleanup

    Webhook signature is verified using Svix for security.
    """
    if not settings.clerk_webhook_secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    # Get the raw body for signature verification
    body = await request.body()

    # Verify the webhook signature
    wh = Webhook(settings.clerk_webhook_secret)
    try:
        payload = wh.verify(
            body,
            {
                "svix-id": svix_id,
                "svix-timestamp": svix_timestamp,
                "svix-signature": svix_signature,
            },
        )
    except WebhookVerificationError as e:
        raise HTTPException(status_code=400, detail=f"Webhook verification failed: {e}")

    event_type = payload.get("type")
    event_data = payload.get("data", {})

    if event_type == "user.created":
        await _handle_user_created(event_data)
    elif event_type == "user.updated":
        await _handle_user_updated(event_data)
    elif event_type == "user.deleted":
        await _handle_user_deleted(event_data)

    return {"status": "ok"}


async def _handle_user_created(data: dict[str, Any]) -> None:
    """Handle user.created webhook event."""
    user_id = data.get("id")
    email = data.get("email_addresses", [{}])[0].get("email_address")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    image_url = data.get("image_url")
    org_id = data.get("organization_memberships", [{}])[0].get("organization", {}).get(
        "id"
    )

    if not user_id or not email:
        return

    async with async_session_maker() as db:
        # Determine firm_id (org_id if in org, otherwise user_id for personal)
        firm_id = org_id or user_id

        # Create firm if needed (personal firm or org firm)
        try:
            result = await db.execute(select(Firm).where(Firm.id == firm_id))
            firm = result.scalar_one_or_none()

            if not firm:
                firm_name = (
                    f"Personal - {email}" if not org_id else data.get("organization", {}).get("name", f"Org {org_id}")
                )
                firm = Firm(id=firm_id, name=firm_name)
                db.add(firm)
                await db.flush()
        except IntegrityError:
            await db.rollback()
            await db.refresh()

        # Create user
        try:
            user = User(
                id=user_id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                image_url=image_url,
                firm_id=org_id,  # NULL for personal accounts
            )
            db.add(user)
            await db.commit()
        except IntegrityError:
            # User already exists, this is fine
            await db.rollback()


async def _handle_user_updated(data: dict[str, Any]) -> None:
    """Handle user.updated webhook event."""
    user_id = data.get("id")
    if not user_id:
        return

    email = data.get("email_addresses", [{}])[0].get("email_address")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    image_url = data.get("image_url")

    async with async_session_maker() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user:
            if email:
                user.email = email
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            if image_url:
                user.image_url = image_url

            await db.commit()


async def _handle_user_deleted(data: dict[str, Any]) -> None:
    """Handle user.deleted webhook event."""
    user_id = data.get("id")
    if not user_id:
        return

    async with async_session_maker() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user:
            # For now, we keep the user record but could add a deleted_at field
            # This preserves referential integrity with projects
            # TODO: Consider adding soft delete with deleted_at timestamp
            pass
