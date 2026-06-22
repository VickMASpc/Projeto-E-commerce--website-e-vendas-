"""Launcher para iniciar o servidor headless com arquivo arrastado no Windows."""

from __future__ import annotations

import json
import os
import shutil
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

APP_NAME = "GrandParfum"
DEFAULT_HOST = ""
DEFAULT_PORT = 5000


def _print_usage() -> None:
    print("Grand Parfum - launcher do servidor headless")
    print("")
    print("Arraste sobre LIGAR_SERVIDOR.bat um destes arquivos:")
    print("  1. serviceAccountKey.json do Firebase; ou")
    print("  2. server_config.json com host, port, credentialsPath, apiToken e allowedOrigins.")
    print("")
    print("Exemplo server_config.json:")
    print('{"host":"0.0.0.0","port":5000,"credentialsPath":"C:/seguro/serviceAccountKey.json","apiToken":"troque-este-token","allowedOrigins":["http://localhost:5173"]}')


def _load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Arquivo JSON invalido: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("O arquivo deve conter um objeto JSON.")
    return data


def _is_service_account(data: dict[str, Any]) -> bool:
    return data.get("type") == "service_account" and "private_key" in data


def _validate_service_account(data: dict[str, Any]) -> None:
    required = ("type", "project_id", "client_email", "private_key")
    missing = [field for field in required if not str(data.get(field) or "").strip()]
    if missing:
        raise ValueError(f"Service account incompleta. Campos ausentes: {', '.join(missing)}")
    if data.get("type") != "service_account":
        raise ValueError("O campo 'type' deve ser 'service_account'.")


def _appdata_dir() -> Path:
    root = os.getenv("APPDATA")
    if root:
        return Path(root) / APP_NAME
    return Path.home() / ".grandparfum"


def _copy_service_account(source: Path) -> Path:
    data = _load_json(source)
    _validate_service_account(data)

    target_dir = _appdata_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "serviceAccountKey.json"
    shutil.copyfile(source, target)
    os.environ["FIREBASE_CREDENTIALS_PATH"] = str(target)
    print(f"Credencial Firebase validada e copiada para: {target}")
    return target


def _as_int(value: Any, name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Campo '{name}' deve ser numerico.") from exc


def _as_origins(value: Any) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return ",".join(item.strip() for item in value if item.strip())
    raise ValueError("Campo 'allowedOrigins' deve ser string ou lista de strings.")


def _apply_config_file(path: Path) -> None:
    data = _load_json(path)

    if _is_service_account(data):
        _copy_service_account(path)
        return

    host = str(data.get("host", data.get("API_HOST", DEFAULT_HOST)) or "")
    port = _as_int(data.get("port", data.get("API_PORT", DEFAULT_PORT)), "port")
    if not 1 <= port <= 65535:
        raise ValueError("Campo 'port' deve estar entre 1 e 65535.")

    os.environ["API_HOST"] = host
    os.environ["API_PORT"] = str(port)

    api_token = str(data.get("apiToken", data.get("API_TOKEN", "")) or "").strip()
    if api_token:
        os.environ["API_TOKEN"] = api_token

    allowed_origins = _as_origins(data.get("allowedOrigins", data.get("ALLOWED_ORIGINS", "")))
    if allowed_origins:
        os.environ["ALLOWED_ORIGINS"] = allowed_origins

    credentials_path = data.get("credentialsPath", data.get("FIREBASE_CREDENTIALS_PATH"))
    if credentials_path:
        credential_file = Path(str(credentials_path)).expanduser()
        if not credential_file.is_absolute():
            credential_file = path.parent / credential_file
        if not credential_file.exists():
            raise ValueError(f"credentialsPath nao encontrado: {credential_file}")
        _copy_service_account(credential_file)

    frontend_export = data.get("frontendExportEnabled", data.get("FRONTEND_EXPORT_ENABLED"))
    if frontend_export is not None:
        os.environ["FRONTEND_EXPORT_ENABLED"] = "true" if bool(frontend_export) else "false"

    print("Configuracao do servidor carregada.")


def _detect_network_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return ""


def _wait_for_health(url: str, timeout_seconds: float = 8.0) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.5) as response:
                if response.status == 200:
                    payload = json.loads(response.read().decode("utf-8"))
                    return payload.get("status") == "ok"
        except (OSError, urllib.error.URLError, json.JSONDecodeError):
            time.sleep(0.4)
    return False


def _server_urls(host: str, port: int) -> tuple[str, str]:
    local_url = f"http://localhost:{port}"
    network_ip = _detect_network_ip()
    network_url = f"http://{network_ip}:{port}" if network_ip and host in {"", "0.0.0.0"} else ""
    return local_url, network_url


def _run_server() -> int:
    import config
    from api.server import start_api_server, stop_api_server

    host = config.API_HOST
    port = config.API_PORT
    local_url, network_url = _server_urls(host, port)

    print(f"Host: {host or '0.0.0.0'}")
    print(f"Porta: {port}")
    print(f"URL local: {local_url}")
    if network_url:
        print(f"URL de rede: {network_url}")

    credentials_path = config.FIREBASE_CREDENTIALS_PATH
    firebase_ready = bool(config.USE_FIREBASE and credentials_path and Path(credentials_path).exists())
    print("Modo de dados: Firebase" if firebase_ready else "Modo de dados: JSON/mock local")
    if not config.API_TOKEN:
        print("Aviso: API_TOKEN nao configurado; rotas de escrita ficarao sem autenticacao.")

    start_api_server(host=host, port=port)
    health_url = f"{local_url}/health"
    if _wait_for_health(health_url):
        print(f"Health check OK: {health_url}")
    else:
        print(f"Aviso: nao foi possivel confirmar /health em {health_url}")

    print("Servidor ativo. Pressione Ctrl+C para encerrar.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nEncerrando servidor...")
    finally:
        stop_api_server()
    return 0


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args or not args[0]:
        _print_usage()
        return 0

    dragged_file = Path(args[0]).expanduser()
    if not dragged_file.exists() or not dragged_file.is_file():
        print(f"Arquivo nao encontrado: {dragged_file}")
        _print_usage()
        return 1

    try:
        _apply_config_file(dragged_file)
        return _run_server()
    except Exception as exc:
        print(f"Erro: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
