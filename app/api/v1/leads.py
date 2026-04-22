"""
Leads API — Dedicated router for Lead CRUD operations and CRM synchronization.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.lead import Lead
from app.core.security import verify_token
from app.services.crm_service import create_crm_contact, update_crm_contact

router = APIRouter()


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
            Lead.company.ilike(term)
        )
    
    total_count = q.count()
    total_pages = (total_count + limit - 1) // limit
    leads = q.order_by(Lead.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    return {
        "leads": [
            {
                "id":          l.id,
                "email":       l.email,
                "name":        l.name or "",
                "company":     l.company or "",
                "phone":       l.phone or "",
                "status":      l.status or "new",
                "deal_value":  l.deal_value or 0,
                "source":      l.source or "",
                "created_at":  str(l.created_at)[:10] if l.created_at else "",
            }
            for l in leads
        ],
        "total_count": total_count,
        "total_pages": total_pages,
        "page": page,
        "limit": limit,
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

    lead = Lead(
        email=email,
        name=payload.get("name"),
        company=payload.get("company"),
        phone=payload.get("phone"),
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
    )

    return lead


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
    if "name" in payload: lead.name = payload["name"]
    if "company" in payload: lead.company = payload["company"]
    if "phone" in payload: lead.phone = payload["phone"]
    if "status" in payload: lead.status = payload["status"]
    if "deal_value" in payload: lead.deal_value = payload["deal_value"]

    db.commit()
    db.refresh(lead)

    # Sync with CRM
    update_crm_contact(
        email=lead.email,
        name=lead.name or "",
        company=lead.company or "",
        phone=lead.phone or "",
    )

    return lead


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
        # We use create_crm_contact; if it fails with 409, we update.
        res = create_crm_contact(
            email=lead.email,
            name=lead.name or "",
            company=lead.company or "",
            phone=lead.phone or "",
        )
        if res["status_code"] in (201, 200, 409):
            if res["status_code"] == 409:
                update_crm_contact(
                    email=lead.email,
                    name=lead.name or "",
                    company=lead.company or "",
                    phone=lead.phone or "",
                )
            results["synced"] += 1
        else:
            results["failed"] += 1
            
    return results
