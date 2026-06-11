from datetime import datetime
from repositories.base import BaseRepository

class FirebaseRepository(BaseRepository):
    def __init__(self, db_client, fallback_repo: BaseRepository):
        self.db = db_client
        self.fallback = fallback_repo

    def read_data(self):
        return self.fallback.read_data()

    def write_data(self, data):
        self.fallback.write_data(data)

    def get_products(self):
        from database import normalize_product
        try:
            docs = self.db.collection("produtos").get()
            return [normalize_product(doc.to_dict() | {"id": doc.id}) for doc in docs]
        except Exception as error:
            print(f"Erro ao buscar produtos no Firebase: {error}")
            return self.fallback.get_products()

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

        try:
            self.db.collection("produtos").document(new_id).set(normalized)
            return new_id
        except Exception as error:
            print(f"Erro ao salvar produto no Firebase: {error}")
            return self.fallback.add_product(nome, descricao, preco, estoque, categoria, detalhes)

    def update_product(self, product_id, dados):
        from database import normalize_product
        normalized = normalize_product({"id": product_id, **(dados or {})})

        try:
            self.db.collection("produtos").document(product_id).set(normalized)
            return True
        except Exception as error:
            print(f"Erro ao atualizar produto no Firebase: {error}")
            return self.fallback.update_product(product_id, dados)

    def update_product_stock(self, product_id, novo_estoque):
        from database import _to_int
        products = self.get_products()
        current = next((product for product in products if product["id"] == product_id), None)
        if not current:
            return

        current["stock"] = _to_int(novo_estoque)
        self.update_product(product_id, current)

    def delete_product(self, produto_id):
        try:
            self.db.collection("produtos").document(produto_id).delete()
        except Exception as error:
            print(f"Erro ao deletar no Firebase: {error}")
            self.fallback.delete_product(produto_id)

    def listen_to_orders(self, callback):
        def on_snapshot(col_snapshot, changes, read_time):
            callback()
        try:
            return self.db.collection("pedidos").on_snapshot(on_snapshot)
        except Exception as error:
            print(f"Erro no snapshot: {error}")
            return self.fallback.listen_to_orders(callback)

    def get_orders(self):
        from database import normalize_order
        try:
            docs = self.db.collection("pedidos").get()
            return [normalize_order(doc.to_dict() | {"id": doc.id}) for doc in docs]
        except Exception as error:
            print(f"Erro ao buscar pedidos no Firebase: {error}")
            return self.fallback.get_orders()

    def get_coupons(self):
        from domain.coupon import normalize_coupon
        try:
            docs = self.db.collection("cupons").get()
            return [normalize_coupon(doc.to_dict() | {"code": doc.id}) for doc in docs]
        except Exception as error:
            print(f"Erro ao buscar cupons no Firebase: {error}")
            return self.fallback.get_coupons()

    def create_local_order(self, order):
        from firebase_admin import firestore
        from database import normalize_order, validate_coupon, normalize_product, _now_iso

        normalized = normalize_order(order, f"ord-{int(datetime.now().timestamp() * 1000)}")
        if not normalized["items"]:
            return {"ok": False, "message": "Pedido sem items.", "order_id": None}

        coupon_result = validate_coupon(normalized.get("coupon_code"), normalized["subtotal"]) if normalized.get("coupon_code") else None
        if normalized.get("coupon_code") and not coupon_result["valid"]:
            return {"ok": False, "message": coupon_result["message"], "order_id": None}

        discount_total = coupon_result["discount"] if coupon_result else 0.0
        expected_total = round(normalized["subtotal"] - discount_total + normalized["shipping"], 2)
        if abs(normalized["total"] - expected_total) > 0.01:
            normalized["total"] = expected_total
        normalized["discount_total"] = discount_total

        transaction = self.db.transaction()

        @firestore.transactional
        def process_order(txn):
            product_refs = {
                item["product_id"]: self.db.collection("produtos").document(item["product_id"])
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
                return {"ok": False, "message": f"Estoque insuficiente para: {', '.join(insufficient_stock)}", "order_id": None}

            for item in normalized["items"]:
                product_id = item["product_id"]
                product_ref = product_refs[product_id]
                current_stock = int(products_by_id[product_id].get("stock", 0))
                txn.update(product_ref, {"stock": current_stock - item["quantity"]})

            from services.inventory_service import InventoryService
            InventoryService(self).reserve_or_deduct_for_order(normalized)

            normalized["status"] = "pago"
            normalized["created_at"] = _now_iso()
            normalized["updated_at"] = normalized["created_at"]
            order_ref = self.db.collection("pedidos").document(normalized["id"])
            txn.set(order_ref, normalized)
            return {"ok": True, "message": "Pedido registrado.", "order_id": normalized["id"]}

        try:
            return process_order(transaction)
        except Exception as error:
            print(f"Erro ao registrar pedido no Firebase: {error}")
            return self.fallback.create_local_order(order)

    def update_order_status(self, pedido_id, novo_status):
        from database import _now_iso
        try:
            self.db.collection("pedidos").document(pedido_id).update({
                "status": novo_status,
                "updated_at": _now_iso(),
            })
        except Exception as error:
            print(f"Erro ao atualizar status no Firebase: {error}")
            self.fallback.update_order_status(pedido_id, novo_status)

    def get_movements(self):
        return self.fallback.get_movements()

    def add_movement(self, movement):
        self.fallback.add_movement(movement)
