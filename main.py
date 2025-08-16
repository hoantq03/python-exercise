# File: main.py
import tkinter as tk
import os
from dotenv import load_dotenv

# Models
from app.models.storage import JsonStorage
from app.schedulers.update_categories_scheduler import UpdateCategoryCronTask

# Services
from app.services.auth import AuthService
from app.services.cart_service import CartService
from app.services.category_service import CategoryService
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

# Schedulers
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
    categories_store = JsonStorage("data/categories.json")

    # --- Khởi tạo các dịch vụ (Services) ---
    auth = AuthService(users_store)
    auth.ensure_admin_seed()

    cust_srv = CustomerService(customers_store)
    prod_srv = ProductService(products_store)
    order_srv = OrderService(orders_store, products_store)
    cart_srv = CartService(carts_store)
    categories_srv = CategoryService(categories_store)

    # --- Cấu hình Scraper và Task ---
    SCRAPER_CONFIG = {
        'PHONE_SCRAPER_ENABLED': PhoneListScraper,
        'PHONE_DETAILS_SCRAPER_ENABLED': PhoneDetailScraper,
        'LAPTOP_SCRAPER_ENABLED': LaptopListScraper,
        'UPDATE_CATEGORIES_ENABLED': UpdateCategoryCronTask,  # Sử dụng CategoryScheduler
    }

    all_initialized_tasks = []

    print("--- Đang kiểm tra cấu hình các tác vụ từ .env ---")
    for env_key, task_class in SCRAPER_CONFIG.items():
        if get_bool_from_env(env_key):
            print(f" -> Đang bật: {task_class.__name__}")

            task_instance = None
            if task_class == UpdateCategoryCronTask:
                # CategoryScheduler là một scheduler cần các tham số riêng
                category_interval = int(os.getenv('CATEGORY_UPDATE_INTERVAL_SECONDS', 600))
                task_instance = task_class(
                    product_service=prod_srv,
                    category_service=categories_srv,
                    interval_seconds=category_interval
                )
            elif hasattr(task_class, '__init__') and 'storage' in task_class.__init__.__code__.co_varnames:
                # Các scraper thông thường cần tham số 'storage'
                task_instance = task_class(storage=products_store)
            else:
                # Các task khác không cần tham số
                task_instance = task_class()

            all_initialized_tasks.append(task_instance)
        else:
            print(f" -> Đã tắt: {task_class.__name__}")

    # --- PHÂN LOẠI VÀ KHỞI ĐỘNG CÁC SCHEDULER ---
    scrapers_for_main_scheduler = []  # Chỉ chứa các đối tượng BaseScraper (có scrape() method)
    other_schedulers_to_start_manually = []  # Chứa các scheduler tự thân (có start() method)

    for task_instance in all_initialized_tasks:
        if isinstance(task_instance, UpdateCategoryCronTask):
            other_schedulers_to_start_manually.append(task_instance)
        elif hasattr(task_instance, 'scrape') and callable(getattr(task_instance, 'scrape')):
            scrapers_for_main_scheduler.append(task_instance)
        else:
            print(f"⚠️ Task '{task_instance.__class__.__name__}' không được phân loại rõ ràng. Không khởi động.")

    # --- Khởi động ScraperScheduler chính (cho các scraper) ---
    main_scraper_scheduler = None
    if scrapers_for_main_scheduler:
        print(f"--- Tìm thấy {len(scrapers_for_main_scheduler)} scraper được bật. Khởi động ScraperScheduler. ---")
        try:
            interval = int(os.getenv('SCRAPER_INTERVAL_SECONDS', 300))
        except ValueError:
            interval = 300
        main_scraper_scheduler = ScraperScheduler(scrapers_to_run=scrapers_for_main_scheduler,
                                                  interval_seconds=interval)
        main_scraper_scheduler.start()
    else:
        print("--- Không có scraper nào được bật cho ScraperScheduler. ---")

    # --- Khởi động các scheduler khác (như CategoryScheduler) ---
    for sched in other_schedulers_to_start_manually:
        print(f"--- Khởi động Scheduler riêng: {sched.__class__.__name__} ---")
        sched.start()

    # --- Khởi tạo giao diện người dùng Tkinter ---
    root = tk.Tk()
    root.withdraw()

    def on_login_success(u):
        win = AppWindow(master=root, session_user=u)

        can_manage_users = auth.authorize(u, ("admin",))
        can_edit_data = auth.authorize(u, ("admin", "staff"))

        if can_manage_users:
            win.add_nav_button("Người dùng", lambda: win.show_view(UsersView, users_store, u))

        win.add_nav_button("Sản phẩm", lambda: win.show_view(ProductsView, prod_srv, cart_srv, categories_srv, can_edit_data))
        win.add_nav_button("🛒 Giỏ hàng", lambda: win.show_view(CartView, cart_srv, order_srv, cust_srv, u))
        win.add_nav_button("Khách hàng", lambda: win.show_view(CustomersView, cust_srv, order_srv, can_edit_data))
        win.add_nav_button("Đơn hàng",
                           lambda: win.show_view(OrdersView, order_srv, cust_srv, prod_srv, u, can_edit_data))

        def logout():
            win.destroy()
            LoginView(root, auth, on_login_success)

        win.add_nav_button("Đăng xuất", logout)

        win.show_view(ProductsView, prod_srv, cart_srv, categories_srv, can_edit_data)

    LoginView(root, auth, on_login_success)
    root.mainloop()

    # --- Dừng TẤT CẢ các schedulers khi ứng dụng đóng ---
    if main_scraper_scheduler and main_scraper_scheduler.is_running:
        main_scraper_scheduler.stop()

    for sched in other_schedulers_to_start_manually:
        if sched.is_running:
            sched.stop()

    print("--- Ứng dụng đã đóng. ---")


if __name__ == "__main__":
    run()
