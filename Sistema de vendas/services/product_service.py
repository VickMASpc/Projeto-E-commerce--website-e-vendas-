"""Product service logic."""

from __future__ import annotations

from typing import Any, Dict, Optional

from domain.product import normalize_product, validate_product
from services.inventory_service import InventoryService


class ProductService:
    def __init__(self, repository):
        self.repository = repository

    def list_products(self) -> list[Dict[str, Any]]:
        return [normalize_product(product) for product in self.repository.get_products()]

    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        if not product_id:
            return None
        return next(
            (product for product in self.list_products() if product.get("id") == product_id),
            None,
        )

    def create_product(self, payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        raw_payload = dict(payload or {})
        normalized = normalize_product(raw_payload)
        validation = validate_product(normalized, raw_payload)
        if "category" not in raw_payload and "categoria" not in raw_payload:
            validation["valid"] = False
            validation["errors"].setdefault("category", []).append(
                {"code": "required", "message": "Category is required."}
            )
        if not validation["valid"]:
            return {
                "ok": False,
                "message": "Invalid product data.",
                "errors": validation["errors"],
                "product": validation["product"],
            }

        details = self._details_from_product(normalized)
        new_id = self.repository.add_product(
            normalized["name"],
            normalized["description"],
            normalized["price"],
            normalized["stock"],
            normalized["category"],
            details,
        )
        created = self.get_product(new_id) if new_id else None
        if not created:
            return {
                "ok": False,
                "message": "Product could not be created.",
                "errors": {"product": [{"code": "create_failed", "message": "Product could not be created."}]},
                "product": None,
            }

        if created.get("stock", 0) > 0:
            InventoryService(self.repository).record_movement(
                product_id=created["id"],
                quantity_delta=created["stock"],
                movement_type="in",
                reason="Inicializacao de estoque",
                note="Criação do produto"
            )

        return {"ok": True, "message": "Product created.", "errors": {}, "product": created}

    def update_product(self, product_id: str, payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        current = self.get_product(product_id)
        if not current:
            return {
                "ok": False,
                "message": "Product not found.",
                "errors": {"id": [{"code": "not_found", "message": "Product not found."}]},
                "product": None,
            }

        raw_payload = dict(payload or {})
        merged_payload = dict(current)
        merged_payload.update(raw_payload)
        merged_payload["id"] = product_id
        validation = validate_product(merged_payload, raw_payload)
        if not validation["valid"]:
            return {
                "ok": False,
                "message": "Invalid product data.",
                "errors": validation["errors"],
                "product": validation["product"],
            }

        updated = self.repository.update_product(product_id, validation["product"])
        if not updated:
            return {
                "ok": False,
                "message": "Product could not be updated.",
                "errors": {"product": [{"code": "update_failed", "message": "Product could not be updated."}]},
                "product": validation["product"],
            }

        if "stock" in raw_payload:
            new_stock = int(raw_payload["stock"])
            old_stock = int(current.get("stock", 0))
            delta = new_stock - old_stock
            if delta != 0:
                InventoryService(self.repository).record_movement(
                    product_id=product_id,
                    quantity_delta=delta,
                    movement_type="adjustment",
                    reason="Atualizacao manual via painel",
                    note=f"De {old_stock} para {new_stock}"
                )

        return {
            "ok": True,
            "message": "Product updated.",
            "errors": {},
            "product": self.get_product(product_id),
        }

    def delete_product(self, product_id: str) -> Dict[str, Any]:
        current = self.get_product(product_id)
        if not current:
            return {
                "ok": False,
                "message": "Product not found.",
                "errors": {"id": [{"code": "not_found", "message": "Product not found."}]},
                "product": None,
            }

        self.repository.delete_product(product_id)
        deleted = self.get_product(product_id)
        return {
            "ok": deleted is None,
            "message": "Product deleted." if deleted is None else "Product could not be deleted.",
            "errors": {} if deleted is None else {"product": [{"code": "delete_failed", "message": "Product could not be deleted."}]},
            "product": current,
        }

    def update_stock(self, product_id: str, new_stock: Any) -> Dict[str, Any]:
        current = self.get_product(product_id)
        if not current:
            return {
                "ok": False,
                "message": "Product not found.",
                "errors": {"id": [{"code": "not_found", "message": "Product not found."}]},
                "product": None,
            }

        return self.update_product(product_id, {"stock": new_stock})

    def filter_products(self, filters: Optional[Dict[str, Any]]) -> list[Dict[str, Any]]:
        products = self.list_products()
        filters = dict(filters or {})
        if not filters:
            return products

        query = str(filters.get("query") or "").strip().lower()
        category = str(filters.get("category") or "").strip().lower()
        brand = str(filters.get("brand") or "").strip().lower()
        min_price = filters.get("min_price")
        max_price = filters.get("max_price")
        min_stock = filters.get("min_stock")
        max_stock = filters.get("max_stock")

        def matches(product: Dict[str, Any]) -> bool:
            if query:
                haystack = " ".join(
                    str(product.get(field, "") or "")
                    for field in ("name", "brand", "category", "description", "sku")
                ).lower()
                if query not in haystack:
                    return False

            if category and str(product.get("category", "")).strip().lower() != category:
                return False

            if brand and str(product.get("brand", "")).strip().lower() != brand:
                return False

            if min_price is not None and product.get("price", 0.0) < float(min_price):
                return False

            if max_price is not None and product.get("price", 0.0) > float(max_price):
                return False

            if min_stock is not None and int(product.get("stock", 0)) < int(float(min_stock)):
                return False

            if max_stock is not None and int(product.get("stock", 0)) > int(float(max_stock)):
                return False

            for key, value in filters.items():
                if key in {"query", "category", "brand", "min_price", "max_price", "min_stock", "max_stock"}:
                    continue
                if value is None:
                    continue
                if str(product.get(key, "")).strip().lower() != str(value).strip().lower():
                    return False

            return True

        return [product for product in products if matches(product)]

    @staticmethod
    def _details_from_product(product: Dict[str, Any]) -> Dict[str, Any]:
        excluded = {"id", "name", "description", "price", "stock", "category"}
        return {key: value for key, value in product.items() if key not in excluded}
