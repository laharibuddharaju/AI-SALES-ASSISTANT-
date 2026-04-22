"""
Analytics API — exposes usage stats for the AI Sales Assistant dashboard.
All responses are flat JSON objects for easy frontend consumption.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models.lead import Lead
from app.models.conversation import Conversation
from app.core.security import verify_token

router = APIRouter()


@router.get("/analytics/summary")
def analytics_summary(
    user: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    """High-level KPI summary (flat structure for dashboard cards)."""
    total_leads     = db.query(func.count(Lead.id)).scalar() or 0
    new_leads       = db.query(func.count(Lead.id)).filter(Lead.status == "new").scalar() or 0
    qualified_leads = db.query(func.count(Lead.id)).filter(Lead.status == "qualified").scalar() or 0
    closed_leads    = db.query(func.count(Lead.id)).filter(Lead.status == "closed").scalar() or 0
    total_chats     = db.query(func.count(Conversation.id)).scalar() or 0

    return {
        "total_leads":     total_leads,
        "new_leads":       new_leads,
        "qualified_leads": qualified_leads,
        "closed_leads":    closed_leads,
        "total_chats":     total_chats,
    }


@router.get("/analytics/intent-distribution")
def intent_distribution(
    user: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    """Breakdown of intents seen in conversations."""
    rows = (
        db.query(Conversation.intent, func.count(Conversation.id).label("count"))
        .filter(
            Conversation.intent.isnot(None),
            Conversation.intent.notin_(["delete_lead", "unknown"])
        )
        .group_by(Conversation.intent)
        .order_by(func.count(Conversation.id).desc())
        .all()
    )
    return [{"intent": r.intent, "count": r.count} for r in rows]


@router.get("/analytics/leads-over-time")
def leads_over_time(
    user: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    """Daily lead creation counts (last 30 days)."""
    rows = (
        db.query(
            func.date(Lead.created_at).label("date"),
            func.count(Lead.id).label("count"),
        )
        .group_by(func.date(Lead.created_at))
        .order_by(func.date(Lead.created_at))
        .limit(30)
        .all()
    )
    return [{"date": str(r.date), "count": r.count} for r in rows]


@router.get("/analytics/lead-status-breakdown")
def lead_status_breakdown(
    user: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    """Count of leads per status."""
    rows = (
        db.query(Lead.status, func.count(Lead.id).label("count"))
        .group_by(Lead.status)
        .all()
    )
    return [{"status": r.status or "unknown", "count": r.count} for r in rows]

