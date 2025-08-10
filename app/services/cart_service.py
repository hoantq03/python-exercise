from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.storage import JsonStorage

# ----- BẠN CẦN THÊM CÁC DÒNG NÀY VÀO ĐẦU FILE -----
from dataclasses import asdict  # Công cụ để chuyển dataclass thành dict
from typing import Dict, List
import uuid

# (Dán code model Cart và CartItem đã tạo ở bước trước vào đây hoặc import chúng)
from dataclasses import dataclass, field


class CartService:
    def __init__(self, storage: JsonStorage):
        self.storage = storage

        # Khởi tạo một giỏ hàng duy nhất khi bắt đầu
        all_carts_data = self.storage.all()
        if not all_carts_data:
            # Tạo một đối tượng Cart mới và lưu trữ nó
            new_cart = Cart(id=str(uuid.uuid4()), items=[])
            self.cart_id = new_cart.id
            # asdict chuyển object thành dictionary để lưu vào JSON
            self.storage.create(asdict(new_cart))
        else:
            # Lấy id của giỏ hàng đầu tiên tìm thấy
            self.cart_id = all_carts_data[0]["id"]

    def _save_cart(self, cart: Cart):
        """
        ## MỚI: Phương thức nội bộ để lưu đối tượng Cart vào storage.
        Chuyển đổi đối tượng Cart thành dictionary trước khi cập nhật.
        """
        self.storage.update(self.cart_id, asdict(cart))

    def get_cart(self) -> Cart:
        """
        ## THAY ĐỔI: Lấy thông tin giỏ hàng và chuyển đổi nó thành đối tượng Cart.
        Trả về một đối tượng Cart thay vì một dictionary.
        """
        cart_data = self.storage.get_by_id(self.cart_id)
        if not cart_data:
            # Xử lý trường hợp không tìm thấy giỏ hàng (an toàn hơn)
            return Cart(id=self.cart_id, items=[])

        # Chuyển đổi danh sách các item (dạng dict) thành danh sách các đối tượng CartItem
        items_list = [CartItem(**item_data) for item_data in cart_data.get("items", [])]

        return Cart(id=cart_data["id"], items=items_list)

    def add_item(self, product: Dict, quantity: int = 1):
        """
        ## THAY ĐỔI: Thêm một sản phẩm vào giỏ hàng, làm việc với các đối tượng.
        """
        cart = self.get_cart()

        # Tìm xem sản phẩm đã có trong giỏ hàng chưa
        found_item = None
        for item in cart.items:
            if item.product_id == product.get("id"):
                found_item = item
                break

        if found_item:
            # Nếu tìm thấy, chỉ cần cập nhật số lượng
            found_item.quantity += quantity
        else:
            # Nếu không tìm thấy, tạo một đối tượng CartItem mới và thêm vào
            new_item = CartItem(
                product_id=product.get("id"),
                name=product.get("name"),
                price=float(product.get("price", 0)),  # Đảm bảo giá là float
                quantity=quantity
            )
            cart.items.append(new_item)

        # Lưu lại toàn bộ giỏ hàng đã được cập nhật
        self._save_cart(cart)

    def update_item_quantity(self, item_id: str, new_quantity: int):
        """## MỚI: Phương thức chuyên dụng để cập nhật số lượng."""
        cart = self.get_cart()
        item_to_update = next((item for item in cart.items if item.item_id == item_id), None)

        if item_to_update:
            if new_quantity > 0:
                item_to_update.quantity = new_quantity
                self._save_cart(cart)
            else:
                # Nếu số lượng mới <= 0, hãy xóa sản phẩm
                self.remove_item(item_id)

    def remove_item(self, item_id: str):
        """
        ## THAY ĐỔI: Xóa một sản phẩm khỏi giỏ hàng.
        """
        cart = self.get_cart()
        # Lọc danh sách items, giữ lại những item không trùng item_id
        cart.items = [item for item in cart.items if item.item_id != item_id]
        self._save_cart(cart)

    def clear_cart(self):
        """
        ## THAY ĐỔI: Xóa tất cả sản phẩm trong giỏ hàng.
        """
        cart = self.get_cart()
        cart.items = []  # Đơn giản chỉ cần xóa sạch danh sách items
        self._save_cart(cart)

    def get_total(self) -> float:
        """
        ## THAY ĐỔI: Tính tổng giá trị giỏ hàng bằng phương thức của model.
        """
        cart = self.get_cart()
        return cart.get_total()  # Ủy quyền việc tính toán cho đối tượng Cart

