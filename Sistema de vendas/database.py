import json
import os
from collections import defaultdict
from copy import deepcopy
from datetime import datetime

USE_FIREBASE = True
db = None

if USE_FIREBASE:
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        cred_path = os.path.join(os.path.dirname(__file__), "serviceAccountKey.json")
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            print("Firebase initialized successfully")
        else:
            print("Aviso: serviceAccountKey.json nao encontrado. Operando em modo mock.")
            USE_FIREBASE = False
    except Exception as error:
        print(f"Erro ao inicializar Firebase: {error}")
        USE_FIREBASE = False


DB_FILE = os.path.join(os.path.dirname(__file__), "db_mock.json")


def _now_iso():
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


SEED_PRODUCTS = [
    {
        "id": "perf-1",
        "name": "Bleu de Chanel",
        "brand": "Chanel",
        "tagline": "Assinatura fresca, amadeirada e precisa.",
        "description": "Fragrancia amadeirada aromatica para o homem moderno e sofisticado.",
        "longDescription": "Bleu de Chanel combina frescor citrico, especiarias elegantes e um fundo amadeirado limpo. Um perfume versatil para quem quer presenca refinada no dia a dia.",
        "price": 850.00,
        "oldPrice": 930.00,
        "stock": 45,
        "category": "Masculino",
        "image_url": "",
        "imageEmoji": "🧊",
        "sku": "BLEU-100-EDP",
        "volume_ml": "100 ml",
        "concentration": "Eau de Parfum",
        "olfactiveFamily": "Aromatico Amadeirado",
        "occasion": "Escritorio, encontros e noite",
        "topNotes": ["Limao siciliano", "Menta", "Toranja"],
        "heartNotes": ["Gengibre", "Noz-moscada", "Jasmin"],
        "baseNotes": ["Incenso", "Cedro", "Sandalo"],
        "highlights": [
            "Fixacao elegante de longa duracao",
            "Perfil sofisticado e versatil",
            "Excelente para uso diario premium",
        ],
        "rating": 4.9,
        "reviews": 187,
        "isSale": True,
        "isNew": False,
        "images": [],
    },
    {
        "id": "perf-2",
        "name": "Dior Sauvage",
        "brand": "Dior",
        "tagline": "Frescor mineral com assinatura intensa.",
        "description": "Uma composicao radical e fresca, inspirada em espacos abertos e ceu azul.",
        "longDescription": "Sauvage mistura bergamota, especiarias e ambroxan em uma estrutura luminosa e expansiva. Funciona muito bem como assinatura masculina contemporanea.",
        "price": 790.00,
        "oldPrice": 850.00,
        "stock": 30,
        "category": "Masculino",
        "image_url": "",
        "imageEmoji": "🌌",
        "sku": "SAUV-100-EDT",
        "volume_ml": "100 ml",
        "concentration": "Eau de Toilette",
        "olfactiveFamily": "Fougere Aromatico",
        "occasion": "Dia a dia, viagens e eventos sociais",
        "topNotes": ["Bergamota da Calabria", "Pimenta"],
        "heartNotes": ["Lavanda", "Pimenta rosa", "Vetiver"],
        "baseNotes": ["Ambroxan", "Cedro", "Labdano"],
        "highlights": [
            "Saida fresca e marcante",
            "Projecao ampla sem perder refinamento",
            "Assinatura masculina atual",
        ],
        "rating": 4.8,
        "reviews": 163,
        "isSale": True,
        "isNew": False,
        "images": [],
    },
    {
        "id": "perf-3",
        "name": "Chanel No. 5",
        "brand": "Chanel",
        "tagline": "O floral aldeidico mais iconico da perfumaria.",
        "description": "O classico atemporal, a essencia mitica da feminilidade.",
        "longDescription": "Chanel No. 5 combina aldeidos luminosos, flores nobres e um fundo cremoso. E um perfume historico com presenca sofisticada e acabamento luxuoso.",
        "price": 920.00,
        "stock": 24,
        "category": "Feminino",
        "image_url": "",
        "imageEmoji": "🌺",
        "sku": "N5-100-EDP",
        "volume_ml": "100 ml",
        "concentration": "Eau de Parfum",
        "olfactiveFamily": "Floral Aldeidico",
        "occasion": "Eventos, jantares e ocasioes especiais",
        "topNotes": ["Aldeidos", "Neroli", "Ylang-ylang"],
        "heartNotes": ["Rosa", "Jasmin", "Lirio-do-vale"],
        "baseNotes": ["Baunilha", "Vetiver", "Sandalo"],
        "highlights": [
            "Classico de altissima assinatura",
            "Acorde floral sofisticado",
            "Presenca memoravel e feminina",
        ],
        "rating": 4.9,
        "reviews": 204,
        "isSale": False,
        "isNew": True,
        "images": [],
    },
    {
        "id": "perf-4",
        "name": "Creed Aventus",
        "brand": "Creed",
        "tagline": "Frutado, amadeirado e extremamente prestigioso.",
        "description": "Uma fragrancia frutada e amadeirada, celebrando forca e sucesso.",
        "longDescription": "Aventus mistura abacaxi, birch e musk em uma assinatura de nicho poderosa. Ideal para quem quer um perfume reconhecivel e de alto impacto.",
        "price": 2450.00,
        "stock": 10,
        "category": "Nicho",
        "image_url": "",
        "imageEmoji": "👑",
        "sku": "AVEN-100-EDP",
        "volume_ml": "100 ml",
        "concentration": "Eau de Parfum",
        "olfactiveFamily": "Frutado Chypre",
        "occasion": "Noite, eventos premium e celebracoes",
        "topNotes": ["Abacaxi", "Bergamota", "Groselha preta"],
        "heartNotes": ["Betula", "Jasmin", "Patchouli"],
        "baseNotes": ["Musgo de carvalho", "Baunilha", "Musk"],
        "highlights": [
            "Nicho de altissimo reconhecimento",
            "Mistura luminosa e poderosa",
            "Excelente para ocasioes especiais",
        ],
        "rating": 5.0,
        "reviews": 118,
        "isSale": False,
        "isNew": False,
        "images": [],
    },
    {
        "id": "perf-5",
        "name": "Tom Ford Lost Cherry",
        "brand": "Tom Ford",
        "tagline": "Gourmand intenso com cereja escura e licor.",
        "description": "Um perfume gourmand luxuoso com notas intensas de cereja negra.",
        "longDescription": "Lost Cherry abre doce e provocante, depois seca para madeiras e fava tonka. Um perfume marcante para clima frio ou producoes noturnas.",
        "price": 1850.00,
        "stock": 12,
        "category": "Nicho",
        "image_url": "",
        "imageEmoji": "🍒",
        "sku": "LOCH-50-EDP",
        "volume_ml": "50 ml",
        "concentration": "Eau de Parfum",
        "olfactiveFamily": "Oriental Gourmand",
        "occasion": "Noite, inverno e producoes marcantes",
        "topNotes": ["Cereja negra", "Licor de cereja", "Amendoa amarga"],
        "heartNotes": ["Rosa turca", "Jasmin sambac", "Ameixa"],
        "baseNotes": ["Fava tonka", "Sandalo", "Vetiver"],
        "highlights": [
            "Perfil gourmand sofisticado",
            "Assinatura sensual e moderna",
            "Excelente para clima frio",
        ],
        "rating": 4.8,
        "reviews": 94,
        "isSale": False,
        "isNew": False,
        "images": [],
    },
    {
        "id": "perf-6",
        "name": "CK One",
        "brand": "Calvin Klein",
        "tagline": "Frescor compartilhavel com assinatura limpa.",
        "description": "Fragrancia revolucionaria unissex, icone de pureza e unidade.",
        "longDescription": "CK One combina citricos, cha verde e musk em uma proposta leve, clara e muito facil de usar. Continua sendo uma excelente porta de entrada para colecoes versateis.",
        "price": 350.00,
        "oldPrice": 410.00,
        "stock": 60,
        "category": "Unissex",
        "image_url": "",
        "imageEmoji": "🤍",
        "sku": "CK1-100-EDT",
        "volume_ml": "100 ml",
        "concentration": "Eau de Toilette",
        "olfactiveFamily": "Citrico Aromatico",
        "occasion": "Rotina leve, calor e viagens",
        "topNotes": ["Bergamota", "Lima", "Abacaxi"],
        "heartNotes": ["Cha verde", "Violeta", "Noz-moscada"],
        "baseNotes": ["Musk", "Amber", "Cedro"],
        "highlights": [
            "Leve, fresco e democratico",
            "Boa opcao de reaplicacao ao longo do dia",
            "Entrada forte para colecao versatil",
        ],
        "rating": 4.7,
        "reviews": 151,
        "isSale": True,
        "isNew": False,
        "images": [],
    },
]


