import uuid
from dataclasses import dataclass, field
from typing import List

from app.models.cart_item import CartItem


@dataclass
class Cart:
    items: List[CartItem]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def get_total(self) -> float:
        return sum(item.get_subtotal() for item in self.items)

    def get_item_count(self) -> int:
        return sum(item.quantity for item in self.items)
