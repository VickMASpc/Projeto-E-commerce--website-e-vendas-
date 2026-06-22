from domain.order import canonical_order_contract, normalize_order


def test_canonical_contract_lists_expected_fields():
    contract = canonical_order_contract()

    assert contract["schema_version"] == 2
    assert contract["fields"] == [
        "id",
        "customer_id",
        "customer_name",
        "customer_email",
        "customer_phone",
        "customer_address",
        "items",
        "subtotal",
        "shipping",
        "discount_total",
        "coupon_code",
        "total",
        "status",
        "created_at",
        "updated_at",
        "schema_version",
    ]


def test_normalize_order_accepts_legacy_payload():
    normalized = normalize_order(
        {
            "id": "ord-legacy",
            "clienteId": "user-1",
            "clienteNome": "Cliente Legado",
            "clienteEmail": "legacy@example.com",
            "clienteTelefone": "11999999999",
            "clienteEndereco": "Rua A",
            "itens": [{"produtoId": "perf-1", "produtoNome": "Bleu", "quantidade": 2, "preco": 850}],
            "subtotal": 1700,
            "shipping": 0,
            "discount": 170,
            "couponCode": "BEMVINDO10",
            "total": 1530,
            "status": "paid",
            "dataCriacao": "2026-06-22T12:00:00Z",
            "schemaVersion": 2,
        }
    )

    assert normalized["customer_id"] == "user-1"
    assert normalized["customer_name"] == "Cliente Legado"
    assert normalized["discount_total"] == 170
    assert normalized["coupon_code"] == "BEMVINDO10"
    assert normalized["status"] == "pago"
    assert normalized["schema_version"] == 2


def test_normalize_order_accepts_new_function_payload_with_coupon():
    normalized = normalize_order(
        {
            "id": "ord-new",
            "customer_id": "user-2",
            "customer_name": "Cliente Novo",
            "customer_email": "novo@example.com",
            "customer_phone": "11888888888",
            "customer_address": "Rua B",
            "items": [
                {"product_id": "perf-1", "product_name": "Bleu", "quantity": 1, "unit_price": 850},
                {"product_id": "perf-2", "product_name": "Sauvage", "quantity": 1, "unit_price": 790},
            ],
            "subtotal": 1640,
            "shipping": 0,
            "discount_total": 100,
            "coupon_code": "VIP100",
            "total": 1540,
            "status": "pago",
            "created_at": "2026-06-22T12:01:00Z",
            "updated_at": "2026-06-22T12:01:30Z",
            "schema_version": 2,
        }
    )

    assert normalized["customer_email"] == "novo@example.com"
    assert len(normalized["items"]) == 2
    assert normalized["coupon_code"] == "VIP100"
    assert normalized["discount_total"] == 100
    assert normalized["schema_version"] == 2


def test_normalize_order_accepts_new_function_payload_without_coupon():
    normalized = normalize_order(
        {
            "id": "ord-no-coupon",
            "customer": {
                "id": "user-3",
                "name": "Cliente Sem Cupom",
                "email": "semcupom@example.com",
                "phone": "11777777777",
                "address": "Rua C",
            },
            "items": [{"id": "perf-3", "name": "N5", "quantity": 1, "unit_price": 920}],
            "subtotal": 920,
            "shipping": 0,
            "total": 920,
            "status": "pending",
        }
    )

    assert normalized["customer_id"] == "user-3"
    assert normalized["coupon_code"] is None
    assert normalized["discount_total"] == 0
    assert normalized["status"] == "pendente"


def test_normalize_order_preserves_multiple_items_and_total():
    normalized = normalize_order(
        {
            "id": "ord-multi",
            "items": [
                {"id": "perf-1", "name": "Bleu", "quantity": 2, "unit_price": 850},
                {"id": "perf-2", "name": "Sauvage", "quantity": 1, "unit_price": 790},
            ],
            "subtotal": 2490,
            "shipping": 0,
            "discount_total": 0,
            "total": 2490,
        }
    )

    assert [item["product_id"] for item in normalized["items"]] == ["perf-1", "perf-2"]
    assert normalized["total"] == 2490