DEFAULT_PRODUCT = {
    "brand": "",
    "tagline": "",
    "description": "",
    "longDescription": "",
    "price": 0.0,
    "oldPrice": 0.0,
    "stock": 0,
    "category": "Masculino",
    "image_url": "",
    "imageEmoji": "✨",
    "sku": "",
    "volume_ml": "100 ml",
    "concentration": "Eau de Parfum",
    "olfactiveFamily": "Amadeirado",
    "occasion": "Uso versatil",
    "topNotes": [],
    "heartNotes": [],
    "baseNotes": [],
    "highlights": [],
    "rating": 4.8,
    "reviews": 0,
    "isSale": False,
    "isNew": False,
    "images": [],
}


SEED_PRODUCTS_BY_ID = {product["id"]: deepcopy(product) for product in SEED_PRODUCTS}
SEED_PRODUCTS_BY_NAME = {
    str(product.get("name", "")).strip().lower(): deepcopy(product)
    for product in SEED_PRODUCTS
    if product.get("name")
}


def _to_float(value, fallback=0.0):
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return fallback


def _to_int(value, fallback=0):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return fallback


def _to_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value == 1
    return str(value).strip().lower() in {"1", "true", "sim", "yes"}


def _parse_list(value):
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if not value:
        return []
    separators = [",", ";", "|", "\n"]
    text = str(value)
    for separator in separators[1:]:
        text = text.replace(separator, separators[0])
    return [item.strip() for item in text.split(separators[0]) if item.strip()]


