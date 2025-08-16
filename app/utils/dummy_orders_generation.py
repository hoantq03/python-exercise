import random
import uuid
from datetime import datetime, timedelta

# Import các service của bạn
# Đảm bảo đường dẫn import chính xác với cấu trúc dự án của bạn
# from app.services.product_service import ProductService
# from app.services.customer_service import CustomerService
# from app.services.order_service import OrderService
# from app.services.user_service import UserService # Đảm bảo bạn đã có UserService

class DummyOrderCreator:
    def __init__(self, product_service, customer_service, order_service, user_service):
        """
        Khởi tạo DummyOrderCreator.

        Args:
            product_service: Đối tượng ProductService của bạn.
            customer_service: Đối tượng CustomerService của bạn.
            order_service: Đối tượng OrderService của bạn.
            user_service: Đối tượng UserService của bạn (để lấy thông tin user_id cho đơn hàng).
        """
        self.product_service = product_service
        self.customer_service = customer_service
        self.order_service = order_service
        self.user_service = user_service

    def create_random_orders(self, count=10, max_days_back=180):
        """
        Tạo và lưu trữ các đơn hàng ngẫu nhiên.
        Sản phẩm, khách hàng và người dùng sẽ được lấy từ các service hiện có.

        Args:
            count (int): Số lượng đơn hàng muốn tạo. Mặc định là 10.
            max_days_back (int): Số ngày tối đa lùi về quá khứ cho ngày đặt hàng.
                                  Mặc định là 180 (khoảng 6 tháng).

        Returns:
            list: Danh sách các đơn hàng đã được tạo (dạng dict).
        """
        # Lấy dữ liệu hiện có từ các service
        products = self.product_service.list()
        customers = self.customer_service.list()
        users = self.user_service.list() # Lấy danh sách người dùng

        # Kiểm tra xem có đủ dữ liệu để tạo đơn hàng không
        if not products:
            print("Không có sản phẩm trong hệ thống. Vui lòng thêm sản phẩm trước khi tạo đơn hàng mẫu.")
            return []
        if not customers:
            print("Không có khách hàng trong hệ thống. Vui lòng thêm khách hàng trước khi tạo đơn hàng mẫu.")
            return []
        if not users:
            print("Không có người dùng trong hệ thống. Vui lòng thêm người dùng trước khi tạo đơn hàng mẫu.")
            return []

        created_orders = []
        for _ in range(count):
            # Chọn ngẫu nhiên một khách hàng và một người dùng
            customer = random.choice(customers)
            user = random.choice(users)

            # Chọn ngẫu nhiên số lượng sản phẩm trong đơn hàng (1 đến 5)
            num_items_in_order = random.randint(1, 5)
            # Chọn ngẫu nhiên các sản phẩm từ danh sách sản phẩm hiện có
            chosen_products_for_order = random.sample(products, min(num_items_in_order, len(products)))

            items_for_order = []
            total_amount_for_order = 0

            # Tạo danh sách các mặt hàng cho đơn hàng
            for prod in chosen_products_for_order:
                quantity = random.randint(1, 10) # Số lượng của mỗi sản phẩm
                item = {
                    "product_id": prod["id"],
                    "price": prod["price"],
                    "quantity": quantity,
                    "name": prod["name"],
                    "item_id": str(uuid.uuid4()) # ID duy nhất cho mỗi item trong đơn hàng
                }
                items_for_order.append(item)
                total_amount_for_order += prod["price"] * quantity

            # Tạo ngày đặt hàng ngẫu nhiên trong khoảng 'max_days_back' ngày gần đây
            order_date = datetime.now() - timedelta(days=random.randint(0, max_days_back))

            # Tạo payload cho đơn hàng
            order_payload = {
                "id": str(uuid.uuid4()), # ID duy nhất cho đơn hàng
                "customer_id": customer["id"],
                "customer_info": { # Thông tin khách hàng tại thời điểm đặt hàng (lưu snapshot)
                    "name": customer["name"],
                    "phone": customer["phone"],
                    "email": customer.get("email", ""),
                    "address": customer.get("address", "")
                },
                "items": items_for_order,
                "total_amount": total_amount_for_order,
                "user_id": user["id"], # Người dùng tạo đơn hàng
                "status": random.choice(["pending", "completed", "cancelled"]), # Trạng thái đơn hàng
                "order_date": order_date.isoformat(timespec="seconds") # Định dạng ISO 8601 (có 'T')
            }

            # Gọi order_service để tạo (lưu) đơn hàng
            self.order_service.create_order(order_payload)
            created_orders.append(order_payload)

        print(f"Đã tạo và lưu trữ {len(created_orders)} đơn hàng mẫu.")
        return created_orders
