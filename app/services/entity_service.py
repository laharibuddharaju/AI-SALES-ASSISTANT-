"""
Entity extraction service.
When LLM is enabled (via intent_service.classify_with_llm), this is called
as a pass-through using the already-extracted entities from the LLM response.
For direct calls, it runs lightweight regex extraction.
"""

import re


def extract_entities(text: str) -> dict:
    """
    Extract structured entities from a message using regex.
    Used as a lightweight complement or fallback alongside LLM extraction.
    """
    # Email
    email_match = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    email = email_match[0] if email_match else None

    # Phone (international and local formats)
    phone_match = re.findall(r"(?:\+?\d[\d\s\-().]{7,}\d)", text)
    phone = phone_match[0].strip() if phone_match else None

    # Deal value — look for currency amounts
    deal_match = re.findall(r"(?:[$€£₹]\s?[\d,]+(?:\.\d+)?|[\d,]+\s?(?:USD|EUR|INR|GBP))", text, re.IGNORECASE)
    deal_value = deal_match[0].strip() if deal_match else None

    # Status keyword
    status_match = re.search(r"\b(new|contacted|qualified|closed|lost)\b", text, re.IGNORECASE)
    status = status_match.group(1).lower() if status_match else None

    return {
        "email": email,
        "phone": phone,
        "deal_value": deal_value,
        "status": status,
        "name": None,     # Best extracted by LLM; regex for names is unreliable
        "company": None,  # Same — let LLM handle this
    }


def merge_entities(llm_entities: dict, regex_entities: dict) -> dict:
    """Merge LLM and regex results — LLM takes priority, regex fills gaps."""
    merged = dict(regex_entities)
    for key, value in llm_entities.items():
        if value is not None:
            merged[key] = value
    return merged
