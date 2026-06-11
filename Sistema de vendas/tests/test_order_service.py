from domain.order import STATUS_ENVIADO, STATUS_PENDENTE, normalize_order
from services import order_service
from ui.orders_view import get_order_action_specs


class FakeOrderRepo:
    def __init__(self, orders):
        self.orders = [dict(order) for order in orders]

    def get_orders(self):
        return [dict(order) for order in self.orders]

    def update_order_status(self, pedido_id, novo_status):
        for order in self.orders:
            if order["id"] == pedido_id:
                order["status"] = novo_status
                order["updated_at"] = "2026-06-11T00:00:00Z"
                return

    def create_local_order(self, order):
        return {"ok": True, "message": "Pedido registrado.", "order_id": order.get("id", "ord-test")}


def test_normalize_order_preserves_legacy_status_aliases():
    normalized = normalize_order({"id": "ord-1", "status": "shipped"})
    assert normalized["status"] == STATUS_ENVIADO


def test_validate_status_transition_rejects_invalid_jump():
    result = order_service.validate_status_transition("pago", "entregue")
    assert result["ok"] is False
    assert "Transicao invalida" in result["message"]


def test_update_status_allows_legacy_direct_to_enviado(monkeypatch):
    repo = FakeOrderRepo([{"id": "ord-1", "status": STATUS_PENDENTE, "items": []}])
    monkeypatch.setattr(order_service, "_get_repo", lambda: repo)

    result = order_service.update_status("ord-1", STATUS_ENVIADO)

    assert result["ok"] is True
    assert result["status"] == STATUS_ENVIADO
    assert result["compatibility_mode"] == "legacy_direct_to_enviado"


def test_list_pending_shipments_excludes_finalized_orders(monkeypatch):
    repo = FakeOrderRepo(
        [
            {"id": "ord-1", "status": "pendente", "items": []},
            {"id": "ord-2", "status": "pronto_envio", "items": []},
            {"id": "ord-3", "status": "enviado", "items": []},
            {"id": "ord-4", "status": "cancelado", "items": []},
        ]
    )
    monkeypatch.setattr(order_service, "_get_repo", lambda: repo)

    pending_ids = [order["id"] for order in order_service.list_pending_shipments()]

    assert pending_ids == ["ord-1", "ord-2"]


def test_order_action_specs_follow_logistics_workflow():
    actions = get_order_action_specs({"id": "ord-10", "status": "embalagem", "items": []})

    assert [action["target_status"] for action in actions] == ["pronto_envio", "enviado", "cancelado"]


def test_order_action_specs_preserve_legacy_direct_sent():
    actions = get_order_action_specs({"id": "ord-11", "status": "pago", "items": []})

    assert [action["target_status"] for action in actions] == ["separacao", "enviado", "cancelado"]
