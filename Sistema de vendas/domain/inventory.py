from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

@dataclass
class InventoryMovement:
    id: str
    product_id: str
    product_name: str
    quantity_delta: int
    movement_type: str  # e.g., 'in', 'out', 'adjustment', 'reserve', 'cancel'
    reason: str
    created_at: str
    source_order_id: Optional[str] = None
    note: Optional[str] = None

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)
