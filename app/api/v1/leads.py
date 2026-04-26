"""
Leads API — Dedicated router for Lead CRUD operations and CRM synchronization.
"""

import re
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.lead import Lead
from app.core.security import verify_token
from app.services.crm_service import create_crm_contact, update_crm_contact

router = APIRouter()

# Alphanumeric validator for product_code (max 20 chars)
_PRODUCT_CODE_RE = re.compile(r'^[A-Za-z0-9]{0,20}$')


def _validate_product_code(code: str | None):
    """Raises 422 if product_code is set and not alphanumeric / > 20 chars."""
    if code is None or code == "":
        return
    if not _PRODUCT_CODE_RE.match(code):
        raise HTTPException(
            status_code=422,
            detail="product_code must be alphanumeric and at most 20 characters.",
        )


def _lead_dict(l) -> dict:
    """Serialize a Lead ORM object to a dict."""
    return {
        "id":           l.id,
        "email":        l.email,
        "name":         l.name or "",
        "company":      l.company or "",
        "phone":        l.phone or "",
        "product_code": l.product_code or "",
        "status":       l.status or "new",
        "deal_value":   l.deal_value or 0,
        "source":       l.source or "",
        "created_at":   str(l.created_at)[:10] if l.created_at else "",
    }


@router.get("/leads")
def list_leads(
    user: dict = Depends(verify_token),
    db: Session = Depends(get_db),
    status: str = Query(None),
    search: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
):
    """Paginated, filterable list of all leads."""
    q = db.query(Lead)
    if status:
        q = q.filter(Lead.status == status)
    if search:
        term = f"%{search}%"
        q = q.filter(
            Lead.email.ilike(term) |
            Lead.name.ilike(term) |
            Lead.company.ilike(term) |
            Lead.product_code.ilike(term)
        )

    total_count = q.count()
    total_pages = (total_count + limit - 1) // limit
    leads = q.order_by(Lead.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    return {
        "leads":       [_lead_dict(l) for l in leads],
        "total_count": total_count,
        "total_pages": total_pages,
        "page":        page,
        "limit":       limit,
    }


@router.post("/leads")
def create_lead(
    payload: dict,
    user: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    """Manually create a lead and sync with CRM."""
    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    if db.query(Lead).filter(Lead.email == email).first():
        raise HTTPException(status_code=400, detail="Lead with this email already exists")

    product_code = payload.get("product_code") or ""
    _validate_product_code(product_code)

    lead = Lead(
        email=email,
        name=payload.get("name"),
        company=payload.get("company"),
        phone=payload.get("phone"),
        product_code=product_code or None,
        status=payload.get("status") or "new",
        deal_value=payload.get("deal_value") or 0,
        source="manual",
        assigned_to=user.get("sub"),
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    # Sync with CRM
    create_crm_contact(
        email=email,
        name=lead.name or "",
        company=lead.company or "",
        phone=lead.phone or "",
        product_code=lead.product_code or "",
    )

    return _lead_dict(lead)


@router.patch("/leads/{lead_id}")
def update_lead(
    lead_id: int,
    payload: dict,
    user: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    """Update lead details and sync with CRM."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Update fields
    if "name" in payload:         lead.name = payload["name"]
    if "company" in payload:      lead.company = payload["company"]
    if "phone" in payload:        lead.phone = payload["phone"]
    if "status" in payload:       lead.status = payload["status"]
    if "deal_value" in payload:   lead.deal_value = payload["deal_value"]
    if "product_code" in payload:
        _validate_product_code(payload["product_code"])
        lead.product_code = payload["product_code"] or None

    db.commit()
    db.refresh(lead)

    # Sync with CRM
    update_crm_contact(
        email=lead.email,
        name=lead.name or "",
        company=lead.company or "",
        phone=lead.phone or "",
        product_code=lead.product_code or "",
    )

    return _lead_dict(lead)


@router.delete("/leads/{lead_id}")
def delete_lead(
    lead_id: int,
    user: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    """Delete a lead (admin bypasses approval gate via this direct endpoint)."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    db.delete(lead)
    db.commit()
    return {"message": "Lead deleted successfully"}


@router.post("/leads/sync")
def sync_all_leads(
    user: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    """Bulk sync all leads to CRM (Pull/Push simulation)."""
    leads = db.query(Lead).all()
    results = {"total": len(leads), "synced": 0, "failed": 0}

    for lead in leads:
        res = create_crm_contact(
            email=lead.email,
            name=lead.name or "",
            company=lead.company or "",
            phone=lead.phone or "",
            product_code=lead.product_code or "",
        )
        if res["status_code"] in (201, 200, 409):
            if res["status_code"] == 409:
                update_crm_contact(
                    email=lead.email,
                    name=lead.name or "",
                    company=lead.company or "",
                    phone=lead.phone or "",
                    product_code=lead.product_code or "",
                )
            results["synced"] += 1
        else:
            results["failed"] += 1

    return results
