"""
action_service.py — Executes CRM and lead operations based on detected intent.

Supported intents:
  - create_lead
  - update_lead
  - delete_lead
  - show_leads
"""

import uuid
import logging
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.lead import Lead
from app.models.conversation import Conversation
from app.services.vector_service import store_message
from app.services.approval_service import requires_approval, request_approval
from app.services.crm_service import create_crm_contact, update_crm_contact

logger = logging.getLogger(__name__)


def execute_action(
    intent: str,
    entities: dict,
    user_id: str = "1",
    message: str = "",
    bypass_approval: bool = False,
) -> dict:
    """
    Executes the business action for the detected intent.
    Handles lead CRUD, conversation persistence, vector memory, and human approval.
    """
    db: Session = SessionLocal()

    try:
        # ── 1. Persist conversation ─────────────────────────────────
        conversation = Conversation(
            user_id=user_id,
            role="user",
            message=message,
            intent=intent,
        )
        db.add(conversation)
        db.commit()

        # ── 2. Store in vector memory ───────────────────────────────
        store_message(user_id, message)

        # ── 3. Human approval gate ──────────────────────────────────
        if requires_approval(intent) and not bypass_approval:
            action_id = str(uuid.uuid4())
            return request_approval(
                action_id,
                {"intent": intent, "entities": entities, "user_id": user_id},
            )

        # ── 4. Route to action ──────────────────────────────────────
        if intent == "create_lead":
            return _create_lead(db, entities, user_id)

        if intent == "update_lead":
            return _update_lead(db, entities)

        if intent == "delete_lead":
            return _delete_lead(db, entities)

        if intent == "show_leads":
            return _show_leads(db, entities, user_id)

        return {"message": f"Intent '{intent}' recognised but no handler is configured."}

    except Exception:
        logger.exception("Action execution failed")
        db.rollback()
        return {"error": "An internal error occurred while processing your request."}

    finally:
        db.close()


# ── Intent Handlers ───────────────────────────────────────────────────────────

def _create_lead(db: Session, entities: dict, user_id: str) -> dict:
    email = entities.get("email")
    if not email:
        return {"error": "Email address is required to create a lead."}

    existing = db.query(Lead).filter(Lead.email == email).first()
    crm_result = create_crm_contact(
        email=email,
        name=entities.get("name") or "",
        phone=entities.get("phone") or "",
        company=entities.get("company") or "",
        product_code=entities.get("product_code") or "",
    )

    if existing:
        return {
            "message": "Lead already exists.",
            "lead": {"id": existing.id, "email": existing.email, "status": existing.status},
            "crm": crm_result,
        }

    lead = Lead(
        email=email,
        name=entities.get("name"),
        phone=entities.get("phone"),
        company=entities.get("company"),
        product_code=entities.get("product_code"),
        source="chat",
        status=entities.get("status") or "new",
        assigned_to=user_id,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    return {
        "message": "Lead created successfully.",
        "lead": {"id": lead.id, "email": lead.email, "name": lead.name, "status": lead.status},
        "crm": crm_result,
    }


def _update_lead(db: Session, entities: dict) -> dict:
    email = entities.get("email")
    if not email:
        return {"error": "Email address is required to identify the lead to update."}

    lead = db.query(Lead).filter(Lead.email == email).first()
    if not lead:
        return {"error": f"No lead found with email: {email}"}

    if entities.get("name"):
        lead.name = entities["name"]
    if entities.get("phone"):
        lead.phone = entities["phone"]
    if entities.get("company"):
        lead.company = entities["company"]
    if entities.get("status"):
        lead.status = entities["status"]
    if entities.get("product_code"):
        lead.product_code = entities["product_code"]
    if entities.get("deal_value"):
        try:
            lead.deal_value = float(str(entities["deal_value"]).replace(",", "").replace("$", "").strip())
        except ValueError:
            pass

    db.commit()
    db.refresh(lead)

    crm_result = update_crm_contact(
        email=email,
        name=lead.name or "",
        phone=lead.phone or "",
        company=lead.company or "",
        product_code=lead.product_code or "",
    )

    return {
        "message": "Lead updated successfully.",
        "lead": {
            "id": lead.id, "email": lead.email,
            "name": lead.name, "status": lead.status, "company": lead.company,
        },
        "crm": crm_result,
    }


def _delete_lead(db: Session, entities: dict) -> dict:
    email = entities.get("email")
    if not email:
        return {"error": "Email address is required to delete a lead."}

    lead = db.query(Lead).filter(Lead.email == email).first()
    if not lead:
        return {"error": f"No lead found with email: {email}"}

    db.delete(lead)
    db.commit()

    return {"message": f"Lead '{email}' deleted successfully."}


def _show_leads(db: Session, entities: dict, user_id: str) -> dict:
    query = db.query(Lead)

    # Optional filters
    if entities.get("status"):
        query = query.filter(Lead.status == entities["status"])

    leads = query.order_by(Lead.created_at.desc()).limit(20).all()

    return {
        "message": f"Found {len(leads)} lead(s).",
        "leads": [
            {
                "id": l.id,
                "email": l.email,
                "name": l.name,
                "company": l.company,
                "product_code": l.product_code,
                "status": l.status,
                "phone": l.phone,
            }
            for l in leads
        ],
    }