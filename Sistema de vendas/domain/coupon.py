from datetime import datetime
from copy import deepcopy
from typing import Dict, Any


DEFAULT_COUPON = {
    "code": "",
    "type": "percent",  # percent or fixed
    "value": 0.0,
    "active": False,
    "min_order_total": 0.0,
    "max_discount": None,
    "usage_limit": None,
    "used_count": 0,
    "starts_at": None,
    "expires_at": None,
    "created_at": None,
}


def normalize_coupon(coupon: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes a coupon dictionary to a standard shape.
    Fields are mapped for compatibility and validated.
    """
    coupon = coupon or {}
    normalized = deepcopy(DEFAULT_COUPON)

    # Map legacy fields if present
    if "min_subtotal" in coupon and "min_order_total" not in coupon:
        coupon["min_order_total"] = coupon["min_subtotal"]

    normalized.update(coupon)

    # Normalize code
    code = str(normalized.get("code", "")).strip().upper()

    # Normalize type
    coupon_type = str(normalized.get("type", "percent")).strip().lower()
    if coupon_type not in {"percent", "fixed"}:
        coupon_type = "percent"

    # Normalize values
    value = float(normalized.get("value") or 0.0)
    if coupon_type == "percent":
        value = max(0.0, min(100.0, value))
    else:
        value = max(0.0, value)

    min_order_total = max(float(normalized.get("min_order_total") or 0.0), 0.0)

    max_discount = normalized.get("max_discount")
    if max_discount is not None and max_discount != "":
        max_discount = max(float(max_discount), 0.0)
    else:
        max_discount = None

    usage_limit = normalized.get("usage_limit")
    if usage_limit is not None and usage_limit != "":
        usage_limit = max(int(float(usage_limit)), 0)
    else:
        usage_limit = None

    used_count = max(int(float(normalized.get("used_count") or 0)), 0)

    # Maintain min_subtotal for backward compatibility
    # though we prefer min_order_total now.

    return {
        "code": code,
        "type": coupon_type,
        "value": value,
        "active": bool(normalized.get("active")),
        "min_order_total": min_order_total,
        "min_subtotal": min_order_total,  # Compatibility
        "max_discount": max_discount,
        "usage_limit": usage_limit,
        "used_count": used_count,
        "starts_at": normalized.get("starts_at"),
        "expires_at": normalized.get("expires_at"),
        "created_at": (
            normalized.get("created_at") or
            datetime.utcnow().isoformat() + "Z"
        ),
    }
