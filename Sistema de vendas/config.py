import os

# Configuração centralizada do aplicativo de Logística

# Informações Gerais
APP_NAME = "Grand Parfum - Sistema Local de Vendas e Logistica"

# Integração e API
API_HOST = ""
API_PORT = 5000

# Persistência de Dados
# Se True, tenta carregar o Firebase. 
# Se falhar ou o arquivo de credenciais não existir, alterna para modo local.
USE_FIREBASE = True
DB_FILE = os.path.join(os.path.dirname(__file__), "db_mock.json")
FIREBASE_CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "serviceAccountKey.json")

# Regras de Negócio
LOW_STOCK_THRESHOLD = 5

# Exportação para Frontend
FRONTEND_EXPORT_ENABLED = True
# Caminho para o arquivo que o frontend consome para exibir 
# produtos em tempo real (modo local)
FRONTEND_EXPORT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "E-commerce", "products_live.js"
)
