"""
api/routes.py
-------------
Route handlers for the embedded HTTPServer.

All handlers are **stateless** – they read/write through `database` and
the service layer.  An optional `on_order_created` callback (injected by
the UI or any other caller) is stored on the HTTPServer instance so the
handler can fire it after a successful order creation without importing
UI code.

Supported routes
----------------
GET  /health
GET  /stats
GET  /products
GET  /orders
POST /order            (legacy alias)
POST /orders           (new alias – same behaviour)
PATCH /orders/{id}/status
POST /coupon/validate
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler
from typing import Any, Dict

import database
from api.schemas import (
    error_response,
    ok_response,
    serialise_health,
    serialise_orders,
    serialise_products,
    validate_coupon_payload,
    validate_order_payload,
    validate_status_patch,
)


class _OrderHandler(BaseHTTPRequestHandler):
    """Request handler. Instances are created by HTTPServer per request."""

    # ------------------------------------------------------------------
    # Silence default request-log noise (override to restore if wanted)
    # ------------------------------------------------------------------
    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: D401
        pass  # suppress per-request console spam

    # ------------------------------------------------------------------
    # CORS pre-flight
    # ------------------------------------------------------------------
    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    # ------------------------------------------------------------------
    # GET dispatcher
    # ------------------------------------------------------------------
    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?")[0].rstrip("/")

        if path == "/health":
            self._json(200, serialise_health())
            return

        if path == "/stats":
            self._json(200, database.get_stats())
            return

        if path == "/products":
            self._json(200, serialise_products(database.get_products()))
            return

        if path == "/orders":
            self._json(200, serialise_orders(database.get_orders()))
            return

        self._json(404, {"status": "error", "message": "Rota nao encontrada."})

    # ------------------------------------------------------------------
    # POST dispatcher
    # ------------------------------------------------------------------
    def do_POST(self) -> None:  # noqa: N802
        payload = self._read_json()
        if payload is None:
            return  # _read_json already sent 400

        path = self.path.split("?")[0].rstrip("/")

        if path == "/coupon/validate":
            valid, msg = validate_coupon_payload(payload)
            if not valid:
                self._json(*error_response(msg))
                return
            result = database.validate_coupon(
                payload.get("code"),
                payload.get("subtotal"),
            )
            self._json(200, result)
            return

        if path in ("/order", "/orders"):
            self._handle_create_order(payload)
            return

        self._json(404, {"status": "error", "message": "Rota nao encontrada."})

    # ------------------------------------------------------------------
    # PATCH dispatcher  (PATCH /orders/{id}/status)
    # ------------------------------------------------------------------
    def do_PATCH(self) -> None:  # noqa: N802
        path = self.path.split("?")[0].rstrip("/")
        parts = path.split("/")

        # Expected shape:  /orders/<id>/status
        if len(parts) == 4 and parts[1] == "orders" and parts[3] == "status":
            order_id = parts[2]
            payload = self._read_json()
            if payload is None:
                return

            valid, msg = validate_status_patch(payload)
            if not valid:
                self._json(*error_response(msg))
                return

            result = database.update_order_status(order_id, payload["status"])
            if not result.get("ok"):
                self._json(400, {"status": "error", "message": result.get("message", "Erro ao atualizar status.")})
                return

            self._json(200, ok_response({"order_id": order_id, "status": result.get("status")}))
            return

        self._json(404, {"status": "error", "message": "Rota nao encontrada."})

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _handle_create_order(self, payload: Dict[str, Any]) -> None:
        valid, msg = validate_order_payload(payload)
        if not valid:
            self._json(*error_response(msg))
            return

        result = database.create_local_order(payload)
        if not result.get("ok"):
            self._json(400, {"status": "error", "message": result.get("message", "Erro ao criar pedido.")})
            return

        # Fire the optional UI callback (injected onto the server instance).
        callback = getattr(self.server, "on_order_created", None)
        if callable(callback):
            try:
                customer_name = database.normalize_order(payload).get("customer_name", "Cliente")
                callback(order_id=result.get("order_id", ""), customer_name=customer_name)
            except Exception:
                pass  # never let a UI callback crash the API thread

        self._json(200, ok_response({"order_id": result.get("order_id")}))

    def _read_json(self) -> Any:
        """Read and parse the request body.  Sends 400 and returns None on failure."""
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length else b"{}"
            return json.loads(body or b"{}")
        except (ValueError, json.JSONDecodeError) as exc:
            self._json(400, {"status": "error", "message": f"Payload invalido: {exc}"})
            return None

    def _cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, status: int, payload: Any) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
