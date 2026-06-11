from services import export_service


def test_build_export_content_keeps_existing_frontend_shape():
    content = export_service.build_export_content(
        [{"id": "perf-1", "name": "Produto"}],
        [{"id": "ord-1", "status": "pago"}],
    )

    assert "const PRODUCTS_LIVE = [" in content
    assert "const ORDERS_LIVE = [" in content
    assert "window.PRODUCTS_LIVE = PRODUCTS_LIVE;" in content
    assert "window.ORDERS_LIVE = ORDERS_LIVE;" in content


def test_export_frontend_snapshot_records_success(tmp_path, monkeypatch):
    export_file = tmp_path / "products_live.js"
    status_file = tmp_path / "export_status.json"

    monkeypatch.setattr(export_service.config, "FRONTEND_EXPORT_ENABLED", True)
    monkeypatch.setattr(export_service.config, "FRONTEND_EXPORT_PATH", str(export_file))
    monkeypatch.setattr(export_service, "STATUS_FILE", str(status_file))

    result = export_service.export_frontend_snapshot(
        {
            "produtos": [{"id": "perf-1"}],
            "pedidos": [{"id": "ord-1"}],
        }
    )

    assert result["status"] == "success"
    assert export_file.exists()
    assert status_file.exists()
    assert "PRODUCTS_LIVE" in export_file.read_text(encoding="utf-8")


def test_export_frontend_snapshot_records_disabled_state(tmp_path, monkeypatch):
    export_file = tmp_path / "products_live.js"
    status_file = tmp_path / "export_status.json"

    monkeypatch.setattr(export_service.config, "FRONTEND_EXPORT_ENABLED", False)
    monkeypatch.setattr(export_service.config, "FRONTEND_EXPORT_PATH", str(export_file))
    monkeypatch.setattr(export_service, "STATUS_FILE", str(status_file))

    result = export_service.export_frontend_snapshot({"produtos": [], "pedidos": []})

    assert result["status"] == "disabled"
    assert not export_file.exists()
    assert status_file.exists()
