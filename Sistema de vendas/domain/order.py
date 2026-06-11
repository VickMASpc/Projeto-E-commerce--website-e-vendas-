"""Order domain model and normalization helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, Dict, Iterable, Mapping, Optional


STATUS_PENDENTE = "pendente"
STATUS_PAGAMENTO_PENDENTE = "pagamento_pendente"
STATUS_PAGO = "pago"
STATUS_SEPARACAO = "separacao"
STATUS_EMBALAGEM = "embalagem"
STATUS_PRONTO_ENVIO = "pronto_envio"
STATUS_ENVIADO = "enviado"
STATUS_ENTREGUE = "entregue"
STATUS_CANCELADO = "cancelado"
STATUS_DEVOLVIDO = "devolvido"

SUPPORTED_ORDER_STATUSES = {
    STATUS_PENDENTE,
    STATUS_PAGAMENTO_PENDENTE,
    STATUS_PAGO,
    STATUS_SEPARACAO,
    STATUS_EMBALAGEM,
    STATUS_PRONTO_ENVIO,
    STATUS_ENVIADO,
    STATUS_ENTREGUE,
    STATUS_CANCELADO,
    STATUS_DEVOLVIDO,
}

LEGACY_STATUS_ALIASES = {
    "pending": STATUS_PENDENTE,
    "paid": STATUS_PAGO,
    "shipped": STATUS_ENVIADO,
}


@dataclass
class OrderItem:
    product_id: str = ""
    product_name: str = "Item"
    quantity: int = 1
    unit_price: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Order:
    id: str = ""
    customer_id: Optional[str] = None
    customer_name: str = "Cliente"
    customer_email: str = ""
    customer_phone: str = ""
    customer_address: str = ""
    items: list[Dict[str, Any]] = field(default_factory=list)
    subtotal: float = 0.0
    shipping: float = 0.0
    discount_total: float = 0.0
    coupon_code: Optional[str] = None
    total: float = 0.0
    status: str = STATUS_PENDENTE
    created_at: str = ""
    updated_at: str = ""
    schema_version: int = 2

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


DEFAULT_ORDER_ITEM = OrderItem().to_dict()
DEFAULT_ORDER = Order().to_dict()


def parse_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return fallback


def parse_int(value: Any, fallback: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return fallback


def parse_date(value: Any, fallback: Optional[datetime] = None) -> datetime:
    if isinstance(value, datetime):
        return value

    text = str(value or "").strip()
    if not text:
        return fallback or datetime.now(UTC)

    normalized = text.replace("Z", "+00:00")
    formats: Iterable[str] = (
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    )

    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        pass

    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    return fallback or datetime.now(UTC)


def normalize_status(status: Any, fallback: str = STATUS_PENDENTE) -> str:
    normalized = str(status or fallback).strip().lower()
    normalized = LEGACY_STATUS_ALIASES.get(normalized, normalized)
    if normalized in SUPPORTED_ORDER_STATUSES:
        return normalized
    return fallback


def normalize_order_item(item: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    item = dict(item or {})
    normalized = OrderItem(
        product_id=str(
            item.get("product_id")
            or item.get("produto_id")
            or item.get("produtoId")
            or item.get("id")
            or ""
        ).strip(),
        product_name=str(
            item.get("product_name")
            or item.get("produtoNome")
            or item.get("nome_prod")
            or item.get("name")
            or "Item"
        ).strip() or "Item",
        quantity=max(parse_int(item.get("quantity", item.get("quantidade", 1)), 1), 1),
        unit_price=parse_float(item.get("unit_price", item.get("preco_unit", item.get("preco", 0.0)))),
    ).to_dict()
    return normalized


def normalize_order(order: Optional[Mapping[str, Any]], fallback_id: Optional[str] = None) -> Dict[str, Any]:
    order = dict(order or {})
    customer = dict(order.get("customer") or {})
    items = order.get("items") or order.get("itens") or []
    normalized_items = [normalize_order_item(item) for item in items]
    subtotal = parse_float(
        order.get("subtotal"),
        sum(item["quantity"] * item["unit_price"] for item in normalized_items),
    )
    shipping = parse_float(order.get("shipping"), 0.0)
    discount_total = max(parse_float(order.get("discount_total", order.get("discount")), 0.0), 0.0)
    total = parse_float(order.get("total"), subtotal - discount_total + shipping)
    coupon_code = str(order.get("coupon_code") or order.get("couponCode") or "").strip().upper() or None
    created_at = str(order.get("created_at") or order.get("dataCriacao") or "").strip()
    updated_at = str(order.get("updated_at") or order.get("atualizadoEm") or "").strip()

    normalized = Order(
        id=str(order.get("id") or fallback_id or "").strip(),
        customer_id=order.get("customer_id") or order.get("clienteId") or order.get("userId") or customer.get("id") or None,
        customer_name=str(order.get("customer_name") or order.get("clienteNome") or customer.get("name") or "Cliente").strip() or "Cliente",
        customer_email=str(order.get("customer_email") or order.get("clienteEmail") or customer.get("email") or "").strip(),
        customer_phone=str(order.get("customer_phone") or order.get("clienteTelefone") or customer.get("phone") or "").strip(),
        customer_address=str(order.get("customer_address") or order.get("clienteEndereco") or customer.get("address") or "").strip(),
        items=normalized_items,
        subtotal=subtotal,
        shipping=shipping,
        discount_total=discount_total,
        coupon_code=coupon_code,
        total=total,
        status=normalize_status(order.get("status"), STATUS_PENDENTE),
        created_at=created_at or parse_date(None).isoformat(timespec="seconds") + "Z",
        updated_at=updated_at or parse_date(None).isoformat(timespec="seconds") + "Z",
        schema_version=parse_int(order.get("schema_version") or order.get("schemaVersion") or 2, 2),
    ).to_dict()
    return normalized
