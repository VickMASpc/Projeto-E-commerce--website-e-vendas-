import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Configurações de Caminho
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "db_mock.json")
CRED_FILE = os.path.join(BASE_DIR, "serviceAccountKey.json")

def migrate():
    # 1. Verifica arquivos necessários
    if not os.path.exists(CRED_FILE):
        print(f"ERRO: Arquivo {CRED_FILE} não encontrado!")
        return

    if not os.path.exists(DB_FILE):
        print(f"ERRO: Arquivo {DB_FILE} não encontrado!")
        return

    # 2. Inicializa Firebase
    print("Iniciando conexão com Firebase...")
    cred = credentials.Certificate(CRED_FILE)
    firebase_admin.initialize_app(cred)
    db = firestore.client()

    # 3. Lê dados locais
    with open(DB_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 4. Migra PRODUTOS
    print("\nMigrando PRODUTOS...")
    produtos = data.get("produtos", [])
    for idx, p in enumerate(produtos):
        # Mapeamento de categorias legado para o novo tema de perfume
        cat_map = {
            "Beleza": "Feminino",
            "Moda": "Unissex",
            "Eletrônicos": "Masculino",
            "Esportes": "Masculino"
        }
        old_cat = p.get("category", p.get("categoria", "Geral"))
        new_cat = cat_map.get(old_cat, old_cat)

        doc_data = {
            "nome": p.get("name", p.get("nome", "Perfume")),
            "descricao": p.get("description", p.get("descricao", "")),
            "preco": float(p.get("price", p.get("preco", 0))),
            "estoque": int(p.get("stock", p.get("estoque", 0))),
            "categoria": new_cat,
            "imageEmoji": p.get("imageEmoji", "✨"),
            "image_url": p.get("image_url", ""),
            "emOferta": p.get("isSale", False),
            "eNovo": p.get("isNew", False)
        }
        
        # Padrão perf-x
        doc_id = p.get("id", f"perf-{idx+1}")
        if "prod-" in str(doc_id):
            doc_id = f"perf-{idx+1}"
            
        db.collection("produtos").document(str(doc_id)).set(doc_data)
        print(f"  + Produto '{doc_data['nome']}' ({doc_id}) enviado.")

    # 5. Migra PEDIDOS
    print("\nMigrando PEDIDOS...")
    pedidos = data.get("pedidos", [])
    for idx, ped in enumerate(pedidos):
        # Padrão ord-xxx
        doc_id = ped.get("id", f"ord-{idx+1:03d}")
        if not str(doc_id).startswith("ord-"):
            doc_id = f"ord-{idx+1:03d}"
            
        db.collection("pedidos").document(str(doc_id)).set(ped)
        print(f"  + Pedido {doc_id} enviado.")

    print("\n✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("As coleções 'produtos' e 'pedidos' foram criadas automaticamente no Console do Firebase.")

if __name__ == "__main__":
    migrate()