def normalize_product(product):
    product = product or {}
    seed_match = {}

    raw_id = product.get("id", "")
    raw_name = str(product.get("name") or product.get("nome") or "").strip().lower()
    if raw_id and raw_id in SEED_PRODUCTS_BY_ID:
        seed_match = deepcopy(SEED_PRODUCTS_BY_ID[raw_id])
    elif raw_name and raw_name in SEED_PRODUCTS_BY_NAME:
        seed_match = deepcopy(SEED_PRODUCTS_BY_NAME[raw_name])

    merged = deepcopy(DEFAULT_PRODUCT)
    merged.update(seed_match)
    merged.update(product or {})

    raw_brand = product.get("brand") or product.get("marca") or ""
    raw_tagline = product.get("tagline") or product.get("subtitulo") or ""
    raw_top_notes = _parse_list(product.get("topNotes") or product.get("notasTopo"))
    legacy_sparse_product = bool(seed_match) and not raw_brand and not raw_tagline and not raw_top_notes

    normalized = {
        "id": merged.get("id", ""),
        "name": merged.get("name") or merged.get("nome") or "Produto",
        "brand": merged.get("brand") or merged.get("marca") or "",
        "tagline": merged.get("tagline") or merged.get("subtitulo") or "",
        "description": merged.get("description") or merged.get("descricao") or "",
        "longDescription": merged.get("longDescription") or merged.get("descricao_longa") or merged.get("description") or merged.get("descricao") or "",
        "price": _to_float(merged.get("price", merged.get("preco", 0.0))),
        "oldPrice": _to_float(merged.get("oldPrice", merged.get("precoAntigo", 0.0))),
        "stock": _to_int(merged.get("stock", merged.get("estoque", 0))),
        "category": merged.get("category") or merged.get("categoria") or "Masculino",
        "image_url": merged.get("image_url") or merged.get("imageUrl") or "",
        "imageEmoji": merged.get("imageEmoji") or merged.get("emoji") or "✨",
        "sku": merged.get("sku") or merged.get("codigo") or "",
        "volume_ml": merged.get("volume_ml") or merged.get("volumeMl") or merged.get("tamanho") or "100 ml",
        "concentration": merged.get("concentration") or merged.get("concentracao") or "Eau de Parfum",
        "olfactiveFamily": merged.get("olfactiveFamily") or merged.get("familiaOlfativa") or "Amadeirado",
        "occasion": merged.get("occasion") or merged.get("ocasiao") or "Uso versatil",
        "topNotes": _parse_list(merged.get("topNotes") or merged.get("notasTopo")),
        "heartNotes": _parse_list(merged.get("heartNotes") or merged.get("notasCoracao")),
        "baseNotes": _parse_list(merged.get("baseNotes") or merged.get("notasBase")),
        "highlights": _parse_list(merged.get("highlights") or merged.get("destaques")),
        "rating": _to_float(merged.get("rating", 4.8), 4.8),
        "reviews": _to_int(merged.get("reviews", 0), 0),
        "isSale": _to_bool(merged.get("isSale") or merged.get("emOferta")),
        "isNew": _to_bool(merged.get("isNew") or merged.get("eNovo")),
        "images": _parse_list(merged.get("images") or merged.get("image_urls") or merged.get("imageUrls")),
    }

    if legacy_sparse_product:
        normalized["brand"] = seed_match.get("brand", normalized["brand"])
        normalized["tagline"] = seed_match.get("tagline", normalized["tagline"])
        normalized["description"] = seed_match.get("description", normalized["description"])
        normalized["longDescription"] = seed_match.get(
            "longDescription", normalized["longDescription"]
        )
        normalized["category"] = seed_match.get("category", normalized["category"])
        normalized["imageEmoji"] = seed_match.get("imageEmoji", normalized["imageEmoji"])
        normalized["volume_ml"] = seed_match.get("volume_ml", normalized["volume_ml"])
        normalized["concentration"] = seed_match.get(
            "concentration", normalized["concentration"]
        )
        normalized["olfactiveFamily"] = seed_match.get(
            "olfactiveFamily", normalized["olfactiveFamily"]
        )
        normalized["occasion"] = seed_match.get("occasion", normalized["occasion"])
        normalized["topNotes"] = seed_match.get("topNotes", normalized["topNotes"])
        normalized["heartNotes"] = seed_match.get("heartNotes", normalized["heartNotes"])
        normalized["baseNotes"] = seed_match.get("baseNotes", normalized["baseNotes"])
        normalized["highlights"] = seed_match.get("highlights", normalized["highlights"])
        normalized["rating"] = seed_match.get("rating", normalized["rating"])
        normalized["reviews"] = seed_match.get("reviews", normalized["reviews"])
        normalized["isSale"] = seed_match.get("isSale", normalized["isSale"])
        normalized["isNew"] = seed_match.get("isNew", normalized["isNew"])

    if normalized["image_url"] and normalized["image_url"] not in normalized["images"]:
        normalized["images"].insert(0, normalized["image_url"])

    if not normalized["sku"] and normalized["id"]:
        normalized["sku"] = normalized["id"].upper()

    return normalized


