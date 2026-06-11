"""Order service logic."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from domain.order import (
    STATUS_CANCELADO,
    STATUS_DEVOLVIDO,
    STATUS_EMBALAGEM,
    STATUS_ENVIADO,
    STATUS_ENTREGUE,
    STATUS_PAGAMENTO_PENDENTE,
    STATUS_PAGO,
    STATUS_PENDENTE,
    STATUS_PRONTO_ENVIO,
    STATUS_SEPARACAO,
    SUPPORTED_ORDER_STATUSES,
    normalize_order,
    normalize_status,
)


STATUS_TRANSITIONS = {
    STATUS_PENDENTE: {STATUS_PAGAMENTO_PENDENTE, STATUS_PAGO, STATUS_CANCELADO},
    STATUS_PAGAMENTO_PENDENTE: {STATUS_PAGO, STATUS_CANCELADO},
    STATUS_PAGO: {STATUS_SEPARACAO, STATUS_CANCELADO},
    STATUS_SEPARACAO: {STATUS_EMBALAGEM, STATUS_CANCELADO},
    STATUS_EMBALAGEM: {STATUS_PRONTO_ENVIO, STATUS_CANCELADO},
    STATUS_PRONTO_ENVIO: {STATUS_ENVIADO},
    STATUS_ENVIADO: {STATUS_ENTREGUE, STATUS_DEVOLVIDO},
    STATUS_ENTREGUE: set(),
    STATUS_CANCELADO: set(),
    STATUS_DEVOLVIDO: set(),
}

LEGACY_DIRECT_ENVIADO_SOURCES = {
    STATUS_PENDENTE,
    STATUS_PAGAMENTO_PENDENTE,
    STATUS_PAGO,
    STATUS_SEPARACAO,
    STATUS_EMBALAGEM,
    STATUS_PRONTO_ENVIO,
}

PENDING_SHIPMENT_STATUSES = {
    STATUS_PENDENTE,
    STATUS_PAGAMENTO_PENDENTE,
    STATUS_PAGO,
    STATUS_SEPARACAO,
    STATUS_EMBALAGEM,
    STATUS_PRONTO_ENVIO,
}


def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _get_repo():
    from database import _get_repo

    return _get_repo()


def list_orders() -> list[Dict[str, Any]]:
    return [normalize_order(order) for order in _get_repo().get_orders()]


def get_order(order_id: str) -> Optional[Dict[str, Any]]:
    order_id = str(order_id or "").strip()
    if not order_id:
        return None

    for order in list_orders():
        if order.get("id") == order_id:
            return order
    return None


def validate_status_transition(current_status: Any, new_status: Any) -> Dict[str, Any]:
    current = normalize_status(current_status)
    target = normalize_status(new_status, "")

    if target not in SUPPORTED_ORDER_STATUSES:
        return {
            "ok": False,
            "message": f"Status invalido: {new_status}.",
            "current_status": current,
            "new_status": target or str(new_status or "").strip().lower(),
        }

    if current == target:
        return {"ok": True, "message": "Status inalterado.", "current_status": current, "new_status": target}

    if target == STATUS_ENVIADO and current in LEGACY_DIRECT_ENVIADO_SOURCES:
        return {
            "ok": True,
            "message": "Transicao legacy mapeada com seguranca para enviado.",
            "current_status": current,
            "new_status": target,
            "compatibility_mode": "legacy_direct_to_enviado",
        }

    allowed = STATUS_TRANSITIONS.get(current, set())
    if target not in allowed:
        allowed_text = ", ".join(sorted(allowed)) or "nenhum"
        return {
            "ok": False,
            "message": f"Transicao invalida de {current} para {target}. Permitidos: {allowed_text}.",
            "current_status": current,
            "new_status": target,
        }

    return {"ok": True, "message": "Transicao valida.", "current_status": current, "new_status": target}


def create_order(payload: Dict[str, Any]) -> Dict[str, Any]:
    return _get_repo().create_local_order(payload)


def update_status(order_id: str, new_status: Any) -> Dict[str, Any]:
    order = get_order(order_id)
    if not order:
        return {"ok": False, "message": f"Pedido {order_id} nao encontrado.", "order_id": order_id}

    validation = validate_status_transition(order.get("status"), new_status)
    if not validation["ok"]:
        return {
            "ok": False,
            "message": validation["message"],
            "order_id": order_id,
            "current_status": validation.get("current_status"),
            "new_status": validation.get("new_status"),
        }

    target_status = validation["new_status"]
    repo = _get_repo()

    # Reuse repository-native update flow so JSON and Firebase keep their current persistence paths.
    repo.update_order_status(order_id, target_status)
    updated = get_order(order_id)

    return {
        "ok": True,
        "message": f"Status do pedido {order_id} atualizado para {target_status}.",
        "order_id": order_id,
        "status": target_status,
        "order": updated,
        "compatibility_mode": validation.get("compatibility_mode"),
        "updated_at": updated.get("updated_at") if updated else _now_iso(),
    }


def list_orders_by_status(status: Any) -> list[Dict[str, Any]]:
    normalized_status = normalize_status(status, "")
    if normalized_status not in SUPPORTED_ORDER_STATUSES:
        return []
    return [order for order in list_orders() if order.get("status") == normalized_status]


def list_pending_shipments() -> list[Dict[str, Any]]:
    return [order for order in list_orders() if order.get("status") in PENDING_SHIPMENT_STATUSES]
