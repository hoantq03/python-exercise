from app.models.storage import JsonStorage
from app.models.order import Order      # Import model mới
from dataclasses import asdict

class OrderService:
    def __init__(self, orders_storage: JsonStorage, products_storage: JsonStorage):
        """
        Khởi tạo OrderService.

        Args:
            orders_storage: Kho lưu trữ cho các đơn hàng.
            products_storage: Kho lưu trữ cho sản phẩm (để cập nhật tồn kho).
        """
        self.orders_storage = orders_storage
        self.products_storage = products_storage

    def create_order(self, payload: dict) -> dict:
        """
        Tạo một đơn hàng mới, cập nhật tồn kho và lưu vào storage.
        Đây chính là phương thức đang bị thiếu.
        """
        # 1. Tạo một đối tượng Order từ payload do CartView gửi qua
        new_order = Order(
            customer_id=payload.get("customer_id"),
            customer_info=payload.get("customer_info"),
            items=payload.get("items"),
            total_amount=payload.get("total_amount"),
            user_id=payload.get("user_id")
        )

        # 2. Cập nhật tồn kho sản phẩm (bước quan trọng)
        try:
            for item in new_order.items:
                product_id = item.get("product_id")
                quantity_ordered = item.get("quantity")

                # Lấy thông tin sản phẩm từ kho
                product_to_update = self.products_storage.get_by_id(product_id)

                if not product_to_update:
                    # Nếu sản phẩm không còn tồn tại, hủy tiến trình
                    raise ValueError(f"Sản phẩm với ID {product_id} không tồn tại.")

                current_stock = int(product_to_update.get("stock", 0))
                if current_stock < quantity_ordered:
                    # Nếu không đủ hàng, hủy tiến trình
                    raise ValueError(f"Không đủ hàng cho sản phẩm '{product_to_update.get('name')}'. "
                                     f"Còn lại: {current_stock}, Cần mua: {quantity_ordered}")

                # Trừ đi số lượng đã bán
                new_stock = current_stock - quantity_ordered
                self.products_storage.update(product_id, {"stock": new_stock})
                print(f"Đã cập nhật tồn kho cho {product_id}: {current_stock} -> {new_stock}")

            # 3. Nếu tất cả cập nhật tồn kho thành công, lưu đơn hàng vào storage
            order_dict = asdict(new_order)
            self.orders_storage.create(order_dict)
            print(f"Đã tạo thành công đơn hàng !")

            # 4. Trả về thông tin đơn hàng vừa tạo (dạng dict)
            return order_dict

        except ValueError as e:
            print(f"LỖI khi tạo đơn hàng: {e}")
            raise e
        except Exception as e:
            print(f"LỖI không xác định khi tạo đơn hàng: {e}")
            raise e

    def list_orders(self):
        """Lấy danh sách tất cả đơn hàng."""
        return self.orders_storage.all()

    def get_order_by_id(self, order_id: str):
        """Lấy một đơn hàng cụ thể bằng ID."""
        return self.orders_storage.get_by_id(order_id)

    def update_order_status(self, order_id: str, new_status: str):
        """Cập nhật trạng thái của một đơn hàng (ví dụ: 'pending' -> 'completed')."""
        return self.orders_storage.update(order_id, {"status": new_status})

