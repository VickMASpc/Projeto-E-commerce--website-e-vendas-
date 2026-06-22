"""Launcher para iniciar o servidor headless com configuração persistida fora do repositório."""

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
DEFAULT_MODE = "production"
CONFIG_FILENAME = "launcher_config.json"


def _print_usage() -> None:
    app_dir = _appdata_dir()
    print("Grand Parfum - launcher do servidor headless")
    print("")
    print("Uso recomendado:")
    print("  1. Primeira configuracao: arraste o serviceAccountKey.json do Firebase sobre LIGAR_SERVIDOR.bat.")
    print("  2. Uso diario: execute LIGAR_SERVIDOR.bat sem arrastar nada.")
    print("")
    print(f"O launcher salva a configuracao local em: {app_dir}")
    print("Arquivos persistidos:")
    print(f"  - {app_dir / 'serviceAccountKey.json'}")
    print(f"  - {app_dir / CONFIG_FILENAME}")
    print("")
    print("Modo padrao:")
    print("  - Producao com Firebase obrigatorio quando houver credencial valida.")
    print("  - Mock/JSON apenas em development/test com flags explicitas.")
    print("")
    print("Tambem e possivel arrastar um server_config.json externo com host/porta/token/origins.")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Arquivo JSON invalido: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("O arquivo deve conter um objeto JSON.")
    return data


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


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


def _persisted_config_path() -> Path:
    return _appdata_dir() / CONFIG_FILENAME


def _persisted_credentials_path() -> Path:
    return _appdata_dir() / "serviceAccountKey.json"


def _load_persisted_config() -> dict[str, Any]:
    path = _persisted_config_path()
    if not path.exists():
        return {}
    return _load_json(path)


def _save_persisted_config(data: dict[str, Any]) -> None:
    _write_json(_persisted_config_path(), data)


def _merge_persisted_config(**updates: Any) -> dict[str, Any]:
    current = _load_persisted_config()
    current.update({key: value for key, value in updates.items() if value is not None})
    _save_persisted_config(current)
    return current


def _copy_service_account(source: Path) -> tuple[Path, dict[str, Any]]:
    data = _load_json(source)
    _validate_service_account(data)

    target_dir = _appdata_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    target = _persisted_credentials_path()
    shutil.copyfile(source, target)
    os.environ["FIREBASE_CREDENTIALS_PATH"] = str(target)
    os.environ["GRAND_PARFUM_MODE"] = DEFAULT_MODE
    os.environ["USE_FIREBASE"] = "true"
    print(f"Credencial Firebase validada e copiada para: {target}")
    print(f"Projeto Firebase identificado: {data.get('project_id', 'desconhecido')}")
    return target, data


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


def _as_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on", "sim"}


def _resolve_external_path(value: Any, base_path: Path) -> Path | None:
    if value in (None, ""):
        return None
    raw = str(value).replace("%APPDATA%", os.getenv("APPDATA", "")).strip()
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = base_path.parent / candidate
    return candidate


def _persist_runtime_config(
    *,
    host: str,
    port: int,
    api_token: str,
    allowed_origins: str,
    frontend_export_enabled: bool | None,
    mode: str,
    credentials_path: Path | None,
    project_id: str | None = None,
) -> dict[str, Any]:
    payload = {
        "host": host,
        "port": port,
        "apiToken": api_token,
        "allowedOrigins": allowed_origins,
        "frontendExportEnabled": frontend_export_enabled,
        "mode": mode,
        "credentialsPath": str(credentials_path) if credentials_path else "",
        "projectId": project_id or "",
    }
    return _merge_persisted_config(**payload)


