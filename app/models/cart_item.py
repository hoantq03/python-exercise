import uuid
from dataclasses import dataclass, field
from typing import List


@dataclass
class CartItem:
    """
    Đại diện cho một món hàng trong giỏ hàng.
    """
    product_id: str
    price: float
    quantity: int
    name: str  # Nên giữ lại tên để hiển thị dễ dàng trong giỏ hàng

    # item_id là id duy nhất cho mỗi dòng trong giỏ hàng, khác với product_id
    # 'id' trong yêu cầu của bạn tương ứng với 'item_id' ở đây.
    item_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def get_subtotal(self) -> float:
        """Tính tổng giá trị của món hàng này (giá * số lượng)."""
        return self.price * self.quantity

