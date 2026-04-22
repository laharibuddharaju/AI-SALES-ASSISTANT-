from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.approval_service import PendingApproval, resolve_approval
from app.services.action_service import execute_action
from app.core.security import verify_token
from app.core.logger import logger

router = APIRouter()


@router.get("/approvals")
def list_approvals(
    status: str = Query("pending", enum=["pending", "approved", "rejected", "all"]),
    user: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    """List approval requests, filtered by status."""
    query = db.query(PendingApproval)
    if status != "all":
        query = query.filter(PendingApproval.status == status)
    
    records = query.order_by(PendingApproval.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "intent": r.intent,
            "payload": r.payload,
            "status": r.status,
            "created_at": str(r.created_at),
        }
        for r in records
    ]


@router.post("/approvals/{action_id}/resolve")
def resolve_approval_endpoint(
    action_id: str,
    approved: bool,
    user: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    """Approve or reject a pending action."""
    # 1. Fetch record
    record = db.query(PendingApproval).filter(PendingApproval.id == action_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Approval request not found")
    
    if record.status != "pending":
        raise HTTPException(status_code=400, detail=f"Request already {record.status}")

    # 2. Mark in DB via service
    resolve_approval(action_id, approved)

    # 3. If approved, trigger the underlying action
    action_result = None
    if approved:
        logger.info(f"Executing approved action {action_id} (intent={record.intent})")
        payload = record.payload
        action_result = execute_action(
            intent=record.intent,
            entities=payload.get("entities", {}),
            user_id=payload.get("user_id", "1"),
            bypass_approval=True
        )

    return {
        "action_id": action_id,
        "status": "approved" if approved else "rejected",
        "action_result": action_result
    }