def _next_order_id(existing_orders):
    highest = 0
    for order in existing_orders:
        raw_id = str(order.get("id", ""))
        if raw_id.startswith("ord-") and raw_id[4:].isdigit():
            highest = max(highest, int(raw_id[4:]))
    return f"ord-{highest + 1:03d}"


def _normalize_order_item(item):
    product_id = (
        item.get("product_id")
        or item.get("produto_id")
        or item.get("produtoId")
        or item.get("id")
        or ""
    )
    product_name = (
        item.get("product_name")
        or item.get("produtoNome")
        or item.get("nome_prod")
        or item.get("name")
        or "Item"
    )
    quantity = _to_int(item.get("quantity", item.get("quantidade", 1)), 1)
    unit_price = _to_float(item.get("unit_price", item.get("preco_unit", item.get("preco", 0))))

    return {
        "product_id": product_id,
        "product_name": product_name,
        "quantity": max(quantity, 1),
        "unit_price": unit_price,
    }


def normalize_order(order, fallback_id=None):
    customer = order.get("customer") or {}
    items = order.get("items") or order.get("itens") or []
    normalized_items = [_normalize_order_item(item) for item in items]
    total = _to_float(
        order.get("total"),
        sum(item["quantity"] * item["unit_price"] for item in normalized_items),
    )

    return {
        "id": order.get("id") or fallback_id or "",
        "customer_id": order.get("customer_id") or order.get("clienteId") or order.get("userId") or customer.get("id") or None,
        "customer_name": order.get("customer_name") or order.get("clienteNome") or customer.get("name") or "Cliente",
        "customer_email": order.get("customer_email") or order.get("clienteEmail") or customer.get("email") or "",
        "customer_phone": order.get("customer_phone") or order.get("clienteTelefone") or customer.get("phone") or "",
        "customer_address": order.get("customer_address") or order.get("clienteEndereco") or customer.get("address") or "",
        "items": normalized_items,
        "total": total,
        "status": str(order.get("status") or "pendente").lower(),
        "created_at": order.get("created_at") or order.get("dataCriacao") or _now_iso(),
        "updated_at": order.get("updated_at") or order.get("atualizadoEm") or _now_iso(),
        "schema_version": int(order.get("schema_version") or order.get("schemaVersion") or 2),
    }


