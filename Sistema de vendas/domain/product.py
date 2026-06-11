"""Product domain model and normalization helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Mapping, Optional


@dataclass
class Product:
    id: str = ""
    name: str = "Produto"
    brand: str = ""
    tagline: str = ""
    description: str = ""
    longDescription: str = ""
    price: float = 0.0
    oldPrice: float = 0.0
    stock: int = 0
    category: str = "Masculino"
    image_url: str = ""
    imageEmoji: str = "✨"
    sku: str = ""
    volume_ml: str = "100 ml"
    concentration: str = "Eau de Parfum"
    olfactiveFamily: str = "Amadeirado"
    occasion: str = "Uso versatil"
    topNotes: list[str] = field(default_factory=list)
    heartNotes: list[str] = field(default_factory=list)
    baseNotes: list[str] = field(default_factory=list)
    highlights: list[str] = field(default_factory=list)
    rating: float = 4.8
    reviews: int = 0
    isSale: bool = False
    isNew: bool = False
    images: list[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


DEFAULT_PRODUCT = Product().to_dict()


def parse_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return fallback


def parse_int(value: Any, fallback: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return fallback


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value == 1
    return str(value).strip().lower() in {"1", "true", "sim", "yes"}


def parse_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if not value:
        return []

    text = str(value)
    for separator in (";", "|", "\n"):
        text = text.replace(separator, ",")
    return [item.strip() for item in text.split(",") if item.strip()]


def _push_error(errors: Dict[str, list[dict[str, str]]], field: str, code: str, message: str) -> None:
    errors.setdefault(field, []).append({"code": code, "message": message})


def _is_blank(value: Any) -> bool:
    return not str(value or "").strip()


def _is_numeric_value(value: Any) -> bool:
    if value in (None, ""):
        return False
    try:
        float(str(value).replace(",", "."))
        return True
    except (TypeError, ValueError):
        return False


def _dedupe_images(images: list[str], image_url: str) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()

    if image_url:
        ordered.append(image_url)
        seen.add(image_url)

    for image in images:
        if image and image not in seen:
            ordered.append(image)
            seen.add(image)

    return ordered


def normalize_product(
    product: Optional[Mapping[str, Any]],
    seed_products_by_id: Optional[Mapping[str, Mapping[str, Any]]] = None,
    seed_products_by_name: Optional[Mapping[str, Mapping[str, Any]]] = None,
) -> Dict[str, Any]:
    product = dict(product or {})
    seed_match: Dict[str, Any] = {}

    raw_id = str(product.get("id", "") or "").strip()
    raw_name = str(product.get("name") or product.get("nome") or "").strip().lower()
    if raw_id and seed_products_by_id and raw_id in seed_products_by_id:
        seed_match = dict(seed_products_by_id[raw_id])
    elif raw_name and seed_products_by_name and raw_name in seed_products_by_name:
        seed_match = dict(seed_products_by_name[raw_name])

    merged = dict(DEFAULT_PRODUCT)
    merged.update(seed_match)
    merged.update(product)

    raw_brand = product.get("brand") or product.get("marca") or ""
    raw_tagline = product.get("tagline") or product.get("subtitulo") or ""
    raw_top_notes = parse_list(product.get("topNotes") or product.get("notasTopo"))
    legacy_sparse_product = bool(seed_match) and not raw_brand and not raw_tagline and not raw_top_notes

    normalized = Product(
        id=str(merged.get("id", "") or "").strip(),
        name=str(merged.get("name") or merged.get("nome") or "Produto").strip() or "Produto",
        brand=str(merged.get("brand") or merged.get("marca") or "").strip(),
        tagline=str(merged.get("tagline") or merged.get("subtitulo") or "").strip(),
        description=str(merged.get("description") or merged.get("descricao") or "").strip(),
        longDescription=str(
            merged.get("longDescription")
            or merged.get("descricao_longa")
            or merged.get("description")
            or merged.get("descricao")
            or ""
        ).strip(),
        price=parse_float(merged.get("price", merged.get("preco", 0.0))),
        oldPrice=parse_float(merged.get("oldPrice", merged.get("precoAntigo", 0.0))),
        stock=parse_int(merged.get("stock", merged.get("estoque", 0))),
        category=str(merged.get("category") or merged.get("categoria") or "Masculino").strip() or "Masculino",
        image_url=str(merged.get("image_url") or merged.get("imageUrl") or "").strip(),
        imageEmoji=str(merged.get("imageEmoji") or merged.get("emoji") or "✨").strip() or "✨",
        sku=str(merged.get("sku") or merged.get("codigo") or "").strip(),
        volume_ml=str(merged.get("volume_ml") or merged.get("volumeMl") or merged.get("tamanho") or "100 ml").strip() or "100 ml",
        concentration=str(merged.get("concentration") or merged.get("concentracao") or "Eau de Parfum").strip() or "Eau de Parfum",
        olfactiveFamily=str(merged.get("olfactiveFamily") or merged.get("familiaOlfativa") or "Amadeirado").strip() or "Amadeirado",
        occasion=str(merged.get("occasion") or merged.get("ocasiao") or "Uso versatil").strip() or "Uso versatil",
        topNotes=parse_list(merged.get("topNotes") or merged.get("notasTopo")),
        heartNotes=parse_list(merged.get("heartNotes") or merged.get("notasCoracao")),
        baseNotes=parse_list(merged.get("baseNotes") or merged.get("notasBase")),
        highlights=parse_list(merged.get("highlights") or merged.get("destaques")),
        rating=parse_float(merged.get("rating", 4.8), 4.8),
        reviews=parse_int(merged.get("reviews", 0), 0),
        isSale=parse_bool(merged.get("isSale") if merged.get("isSale") is not None else merged.get("emOferta")),
        isNew=parse_bool(merged.get("isNew") if merged.get("isNew") is not None else merged.get("eNovo")),
        images=parse_list(merged.get("images") or merged.get("image_urls") or merged.get("imageUrls")),
    ).to_dict()

    if legacy_sparse_product:
        for field_name in (
            "brand",
            "tagline",
            "description",
            "longDescription",
            "category",
            "imageEmoji",
            "volume_ml",
            "concentration",
            "olfactiveFamily",
            "occasion",
            "topNotes",
            "heartNotes",
            "baseNotes",
            "highlights",
            "rating",
            "reviews",
            "isSale",
            "isNew",
        ):
            normalized[field_name] = seed_match.get(field_name, normalized[field_name])

    normalized["images"] = _dedupe_images(normalized["images"], normalized["image_url"])
    if not normalized["sku"] and normalized["id"]:
        normalized["sku"] = normalized["id"].upper()

    return normalized


def validate_product(
    product: Optional[Mapping[str, Any]],
    raw_product: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    normalized = normalize_product(product)
    raw_product = dict(raw_product or {})
    errors: Dict[str, list[dict[str, str]]] = {}

    if _is_blank(normalized.get("name")) or normalized.get("name") == "Produto":
        _push_error(errors, "name", "required", "Name is required.")

    raw_category = raw_product.get("category", raw_product.get("categoria"))
    if ("category" in raw_product or "categoria" in raw_product) and _is_blank(raw_category):
        _push_error(errors, "category", "required", "Category is required.")
    elif _is_blank(normalized.get("category")):
        _push_error(errors, "category", "required", "Category is required.")

    if "price" in raw_product or "preco" in raw_product:
        raw_price = raw_product.get("price", raw_product.get("preco"))
        if not _is_numeric_value(raw_price):
            _push_error(errors, "price", "invalid", "Price must be a number.")
    if normalized.get("price", 0.0) < 0:
        _push_error(errors, "price", "min_value", "Price must be greater than or equal to 0.")

    if "stock" in raw_product or "estoque" in raw_product:
        raw_stock = raw_product.get("stock", raw_product.get("estoque"))
        if not _is_numeric_value(raw_stock):
            _push_error(errors, "stock", "invalid", "Stock must be an integer.")
    if normalized.get("stock", 0) < 0:
        _push_error(errors, "stock", "min_value", "Stock must be greater than or equal to 0.")

    return {
        "valid": not errors,
        "errors": errors,
        "product": normalized,
    }
