"""
Approval service with persistent storage in the database.
Critical actions (delete_lead, apply_discount) require human approval before execution.
"""

import logging
from datetime import datetime
from sqlalchemy import Column, String, JSON, DateTime
from sqlalchemy.sql import func
from app.db.session import Base, SessionLocal

logger = logging.getLogger(__name__)

REQUIRES_APPROVAL_INTENTS = {"delete_lead", "apply_discount"}


class PendingApproval(Base):
    """Persistent approval queue stored in the database."""
    __tablename__ = "pending_approvals"

    id         = Column(String, primary_key=True)
    intent     = Column(String, nullable=False)
    payload    = Column(JSON, nullable=False)
    status     = Column(String, default="pending")   # "pending" | "approved" | "rejected"
    created_at = Column(DateTime(timezone=True), server_default=func.now())


def requires_approval(intent: str) -> bool:
    return intent in REQUIRES_APPROVAL_INTENTS


def request_approval(action_id: str, payload: dict) -> dict:
    """Persist an approval request and return a pending response."""
    db = SessionLocal()
    try:
        record = PendingApproval(
            id=action_id,
            intent=payload.get("intent", "unknown"),
            payload=payload,
            status="pending",
        )
        db.add(record)
        db.commit()
        logger.info(f"Approval requested: {action_id} for intent '{payload.get('intent')}'")
    except Exception:
        logger.exception("Failed to persist approval request")
    finally:
        db.close()

    return {
        "message": "Action requires human approval before execution.",
        "action_id": action_id,
        "status": "pending",
        "payload": payload,
    }


def resolve_approval(action_id: str, approved: bool) -> dict:
    """Mark a pending approval as approved or rejected."""
    db = SessionLocal()
    try:
        record = db.query(PendingApproval).filter(PendingApproval.id == action_id).first()
        if not record:
            return {"error": f"Approval ID {action_id} not found"}

        record.status = "approved" if approved else "rejected"
        db.commit()
        return {"action_id": action_id, "status": record.status}
    finally:
        db.close()
