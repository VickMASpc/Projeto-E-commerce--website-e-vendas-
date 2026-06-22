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
    """Return (is_valid, error_message) for /order or /orders."""
    if not isinstance(payload, dict):
        return False, "Payload deve ser um objeto JSON."

    raw_items = payload.get("items") or payload.get("itens")
    if not isinstance(raw_items, list) or not raw_items:
        return False, "O campo 'items' deve conter ao menos um item."

    for item in raw_items:
        if not isinstance(item, dict):
            continue
        product_id = item.get("product_id") or item.get("produto_id") or item.get("produtoId") or item.get("id")
        quantity = item.get("quantity", item.get("quantidade", 0))
        try:
            quantity_value = int(float(quantity))
        except (TypeError, ValueError):
            quantity_value = 0
        if str(product_id or "").strip() and quantity_value > 0:
            return True, ""

    return False, "Pedido deve ter ao menos um item com product_id e quantity > 0."


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
