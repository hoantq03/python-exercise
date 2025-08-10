import uuid
from dataclasses import dataclass, field
from typing import List

from app.models.cart_item import CartItem


@dataclass
class Cart:
    """
    Đại diện cho toàn bộ giỏ hàng của người dùng.
    """
    items: List[CartItem]

    # id của giỏ hàng, để phân biệt với các giỏ hàng khác nếu hệ thống mở rộng
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def get_total(self) -> float:
        """Tính tổng giá trị của toàn bộ giỏ hàng."""
        return sum(item.get_subtotal() for item in self.items)

    def get_item_count(self) -> int:
        """Đếm tổng số lượng sản phẩm trong giỏ."""
        return sum(item.quantity for item in self.items)