def _initial_data():
    return {
        "produtos": [normalize_product(product) for product in SEED_PRODUCTS],
        "pedidos": [
            {
                "id": "ord-001",
                "customer_name": "Juliana Silva",
                "customer_email": "juliana@example.com",
                "items": [
                    {
                        "product_id": "perf-3",
                        "product_name": "Chanel No. 5",
                        "quantity": 1,
                        "unit_price": 920.00,
                    }
                ],
                "total": 920.00,
                "status": "enviado",
                "created_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
            }
        ],
        "vendas": [],
    }


def _init_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w", encoding="utf-8") as file:
            json.dump(_initial_data(), file, indent=4, ensure_ascii=False)


def _read_db():
    _init_db()
    with open(DB_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    data["produtos"] = [normalize_product(product) for product in data.get("produtos", [])]
    data["pedidos"] = [normalize_order(order) for order in data.get("pedidos", [])]
    data.setdefault("vendas", [])
    return data


def _write_db(data):
    clean_data = {
        "produtos": [normalize_product(product) for product in data.get("produtos", [])],
        "pedidos": [normalize_order(order) for order in data.get("pedidos", [])],
        "vendas": data.get("vendas", []),
    }

    with open(DB_FILE, "w", encoding="utf-8") as file:
        json.dump(clean_data, file, indent=4, ensure_ascii=False)

    _export_to_frontend(clean_data)


def _export_to_frontend(data):
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "E-commerce")
    if not os.path.exists(frontend_dir):
        return

    export_path = os.path.join(frontend_dir, "products_live.js")
    content = "/* Gerado automaticamente pelo Sistema de Vendas */\n"
    content += f"const PRODUCTS_LIVE = {json.dumps(data['produtos'], indent=2, ensure_ascii=False)};\n"
    content += f"const ORDERS_LIVE = {json.dumps(data['pedidos'], indent=2, ensure_ascii=False)};\n"
    content += "window.PRODUCTS_LIVE = PRODUCTS_LIVE;\n"
    content += "window.ORDERS_LIVE = ORDERS_LIVE;\n"

    with open(export_path, "w", encoding="utf-8") as file:
        file.write(content)


def get_products():
    if USE_FIREBASE and db is not None:
        try:
            docs = db.collection("produtos").get()
            return [normalize_product(doc.to_dict() | {"id": doc.id}) for doc in docs]
        except Exception as error:
            print(f"Erro ao buscar produtos no Firebase: {error}")
            return []

    return _read_db()["produtos"]


def add_product(nome, descricao, preco, estoque, categoria, detalhes=None):
    new_id = f"perf-{int(datetime.now().timestamp() % 1000000)}"
    payload = {
        "id": new_id,
        "name": nome,
        "description": descricao,
        "price": preco,
        "stock": estoque,
        "category": categoria,
    }
    if detalhes:
        payload.update(detalhes)

    normalized = normalize_product(payload)
    normalized["id"] = new_id

    if USE_FIREBASE and db is not None:
        try:
            db.collection("produtos").document(new_id).set(normalized)
            return new_id
        except Exception as error:
            print(f"Erro ao salvar produto no Firebase: {error}")
            return None

    data = _read_db()
    data["produtos"].append(normalized)
    _write_db(data)
    return new_id


def update_product(product_id, dados):
    normalized = normalize_product({"id": product_id, **(dados or {})})

    if USE_FIREBASE and db is not None:
        try:
            db.collection("produtos").document(product_id).set(normalized)
            return True
        except Exception as error:
            print(f"Erro ao atualizar produto no Firebase: {error}")
            return False

    data = _read_db()
    updated = False
    for index, product in enumerate(data["produtos"]):
        if product["id"] == product_id:
            data["produtos"][index] = normalized
            updated = True
            break

    if updated:
        _write_db(data)
    return updated