def _apply_env_config(config_data: dict[str, Any]) -> dict[str, Any]:
    host = str(config_data.get("host", config_data.get("API_HOST", DEFAULT_HOST)) or "")
    port = _as_int(config_data.get("port", config_data.get("API_PORT", DEFAULT_PORT)), "port")
    if not 1 <= port <= 65535:
        raise ValueError("Campo 'port' deve estar entre 1 e 65535.")

    mode = str(config_data.get("mode", config_data.get("GRAND_PARFUM_MODE", DEFAULT_MODE)) or DEFAULT_MODE).strip().lower()
    if mode not in {"production", "development", "test"}:
        raise ValueError(f"Modo invalido: {mode!r}.")

    api_token = str(config_data.get("apiToken", config_data.get("API_TOKEN", "")) or "").strip()
    allowed_origins = _as_origins(config_data.get("allowedOrigins", config_data.get("ALLOWED_ORIGINS", "")))
    frontend_export_enabled = config_data.get("frontendExportEnabled", config_data.get("FRONTEND_EXPORT_ENABLED"))
    credentials_path = str(config_data.get("credentialsPath", config_data.get("FIREBASE_CREDENTIALS_PATH", "")) or "").strip()
    allow_mock = _as_bool(config_data.get("allowMock", config_data.get("GRAND_PARFUM_ALLOW_MOCK", False)), False)
    use_firebase = _as_bool(config_data.get("useFirebase", config_data.get("USE_FIREBASE", True)), True)

    os.environ["API_HOST"] = host
    os.environ["API_PORT"] = str(port)
    os.environ["GRAND_PARFUM_MODE"] = mode
    os.environ["USE_FIREBASE"] = "true" if use_firebase else "false"
    if allow_mock:
        os.environ["GRAND_PARFUM_ALLOW_MOCK"] = "true"
    else:
        os.environ.pop("GRAND_PARFUM_ALLOW_MOCK", None)

    if api_token:
        os.environ["API_TOKEN"] = api_token
    elif "API_TOKEN" in os.environ:
        del os.environ["API_TOKEN"]

    if allowed_origins:
        os.environ["ALLOWED_ORIGINS"] = allowed_origins
    elif "ALLOWED_ORIGINS" in os.environ:
        del os.environ["ALLOWED_ORIGINS"]

    if frontend_export_enabled is not None:
        os.environ["FRONTEND_EXPORT_ENABLED"] = "true" if bool(frontend_export_enabled) else "false"

    if credentials_path:
        os.environ["FIREBASE_CREDENTIALS_PATH"] = credentials_path
    elif "FIREBASE_CREDENTIALS_PATH" in os.environ:
        del os.environ["FIREBASE_CREDENTIALS_PATH"]

    return {
        "host": host,
        "port": port,
        "mode": mode,
        "credentials_path": credentials_path,
        "api_token": api_token,
        "allowed_origins": allowed_origins,
        "frontend_export_enabled": frontend_export_enabled,
    }


def _apply_config_file(path: Path) -> dict[str, Any]:
    data = _load_json(path)

    if _is_service_account(data):
        credentials_path, credential_data = _copy_service_account(path)
        return _persist_runtime_config(
            host=DEFAULT_HOST,
            port=DEFAULT_PORT,
            api_token="",
            allowed_origins="",
            frontend_export_enabled=None,
            mode=DEFAULT_MODE,
            credentials_path=credentials_path,
            project_id=str(credential_data.get("project_id") or ""),
        )

    host = str(data.get("host", data.get("API_HOST", DEFAULT_HOST)) or "")
    port = _as_int(data.get("port", data.get("API_PORT", DEFAULT_PORT)), "port")
    if not 1 <= port <= 65535:
        raise ValueError("Campo 'port' deve estar entre 1 e 65535.")

    api_token = str(data.get("apiToken", data.get("API_TOKEN", "")) or "").strip()
    allowed_origins = _as_origins(data.get("allowedOrigins", data.get("ALLOWED_ORIGINS", "")))
    frontend_export_enabled = data.get("frontendExportEnabled", data.get("FRONTEND_EXPORT_ENABLED"))
    mode = str(data.get("mode", data.get("GRAND_PARFUM_MODE", DEFAULT_MODE)) or DEFAULT_MODE).strip().lower()

    credentials_path = data.get("credentialsPath", data.get("FIREBASE_CREDENTIALS_PATH"))
    resolved_credentials: Path | None = None
    project_id = ""
    if credentials_path:
        credential_file = _resolve_external_path(credentials_path, path)
        if credential_file is None or not credential_file.exists():
            raise ValueError(f"credentialsPath nao encontrado: {credential_file}")
        resolved_credentials, credential_data = _copy_service_account(credential_file)
        project_id = str(credential_data.get("project_id") or "")
        mode = DEFAULT_MODE if mode == DEFAULT_MODE or not mode else mode

    persisted = _persist_runtime_config(
        host=host,
        port=port,
        api_token=api_token,
        allowed_origins=allowed_origins,
        frontend_export_enabled=bool(frontend_export_enabled) if frontend_export_enabled is not None else None,
        mode=mode,
        credentials_path=resolved_credentials or (_resolve_external_path(credentials_path, path) if credentials_path else _persisted_credentials_path() if _persisted_credentials_path().exists() else None),
        project_id=project_id or _load_persisted_config().get("projectId", ""),
    )
    print("Configuracao do servidor carregada e salva fora do repositorio.")
    return persisted


