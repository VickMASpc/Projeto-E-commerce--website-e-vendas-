"""Export service logic."""

from __future__ import annotations

import json
import os
from datetime import datetime

import config

STATUS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "export_status.json")


def build_export_content(products, orders) -> str:
    return (
        "/* Gerado automaticamente pelo Sistema de Vendas */\n"
        f"const PRODUCTS_LIVE = {json.dumps(products, indent=2, ensure_ascii=False)};\n"
        f"const ORDERS_LIVE = {json.dumps(orders, indent=2, ensure_ascii=False)};\n"
        "window.PRODUCTS_LIVE = PRODUCTS_LIVE;\n"
        "window.ORDERS_LIVE = ORDERS_LIVE;\n"
    )


def load_last_export_status() -> dict | None:
    if not os.path.exists(STATUS_FILE):
        return None

    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception:
        return None

    if not isinstance(data, dict):
        return None
    return data


def _save_export_status(status: str, message: str, export_path: str) -> dict:
    payload = {
        "status": status,
        "message": message,
        "export_path": export_path,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    try:
        with open(STATUS_FILE, "w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2, ensure_ascii=False)
    except Exception:
        pass
    return payload


def export_frontend_snapshot(data: dict, *, record_status: bool = True) -> dict:
    export_path = config.FRONTEND_EXPORT_PATH

    if not config.FRONTEND_EXPORT_ENABLED:
        message = "Exportacao para frontend esta desativada."
        return _save_export_status("disabled", message, export_path) if record_status else {
            "status": "disabled",
            "message": message,
            "export_path": export_path,
        }

    export_dir = os.path.dirname(export_path)
    if not os.path.exists(export_dir):
        message = "Diretorio de exportacao nao encontrado."
        return _save_export_status("error", message, export_path) if record_status else {
            "status": "error",
            "message": message,
            "export_path": export_path,
        }

    content = build_export_content(
        data.get("produtos", []),
        data.get("pedidos", []),
    )

    try:
        with open(export_path, "w", encoding="utf-8") as file:
            file.write(content)
    except Exception as error:
        message = f"Erro ao exportar para frontend: {error}"
        return _save_export_status("error", message, export_path) if record_status else {
            "status": "error",
            "message": message,
            "export_path": export_path,
        }

    message = "Exportacao concluida com sucesso."
    return _save_export_status("success", message, export_path) if record_status else {
        "status": "success",
        "message": message,
        "export_path": export_path,
    }


def export_current_data() -> dict:
    import database

    return export_frontend_snapshot(
        {
            "produtos": database.get_products(),
            "pedidos": database.get_orders(),
        }
    )
