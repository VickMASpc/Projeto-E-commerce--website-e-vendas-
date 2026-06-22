"""
api/server.py
-------------
Manage the lifecycle of the embedded HTTP API server.

Usage
-----
    from api.server import start_api_server, stop_api_server

    start_api_server(
        host="",
        port=5000,
        on_order_created=my_callback,   # optional
    )

    # later (if needed):
    stop_api_server()

The optional ``on_order_created`` callback receives keyword arguments:
    on_order_created(order_id: str, customer_name: str)

The server runs in a **daemon** thread so it is automatically torn down
when the main process exits.  Calling ``stop_api_server()`` explicitly
triggers an orderly HTTPServer.shutdown() from a separate thread to
avoid deadlocking the server's own thread.
"""

from __future__ import annotations

import threading
from http.server import HTTPServer
from typing import Callable, Optional

from api.routes import _OrderHandler



# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------
_server: Optional[HTTPServer] = None
_server_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def start_api_server(
    host: str = "",
    port: int = 5000,
    on_order_created: Optional[Callable[..., None]] = None,
) -> HTTPServer:
    """Start the API server in a daemon thread.

    Parameters
    ----------
    host:
        Bind address.  Empty string means all interfaces (same as ``config.API_HOST``).
    port:
        TCP port. Defaults to ``config.API_PORT`` if not overridden.
    on_order_created:
        Optional callback fired when POST /order or POST /orders succeeds.
        Signature: ``on_order_created(order_id: str, customer_name: str)``.

    Returns
    -------
    HTTPServer
        The created server instance (already running in the daemon thread).
    """
    global _server

    with _server_lock:
        if _server is not None:
            return _server  # already running – idempotent

        httpd = HTTPServer((host, port), _OrderHandler)

        # Inject optional callback so _OrderHandler can reach it without
        # importing any UI module.
        httpd.on_order_created = on_order_created  # type: ignore[attr-defined]

        _server = httpd

        try:
            import config
            if not config.API_TOKEN:
                print("[API] Aviso: API_TOKEN nao definido; rotas de escrita estao sem autenticacao.")
        except Exception:
            pass

    def _serve() -> None:
        print(f"[API] Servidor de integracao rodando em http://{host or '0.0.0.0'}:{port}/")
        try:
            httpd.serve_forever()
        except Exception as exc:
            print(f"[API] Servidor encerrado: {exc}")

    thread = threading.Thread(target=_serve, daemon=True, name="ApiServer")
    thread.start()
    return httpd


def stop_api_server() -> None:
    """Orderly shutdown of the running API server (if any)."""
    global _server

    with _server_lock:
        server = _server
        _server = None

    if server is not None:
        # shutdown() blocks until serve_forever() returns, so call it
        # from a separate thread to avoid blocking the caller.
        threading.Thread(target=server.shutdown, daemon=True, name="ApiServerShutdown").start()
        print("[API] Servidor encerrado.")
