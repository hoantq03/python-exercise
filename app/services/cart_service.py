from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.storage import JsonStorage

from dataclasses import asdict
from typing import Dict, List
import uuid

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
        cart_data = self.storage.get_by_id(self.cart_id)
        if not cart_data:
            return Cart(id=self.cart_id, items=[])

        items_list = [CartItem(**item_data) for item_data in cart_data.get("items", [])]

        return Cart(id=cart_data["id"], items=items_list)

    def add_item(self, product: Dict, quantity: int = 1):
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
                price=float(product.get("price", 0)),
                quantity=quantity,
                avatar=product.get("avatar", ""),
            )
            cart.items.append(new_item)

        # Lưu lại toàn bộ giỏ hàng đã được cập nhật
        self._save_cart(cart)

    def update_item_quantity(self, item_id: str, new_quantity: int):
        cart = self.get_cart()
        item_to_update = next((item for item in cart.items if item.item_id == item_id), None)

        if item_to_update:
            if new_quantity > 0:
                item_to_update.quantity = new_quantity
                self._save_cart(cart)
            else:
                self.remove_item(item_id)

    def remove_item(self, item_id: str):
        cart = self.get_cart()
        cart.items = [item for item in cart.items if item.item_id != item_id]
        self._save_cart(cart)

    def clear_cart(self):
        cart = self.get_cart()
        cart.items = []
        self._save_cart(cart)

    def get_total(self) -> float:
        cart = self.get_cart()
        return cart.get_total()
