"""
api/schemas.py
--------------
Lightweight request/response validation helpers.
No external dependencies – pure standard library.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Generic result helpers
# ---------------------------------------------------------------------------

def ok_response(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Wrap a successful payload."""
    return {"status": "success", **payload}


def error_response(message: str, code: int = 400) -> Tuple[int, Dict[str, Any]]:
    """Return (http_status, body) tuple for errors."""
    return code, {"status": "error", "message": message}


# ---------------------------------------------------------------------------
# Request validators
# ---------------------------------------------------------------------------

def validate_order_payload(payload: Any) -> Tuple[bool, str]:
    """Return (is_valid, error_message).
    
    Accepts the raw *order* dict posted to /order or /orders.
    Minimal validation: we just need it to be a non-empty mapping.
    Field-level validation is delegated to the service layer.
    """
    if not isinstance(payload, dict):
        return False, "Payload deve ser um objeto JSON."
    return True, ""


def validate_coupon_payload(payload: Any) -> Tuple[bool, str]:
    """Return (is_valid, error_message) for /coupon/validate."""
    if not isinstance(payload, dict):
        return False, "Payload deve ser um objeto JSON."
    if not payload.get("code"):
        return False, "O campo 'code' e obrigatorio."
    return True, ""


def validate_status_patch(payload: Any) -> Tuple[bool, str]:
    """Return (is_valid, error_message) for PATCH /orders/{id}/status."""
    if not isinstance(payload, dict):
        return False, "Payload deve ser um objeto JSON."
    if not payload.get("status"):
        return False, "O campo 'status' e obrigatorio."
    return True, ""


# ---------------------------------------------------------------------------
# Response serialisers
# ---------------------------------------------------------------------------

def serialise_products(products: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"products": products}


def serialise_orders(orders: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"orders": orders}


def serialise_health() -> Dict[str, Any]:
    return {"status": "ok"}
