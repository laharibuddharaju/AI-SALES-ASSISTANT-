from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.schemas.chat import ChatRequest
from app.services.intent_service import classify_with_llm
from app.services.entity_service import extract_entities, merge_entities
from app.services.action_service import execute_action
from app.core.security import verify_token
from app.core.logger import logger
from app.db.session import get_db

router = APIRouter()


@router.post("/chat")
def chat_endpoint(
    request: ChatRequest,
    user: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    try:
        logger.info(f"Chat from user={user.get('sub')}: {request.message!r}")

        # Use LLM to classify intent and extract entities in one call
        llm_result = classify_with_llm(request.message)
        intent = llm_result.get("intent", "unknown")
        llm_entities = llm_result.get("entities", {})

        # Merge with regex-extracted entities (regex fills gaps LLM may miss)
        regex_entities = extract_entities(request.message)
        entities = merge_entities(llm_entities, regex_entities)

        result = execute_action(
            intent=intent,
            entities=entities,
            user_id=user.get("sub"),
            message=request.message,
        )

        return {
            "intent": intent,
            "entities": entities,
            "result": result,
        }

    except Exception:
        logger.exception("Chat endpoint error")
        raise HTTPException(status_code=500, detail="Internal Server Error")