def update_product_stock(product_id, novo_estoque):
    products = get_products()
    current = next((product for product in products if product["id"] == product_id), None)
    if not current:
        return

    current["stock"] = _to_int(novo_estoque)
    update_product(product_id, current)


def delete_product(produto_id):
    if USE_FIREBASE and db is not None:
        try:
            db.collection("produtos").document(produto_id).delete()
            return
        except Exception as error:
            print(f"Erro ao deletar no Firebase: {error}")

    data = _read_db()
    data["produtos"] = [product for product in data["produtos"] if product["id"] != produto_id]
    _write_db(data)


def listen_to_orders(callback):
    if not USE_FIREBASE or db is None:
        return None

    def on_snapshot(col_snapshot, changes, read_time):
        callback()

    return db.collection("pedidos").on_snapshot(on_snapshot)


def get_orders():
    if USE_FIREBASE and db is not None:
        try:
            docs = db.collection("pedidos").get()
            return [normalize_order(doc.to_dict() | {"id": doc.id}) for doc in docs]
        except Exception as error:
            print(f"Erro ao buscar pedidos no Firebase: {error}")
            return []

    return _read_db()["pedidos"]


def create_local_order(order):
    if USE_FIREBASE and db is not None:
        normalized = normalize_order(order, f"ord-{int(datetime.now().timestamp() * 1000)}")
        if not normalized["items"]:
            return {
                "ok": False,
                "message": "Pedido sem itens.",
                "order_id": None,
            }

        transaction = db.transaction()

        @firestore.transactional
        def process_order(txn):
            product_refs = {
                item["product_id"]: db.collection("produtos").document(item["product_id"])
                for item in normalized["items"]
                if item.get("product_id")
            }

            snapshots = {
                product_id: product_ref.get(transaction=txn)
                for product_id, product_ref in product_refs.items()
            }

            insufficient_stock = []
            products_by_id = {}
            for item in normalized["items"]:
                product_id = item.get("product_id")
                snapshot = snapshots.get(product_id)
                if snapshot is None or not snapshot.exists:
                    insufficient_stock.append(item["product_name"])
                    continue

                product = normalize_product(snapshot.to_dict() | {"id": snapshot.id})
                products_by_id[product_id] = product
                if int(product.get("stock", 0)) < item["quantity"]:
                    insufficient_stock.append(item["product_name"])

            if insufficient_stock:
                return {
                    "ok": False,
                    "message": f"Estoque insuficiente para: {', '.join(insufficient_stock)}",
                    "order_id": None,
                }

            for item in normalized["items"]:
                product_id = item["product_id"]
                product_ref = product_refs[product_id]
                current_stock = int(products_by_id[product_id].get("stock", 0))
                txn.update(product_ref, {"stock": current_stock - item["quantity"]})

            normalized["status"] = "pago"
            normalized["created_at"] = _now_iso()
            normalized["updated_at"] = normalized["created_at"]
            order_ref = db.collection("pedidos").document(normalized["id"])
            txn.set(order_ref, normalized)
            return {"ok": True, "message": "Pedido registrado.", "order_id": normalized["id"]}

        try:
            return process_order(transaction)
        except Exception as error:
            print(f"Erro ao registrar pedido no Firebase: {error}")
            return {
                "ok": False,
                "message": "Nao foi possivel registrar o pedido no Firebase.",
                "order_id": None,
            }

    data = _read_db()
    normalized = normalize_order(order, _next_order_id(data["pedidos"]))
    if not normalized["items"]:
        return {
            "ok": False,
            "message": "Pedido sem itens.",
            "order_id": None,
        }

    products_by_id = {product["id"]: product for product in data["produtos"]}
    insufficient_stock = []
    for item in normalized["items"]:
        product = products_by_id.get(item["product_id"])
        if not product or int(product.get("stock", 0)) < item["quantity"]:
            insufficient_stock.append(item["product_name"])

    if insufficient_stock:
        return {
            "ok": False,
            "message": f"Estoque insuficiente para: {', '.join(insufficient_stock)}",
            "order_id": None,
        }

    for item in normalized["items"]:
        product = products_by_id.get(item["product_id"])
        if product:
            product["stock"] = int(product.get("stock", 0)) - item["quantity"]

    normalized["status"] = "pago"
    normalized["created_at"] = _now_iso()
    normalized["updated_at"] = normalized["created_at"]
    data["pedidos"].append(normalized)
    _write_db(data)
    return {"ok": True, "message": "Pedido registrado.", "order_id": normalized["id"]}


