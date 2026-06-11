from datetime import datetime
from typing import List, Optional, Dict, Any
from domain.inventory import InventoryMovement
from repositories.base import BaseRepository

class InventoryService:
    def __init__(self, repository: BaseRepository):
        self.repository = repository

    def list_movements(self, product_id: Optional[str] = None) -> List[Dict[str, Any]]:
        movements = self.repository.get_movements()
        if product_id:
            return [m for m in movements if m.get("product_id") == product_id]
        return movements

    def record_movement(self, product_id: str, quantity_delta: int, movement_type: str, reason: str, source_order_id: Optional[str] = None, note: Optional[str] = None):
        products = self.repository.get_products()
        product = next((p for p in products if p["id"] == product_id), None)
        product_name = product["name"] if product else "Produto Desconhecido"
        
        movement = InventoryMovement(
            id=f"mov-{int(datetime.now().timestamp() * 1000)}",
            product_id=product_id,
            product_name=product_name,
            quantity_delta=quantity_delta,
            movement_type=movement_type,
            reason=reason,
            source_order_id=source_order_id,
            created_at=datetime.utcnow().isoformat() + "Z",
            note=note
        )
        self.repository.add_movement(movement.to_dict())

    def adjust_stock(self, product_id: str, quantity_delta: int, reason: str, note: Optional[str] = None):
        products = self.repository.get_products()
        product = next((p for p in products if p["id"] == product_id), None)
        if not product:
            return False
            
        new_stock = int(product.get("stock", 0)) + quantity_delta
        self.repository.update_product_stock(product_id, new_stock)
        
        movement_type = "adjustment"
        if quantity_delta > 0:
            movement_type = "in"
        elif quantity_delta < 0:
            movement_type = "out"
            
        self.record_movement(
            product_id=product_id,
            quantity_delta=quantity_delta,
            movement_type=movement_type,
            reason=reason,
            note=note
        )
        return True

    def reserve_or_deduct_for_order(self, order: Dict[str, Any]):
        order_id = order.get("id")
        for item in order.get("items", []):
            product_id = item.get("product_id")
            quantity = item.get("quantity", 0)
            if product_id and quantity > 0:
                self.record_movement(
                    product_id=product_id,
                    quantity_delta=-quantity,
                    movement_type="out",
                    reason="Venda (Pedido)",
                    source_order_id=order_id
                )

    def restore_stock_for_order(self, order: Dict[str, Any]):
        order_id = order.get("id")
        for item in order.get("items", []):
            product_id = item.get("product_id")
            quantity = item.get("quantity", 0)
            if product_id and quantity > 0:
                # First update actual stock
                products = self.repository.get_products()
                product = next((p for p in products if p["id"] == product_id), None)
                if product:
                    new_stock = int(product.get("stock", 0)) + quantity
                    self.repository.update_product_stock(product_id, new_stock)
                
                self.record_movement(
                    product_id=product_id,
                    quantity_delta=quantity,
                    movement_type="in",
                    reason="Cancelamento de Pedido",
                    source_order_id=order_id
                )

    def get_low_stock_products(self, threshold: int) -> List[Dict[str, Any]]:
        products = self.repository.get_products()
        return [p for p in products if int(p.get("stock", 0)) < threshold]
