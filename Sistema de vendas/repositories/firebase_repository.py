from datetime import datetime

from repositories.base import BaseRepository


class FirebaseRepository(BaseRepository):
    def __init__(self, db_client, fallback_repo: BaseRepository, allow_mock_fallback: bool = False):
        self.db = db_client
        self.fallback = fallback_repo
        self.allow_mock_fallback = allow_mock_fallback

    def _run_with_policy(self, action_name, firebase_operation, fallback_operation):
        try:
            return firebase_operation()
        except Exception as error:
            if not self.allow_mock_fallback:
                raise RuntimeError(
                    f"[DATA][FIREBASE-ONLY] Operacao '{action_name}' falhou no Firebase e o fallback mock nao esta permitido: {error}"
                ) from error

            print(
                f"[DATA][MOCK-FALLBACK] Operacao '{action_name}' falhou no Firebase ({error}). "
                "Usando repositorio JSON/mock por configuracao explicita."
            )
            return fallback_operation()

    def _collection_docs(self, collection_name):
        return list(self.db.collection(collection_name).get())

    def _snapshot_data(self):
        from database import normalize_order, normalize_product
        from domain.coupon import normalize_coupon

        products = [
            normalize_product(doc.to_dict() | {"id": doc.id})
            for doc in self._collection_docs("produtos")
        ]
        orders = [
            normalize_order(doc.to_dict() | {"id": doc.id})
            for doc in self._collection_docs("pedidos")
        ]
        coupons = [
            normalize_coupon(doc.to_dict() | {"code": doc.id})
            for doc in self._collection_docs("cupons")
        ]
        movements = [
            dict(doc.to_dict() | {"id": doc.id})
            for doc in self._collection_docs("estoque_movimentos")
        ]
        return {
            "produtos": products,
            "pedidos": orders,
            "cupons": coupons,
            "vendas": [],
            "estoque_movimentos": movements,
        }

    def _write_collection(self, collection_name, entries, id_field):
        target = self.db.collection(collection_name)
        existing_docs = {doc.id for doc in target.get()}
        next_ids = set()
        batch = self.db.batch()

        for entry in entries:
            payload = dict(entry or {})
            document_id = str(payload.get(id_field) or "").strip()
            if not document_id:
                continue
            next_ids.add(document_id)
            payload.pop(id_field, None)
            batch.set(target.document(document_id), payload)

        for document_id in existing_docs - next_ids:
            batch.delete(target.document(document_id))

        batch.commit()

    def read_data(self):
        return self._run_with_policy("read_data", self._snapshot_data, self.fallback.read_data)

    def write_data(self, data):
        return self._run_with_policy(
            "write_data",
            lambda: (
                self._write_collection("produtos", data.get("produtos", []), "id"),
                self._write_collection("pedidos", data.get("pedidos", []), "id"),
                self._write_collection("cupons", data.get("cupons", []), "code"),
                self._write_collection("estoque_movimentos", data.get("estoque_movimentos", []), "id"),
            ),
            lambda: self.fallback.write_data(data),
        )

    def get_products(self):
        from database import normalize_product

        return self._run_with_policy(
            "get_products",
            lambda: [
                normalize_product(doc.to_dict() | {"id": doc.id})
                for doc in self.db.collection("produtos").get()
            ],
            self.fallback.get_products,
        )

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

        return self._run_with_policy(
            "add_product",
            lambda: (self.db.collection("produtos").document(new_id).set(normalized), new_id)[1],
            lambda: self.fallback.add_product(nome, descricao, preco, estoque, categoria, detalhes),
        )

    def update_product(self, product_id, dados):
        from database import normalize_product

        normalized = normalize_product({"id": product_id, **(dados or {})})
        return self._run_with_policy(
            "update_product",
            lambda: (self.db.collection("produtos").document(product_id).set(normalized), True)[1],
            lambda: self.fallback.update_product(product_id, dados),
        )

    def update_product_stock(self, product_id, novo_estoque):
        from database import _to_int

        products = self.get_products()
        current = next((product for product in products if product["id"] == product_id), None)
        if not current:
            return

        current["stock"] = _to_int(novo_estoque)
        self.update_product(product_id, current)

    def delete_product(self, produto_id):
        return self._run_with_policy(
            "delete_product",
            lambda: self.db.collection("produtos").document(produto_id).delete(),
            lambda: self.fallback.delete_product(produto_id),
        )

    def listen_to_orders(self, callback):
        def on_snapshot(col_snapshot, changes, read_time):
            callback()

        return self._run_with_policy(
            "listen_to_orders",
            lambda: self.db.collection("pedidos").on_snapshot(on_snapshot),
            lambda: self.fallback.listen_to_orders(callback),
        )

    def get_orders(self):
        from database import normalize_order

        return self._run_with_policy(
            "get_orders",
            lambda: [
                normalize_order(doc.to_dict() | {"id": doc.id})
                for doc in self.db.collection("pedidos").get()
            ],
            self.fallback.get_orders,
        )

    def get_coupons(self):
        from domain.coupon import normalize_coupon

        return self._run_with_policy(
            "get_coupons",
            lambda: [
                normalize_coupon(doc.to_dict() | {"code": doc.id})
                for doc in self.db.collection("cupons").get()
            ],
            self.fallback.get_coupons,
        )

    def create_local_order(self, order):
        from firebase_admin import firestore
        from database import normalize_order, validate_coupon, normalize_product, _now_iso

        normalized = normalize_order(order, f"ord-{int(datetime.now().timestamp() * 1000)}")
        if not normalized["items"]:
            return {"ok": False, "message": "Pedido sem items.", "order_id": None}

        coupon_result = (
            validate_coupon(normalized.get("coupon_code"), normalized["subtotal"])
            if normalized.get("coupon_code")
            else None
        )
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

            from services.inventory_service import InventoryService

            InventoryService(self).reserve_or_deduct_for_order(normalized)

            normalized["status"] = "pago"
            normalized["created_at"] = _now_iso()
            normalized["updated_at"] = normalized["created_at"]
            order_ref = self.db.collection("pedidos").document(normalized["id"])
            txn.set(order_ref, normalized)
            return {"ok": True, "message": "Pedido registrado.", "order_id": normalized["id"]}

        return self._run_with_policy(
            "create_local_order",
            lambda: process_order(transaction),
            lambda: self.fallback.create_local_order(order),
        )

    def update_order_status(self, pedido_id, novo_status):
        from database import _now_iso

        return self._run_with_policy(
            "update_order_status",
            lambda: self.db.collection("pedidos").document(pedido_id).update(
                {
                    "status": novo_status,
                    "updated_at": _now_iso(),
                }
            ),
            lambda: self.fallback.update_order_status(pedido_id, novo_status),
        )

    def get_movements(self):
        return self._run_with_policy(
            "get_movements",
            lambda: [dict(doc.to_dict() | {"id": doc.id}) for doc in self.db.collection("estoque_movimentos").get()],
            self.fallback.get_movements,
        )

    def add_movement(self, movement):
        return self._run_with_policy(
            "add_movement",
            lambda: self.db.collection("estoque_movimentos").document(
                str((movement or {}).get("id") or f"mov-{int(datetime.now().timestamp() * 1000)}")
            ).set(dict(movement or {})),
            lambda: self.fallback.add_movement(movement),
        )
