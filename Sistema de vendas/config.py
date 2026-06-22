import os
import json
from pathlib import Path

# Configuração centralizada do aplicativo de Logística
BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent


def _env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "sim"}


def _env_int(name, default):
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError:
        print(f"Aviso: {name} invalido ({value!r}); usando {default}.")
        return default


def _env_list(name):
    value = os.getenv(name, "")
    return [item.strip() for item in value.split(",") if item.strip()]


def _env_mode(name, default="development"):
    value = str(os.getenv(name, default) or default).strip().lower()
    if value not in {"production", "development", "test"}:
        print(f"Aviso: {name} invalido ({value!r}); usando {default}.")
        return default
    return value


# Informações Gerais
APP_NAME = "Grand Parfum - Sistema Local de Vendas e Logistica"

# Integração e API
API_HOST = os.getenv("API_HOST", "")
API_PORT = _env_int("API_PORT", 5000)
ALLOWED_ORIGINS = _env_list("ALLOWED_ORIGINS")
API_TOKEN = os.getenv("API_TOKEN", "").strip()

# Persistência de Dados
GRAND_PARFUM_MODE = _env_mode("GRAND_PARFUM_MODE", "development")
GRAND_PARFUM_ALLOW_MOCK = _env_bool("GRAND_PARFUM_ALLOW_MOCK", False)
_USE_FIREBASE_REQUESTED = _env_bool("USE_FIREBASE", True)
USE_FIREBASE = True if GRAND_PARFUM_MODE == "production" else _USE_FIREBASE_REQUESTED
if GRAND_PARFUM_MODE == "production" and not _USE_FIREBASE_REQUESTED:
    print("Aviso: USE_FIREBASE=false foi ignorado porque GRAND_PARFUM_MODE=production exige Firebase.")

ALLOW_MOCK = GRAND_PARFUM_MODE in {"development", "test"} and (
    (not USE_FIREBASE) or GRAND_PARFUM_ALLOW_MOCK
)
FIREBASE_REQUIRED = USE_FIREBASE and not ALLOW_MOCK

DB_FILE = os.getenv("DB_FILE", str(BASE_DIR / "db_mock.json"))
_DEFAULT_FIREBASE_CREDENTIALS = str(BASE_DIR / "serviceAccountKey.json")
FIREBASE_CREDENTIALS_PATH = (
    os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    or os.getenv("FIREBASE_CREDENTIALS_PATH")
    or _DEFAULT_FIREBASE_CREDENTIALS
)
FIREBASE_CREDENTIALS_SOURCE = (
    "GOOGLE_APPLICATION_CREDENTIALS" if os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    else "FIREBASE_CREDENTIALS_PATH" if os.getenv("FIREBASE_CREDENTIALS_PATH")
    else "local default"
)

# Regras de Negócio
LOW_STOCK_THRESHOLD = _env_int("LOW_STOCK_THRESHOLD", 5)

# Exportação para Frontend
FRONTEND_EXPORT_ENABLED = _env_bool("FRONTEND_EXPORT_ENABLED", True)
FRONTEND_EXPORT_PATH = os.getenv(
    "FRONTEND_EXPORT_PATH",
    str(PROJECT_DIR / "E-commerce" / "products_live.js"),
)


def firebase_credentials_exists() -> bool:
    return bool(FIREBASE_CREDENTIALS_PATH and Path(FIREBASE_CREDENTIALS_PATH).exists())


def firebase_project_hint() -> str:
    try:
        if not firebase_credentials_exists():
            return "desconhecido"
        with Path(FIREBASE_CREDENTIALS_PATH).open("r", encoding="utf-8") as file:
            data = json.load(file)
        return str(data.get("project_id") or "desconhecido")
    except Exception:
        return "desconhecido"
