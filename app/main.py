# File: main.py
import tkinter as tk
import os
from dotenv import load_dotenv

# Giả định cấu trúc file của bạn là đúng
# Models
from app.models.storage import JsonStorage

# Services
from app.services.auth import AuthService
from app.services.cart_service import CartService
from app.services.customer_service import CustomerService
from app.services.product_service import ProductService
from app.services.order_service import OrderService

# UI Views
from app.ui.app_window import AppWindow
from app.ui.cart_view import CartView
from app.ui.login_view import LoginView
from app.ui.users_view import UsersView
from app.ui.customers_view import CustomersView
from app.ui.products_view import ProductsView
from app.ui.orders_view import OrdersView

# Hệ thống cào dữ liệu (Scraper) - Giữ nguyên không thay đổi
from app.scrapers.phone_detail_scraper import PhoneDetailScraper
from app.scrapers.phone_list_scraper import PhoneListScraper
from app.scrapers.laptop_list_scraper import LaptopListScraper
from app.schedulers.scraper_scheduler import ScraperScheduler


def get_bool_from_env(key: str, default: bool = False) -> bool:
    """Hàm trợ giúp để đọc giá trị boolean từ file .env một cách an toàn."""
    value = os.getenv(key, str(default)).lower()
    return value in ('true', '1', 't', 'on')


def run():
    # --- Nạp các biến môi trường từ file .env ---
    load_dotenv()

    # --- Khởi tạo các kho lưu trữ (Storage) ---
    users_store = JsonStorage("data/users.json")
    customers_store = JsonStorage("data/customers.json")
    products_store = JsonStorage("data/products.json")
    orders_store = JsonStorage("data/orders.json")
    carts_store = JsonStorage("data/carts.json")

    # --- Khởi tạo các dịch vụ (Services) ---
    auth = AuthService(users_store)
    auth.ensure_admin_seed()

    cust_srv = CustomerService(customers_store)
    prod_srv = ProductService(products_store)
    order_srv = OrderService(orders_store, products_store)
    cart_srv = CartService(carts_store)

    # --- Phần Scraper và Scheduler giữ nguyên, không cần thay đổi ---
    # (code scraper của bạn ở đây)
    SCRAPER_CONFIG = {
        'PHONE_SCRAPER_ENABLED': PhoneListScraper,
        'PHONE_DETAILS_SCRAPER_ENABLED': PhoneDetailScraper,
        'LAPTOP_SCRAPER_ENABLED': LaptopListScraper,
    }
    scraper_tasks = []
    print("--- Đang kiểm tra cấu hình scraper từ .env ---")
    for env_key, scraper_class in SCRAPER_CONFIG.items():
        if get_bool_from_env(env_key):
            print(f" -> Đang bật: {scraper_class.__name__}")
            scraper_tasks.append(scraper_class())
        else:
            print(f" -> Đã tắt: {scraper_class.__name__}")
    scheduler = None
    if scraper_tasks:
        print(f"--- Tìm thấy {len(scraper_tasks)} scraper được bật. Khởi động Scheduler. ---")
        try:
            interval = int(os.getenv('SCRAPER_INTERVAL_SECONDS', 300))
        except ValueError:
            interval = 300
        scheduler = ScraperScheduler(scrapers_to_run=scraper_tasks, interval_seconds=interval)
        scheduler.start()
    else:
        print("--- Không có scraper nào được bật. Scheduler sẽ không chạy. ---")
    # --- Kết thúc phần Scraper ---

    # --- Khởi tạo giao diện người dùng Tkinter ---
    root = tk.Tk()
    root.withdraw()

    def on_login_success(u):
        # MODIFIED: Truyền `master=root` để liên kết đúng cửa sổ
        win = AppWindow(master=root, session_user=u)

        can_manage_users = auth.authorize(u, ("admin",))
        can_edit_data = auth.authorize(u, ("admin", "staff"))

        # --- CẬP NHẬT CÁCH GỌI show_view ---
        # Thay vì tạo instance `View(win.content, ...)`
        # Ta truyền `TênLớp, các_tham_số...`
        # `AppWindow` sẽ tự động thêm `win.content_frame` vào làm tham số đầu tiên.
        if can_manage_users:
            win.add_nav_button("Người dùng", lambda: win.show_view(UsersView, users_store, u))

        win.add_nav_button("🛒 Giỏ hàng", lambda: win.show_view(
            CartView,
            cart_srv,
            order_srv,
            cust_srv,
            u # Truyền thông tin user đang đăng nhập
        ))
        win.add_nav_button("Khách hàng", lambda: win.show_view(CustomersView, cust_srv, can_edit_data))
        win.add_nav_button("Sản phẩm", lambda: win.show_view(ProductsView, prod_srv, cart_srv, can_edit_data))
        win.add_nav_button("Đơn hàng", lambda: win.show_view(
            OrdersView,
            order_srv,
            cust_srv,
            prod_srv,
            u,
            can_edit_data
        ))

        def logout():
            win.destroy()
            LoginView(root, auth, on_login_success)

        win.add_nav_button("Đăng xuất", logout)

        # MODIFIED & FIXED: Hiển thị view mặc định và sửa lỗi thiếu tham số
        # Lời gọi cũ của bạn: win.show_view(ProductsView(win.content, prod_srv, can_edit_data))
        # -> Lỗi 1: Dùng cách gọi cũ.
        # -> Lỗi 2: Thiếu tham số `cart_srv`.
        win.show_view(ProductsView, prod_srv, cart_srv, can_edit_data)

        # BỎ win.mainloop() ở đây, vì root.mainloop() ở dưới sẽ quản lý
        # win.mainloop()

    LoginView(root, auth, on_login_success)
    root.mainloop()

    # Dừng scheduler khi ứng dụng đóng hoàn toàn
    if scheduler:
        scheduler.stop()
    print("--- Ứng dụng đã đóng. ---")


if __name__ == "__main__":
    run()

