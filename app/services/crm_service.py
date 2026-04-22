"""
HubSpot CRM service.
Supports: create_contact, update_contact.
All calls use HUBSPOT_API_KEY from environment.
"""

import logging
import requests
from app.core.config import HUBSPOT_API_KEY

logger = logging.getLogger(__name__)
HUBSPOT_BASE = "https://api.hubapi.com/crm/v3/objects/contacts"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {HUBSPOT_API_KEY}",
        "Content-Type": "application/json",
    }


def _build_properties(email: str, name: str = "", phone: str = "", company: str = "") -> dict:
    """Build HubSpot contact property payload."""
    first, *rest = (name.strip().split(" ") if name else ["", ""])
    props = {"email": email}
    if first:
        props["firstname"] = first
    if rest:
        props["lastname"] = " ".join(rest)
    if phone:
        props["phone"] = phone
    if company:
        props["company"] = company
    return {"properties": props}


def _safe_call(method: str, url: str, **kwargs) -> dict:
    """Wrapper that handles timeouts, JSON errors, and missing API key."""
    if not HUBSPOT_API_KEY:
        logger.warning("HUBSPOT_API_KEY not configured — CRM call skipped.")
        return {"status_code": 0, "data": {"warning": "HubSpot not configured"}}

    try:
        resp = getattr(requests, method)(url, headers=_headers(), timeout=10, **kwargs)
        try:
            data = resp.json()
        except ValueError:
            data = {"error": "Invalid JSON from HubSpot", "raw": resp.text}

        logger.info(f"HubSpot {method.upper()} {url} → {resp.status_code}")
        return {"status_code": resp.status_code, "data": data}

    except requests.exceptions.Timeout:
        logger.error("HubSpot request timed out")
        return {"status_code": 504, "data": {"error": "HubSpot timeout"}}
    except requests.exceptions.RequestException as exc:
        logger.exception("HubSpot request failed")
        return {"status_code": 500, "data": {"error": str(exc)}}


def create_crm_contact(email: str, name: str = "", phone: str = "", company: str = "") -> dict:
    """Create a new contact in HubSpot. Returns 409 if contact already exists."""
    payload = _build_properties(email, name, phone, company)
    return _safe_call("post", HUBSPOT_BASE, json=payload)


def update_crm_contact(email: str, name: str = "", phone: str = "", company: str = "") -> dict:
    """
    Update an existing HubSpot contact by email.
    HubSpot requires fetching the contact ID first, then PATCHing it.
    """
    # Step 1: Search for contact by email
    search_url = "https://api.hubapi.com/crm/v3/objects/contacts/search"
    search_payload = {
        "filterGroups": [{"filters": [{"propertyName": "email", "operator": "EQ", "value": email}]}],
        "properties": ["id"],
    }
    search_result = _safe_call("post", search_url, json=search_payload)
    results = search_result.get("data", {}).get("results", [])

    if not results:
        logger.warning(f"HubSpot contact not found for update: {email}")
        return {"status_code": 404, "data": {"error": f"Contact {email} not found in HubSpot"}}

    contact_id = results[0]["id"]

    # Step 2: PATCH the contact
    patch_url = f"{HUBSPOT_BASE}/{contact_id}"
    payload = _build_properties(email, name, phone, company)
    return _safe_call("patch", patch_url, json=payload)