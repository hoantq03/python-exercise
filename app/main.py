import tkinter as tk
import os
from dotenv import load_dotenv

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

# Hệ thống cào dữ liệu (Scraper)
from app.scrapers.phone_detail_scraper import PhoneDetailScraper
from app.scrapers.phone_list_scraper import PhoneListScraper
from app.scrapers.laptop_list_scraper import LaptopListScraper
from app.schedulers.scraper_scheduler import ScraperScheduler


def get_bool_from_env(key: str, default: bool = False) -> bool:
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
        win = AppWindow(master=root, session_user=u)

        can_manage_users = auth.authorize(u, ("admin",))
        can_edit_data = auth.authorize(u, ("admin", "staff"))

        if can_manage_users:
            win.add_nav_button("Người dùng", lambda: win.show_view(UsersView, users_store, u))

        win.add_nav_button("Sản phẩm", lambda: win.show_view(ProductsView, prod_srv, cart_srv, can_edit_data))
        win.add_nav_button("🛒 Giỏ hàng", lambda: win.show_view(CartView, cart_srv, order_srv, cust_srv, u))
        win.add_nav_button("Khách hàng", lambda: win.show_view(CustomersView, cust_srv, order_srv, can_edit_data))
        win.add_nav_button("Đơn hàng", lambda: win.show_view(OrdersView, order_srv, cust_srv, prod_srv, u, can_edit_data))

        def logout():
            win.destroy()
            LoginView(root, auth, on_login_success)

        win.add_nav_button("Đăng xuất", logout)

        win.show_view(ProductsView, prod_srv, cart_srv, can_edit_data)

    LoginView(root, auth, on_login_success)
    root.mainloop()

    if scheduler and scheduler.is_running():
        scheduler.stop()
    print("--- Ứng dụng đã đóng. ---")


if __name__ == "__main__":
    run()
