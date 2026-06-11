import json
import os
from datetime import datetime
from repositories.base import BaseRepository

class JsonRepository(BaseRepository):
    def __init__(self, db_file: str):
        self.db_file = db_file

    def _initial_data(self):
        from database import SEED_PRODUCTS, SEED_COUPONS, normalize_product
        from domain.coupon import normalize_coupon
        return {
            "produtos": [normalize_product(product) for product in SEED_PRODUCTS],
            "cupons": [normalize_coupon(coupon) for coupon in SEED_COUPONS],
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
                    "subtotal": 920.00,
                    "shipping": 0.0,
                    "discount_total": 0.0,
                    "coupon_code": None,
                    "total": 920.00,
                    "status": "enviado",
                    "created_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
                }
            ],
            "vendas": [],
            "estoque_movimentos": [],
        }

    def _init_db(self):
        if not os.path.exists(self.db_file):
            with open(self.db_file, "w", encoding="utf-8") as file:
                json.dump(self._initial_data(), file, indent=4, ensure_ascii=False)

    def read_data(self):
        self._init_db()
        from database import normalize_product, normalize_order, SEED_COUPONS
        from domain.coupon import normalize_coupon
        with open(self.db_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        data["produtos"] = [normalize_product(product) for product in data.get("produtos", [])]
        data["cupons"] = [normalize_coupon(coupon) for coupon in data.get("cupons", SEED_COUPONS or [])]
        data["pedidos"] = [normalize_order(order) for order in data.get("pedidos", [])]
        data.setdefault("vendas", [])
        data.setdefault("estoque_movimentos", [])
        return data

    def write_data(self, data):
        from database import normalize_product, normalize_order, _export_to_frontend
        from domain.coupon import normalize_coupon
        clean_data = {
            "produtos": [normalize_product(product) for product in data.get("produtos", [])],
            "cupons": [normalize_coupon(coupon) for coupon in data.get("cupons", [])],
            "pedidos": [normalize_order(order) for order in data.get("pedidos", [])],
            "vendas": data.get("vendas", []),
            "estoque_movimentos": data.get("estoque_movimentos", []),
        }

        with open(self.db_file, "w", encoding="utf-8") as file:
            json.dump(clean_data, file, indent=4, ensure_ascii=False)

        _export_to_frontend(clean_data)

    def get_products(self):
        return self.read_data()["produtos"]

    def add_product(self, nome, descricao, preco, estoque, categoria, detalhes=None):
        from database import normalize_product
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

        data = self.read_data()
        data["produtos"].append(normalized)
        self.write_data(data)
        return new_id

    def update_product(self, product_id, dados):
        from database import normalize_product
        normalized = normalize_product({"id": product_id, **(dados or {})})
        data = self.read_data()
        updated = False
        for index, product in enumerate(data["produtos"]):
            if product["id"] == product_id:
                data["produtos"][index] = normalized
                updated = True
                break

        if updated:
            self.write_data(data)
        return updated

    def update_product_stock(self, product_id, novo_estoque):
        from database import _to_int
        products = self.get_products()
        current = next((product for product in products if product["id"] == product_id), None)
        if not current:
            return

        current["stock"] = _to_int(novo_estoque)
        self.update_product(product_id, current)

    def delete_product(self, produto_id):
        data = self.read_data()
        data["produtos"] = [product for product in data["produtos"] if product["id"] != produto_id]
        self.write_data(data)

    def listen_to_orders(self, callback):
        return None

    def get_orders(self):
        return self.read_data()["pedidos"]

    def get_coupons(self):
        return self.read_data()["cupons"]

    def create_local_order(self, order):
        from database import normalize_order, _next_order_id, validate_coupon, _now_iso
        data = self.read_data()
        normalized = normalize_order(order, _next_order_id(data["pedidos"]))
        if not normalized["items"]:
            return {"ok": False, "message": "Pedido sem itens.", "order_id": None}

        coupon_result = validate_coupon(normalized.get("coupon_code"), normalized["subtotal"], data["pedidos"]) if normalized.get("coupon_code") else None
        if normalized.get("coupon_code") and not coupon_result["valid"]:
            return {"ok": False, "message": coupon_result["message"], "order_id": None}

        normalized["discount_total"] = coupon_result["discount"] if coupon_result else 0.0
        normalized["total"] = round(normalized["subtotal"] - normalized["discount_total"] + normalized["shipping"], 2)

        products_by_id = {product["id"]: product for product in data["produtos"]}
        insufficient_stock = []
        for item in normalized["items"]:
            product = products_by_id.get(item["product_id"])
            if not product or int(product.get("stock", 0)) < item["quantity"]:
                insufficient_stock.append(item["product_name"])

        if insufficient_stock:
            return {"ok": False, "message": f"Estoque insuficiente para: {', '.join(insufficient_stock)}", "order_id": None}

        for item in normalized["items"]:
            product = products_by_id.get(item["product_id"])
            if product:
                product["stock"] = int(product.get("stock", 0)) - item["quantity"]
        
        data["pedidos"].append(normalized)
        self.write_data(data)

        from services.inventory_service import InventoryService
        InventoryService(self).reserve_or_deduct_for_order(normalized)

        return {"ok": True, "message": "Pedido registrado.", "order_id": normalized["id"]}

    def update_order_status(self, pedido_id, novo_status):
        from database import _now_iso
        data = self.read_data()
        for order in data["pedidos"]:
            if order["id"] == pedido_id:
                order["status"] = novo_status
                order["updated_at"] = _now_iso()
                break
        self.write_data(data)

    def get_movements(self):
        return self.read_data().get("estoque_movimentos", [])

    def add_movement(self, movement):
        data = self.read_data()
        data.setdefault("estoque_movimentos", [])
        data["estoque_movimentos"].append(movement)
        self.write_data(data)
