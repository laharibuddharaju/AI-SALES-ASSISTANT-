"""
Run three lead operations:
1. Create a new lead for Rahul from Infosys
2. Show all new leads from this week
3. Add note: client asked for pricing details
"""

import sys, json
from datetime import datetime, timedelta
from app.db.session import get_db, engine
from sqlalchemy import text

# Inline DB session
from sqlalchemy.orm import Session
db: Session = next(get_db())

from app.models.lead import Lead

# ─── 1. CREATE LEAD ───────────────────────────────────────────────────────────
print("\n" + "="*60)
print("QUERY 1: Create a new lead for Rahul from Infosys")
print("="*60)

existing = db.query(Lead).filter(Lead.email == "rahul@infosys.com").first()
if existing:
    print(f"[SKIP] Lead already exists: id={existing.id}, name={existing.name}")
    new_lead = existing
else:
    new_lead = Lead(
        email="rahul@infosys.com",
        name="Rahul",
        company="Infosys",
        phone="",
        status="new",
        deal_value=0,
        source="manual",
        assigned_to="1",
    )
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    print(f"[OK] Lead created successfully!")

print(json.dumps({
    "id":         new_lead.id,
    "name":       new_lead.name,
    "email":      new_lead.email,
    "company":    new_lead.company,
    "status":     new_lead.status,
    "source":     new_lead.source,
    "deal_value": new_lead.deal_value,
    "created_at": str(new_lead.created_at)[:19] if new_lead.created_at else "N/A",
}, indent=2))

# ─── 2. NEW LEADS THIS WEEK ──────────────────────────────────────────────────
print("\n" + "="*60)
print("QUERY 2: All 'new' leads created this week")
print("="*60)

# Week start = Monday of current week
today = datetime.now()
week_start = today - timedelta(days=today.weekday())   # Monday 00:00
week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

new_leads_this_week = (
    db.query(Lead)
    .filter(Lead.status == "new")
    .filter(Lead.created_at >= week_start.strftime("%Y-%m-%d 00:00:00"))
    .order_by(Lead.created_at.desc())
    .all()
)

print(f"Week start: {week_start.strftime('%Y-%m-%d')} | Found: {len(new_leads_this_week)} lead(s)\n")
if new_leads_this_week:
    print(f"{'ID':<5} {'Name':<20} {'Company':<20} {'Email':<30} {'Status':<10} {'Created'}")
    print("-"*100)
    for l in new_leads_this_week:
        print(f"{l.id:<5} {(l.name or ''):<20} {(l.company or ''):<20} {l.email:<30} {(l.status or ''):<10} {str(l.created_at)[:19]}")
else:
    print("No new leads found this week.")

# ─── 3. ADD NOTE ─────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("QUERY 3: Add note to Rahul's lead — 'client asked for pricing details'")
print("="*60)

# Check if Lead model has a notes field; if not, use the conversation/notes table or store in a notes column
lead_to_note = db.query(Lead).filter(Lead.email == "rahul@infosys.com").first()
if lead_to_note:
    # Check available columns
    cols = [c.key for c in Lead.__table__.columns]
    print(f"Lead columns: {cols}")
    if "notes" in cols:
        lead_to_note.notes = "client asked for pricing details"
        db.commit()
        db.refresh(lead_to_note)
        print(f"[OK] Note added to lead id={lead_to_note.id}")
        print(f"Note: {lead_to_note.notes}")
    else:
        print(f"[INFO] Lead model has no 'notes' column (columns: {cols})")
        print(f"[INFO] The note 'client asked for pricing details' would be stored in a notes/activity table.")
        print(f"[INFO] Recording note as a chat/conversation entry instead...\n")
        # Try to log it via conversation model if available
        try:
            from app.models.conversation import Conversation
            note_conv = Conversation(
                user_id=1,
                role="system",
                message=f"[NOTE on lead {lead_to_note.id} - {lead_to_note.name} @ {lead_to_note.company}]: client asked for pricing details",
            )
            db.add(note_conv)
            db.commit()
            db.refresh(note_conv)
            print(f"[OK] Note recorded in conversations (id={note_conv.id}): {note_conv.message}")
        except Exception as e:
            print(f"[WARN] Could not store in conversation table: {e}")
            print(f"[NOTE CAPTURED]: client asked for pricing details — for lead: {lead_to_note.name} @ {lead_to_note.company}")
else:
    print("[ERROR] Lead not found for note.")

print("\n" + "="*60)
print("ALL QUERIES COMPLETE")
print("="*60 + "\n")
db.close()
