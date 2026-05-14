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

USE_FIREBASE = True # Mude para True quando tiver o arquivo serviceAccountKey.json

db = None

if USE_FIREBASE:
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        
        # O arquivo deve estar na mesma pasta ou o caminho completo deve ser fornecido
        cred_path = os.path.join(os.path.dirname(__file__), "serviceAccountKey.json")
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            print("Firebase Initialized Successfully")
        else:
            print("Aviso: serviceAccountKey.json não encontrado. Operando em modo MOCK.")
            USE_FIREBASE = False
    except Exception as e:
        print(f"Erro ao inicializar Firebase: {e}")
        USE_FIREBASE = False


DB_FILE = os.path.join(os.path.dirname(__file__), "db_mock.json")

def _init_db():
    """Inicializa o banco test dummy caso não exista."""
    if not os.path.exists(DB_FILE):
        data = {
            "produtos": [
                {"id": "perf-1", "name": "Bleu de Chanel", "description": "Fragrância amadeirada aromática para o homem moderno e sofisticado.", "price": 850.00, "stock": 45, "category": "Masculino", "image_url": ""},
                {"id": "perf-2", "name": "Dior Sauvage", "description": "Uma composição radical e fresca, inspirada em espaços abertos e céu azul.", "price": 790.00, "stock": 30, "category": "Masculino", "image_url": ""},
                {"id": "perf-3", "name": "Chanel No. 5", "description": "O clássico atemporal, a essência mítica da feminilidade.", "price": 920.00, "stock": 25, "category": "Feminino", "image_url": ""},
                {"id": "perf-4", "name": "Creed Aventus", "description": "Uma fragrância frutada e amadeirada, celebrando força e sucesso.", "price": 2450.00, "stock": 10, "category": "Nicho", "image_url": ""},
                {"id": "perf-5", "name": "Tom Ford Lost Cherry", "description": "Um perfume gourmand luxuoso com notas intensas de cereja negra.", "price": 1850.00, "stock": 12, "category": "Nicho", "image_url": ""},
                {"id": "perf-6", "name": "CK One", "description": "Fragrância revolucionária unissex, ícone de pureza e unidade.", "price": 350.00, "stock": 60, "category": "Unissex", "image_url": ""}
            ],
            "pedidos": [
                {
                    "id": "ord-001",
                    "customer_name": "Juliana Silva",
                    "customer_email": "juliana@example.com",
                    "items": [{"product_id": "perf-3", "product_name": "Chanel No. 5", "quantity": 1, "unit_price": 920.00}],
                    "total": 920.00,
                    "status": "enviado",
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
    if USE_FIREBASE:
        try:
            docs = db.collection("produtos").get()
            return [doc.to_dict() | {"id": doc.id} for doc in docs]
        except Exception as e:
            print(f"Erro ao buscar produtos no Firebase: {e}")
            return []
    
    data = _read_db()
    return data["produtos"]

def add_product(nome, descricao, preco, estoque, categoria):
    """Adiciona um produto novo."""
    new_id = f"perf-{int(datetime.now().timestamp() % 1000000)}"
    prod = {
        "name": nome,
        "description": descricao,
        "price": float(preco),
        "stock": int(estoque),
        "category": categoria,
        "image_url": ""
    }

    if USE_FIREBASE:
        try:
            db.collection("produtos").document(new_id).set(prod)
            return new_id
        except Exception as e:
            print(f"Erro ao salvar produto no Firebase: {e}")
            return None

    data = _read_db()
    prod["id"] = new_id
    data["produtos"].append(prod)
    _write_db(data)
    return new_id

def update_product_stock(product_id, novo_estoque):
    """Atualiza número do estoque de um produto."""
    if USE_FIREBASE:
        try:
            db.collection("produtos").document(product_id).update({
                "stock": int(novo_estoque)
            })
            return
        except Exception as e:
            print(f"Erro ao atualizar estoque no Firebase: {e}")
    
    data = _read_db()
    for prod in data["produtos"]:
        if prod["id"] == product_id:
            prod["stock"] = int(novo_estoque)
            break
    _write_db(data)

def delete_product(produto_id):
    """Remove um produto permanentemente."""
    if USE_FIREBASE:
        try:
            db.collection("produtos").document(produto_id).delete()
            return
        except Exception as e:
            print(f"Erro ao deletar no Firebase: {e}")

    data = _read_db()
    data["produtos"] = [p for p in data["produtos"] if p["id"] != produto_id]
    _write_db(data)


# ==========================================
# PEDIDOS E LOGÍSTICA
# ==========================================
def listen_to_orders(callback):
    """
    Configura um listener em tempo real para a coleção de pedidos no Firebase.
    O callback será chamado sempre que houver mudanças.
    """
    if not USE_FIREBASE or db is None:
        return None

    def on_snapshot(col_snapshot, changes, read_time):
        # Sempre que houver uma mudança, chamamos o callback
        # Podemos passar os dados processados ou apenas notificar a mudança
        callback()

    # Registra o listener na coleção 'pedidos'
    query_watch = db.collection("pedidos").on_snapshot(on_snapshot)
    return query_watch

def get_orders():
    """Retorna lista de dicionários de pedidos."""
    if USE_FIREBASE:
        try:
            docs = db.collection("pedidos").get()
            return [doc.to_dict() | {"id": doc.id} for doc in docs]
        except Exception as e:
            print(f"Erro ao buscar pedidos no Firebase: {e}")
            return []
    
    data = _read_db()
    return data["pedidos"]

def update_order_status(pedido_id, novo_status):
    """Atualiza o status de um pedido."""
    if USE_FIREBASE:
        try:
            db.collection("pedidos").document(pedido_id).update({
                "status": novo_status
            })
            return
        except Exception as e:
            print(f"Erro ao atualizar status no Firebase: {e}")
    
    data = _read_db()
    for ped in data["pedidos"]:
        if ped["id"] == pedido_id:
            ped["status"] = novo_status
            break
    _write_db(data)
