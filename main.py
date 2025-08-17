# -*- coding: utf-8 -*-
# Hoặc
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
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
from app.services.user_service import UserService

# UI Views
from app.ui.app_window import AppWindow
from app.ui.cart_view import CartView
from app.ui.login_view import LoginView
from app.ui.profile_view import ProfileView
from app.ui.report_view import ReportFrame
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
from app.utils.dummy_orders_generation import DummyOrderCreator


def get_bool_from_env(key: str, default: bool = False) -> bool:
    value = os.getenv(key, str(default)).lower()
    return value in ('true', '1', 't', 'on')


# Các vai trò (roles) trong hệ thống của bạn
ROLES_ENUM = {
    'ADMIN': 'administrator',
    'EMP_MANAGER': 'employee_manager',
    'SALES_MANAGER': 'sales_manager',
    'SALES_PERSON': 'sales_person',
    'ACCOUNTANT': 'accountant',
}


def resource_path(relative_path):
    """
    Lấy đường dẫn tuyệt đối đến tài nguyên.
    Hoạt động cho cả môi trường dev (chạy từ terminal) và khi đã đóng gói bằng PyInstaller.
    """
    # Kiểm tra xem ứng dụng có đang chạy dưới dạng file đã đóng gói (frozen) không
    if getattr(sys, 'frozen', False):
        # NẾU ĐÃ ĐÓNG GÓI (CHẠY BẰNG FILE .EXE)
        # base_path là thư mục tạm _MEIPASS do PyInstaller tạo ra.
        base_path = sys._MEIPASS
        # Dữ liệu nằm trực tiếp trong thư mục này (ví dụ: _MEIPASS/data/users.json)
        # nên chúng ta chỉ cần nối base_path với đường dẫn tương đối.
        return os.path.join(base_path, relative_path)
    else:
        # NẾU CHẠY TỪ MÃ NGUỒN (CHẠY BẰNG TERMINAL)
        # base_path là thư mục gốc của dự án (nơi chứa main.py).
        base_path = os.path.abspath(".")
        # Trong mã nguồn, thư mục dữ liệu nằm bên trong 'app'.
        # Vì vậy, chúng ta phải nối base_path với 'app' rồi mới đến đường dẫn tương đối.
        return os.path.join(base_path, 'app', relative_path)