def _apply_persisted_runtime() -> dict[str, Any]:
    persisted = _load_persisted_config()
    credentials_path = _persisted_credentials_path()

    if credentials_path.exists():
        persisted.setdefault("credentialsPath", str(credentials_path))
        persisted.setdefault("mode", DEFAULT_MODE)
        persisted.setdefault("useFirebase", True)

    if not persisted:
        raise RuntimeError(
            "Nenhuma configuracao local foi encontrada. "
            "Arraste o serviceAccountKey.json do Firebase sobre LIGAR_SERVIDOR.bat na primeira configuracao."
        )

    if persisted.get("mode", DEFAULT_MODE) == "production" and not credentials_path.exists():
        raise RuntimeError(
            "Configuracao local encontrada, mas a credencial Firebase nao esta presente em "
            f"{credentials_path}. Refaça a configuracao inicial com o serviceAccountKey.json."
        )

    env_applied = _apply_env_config(persisted)
    print("Configuracao local carregada.")
    if credentials_path.exists():
        print(f"Usando credencial persistida em: {credentials_path}")
    return env_applied


def _detect_network_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return ""


def _wait_for_health(url: str, timeout_seconds: float = 8.0) -> tuple[bool, dict[str, Any] | None]:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.5) as response:
                payload = json.loads(response.read().decode("utf-8"))
                if response.status == 200 and payload.get("status") == "ok":
                    return True, payload
        except (OSError, urllib.error.URLError, json.JSONDecodeError):
            time.sleep(0.4)
    return False, None


def _server_urls(host: str, port: int) -> tuple[str, str]:
    local_url = f"http://localhost:{port}"
    network_ip = _detect_network_ip()
    network_url = f"http://{network_ip}:{port}" if network_ip and host in {"", "0.0.0.0"} else ""
    return local_url, network_url


def _run_server() -> int:
    import config
    import database
    from api.server import start_api_server, stop_api_server

    host = config.API_HOST
    port = config.API_PORT
    local_url, network_url = _server_urls(host, port)

    print(f"Host: {host or '0.0.0.0'}")
    print(f"Porta: {port}")
    print(f"URL local: {local_url}")
    if network_url:
        print(f"URL de rede: {network_url}")

    runtime = database.get_runtime_summary()
    print(f"Modo de execucao: {str(runtime.get('mode', 'development')).upper()}")
    print(f"Firebase: {'ATIVO' if runtime.get('backend') == 'firebase' else 'INATIVO'}")
    print(f"Backend de dados: {str(runtime.get('backend', 'desconhecido')).upper()}")
    print(f"Projeto Firebase: {runtime.get('project_id', 'desconhecido')}")
    print(
        "Credencial Firebase: "
        f"{'presente' if runtime.get('credentials_present') else 'ausente'} "
        f"({runtime.get('credentials_source', 'desconhecido')}: {runtime.get('credentials_path', 'nao configurado')})"
    )
    print(f"Status de conexao: {runtime.get('message', 'sem mensagem')}")
    if not config.API_TOKEN:
        print("Aviso: API_TOKEN nao configurado; rotas de escrita ficarao sem autenticacao.")

    start_api_server(host=host, port=port)
    health_url = f"{local_url}/health"
    ok, payload = _wait_for_health(health_url)
    if ok:
        print(f"Health check OK: {health_url}")
        if payload:
            print(
                "Resumo /health: "
                f"mode={payload.get('mode', 'desconhecido')} "
                f"backend={payload.get('backend', 'desconhecido')} "
                f"project_id={payload.get('project_id', 'desconhecido')}"
            )
    else:
        print(f"Erro: nao foi possivel confirmar /health em {health_url}")
        stop_api_server()
        return 1

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

    try:
        if args and args[0]:
            dragged_file = Path(args[0]).expanduser()
            if not dragged_file.exists() or not dragged_file.is_file():
                raise FileNotFoundError(f"Arquivo nao encontrado: {dragged_file}")
            _apply_config_file(dragged_file)
        else:
            _print_usage()
            print("")
            _apply_persisted_runtime()

        return _run_server()
    except Exception as exc:
        print(f"Erro: {exc}")
        print("O servidor nao sera iniciado enquanto o Firebase obrigatorio nao estiver valido.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
