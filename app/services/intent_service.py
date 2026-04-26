"""
LLM-powered intent classification using OpenAI.
Falls back to regex if OPENAI_API_KEY is not set.
"""

import re
import json
import logging
from app.core.config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

INTENT_SYSTEM_PROMPT = """
You are an intent classifier for a B2B sales assistant.
Classify the user message into exactly ONE of these intents:
- create_lead
- update_lead
- delete_lead
- show_leads
- create_deal
- schedule_follow_up
- unknown

Also extract entities from the message.

Respond ONLY with valid JSON in this format:
{
  "intent": "<intent>",
  "entities": {
    "email": "<email or null>",
    "name": "<full name or null>",
    "phone": "<phone or null>",
    "company": "<company name or null>",
    "status": "<lead status or null>",
    "deal_value": "<numeric value or null>",
    "product_code": "<product code or null>"
  }
}
""".strip()


def detect_intent(message: str) -> str:
    """Return the intent string for the given user message."""
    result = classify_with_llm(message)
    return result.get("intent", "unknown")


def classify_with_llm(message: str) -> dict:
    """
    Use OpenAI to classify intent and extract entities.
    Automatically falls back to regex if API key is missing.
    """
    if OPENAI_API_KEY:
        try:
            import openai
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                    {"role": "user",   "content": message},
                ],
                temperature=0,
                max_tokens=200,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.warning(f"LLM classification failed, falling back to regex: {e}")

    # ── Regex Fallback ──────────────────────────────────────────────
    return _regex_classify(message)


def _regex_classify(message: str) -> dict:
    """Simple regex-based fallback classifier."""
    msg = message.lower()
    email_match = re.findall(r"\S+@\S+\.\S+", message)
    email = email_match[0] if email_match else None

    if re.search(r"\b(create|add|register|save|new)\b", msg) and email:
        intent = "create_lead"
    elif re.search(r"\b(delete|remove)\b", msg) and email:
        intent = "delete_lead"
    elif re.search(r"\b(update|change|edit|modify)\b", msg) and email:
        intent = "update_lead"
    elif re.search(r"\b(show|list|display|get|fetch)\b", msg) and "lead" in msg:
        intent = "show_leads"
    else:
        intent = "unknown"

    return {"intent": intent, "entities": {"email": email, "name": None, "phone": None, "company": None, "status": None, "deal_value": None, "product_code": None}}