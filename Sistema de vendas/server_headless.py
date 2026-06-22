"""Entrypoint headless para iniciar somente a API HTTP do sistema de vendas."""

from __future__ import annotations

import os
import time

import config
import database
from api.server import start_api_server, stop_api_server


def _runtime_lines() -> list[str]:
    runtime = database.get_runtime_summary()
    backend = runtime.get("backend", "desconhecido").upper()
    mode = str(runtime.get("mode", "development")).upper()
    project_id = runtime.get("project_id", "desconhecido")
    credentials_path = runtime.get("credentials_path", "nao configurado")
    credentials_source = runtime.get("credentials_source", "desconhecido")
    credentials_present = "presente" if runtime.get("credentials_present") else "ausente"
    return [
        f"[Headless] Modo de execucao: {mode}",
        f"[Headless] Backend de dados: {backend}",
        f"[Headless] Projeto Firebase: {project_id}",
        f"[Headless] Credencial Firebase: {credentials_present} ({credentials_source}: {credentials_path})",
        f"[Headless] Runtime: {runtime.get('message', 'sem mensagem')}",
    ]


def main() -> None:
    host = config.API_HOST
    port = config.API_PORT
    display_host = host or "0.0.0.0"
    url_host = "localhost" if host in {"", "0.0.0.0"} else host

    print(f"[Headless] Host: {display_host}")
    print(f"[Headless] Porta: {port}")
    print(f"[Headless] URL local: http://{url_host}:{port}/health")
    for line in _runtime_lines():
        print(line)
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
