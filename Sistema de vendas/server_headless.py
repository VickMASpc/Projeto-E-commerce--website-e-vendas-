"""Entrypoint headless para iniciar somente a API HTTP do sistema de vendas."""

from __future__ import annotations

import os
import time

import config
from api.server import start_api_server, stop_api_server


def _firebase_mode() -> str:
    credentials_path = config.FIREBASE_CREDENTIALS_PATH
    if config.USE_FIREBASE and credentials_path and os.path.exists(credentials_path):
        return f"Firebase ({config.FIREBASE_CREDENTIALS_SOURCE}: {credentials_path})"
    return "JSON/mock local (credencial Firebase ausente ou desabilitada)"


def main() -> None:
    host = config.API_HOST
    port = config.API_PORT
    display_host = host or "0.0.0.0"
    url_host = "localhost" if host in {"", "0.0.0.0"} else host

    print(f"[Headless] Host: {display_host}")
    print(f"[Headless] Porta: {port}")
    print(f"[Headless] URL local: http://{url_host}:{port}/health")
    print(f"[Headless] Modo de dados: {_firebase_mode()}")
    print("[Headless] Pressione Ctrl+C para encerrar.")

    start_api_server(host=host, port=port)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Headless] Encerrando servidor...")
    finally:
        stop_api_server()


if __name__ == "__main__":
    main()