def run():
    # --- Nạp các biến môi trường từ file .env ---
    load_dotenv(resource_path(".env"))

    # --- Khởi tạo các kho lưu trữ (Storage) ---
    users_store = JsonStorage(resource_path("data/users.json"))
    customers_store = JsonStorage(resource_path("data/customers.json"))
    products_store = JsonStorage(resource_path("data/products.json"))
    orders_store = JsonStorage(resource_path("data/orders.json"))
    carts_store = JsonStorage(resource_path("data/carts.json"))
    categories_store = JsonStorage(resource_path("data/categories.json"))

    # --- Khởi tạo các dịch vụ (Services) ---
    auth = AuthService(users_store)
    auth.ensure_admin_seed()

    cust_srv = CustomerService(customers_store)
    prod_srv = ProductService(products_store)
    order_srv = OrderService(orders_store, products_store)
    cart_srv = CartService(carts_store)
    categories_srv = CategoryService(categories_store)
    user_srv = UserService(users_store)

    # --- Cấu hình Scraper và Task ---
    SCRAPER_CONFIG = {
        'PHONE_SCRAPER_ENABLED': PhoneListScraper,
        'PHONE_DETAILS_SCRAPER_ENABLED': PhoneDetailScraper,
        'LAPTOP_SCRAPER_ENABLED': LaptopListScraper,
        'UPDATE_CATEGORIES_ENABLED': UpdateCategoryCronTask,
    }

    all_initialized_tasks = []

    print("--- Đang kiểm tra cấu hình các tác vụ từ .env ---")
    for env_key, task_class in SCRAPER_CONFIG.items():
        if get_bool_from_env(env_key):
            print(f" -> Đang bật: {task_class.__name__}")
            task_instance = None
            if task_class == UpdateCategoryCronTask:
                category_interval = int(os.getenv('CATEGORY_UPDATE_INTERVAL_SECONDS', 600))
                task_instance = task_class(product_service=prod_srv, category_service=categories_srv,
                                           interval_seconds=category_interval)
            elif hasattr(task_class, '__init__') and 'storage' in task_class.__init__.__code__.co_varnames:
                task_instance = task_class(storage=products_store)
            else:
                task_instance = task_class()
            all_initialized_tasks.append(task_instance)
        else:
            print(f" -> Đã tắt: {task_class.__name__}")

    # --- PHÂN LOẠI VÀ KHỞI ĐỘNG CÁC SCHEDULER ---
    scrapers_for_main_scheduler = []
    other_schedulers_to_start_manually = []

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
        interval = int(os.getenv('SCRAPER_INTERVAL_SECONDS', 300))
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

    # <<< THAY ĐỔI 1: TẠO HÀM SHUTDOWN TẬP TRUNG >>>
    # Hàm này sẽ được gọi khi người dùng đóng bất kỳ cửa sổ chính nào.
    def shutdown_app():
        print("--- Bắt đầu quá trình tắt ứng dụng ---")

        # 1. Dừng tất cả các scheduler đang chạy
        if main_scraper_scheduler and main_scraper_scheduler.is_running:
            print("Đang dừng ScraperScheduler chính...")
            main_scraper_scheduler.stop()

        for sched in other_schedulers_to_start_manually:
            if sched.is_running:
                print(f"Đang dừng scheduler: {sched.__class__.__name__}...")
                sched.stop()

        # 2. Phá hủy cửa sổ root để kết thúc ứng dụng hoàn toàn
        print("Đang đóng giao diện người dùng...")
        root.destroy()
        print("--- Ứng dụng đã đóng hoàn toàn. ---")

    def on_login_success(u):
        win = AppWindow(master=root, session_user=u)

        # <<< THAY ĐỔI 2: GẮN HÀM SHUTDOWN VÀO CỬA SỔ CHÍNH >>>
        # Khi người dùng nhấn nút "X" trên cửa sổ AppWindow, hàm shutdown_app sẽ được gọi.
        win.protocol("WM_DELETE_WINDOW", shutdown_app)

        # --- Xác định quyền hạn theo vai trò (giữ nguyên) ---
        can_manage_users = auth.authorize(u, (ROLES_ENUM['ADMIN'], ROLES_ENUM['EMP_MANAGER']))
        can_access_products = auth.authorize(u, (
        ROLES_ENUM['ADMIN'], ROLES_ENUM['SALES_MANAGER'], ROLES_ENUM['SALES_PERSON']))
        can_access_cart = auth.authorize(u,
                                         (ROLES_ENUM['ADMIN'], ROLES_ENUM['SALES_MANAGER'], ROLES_ENUM['SALES_PERSON']))
        can_access_customers = auth.authorize(u, (
        ROLES_ENUM['ADMIN'], ROLES_ENUM['SALES_MANAGER'], ROLES_ENUM['SALES_PERSON']))
        can_access_orders = auth.authorize(u,
                                           (ROLES_ENUM['ADMIN'], ROLES_ENUM['SALES_MANAGER'], ROLES_ENUM['ACCOUNTANT']))
        can_view_reports = auth.authorize(u,
                                          (ROLES_ENUM['ADMIN'], ROLES_ENUM['SALES_MANAGER'], ROLES_ENUM['ACCOUNTANT']))

        # --- Thêm các nút điều hướng (giữ nguyên) ---
        initial_view_button = None
        win.add_nav_button("Thông tin cá nhân", ProfileView, u)
        if can_manage_users:
            win.add_nav_button("Người dùng", UsersView, users_store, u)
        if can_access_products:
            initial_view_button = win.add_nav_button("Sản phẩm", ProductsView, prod_srv, cart_srv, categories_srv, True)
        if can_access_cart:
            win.add_nav_button("🛒 Giỏ hàng", CartView, cart_srv, order_srv, cust_srv, u)
        if can_access_customers:
            win.add_nav_button("Khách hàng", CustomersView, cust_srv, order_srv, True)
        if can_access_orders:
            win.add_nav_button("Đơn hàng", OrdersView, order_srv, cust_srv, prod_srv, u, True)
        if can_view_reports:
            win.add_nav_button("Báo cáo", ReportFrame, order_srv, prod_srv, cust_srv, user_srv)

        def logout():
            win.destroy()
            # Gọi lại LoginView và truyền hàm shutdown vào
            login_view = LoginView(root, auth, on_login_success)
            login_view.protocol("WM_DELETE_WINDOW", shutdown_app)

        win.add_nav_button("Đăng xuất", command=logout)
        win.show_view(ProfileView, u)
        if initial_view_button:
            win._select_button_style(initial_view_button)

    # <<< THAY ĐỔI 3: GẮN HÀM SHUTDOWN VÀO CỬA SỔ ĐĂNG NHẬP >>>
    # Rất quan trọng: nếu người dùng đóng cửa sổ đăng nhập, ứng dụng cũng phải tắt hẳn.
    login_view = LoginView(root, auth, on_login_success)
    login_view.protocol("WM_DELETE_WINDOW", shutdown_app)

    root.mainloop()

if __name__ == "__main__":
    run()

