"""
services/dashboard_service.py
------------------------------
Centralised dashboard metrics service.

All public methods operate only through the repository interface so they
work identically in Firebase mode and local-JSON mode.

``database.get_stats()`` is kept as the backwards-compatibility facade and
now delegates entirely to ``DashboardService.get_dashboard_stats()``.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

import config


# ---------------------------------------------------------------------------
# Internal helpers (no external imports needed beyond stdlib)
# ---------------------------------------------------------------------------

def _to_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return fallback


def _to_int(value: Any, fallback: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return fallback


def _parse_date(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value

    raw = str(value or "").strip()
    for fmt in (
        "%d/%m/%Y %H:%M",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
    ):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue

    if raw.endswith("+00:00"):
        trimmed = raw[:-6]
        for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(trimmed, fmt)
            except ValueError:
                continue

    return datetime.now()


def _build_time_series(orders: List[Dict[str, Any]], min_days: int = 30) -> List[Dict[str, Any]]:
    orders_by_day: Dict = defaultdict(lambda: {"sales": 0.0, "orders": 0})

    if orders:
        parsed = [_parse_date(o.get("created_at")) for o in orders]
        end_date = max(parsed).date()
        start_date = min(parsed).date()
    else:
        end_date = datetime.now().date()
        start_date = end_date

    span = max((end_date - start_date).days + 1, 1)
    days = max(min_days, span)
    start_date = end_date.fromordinal(end_date.toordinal() - max(days - 1, 0))

    for order in orders:
        od = _parse_date(order.get("created_at")).date()
        if start_date <= od <= end_date:
            bucket = orders_by_day[od]
            bucket["sales"] += _to_float(order.get("total"))
            bucket["orders"] += 1

    points = []
    for offset in range(days):
        cd = start_date.fromordinal(start_date.toordinal() + offset)
        bucket = orders_by_day[cd]
        points.append({
            "date": cd.strftime("%d/%m"),
            "isoDate": cd.isoformat(),
            "sales": round(bucket["sales"], 2),
            "orders": bucket["orders"],
        })
    return points


def _period_totals(orders, start_date, end_date) -> Dict[str, Any]:
    selected = [o for o in orders if start_date <= _parse_date(o.get("created_at")).date() <= end_date]
    total_revenue = sum(_to_float(o.get("total")) for o in selected)
    return {"orders": len(selected), "revenue": round(total_revenue, 2)}


def _growth_pct(current: float, previous: float) -> float:
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100, 1)


# ---------------------------------------------------------------------------
# DashboardService
# ---------------------------------------------------------------------------

class DashboardService:
    """Computes all dashboard metrics from repository data."""

    def __init__(self, repository) -> None:
        self._repo = repository

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Full consolidated stats payload (backwards-compatible with get_stats())."""
        products = self._products()
        orders = self._orders()

        revenue = self.get_revenue_summary(products=products, orders=orders)
        order_summary = self.get_order_status_summary(orders=orders)
        low_stock = self.get_low_stock_summary(products=products)
        activity = self.get_recent_activity(orders=orders)
        top_prods = self.get_top_products(orders=orders, products=products)
        category_perf = self.get_category_performance(orders=orders, products=products)

        paid_orders = [o for o in orders if o.get("status") in {"pago", "enviado", "pendente"}]
        inventory_by_category: Dict[str, int] = defaultdict(int)
        for p in products:
            inventory_by_category[p.get("category", "Outros")] += _to_int(p.get("stock", 0))

        customer_sales: Dict[str, Dict] = defaultdict(lambda: {"revenue": 0.0, "orders": 0})
        for o in paid_orders:
            name = o.get("customer_name", "Cliente")
            customer_sales[name]["revenue"] += _to_float(o.get("total"))
            customer_sales[name]["orders"] += 1

        top_customers = sorted(
            ({"name": n, "revenue": round(m["revenue"], 2), "orders": m["orders"]} for n, m in customer_sales.items()),
            key=lambda x: x["revenue"],
            reverse=True,
        )[:5]

        last_day = datetime.now().date()
        last_7_start = last_day.fromordinal(last_day.toordinal() - 6)
        prev_7_end = last_day.fromordinal(last_day.toordinal() - 7)
        prev_7_start = prev_7_end.fromordinal(prev_7_end.toordinal() - 6)
        current_period = _period_totals(paid_orders, last_7_start, last_day)
        previous_period = _period_totals(paid_orders, prev_7_start, prev_7_end)

        orders_today = sum(
            1 for o in orders if _parse_date(o.get("created_at")).date() == last_day
        )
        realtime_revenue = sum(
            _to_float(o.get("total"))
            for o in orders
            if _parse_date(o.get("created_at")).date() == last_day
        )

        total_revenue = revenue["total_revenue"]
        total_orders = revenue["total_orders"]
        average_ticket = revenue["average_ticket"]

        status_map = order_summary["status_map"]

        return {
            "totalRevenue": round(total_revenue, 2),
            "totalOrders": total_orders,
            "averageTicket": round(average_ticket, 2),
            "inventoryUnits": sum(_to_int(p.get("stock", 0)) for p in products),
            "activeCategories": len(inventory_by_category),
            "ordersToday": orders_today,
            "paidOrders": status_map.get("pago", 0),
            "pendingOrders": status_map.get("pendente", 0),
            "shippedOrders": status_map.get("enviado", 0),
            "lowStockCount": low_stock["count"],
            "revenueDeltaPct": _growth_pct(current_period["revenue"], previous_period["revenue"]),
            "ordersDeltaPct": _growth_pct(current_period["orders"], previous_period["orders"]),
            "realtimeRevenue": round(realtime_revenue, 2),
            "lastUpdated": datetime.now().isoformat(timespec="seconds"),
            "periodSummary": {
                "current": current_period,
                "previous": previous_period,
            },
            "inventoryStatus": [
                {"name": cat, "value": qty}
                for cat, qty in sorted(inventory_by_category.items())
            ],
            "salesOverTime": _build_time_series(paid_orders, 30),
            "topProducts": top_prods,
            "recentActivity": activity,
            "categoryPerformance": category_perf,
            "orderStatus": [
                {"name": s.title(), "value": v}
                for s, v in sorted(status_map.items())
            ],
            "lowStockItems": low_stock["items"],
            "topCustomers": top_customers,
        }

    def get_revenue_summary(
        self,
        products: Optional[List] = None,
        orders: Optional[List] = None,
    ) -> Dict[str, Any]:
        """Total revenue, orders and average ticket from paid orders."""
        orders = orders if orders is not None else self._orders()
        paid = [o for o in orders if o.get("status") in {"pago", "enviado", "pendente"}]
        total_revenue = sum(_to_float(o.get("total")) for o in paid)
        total_orders = len(paid)
        average_ticket = total_revenue / total_orders if total_orders else 0.0
        return {
            "total_revenue": round(total_revenue, 2),
            "total_orders": total_orders,
            "average_ticket": round(average_ticket, 2),
        }

    def get_order_status_summary(self, orders: Optional[List] = None) -> Dict[str, Any]:
        """Count of orders grouped by status."""
        orders = orders if orders is not None else self._orders()
        status_map: Dict[str, int] = defaultdict(int)
        for o in orders:
            status_map[str(o.get("status", "pendente")).lower()] += 1

        pending_shipment = sum(
            v for k, v in status_map.items()
            if k in {"pago", "pendente", "separacao", "embalagem", "pronto_envio", "pagamento_pendente"}
        )
        return {
            "status_map": dict(status_map),
            "pending_shipment_count": pending_shipment,
        }

    def get_low_stock_summary(self, products: Optional[List] = None) -> Dict[str, Any]:
        """Products at or below LOW_STOCK_THRESHOLD."""
        products = products if products is not None else self._products()
        threshold = config.LOW_STOCK_THRESHOLD
        low = sorted(
            [
                {
                    "id": p["id"],
                    "name": p.get("name", "Produto"),
                    "category": p.get("category", "Outros"),
                    "stock": _to_int(p.get("stock", 0)),
                }
                for p in products
                if _to_int(p.get("stock", 0)) <= threshold
            ],
            key=lambda x: x["stock"],
        )[:10]
        return {"count": len(low), "items": low, "threshold": threshold}

    def get_recent_activity(self, orders: Optional[List] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Most recent order events."""
        orders = orders if orders is not None else self._orders()
        paid = [o for o in orders if o.get("status") in {"pago", "enviado", "pendente"}]
        activity = [
            {
                "id": o.get("id", ""),
                "label": f"Pedido {o.get('id', '')} - {o.get('status', 'pendente')}",
                "customer": o.get("customer_name", "Cliente"),
                "created_at": o.get("created_at", ""),
                "total": round(_to_float(o.get("total")), 2),
                "status": o.get("status", "pendente"),
            }
            for o in paid
        ]
        return activity[-limit:][::-1]

    def get_top_products(
        self,
        orders: Optional[List] = None,
        products: Optional[List] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Most sold products by unit count."""
        orders = orders if orders is not None else self._orders()
        products = products if products is not None else self._products()
        product_names = {p["id"]: p.get("name", "Produto") for p in products}
        sales: Dict[str, int] = defaultdict(int)
        for o in orders:
            for item in o.get("items", []):
                name = item.get("product_name") or product_names.get(item.get("product_id"), "Item")
                qty = _to_int(item.get("quantity"), 1)
                sales[name] += qty
        return sorted(
            ({"name": n, "sales": s} for n, s in sales.items()),
            key=lambda x: x["sales"],
            reverse=True,
        )[:limit]

    def get_category_performance(
        self,
        orders: Optional[List] = None,
        products: Optional[List] = None,
    ) -> List[Dict[str, Any]]:
        """Revenue and unit sales grouped by product category."""
        orders = orders if orders is not None else self._orders()
        products = products if products is not None else self._products()
        products_by_id = {p["id"]: p for p in products}
        perf: Dict[str, Dict] = defaultdict(lambda: {"value": 0.0, "orders": 0, "units": 0})
        for o in orders:
            seen: set = set()
            for item in o.get("items", []):
                product = products_by_id.get(item.get("product_id")) or {}
                cat = product.get("category", "Outros")
                qty = _to_int(item.get("quantity"), 1)
                price = _to_float(item.get("unit_price"))
                perf[cat]["value"] += qty * price
                perf[cat]["units"] += qty
                if cat not in seen:
                    perf[cat]["orders"] += 1
                    seen.add(cat)
        return sorted(
            ({"name": cat, "value": round(m["value"], 2), "orders": m["orders"], "units": m["units"]}
             for cat, m in perf.items()),
            key=lambda x: x["value"],
            reverse=True,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _products(self) -> List[Dict[str, Any]]:
        from services.product_service import ProductService
        return ProductService(self._repo).list_products()

    def _orders(self) -> List[Dict[str, Any]]:
        return self._repo.get_orders()

    def _coupons(self) -> List[Dict[str, Any]]:
        return self._repo.get_coupons()
