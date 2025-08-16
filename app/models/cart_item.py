import uuid
from dataclasses import dataclass, field
from typing import List


@dataclass
class CartItem:
    product_id: str
    price: float
    quantity: int
    name: str
    avatar: str = ""

    item_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def get_subtotal(self) -> float:
        return self.price * self.quantity

