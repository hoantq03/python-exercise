import threading
import time
import json

from app.services.product_service import ProductService
from app.models.storage import JsonStorage


class UpdateCategoryCronTask: # Trước đây gọi là UpdateCategoryCronTask
    """
    Scheduler chạy định kỳ để trích xuất và cập nhật danh sách
    các danh mục (categories) từ dữ liệu sản phẩm.
    """

    def __init__(self, product_service: ProductService, categories_storage: JsonStorage, interval_seconds: int):
        self.product_service = product_service
        self.categories_storage = categories_storage
        self.interval = interval_seconds
        self._timer = None
        self.is_running = False

    def _extract_unique_categories(self, products_data: list) -> list:
        """
        Trích xuất danh sách các danh mục duy nhất từ dữ liệu sản phẩm.
        """
        unique_categories = {}
        for product in products_data:
            for category in product.get("categories", []):
                cat_id = category.get("categoryId")
                if cat_id is not None:
                    unique_categories[cat_id] = {
                        "categoryId": cat_id,
                        "categoryName": category.get("name"),
                        "categoryUri": category.get("uri")
                    }

        sorted_list = sorted(list(unique_categories.values()), key=lambda x: x['categoryName'])
        return sorted_list

    def _run_task(self):
        """Hàm được thực thi mỗi khi scheduler chạy."""
        if self.is_running:
            self._timer = threading.Timer(self.interval, self._run_task)
            self._timer.daemon = True
            self._timer.start()

        print("🔄 [CategoryScheduler] Bắt đầu tác vụ cập nhật danh mục...")
        try:
            all_products = self.product_service.list()

            if not all_products:
                print("⚠️ [CategoryScheduler] Không tìm thấy sản phẩm nào để cập nhật danh mục.")
                return

            unique_categories = self._extract_unique_categories(all_products)
            self.categories_storage.save_all(unique_categories)

            print(f"✅ [CategoryScheduler] Cập nhật thành công {len(unique_categories)} danh mục.")

        except Exception as e:
            print(f"❌ [CategoryScheduler] Lỗi trong quá trình cập nhật danh mục: {e}")

    def start(self):
        """Bắt đầu chạy scheduler lần đầu."""
        if not self.is_running:
            self.is_running = True
            self._timer = threading.Timer(self.interval, self._run_task)
            self._timer.daemon = True
            self._timer.start()
            print("[CategoryScheduler] Đã được khởi động và sẽ chạy lần đầu sau", self.interval, "giây.")

    def stop(self):
        """Dừng scheduler."""
        self.is_running = False
        if self._timer:
            self._timer.cancel() # Hủy timer hiện tại
        print("⏹️ [CategoryScheduler] Đã dừng.")
