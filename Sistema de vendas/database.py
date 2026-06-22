import json
import os
import config
from collections import defaultdict
from copy import deepcopy
from datetime import datetime
from domain.product import (
    DEFAULT_PRODUCT as DOMAIN_DEFAULT_PRODUCT,
    normalize_product as domain_normalize_product,
    parse_bool as domain_parse_bool,
    parse_float as domain_parse_float,
    parse_int as domain_parse_int,
    parse_list as domain_parse_list,
)
from domain.order import (
    normalize_order as domain_normalize_order,
    normalize_order_item as domain_normalize_order_item,
)
from services.product_service import ProductService
from services.inventory_service import InventoryService
from services.coupon_service import CouponService
from services.dashboard_service import DashboardService

USE_FIREBASE = config.USE_FIREBASE
db = None

if USE_FIREBASE:
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        cred_path = config.FIREBASE_CREDENTIALS_PATH
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            db = firestore.client()
            print("Firebase initialized successfully")
        else:
            configured_path = cred_path or "nao configurado"
            print(f"Aviso: credencial Firebase ({configured_path}) nao encontrada. Operando em modo mock.")
            USE_FIREBASE = False
    except Exception as error:
        print(f"Erro ao inicializar Firebase: {error}")
        USE_FIREBASE = False


DB_FILE = config.DB_FILE


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

from domain.coupon import DEFAULT_COUPON, normalize_coupon as domain_normalize_coupon

SEED_COUPONS = [
    {
        "code": "BEMVINDO10",
        "type": "percent",
        "value": 10,
        "active": True,
        "min_order_total": 250,
        "max_discount": 180,
    },
    {
        "code": "VIP150",
        "type": "fixed",
        "value": 150,
        "active": True,
        "min_order_total": 1200,
        "usage_limit": 25,
    },
    {
        "code": "INATIVO5",
        "type": "percent",
        "value": 5,
        "active": False,
        "min_order_total": 0,
    },
]


SEED_PRODUCTS_BY_ID = {product["id"]: deepcopy(product) for product in SEED_PRODUCTS}
SEED_PRODUCTS_BY_NAME = {
    str(product.get("name", "")).strip().lower(): deepcopy(product)
    for product in SEED_PRODUCTS
    if product.get("name")
}


def _to_float(value, fallback=0.0):
    return domain_parse_float(value, fallback)


def _to_int(value, fallback=0):
    return domain_parse_int(value, fallback)


def _to_bool(value):
    return domain_parse_bool(value)


def _parse_list(value):
    return domain_parse_list(value)


def _parse_optional_date(value):
    if not value:
        return None
    parsed = _parse_date(value)
    return parsed if parsed.year > 1970 else None


def _normalize_coupon_type(value):
    coupon_type = str(value or "percent").strip().lower()
    return coupon_type if coupon_type in {"percent", "fixed"} else "percent"


def normalize_coupon(coupon):
    return domain_normalize_coupon(coupon)


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
    return domain_normalize_order_item(item)


def normalize_order(order, fallback_id=None):
    return domain_normalize_order(order, fallback_id)


repository = None

def _get_repo():
    global repository
    if repository is None:
        from repositories.json_repository import JsonRepository
        from repositories.firebase_repository import FirebaseRepository
        import config
        json_repo = JsonRepository(config.DB_FILE)
        if USE_FIREBASE and db is not None:
            repository = FirebaseRepository(db, json_repo)
        else:
            repository = json_repo
    return repository

def _init_db():
    pass

def _read_db():
    return _get_repo().read_data()

def _write_db(data):
    _get_repo().write_data(data)


def _export_to_frontend(data):
    from services.export_service import export_frontend_snapshot

    result = export_frontend_snapshot(data)
    if result.get("status") == "error":
        print(result.get("message", "Erro ao exportar para frontend."))


def get_products():
    return ProductService(_get_repo()).list_products()


def add_product(nome, descricao, preco, estoque, categoria, detalhes=None):
    payload = {
        "name": nome,
        "description": descricao,
        "price": preco,
        "stock": estoque,
        "category": categoria,
    }
    if detalhes:
        payload.update(detalhes)

    result = ProductService(_get_repo()).create_product(payload)
    product = result.get("product") or {}
    return product.get("id") if result.get("ok") else None


def update_product(product_id, dados):
    return ProductService(_get_repo()).update_product(product_id, dados).get("ok", False)


def update_product_stock(product_id, novo_estoque):
    return ProductService(_get_repo()).update_stock(product_id, novo_estoque).get("ok", False)


def delete_product(produto_id):
    return ProductService(_get_repo()).delete_product(produto_id).get("ok", False)


def listen_to_orders(callback):
    return _get_repo().listen_to_orders(callback)


def get_orders():
    return _get_repo().get_orders()


def get_coupons():
    return _get_repo().get_coupons()


def _count_coupon_usage(coupon_code, orders):
    code = str(coupon_code or "").strip().upper()
    if not code:
        return 0
    return sum(1 for order in orders if str(order.get("coupon_code") or "").strip().upper() == code)


def validate_coupon(code, subtotal, orders=None):
    # 'orders' parameter is ignored now as we use used_count in the coupon itself
    # or the service handles it. But we keep it for signature compatibility.
    from services.coupon_service import CouponService
    return CouponService(_get_repo()).validate_coupon(code, subtotal)


def create_local_order(order):
    from services.order_service import create_order

    return create_order(order)


def update_order_status(pedido_id, novo_status):
    from services.order_service import update_status

    return update_status(pedido_id, novo_status)


def list_inventory_movements(product_id=None):
    return InventoryService(_get_repo()).list_movements(product_id)


def record_inventory_movement(product_id, quantity_delta, movement_type, reason, source_order_id=None, note=None):
    return InventoryService(_get_repo()).record_movement(product_id, quantity_delta, movement_type, reason, source_order_id, note)


def adjust_inventory_stock(product_id, quantity_delta, reason, note=None):
    return InventoryService(_get_repo()).adjust_stock(product_id, quantity_delta, reason, note)


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
    """Compatibility facade – delegates to DashboardService."""
    return DashboardService(_get_repo()).get_dashboard_stats()