def update_order_status(pedido_id, novo_status):
    if USE_FIREBASE and db is not None:
        try:
            db.collection("pedidos").document(pedido_id).update({
                "status": novo_status,
                "updated_at": _now_iso(),
            })
            return
        except Exception as error:
            print(f"Erro ao atualizar status no Firebase: {error}")

    data = _read_db()
    for order in data["pedidos"]:
        if order["id"] == pedido_id:
            order["status"] = novo_status
            order["updated_at"] = _now_iso()
            break
    _write_db(data)


def _parse_date(value):
    if hasattr(value, "strftime"):
        try:
            return value
        except Exception:
            pass

    if hasattr(value, "to_datetime"):
        try:
            return value.to_datetime()
        except Exception:
            pass

    raw_value = str(value).strip()

    for pattern in (
        "%d/%m/%Y %H:%M",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
    ):
        try:
            return datetime.strptime(raw_value, pattern)
        except ValueError:
            continue

    if raw_value.endswith("+00:00"):
        trimmed = raw_value[:-6]
        for pattern in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(trimmed, pattern)
            except ValueError:
                continue
    return datetime.now()


def _build_time_series(orders, min_days=30):
    orders_by_day = defaultdict(lambda: {"sales": 0.0, "orders": 0})

    if orders:
        parsed_dates = [_parse_date(order.get("created_at")) for order in orders]
        end_date = max(parsed_dates).date()
        start_date = min(parsed_dates).date()
    else:
        end_date = datetime.now().date()
        start_date = end_date

    span_days = max((end_date - start_date).days + 1, 1)
    days = max(min_days, span_days)
    start_date = end_date.fromordinal(end_date.toordinal() - max(days - 1, 0))

    for order in orders:
        order_date = _parse_date(order.get("created_at")).date()
        if order_date < start_date or order_date > end_date:
            continue

        bucket = orders_by_day[order_date]
        bucket["sales"] += _to_float(order.get("total"))
        bucket["orders"] += 1

    points = []
    for offset in range(days):
        current_date = start_date.fromordinal(start_date.toordinal() + offset)
        bucket = orders_by_day[current_date]
        points.append(
            {
                "date": current_date.strftime("%d/%m"),
                "isoDate": current_date.isoformat(),
                "sales": round(bucket["sales"], 2),
                "orders": bucket["orders"],
            }
        )

    return points


def _period_totals(orders, start_date, end_date):
    selected = []
    for order in orders:
        order_date = _parse_date(order.get("created_at")).date()
        if start_date <= order_date <= end_date:
            selected.append(order)

    total_revenue = sum(_to_float(order.get("total")) for order in selected)
    return {
        "orders": len(selected),
        "revenue": round(total_revenue, 2),
    }


def _growth_pct(current, previous):
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100, 1)


