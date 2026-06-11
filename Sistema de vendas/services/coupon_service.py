from datetime import datetime
from typing import List, Dict, Any, Optional
from domain.coupon import normalize_coupon


class CouponService:
    def __init__(self, repository):
        self.repository = repository

    def list_coupons(self) -> List[Dict[str, Any]]:
        """Returns all coupons, normalized."""
        coupons = self.repository.get_coupons()
        return [normalize_coupon(c) for c in coupons]

    def get_coupon(self, code: str) -> Optional[Dict[str, Any]]:
        """Finds a coupon by code."""
        if not code:
            return None
        normalized_code = code.strip().upper()
        coupons = self.list_coupons()
        return next((c for c in coupons if c["code"] == normalized_code), None)

    def create_coupon(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a new coupon."""
        normalized = normalize_coupon(payload)

        # Check if code already exists
        existing = self.get_coupon(normalized["code"])
        if existing:
            return {
                "ok": False,
                "message": f"Cupom '{normalized['code']}' já existe."
            }

        data = self.repository.read_data()
        data.setdefault("cupons", [])
        data["cupons"].append(normalized)
        self.repository.write_data(data)

        return {"ok": True, "coupon": normalized}

    def update_coupon(
        self,
        code: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Updates an existing coupon."""
        normalized_code = code.strip().upper()
        data = self.repository.read_data()
        coupons = data.get("cupons", [])

        found_index = -1
        for i, c in enumerate(coupons):
            if c.get("code", "").upper() == normalized_code:
                found_index = i
                break

        if found_index == -1:
            return {"ok": False, "message": "Cupom não encontrado."}

        # Merge and normalize
        updated_coupon = {**coupons[found_index], **payload}
        normalized = normalize_coupon(updated_coupon)
        # Ensure code doesn't change unless explicitly intended
        normalized["code"] = normalized_code

        data["cupons"][found_index] = normalized
        self.repository.write_data(data)

        return {"ok": True, "coupon": normalized}

    def deactivate_coupon(self, code: str) -> Dict[str, Any]:
        """Deactivates a coupon."""
        return self.update_coupon(code, {"active": False})

    def validate_coupon(self, code: str, order_total: float) -> Dict[str, Any]:
        """
        Validates if a coupon can be applied to an order total.
        Returns a result compatible with the UI/API.
        """
        normalized_code = str(code or "").strip().upper()
        total_value = max(float(order_total or 0.0), 0.0)

        if not normalized_code:
            return {
                "valid": False,
                "code": None,
                "discount": 0.0,
                "message": "Informe um cupom.",
                "adjusted_total": total_value,
            }

        coupon = self.get_coupon(normalized_code)
        if not coupon:
            return {
                "valid": False,
                "code": normalized_code,
                "discount": 0.0,
                "message": "Cupom não encontrado.",
                "adjusted_total": total_value,
            }

        if not coupon.get("active"):
            return {
                "valid": False,
                "code": normalized_code,
                "discount": 0.0,
                "message": "Cupom inativo.",
                "adjusted_total": total_value,
            }

        # Date validation
        now = datetime.utcnow()

        starts_at = self._parse_iso_date(coupon.get("starts_at"))
        if starts_at and starts_at > now:
            return {
                "valid": False,
                "code": normalized_code,
                "discount": 0.0,
                "message": "Este cupom ainda não é válido.",
                "adjusted_total": total_value,
            }

        expires_at = self._parse_iso_date(coupon.get("expires_at"))
        if expires_at and expires_at < now:
            return {
                "valid": False,
                "code": normalized_code,
                "discount": 0.0,
                "message": "Cupom expirado.",
                "adjusted_total": total_value,
            }

        # Min total validation
        min_total = coupon.get("min_order_total", 0.0)
        if total_value < min_total:
            return {
                "valid": False,
                "code": normalized_code,
                "discount": 0.0,
                "message": (
                    f"Cupom disponível apenas para pedidos "
                    f"acima de R$ {min_total:.2f}."
                ),
                "adjusted_total": total_value,
            }

        # Usage limit validation
        usage_limit = coupon.get("usage_limit")
        used_count = coupon.get("used_count", 0)
        if usage_limit is not None and used_count >= usage_limit:
            return {
                "valid": False,
                "code": normalized_code,
                "discount": 0.0,
                "message": "Cupom esgotado.",
                "adjusted_total": total_value,
            }

        # Calculate discount
        discount = self.calculate_discount(coupon, total_value)
        adjusted_total = max(total_value - discount, 0.0)

        return {
            "valid": True,
            "code": normalized_code,
            "discount": round(discount, 2),
            "message": "Cupom aplicado com sucesso.",
            "adjusted_total": round(adjusted_total, 2),
        }

    def calculate_discount(
        self,
        coupon: Dict[str, Any],
        order_total: float
    ) -> float:
        """Calculates the discount amount for a given coupon and total."""
        if coupon.get("type") == "fixed":
            discount = float(coupon.get("value", 0.0))
        else:
            discount = order_total * (float(coupon.get("value", 0.0)) / 100.0)

        max_discount = coupon.get("max_discount")
        if max_discount is not None:
            discount = min(discount, float(max_discount))

        return max(0.0, min(discount, order_total))

    def mark_coupon_used(self, code: str) -> bool:
        """Increments the used_count of a coupon."""
        coupon = self.get_coupon(code)
        if not coupon:
            return False

        updated = self.update_coupon(
            code,
            {"used_count": coupon.get("used_count", 0) + 1}
        )
        return updated["ok"]

    def _parse_iso_date(self, date_str: Any) -> Optional[datetime]:
        if not date_str or not isinstance(date_str, str):
            return None
        try:
            # Handle Z suffix
            if date_str.endswith("Z"):
                date_str = date_str[:-1]
            return datetime.fromisoformat(date_str)
        except ValueError:
            return None
