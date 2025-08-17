# -*- coding: utf-8 -*-
# Hoặc
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
from app.services.user_service import UserService  # <-- Import UserService

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
    # KHỞI TẠO UserService TRƯỚC VÌ CÁC DỊCH VỤ KHÁC CÓ THỂ PHỤ THUỘC VÀO NÓ
    auth = AuthService(users_store)  # auth vẫn dùng users_store trực tiếp, không sao
    auth.ensure_admin_seed()

    cust_srv = CustomerService(customers_store)
    prod_srv = ProductService(products_store)
    order_srv = OrderService(orders_store, products_store)
    cart_srv = CartService(carts_store)
    categories_srv = CategoryService(categories_store)
    user_srv = UserService(users_store)

    # --- Cấu hình Scraper và Task --- (phần còn lại giữ nguyên)
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

        # --- Xác định quyền hạn theo vai trò ---

        # Quyền quản lý người dùng: Admin và Employee Manager
        can_manage_users = auth.authorize(u, (ROLES_ENUM['ADMIN'], ROLES_ENUM['EMP_MANAGER']))

        # Quyền truy cập sản phẩm: Admin, Sales Manager và Sales Person
        can_access_products = auth.authorize(u, (
            ROLES_ENUM['ADMIN'], ROLES_ENUM['SALES_MANAGER'], ROLES_ENUM['SALES_PERSON']))

        # Quyền truy cập giỏ hàng: Admin, Sales Manager và Sales Person
        can_access_cart = auth.authorize(u, (
            ROLES_ENUM['ADMIN'], ROLES_ENUM['SALES_MANAGER'], ROLES_ENUM['SALES_PERSON']))

        # Quyền truy cập khách hàng: Admin và Sales Manager
        can_access_customers = auth.authorize(u, (
            ROLES_ENUM['ADMIN'], ROLES_ENUM['SALES_MANAGER'], ROLES_ENUM['SALES_PERSON']))

        # Quyền truy cập đơn hàng: Admin và Sales Manager
        can_access_orders = auth.authorize(u, (
            ROLES_ENUM['ADMIN'], ROLES_ENUM['SALES_MANAGER'], ROLES_ENUM['ACCOUNTANT']))

        # Quyền xem báo cáo: Admin, Sales Manager và Accountant
        can_view_reports = auth.authorize(u, (
            ROLES_ENUM['ADMIN'], ROLES_ENUM['SALES_MANAGER'], ROLES_ENUM['ACCOUNTANT']))

        # --- Thêm các nút điều hướng (tab) dựa trên quyền hạn ---

        # Tab "Thông tin cá nhân": Luôn hiển thị cho tất cả người dùng đã đăng nhập
        win.add_nav_button("Thông tin cá nhân", ProfileView, u)

        # Tab "Người dùng": Chỉ Admin và Employee Manager
        if can_manage_users:
            win.add_nav_button("Người dùng", UsersView, users_store, u)

        # Tab "Sản phẩm": Admin, Sales Manager và Sales Person
        if can_access_products:
            initial_view_button = win.add_nav_button("Sản phẩm", ProductsView, prod_srv, cart_srv, categories_srv, True)

        # Tab "Giỏ hàng": Admin, Sales Manager và Sales Person
        if can_access_cart:
            win.add_nav_button("🛒 Giỏ hàng", CartView, cart_srv, order_srv, cust_srv, u)

        # Tab "Khách hàng": Admin và Sales Manager
        if can_access_customers:
            win.add_nav_button("Khách hàng", CustomersView, cust_srv, order_srv, True)

        # Tab "Đơn hàng": Admin và Sales Manager
        if can_access_orders:
            win.add_nav_button("Đơn hàng", OrdersView, order_srv, cust_srv, prod_srv, u, True)

        # Tab "Báo cáo": Admin, Sales Manager và Accountant
        if can_view_reports:
            win.add_nav_button("Báo cáo", ReportFrame, order_srv, prod_srv, cust_srv, user_srv)

        # Nút "Đăng xuất": Luôn hiển thị
        def logout():
            win.destroy()
            LoginView(root, auth, on_login_success)

        win.add_nav_button("Đăng xuất", command=logout)

        win.show_view(ProfileView, u)

        # Manually select the button for the initial view
        if initial_view_button:
            win._select_button_style(initial_view_button)

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