def get_stats():
    products = get_products()
    orders = get_orders()

    paid_orders = [order for order in orders if order.get("status") in {"pago", "enviado", "pendente"}]
    total_revenue = sum(_to_float(order.get("total")) for order in paid_orders)
    total_orders = len(paid_orders)
    average_ticket = total_revenue / total_orders if total_orders else 0

    inventory_by_category = defaultdict(int)
    products_by_id = {product["id"]: product for product in products}
    product_names = {product["id"]: product["name"] for product in products}
    for product in products:
        inventory_by_category[product.get("category", "Outros")] += int(product.get("stock", 0))

    sales_by_product = defaultdict(int)
    category_sales = defaultdict(lambda: {"value": 0.0, "orders": 0, "units": 0})
    customer_sales = defaultdict(lambda: {"revenue": 0.0, "orders": 0})
    recent_activity = []
    for order in paid_orders:
        order_total = _to_float(order.get("total"))
        recent_activity.append(
            {
                "id": order.get("id", ""),
                "label": f"Pedido {order.get('id', '')} - {order.get('status', 'pendente')}",
                "customer": order.get("customer_name", "Cliente"),
                "created_at": order.get("created_at", ""),
                "total": round(order_total, 2),
                "status": order.get("status", "pendente"),
            }
        )

        customer_name = order.get("customer_name", "Cliente")
        customer_sales[customer_name]["revenue"] += order_total
        customer_sales[customer_name]["orders"] += 1

        seen_categories = set()
        for item in order.get("items", []):
            name = item.get("product_name") or product_names.get(item.get("product_id"), "Item")
            quantity = _to_int(item.get("quantity"), 1)
            unit_price = _to_float(item.get("unit_price"))
            product = products_by_id.get(item.get("product_id"))
            category_name = (product or {}).get("category", "Outros")

            sales_by_product[name] += quantity
            category_sales[category_name]["value"] += quantity * unit_price
            category_sales[category_name]["units"] += quantity
            if category_name not in seen_categories:
                category_sales[category_name]["orders"] += 1
                seen_categories.add(category_name)

    top_products = sorted(
        ({"name": name, "sales": quantity} for name, quantity in sales_by_product.items()),
        key=lambda item: item["sales"],
        reverse=True,
    )[:5]

    timeline = _build_time_series(paid_orders, 30)
    sales_over_time = [
        {
            "date": point["date"],
            "isoDate": point["isoDate"],
            "sales": point["sales"],
            "orders": point["orders"],
        }
        for point in timeline
    ]

    last_day = datetime.now().date()
    last_7_start = last_day.fromordinal(last_day.toordinal() - 6)
    prev_7_end = last_day.fromordinal(last_day.toordinal() - 7)
    prev_7_start = prev_7_end.fromordinal(prev_7_end.toordinal() - 6)

    current_period = _period_totals(paid_orders, last_7_start, last_day)
    previous_period = _period_totals(paid_orders, prev_7_start, prev_7_end)

    low_stock_items = sorted(
        [
            {
                "id": product["id"],
                "name": product.get("name", "Produto"),
                "category": product.get("category", "Outros"),
                "stock": int(product.get("stock", 0)),
            }
            for product in products
            if int(product.get("stock", 0)) <= 12
        ],
        key=lambda item: item["stock"],
    )[:6]

    order_status = defaultdict(int)
    for order in orders:
        order_status[str(order.get("status", "pendente")).lower()] += 1

    category_performance = sorted(
        (
            {
                "name": category,
                "value": round(metrics["value"], 2),
                "orders": metrics["orders"],
                "units": metrics["units"],
            }
            for category, metrics in category_sales.items()
        ),
        key=lambda item: item["value"],
        reverse=True,
    )

    top_customers = sorted(
        (
            {
                "name": customer,
                "revenue": round(metrics["revenue"], 2),
                "orders": metrics["orders"],
            }
            for customer, metrics in customer_sales.items()
        ),
        key=lambda item: item["revenue"],
        reverse=True,
    )[:5]

    orders_today = sum(
        1 for order in orders if _parse_date(order.get("created_at")).date() == last_day
    )
    realtime_revenue = sum(
        _to_float(order.get("total"))
        for order in orders
        if _parse_date(order.get("created_at")).date() == last_day
    )

    return {
        "totalRevenue": round(total_revenue, 2),
        "totalOrders": total_orders,
        "averageTicket": round(average_ticket, 2),
        "inventoryUnits": sum(int(product.get("stock", 0)) for product in products),
        "activeCategories": len(inventory_by_category),
        "ordersToday": orders_today,
        "paidOrders": order_status["pago"],
        "pendingOrders": order_status["pendente"],
        "shippedOrders": order_status["enviado"],
        "lowStockCount": len(low_stock_items),
        "revenueDeltaPct": _growth_pct(
            current_period["revenue"], previous_period["revenue"]
        ),
        "ordersDeltaPct": _growth_pct(
            current_period["orders"], previous_period["orders"]
        ),
        "realtimeRevenue": round(realtime_revenue, 2),
        "lastUpdated": datetime.now().isoformat(timespec="seconds"),
        "periodSummary": {
            "current": current_period,
            "previous": previous_period,
        },
        "inventoryStatus": [
            {"name": category, "value": quantity}
            for category, quantity in sorted(inventory_by_category.items())
        ],
        "salesOverTime": sales_over_time,
        "topProducts": top_products,
        "recentActivity": recent_activity[-5:][::-1],
        "categoryPerformance": category_performance,
        "orderStatus": [
            {"name": status.title(), "value": total}
            for status, total in sorted(order_status.items())
        ],
        "lowStockItems": low_stock_items,
        "topCustomers": top_customers,
    }
