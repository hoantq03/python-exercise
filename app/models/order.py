# File: app/models/order.py
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any


@dataclass
class Order:
    # --- THÊM DÒNG NÀY ---
    customer_id: str  # ID của khách hàng đặt đơn

    customer_info: Dict[str, str]
    items: List[Dict[str, Any]]
    total_amount: float
    user_id: str

    status: str = "completed"
    order_date: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
