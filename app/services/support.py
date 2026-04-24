"""Support requests: create, resolve, find by group message."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models import (
    SupportRequest, SupportStatus, User, UserRole,
)


class SupportError(Exception):
    def __init__(self, code: str, **extra):
        self.code = code
        self.extra = extra
        super().__init__(code)


def create_support_request(
    db: Session,
    user: User,
    category: str,
    text: str,
    photo_file_id: str | None = None,
) -> SupportRequest:
    """Create a new support request in 'open' status.

    The handler should then post to the appropriate Telegram group and
    update group_chat_id / group_message_id on the returned object.
    """
    if category not in ("engineer", "complaint", "techsupport"):
        raise SupportError("invalid_category")
    if not text or not text.strip():
        raise SupportError("empty_text")
    if len(text) > 4000:
        raise SupportError("text_too_long")

    req = SupportRequest(
        user_id=user.id,
        category=category,
        content=text.strip(),
        photo_file_id=photo_file_id,
        status=SupportStatus.OPEN.value,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def attach_group_message(
    db: Session, request_id: uuid.UUID, chat_id: int, message_id: int,
) -> None:
    """Record which group message corresponds to this request."""
    req = db.get(SupportRequest, request_id)
    if req is None:
        return
    req.group_chat_id = chat_id
    req.group_message_id = message_id
    db.commit()


def find_by_group_message(
    db: Session, chat_id: int, message_id: int,
) -> SupportRequest | None:
    """Used when handling inline-button callbacks in group."""
    return (
        db.query(SupportRequest)
        .filter(
            SupportRequest.group_chat_id == chat_id,
            SupportRequest.group_message_id == message_id,
        )
        .first()
    )


def transition_status(
    db: Session,
    request: SupportRequest,
    new_status: str,
    resolver: User,
    note: str | None = None,
) -> SupportRequest:
    """Move a request through statuses with minimal validation.

    Terminal statuses (resolved / rejected) record resolver and time.
    """
    valid = {"accepted", "in_progress", "resolved", "rejected"}
    if new_status not in valid:
        raise SupportError("invalid_status")
    # Don't go backwards from terminal
    if request.status in (SupportStatus.RESOLVED.value, SupportStatus.REJECTED.value):
        raise SupportError("already_closed")

    request.status = new_status
    if new_status in (SupportStatus.RESOLVED.value, SupportStatus.REJECTED.value):
        request.resolved_at = datetime.now(timezone.utc)
        request.resolver_id = resolver.id
        if note:
            request.resolution_note = note[:4000]
    db.commit()
    db.refresh(request)
    return request
