import json
import os
from datetime import datetime

# ==============================================================================
# Gerenciador de Banco de Dados Local (MOCK)
# ==============================================================================
# ATENÇÃO: 
# Este arquivo simula um banco de dados usando um arquivo JSON local chamado
# `db_mock.json`. Uma vez que o Firebase Firestore for configurado, estas funções 
# devem ser substituídas para utilizar a biblioteca `firebase-admin`.
# A interface do Tkinter não precisará ser reescrita se os métodos aqui 
# mantiverem as assinaturas (entrada/saída).
# ==============================================================================

USE_FIREBASE = False # Mude para True quando tiver as credenciais

try:
    if USE_FIREBASE:
        import firebase_admin
        from firebase_admin import credentials, firestore
        # cred = credentials.Certificate("path/to/serviceAccountKey.json")
        # firebase_admin.initialize_app(cred)
        # db = firestore.client()
except ImportError:
    USE_FIREBASE = False


DB_FILE = os.path.join(os.path.dirname(__file__), "db_mock.json")

def _init_db():
    """Inicializa o banco test dummy caso não exista."""
    if not os.path.exists(DB_FILE):
        data = {
            "produtos": [
                {"id": "prod-1", "name": "Fone Bluetooth Pro Max", "description": "Fone de ouvido com cancelamento de ruído", "price": 319.90, "stock": 100, "category": "Eletrônicos", "image_url": ""},
                {"id": "prod-2", "name": "Tênis Running Ultra Boost", "description": "Tênis de corrida de alta performance", "price": 459.90, "stock": 50, "category": "Esportes", "image_url": ""},
                {"id": "prod-3", "name": "Smartwatch Fit Series 3", "description": "Relógio inteligente com monitor cardíaco", "price": 699.00, "stock": 15, "category": "Eletrônicos", "image_url": ""},
                {"id": "prod-4", "name": "Kit Skincare Premium", "description": "Produtos para cuidados completos", "price": 189.90, "stock": 8, "category": "Beleza", "image_url": ""}
            ],
            "pedidos": [
                {
                    "id": "ord-001",
                    "customer_name": "Maria Fernanda",
                    "customer_email": "maria@example.com",
                    "items": [{"product_id": "prod-1", "product_name": "Fone Bluetooth Pro Max", "quantity": 1, "unit_price": 319.90}],
                    "total": 319.90,
                    "status": "pago", # pending, paid, shipped, delivered
                    "created_at": datetime.now().strftime("%d/%m/%Y %H:%M")
                }
            ],
            "vendas": []
        }
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

def _read_db():
    _init_db()
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def _write_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    # Exportar para o E-commerce para sincronização local instantânea
    _export_to_frontend(data)

def _export_to_frontend(data):
    """Gera um arquivo .js que o front-end pode carregar sem CORS/Backend."""
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "E-commerce")
    if os.path.exists(frontend_dir):
        export_path = os.path.join(frontend_dir, "products_live.js")
        content = "/* Gerado automaticamente pelo Sistema de Vendas */\n"
        content += f"const PRODUCTS_LIVE = {json.dumps(data['produtos'], indent=4, ensure_ascii=False)};\n"
        content += f"const ORDERS_LIVE = {json.dumps(data['pedidos'], indent=4, ensure_ascii=False)};\n"
        with open(export_path, 'w', encoding='utf-8') as f:
            f.write(content)



# ==========================================
# PRODUTOS (Gestão de Estoque)
# ==========================================
def get_products():
    """Retorna lista de dicionários de produtos."""
    data = _read_db()
    return data["produtos"]

def add_product(name, description, price, stock, category):
    """Adiciona um produto novo."""
    data = _read_db()
    # Gera um id simples baseado no tempo atual
    new_id = f"prod-{int(datetime.now().timestamp())}"
    prod = {
        "id": new_id,
        "name": name,
        "description": description,
        "price": float(price),
        "stock": int(stock),
        "category": category,
        "image_url": ""
    }
    data["produtos"].append(prod)
    _write_db(data)
    return new_id

def update_product_stock(product_id, new_stock):
    """Atualiza número do estoque de um produto."""
    data = _read_db()
    for prod in data["produtos"]:
        if prod["id"] == product_id:
            prod["stock"] = int(new_stock)
            break
    _write_db(data)

def delete_product(produto_id):
    """Remove um produto permanentemente."""
    data = _read_db()
    data["produtos"] = [p for p in data["produtos"] if p["id"] != produto_id]
    _write_db(data)


# ==========================================
# PEDIDOS E LOGÍSTICA
# ==========================================
def get_orders():
    """Retorna a fila de pedidos gerados pelo E-commerce."""
    data = _read_db()
    return data["pedidos"]

def update_order_status(ord_id, novo_status):
    """
    Logística pode atualizar o status do pedido,
    ex: de 'pago' para 'enviado'.
    """
    data = _read_db()
    for order in data["pedidos"]:
        if order["id"] == ord_id:
            order["status"] = novo_status
            break
    _write_db(data)
