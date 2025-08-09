from dataclasses import dataclass, field
from typing import List, Dict, Any
@dataclass
class OrderItem:
    product_id: str
    qty: int
    price: float

@dataclass
class Order:
    id: str
    customer_id: str
    items: List[OrderItem] = field(default_factory=list)
    total: float = 0.0
    status: str = "NEW"  # NEW | PAID | CANCELED
    created_at: str = ""
    created_by: str = ""
