import threading
import time
import json
from typing import Dict, List

from app.services.product_service import ProductService
from app.services.category_service import CategoryService
from app.models.storage import JsonStorage  # Có thể không cần nếu CategoryService đã xử lý mọi thứ


class UpdateCategoryCronTask:
    """
    Scheduler chạy định kỳ để trích xuất và cập nhật danh sách
    các danh mục (categories) từ dữ liệu sản phẩm, sử dụng CategoryService.
    """

    def __init__(self, product_service: ProductService, category_service: CategoryService, interval_seconds: int):
        self.product_service = product_service
        self.category_service = category_service
        self.interval = interval_seconds
        self._timer = None
        self.is_running = False

    def _extract_unique_categories(self, products_data: list) -> List[Dict]:
        """
        Trích xuất danh sách các danh mục duy nhất từ dữ liệu sản phẩm.
        Đảm bảo mỗi danh mục có đủ thông tin (categoryId, categoryName, categoryUri).
        """
        unique_categories_map = {}  # Dùng map để dễ dàng kiểm tra duy nhất theo categoryUri
        for product in products_data:
            # Lưu ý: product.get("categories", []) có thể chứa dict chỉ có name, uri,
            # hoặc cả categoryId. Cần đảm bảo có đủ thông tin để tạo Category object nếu cần.
            for category_info in product.get("categories", []):
                # Sử dụng categoryUri làm khóa chính tạm thời để đảm bảo tính duy nhất
                cat_uri = category_info.get("uri")
                if cat_uri:
                    # Tạo một cấu trúc chuẩn cho danh mục
                    standardized_category = {
                        "categoryName": category_info.get("name"),
                        "categoryUri": cat_uri,
                        "categoryId": category_info.get("categoryId", 0)  # Gán 0 hoặc ID mặc định nếu thiếu
                    }
                    # Nếu có ID, ưu tiên sử dụng ID để tránh trùng lặp
                    if standardized_category["categoryId"] == 0:
                        # Tạm thời tạo một ID dựa trên hash của URI nếu không có ID cụ thể
                        # Trong thực tế, ID nên được quản lý bởi CategoryService/storage
                        standardized_category["categoryId"] = hash(cat_uri) % (10 ** 9)  # Một cách tạo ID số đơn giản

                    # Cập nhật hoặc thêm vào map, đảm bảo thông tin đầy đủ nhất
                    # hoặc thông tin từ sản phẩm được ưu tiên nếu đó là nguồn chính
                    if cat_uri not in unique_categories_map:
                        unique_categories_map[cat_uri] = standardized_category
                    else:
                        # Hợp nhất thông tin nếu có thông tin bổ sung
                        current_cat = unique_categories_map[cat_uri]
                        if not current_cat.get("categoryName") and standardized_category.get("categoryName"):
                            current_cat["categoryName"] = standardized_category["categoryName"]
                        if not current_cat.get("categoryId") and standardized_category.get("categoryId"):
                            current_cat["categoryId"] = standardized_category["categoryId"]

        # Chuyển map thành list và sắp xếp
        sorted_list = sorted(list(unique_categories_map.values()), key=lambda x: x.get('categoryName', ''))
        return sorted_list

    def _run_task(self):
        """Hàm được thực thi mỗi khi scheduler chạy."""
        if self.is_running:
            self._timer = threading.Timer(self.interval, self._run_task)
            self._timer.daemon = True
            self._timer.start()

        print("🔄 [CategoryCronTask] Bắt đầu tác vụ cập nhật danh mục...")
        try:
            all_products = self.product_service.list()

            if not all_products:
                print("⚠️ [CategoryCronTask] Không tìm thấy sản phẩm nào để trích xuất danh mục.")
                # Nếu không có sản phẩm, có thể bạn muốn xóa hết danh mục hoặc không làm gì
                # Hiện tại, sẽ không có danh mục mới nào được trích xuất
                return

            # Bước 1: Trích xuất các danh mục mới từ sản phẩm
            extracted_categories = self._extract_unique_categories(all_products)

            # Bước 2: Lấy các danh mục hiện có trong CategoryService
            existing_categories = self.category_service.list_all_categories()
            existing_categories_map = {cat.get('categoryUri'): cat for cat in existing_categories}

            updated_count = 0
            created_count = 0
            deleted_count = 0

            # Bước 3: Đồng bộ hóa danh mục (thêm / cập nhật)
            for extracted_cat_data in extracted_categories:
                cat_uri = extracted_cat_data.get('categoryUri')

                if cat_uri in existing_categories_map:
                    # Danh mục đã tồn tại, kiểm tra xem có cần cập nhật không
                    existing_cat_data = existing_categories_map[cat_uri]

                    # So sánh các trường quan trọng (tên, ID)
                    if (existing_cat_data.get('categoryName') != extracted_cat_data.get('categoryName') or
                            existing_cat_data.get('categoryId') != extracted_cat_data.get('categoryId')):
                        # Cập nhật danh mục
                        # Lưu ý: cần id thật của danh mục để update
                        # Giả định CategoryService.update_category nhận ID của Category object
                        self.category_service.update_category(
                            existing_cat_data['id'],  # Dùng ID của Category object
                            {
                                "categoryName": extracted_cat_data.get("categoryName"),
                                "categoryUri": extracted_cat_data.get("categoryUri"),
                                "categoryId": extracted_cat_data.get("categoryId")
                            }
                        )
                        updated_count += 1
                    # Xóa khỏi map để theo dõi những danh mục cần xóa
                    del existing_categories_map[cat_uri]
                else:
                    # Danh mục chưa tồn tại, tạo mới
                    # Sử dụng CategoryService.create_category()
                    # Cần đảm bảo categoryId là duy nhất nếu không dùng uuid
                    new_category_payload = {
                        "categoryId": extracted_cat_data.get("categoryId"),  # Sử dụng ID từ dữ liệu trích xuất
                        "categoryName": extracted_cat_data.get("categoryName"),
                        "categoryUri": extracted_cat_data.get("categoryUri"),
                    }
                    self.category_service.create_category(new_category_payload)
                    created_count += 1

            # Bước 4: Xóa các danh mục không còn tồn tại trong dữ liệu sản phẩm
            for uri_to_delete, cat_data_to_delete in existing_categories_map.items():
                self.category_service.delete_category(cat_data_to_delete['id'])  # Dùng ID của Category object
                deleted_count += 1

            print(
                f"✅ [CategoryCronTask] Cập nhật hoàn tất: Tạo {created_count}, Cập nhật {updated_count}, Xóa {deleted_count} danh mục.")

        except Exception as e:
            print(f"❌ [CategoryCronTask] Lỗi trong quá trình cập nhật danh mục: {e}")
            import traceback
            traceback.print_exc()  # In stack trace để debug

    def start(self):
        """Bắt đầu chạy scheduler lần đầu."""
        if not self.is_running:
            self.is_running = True
            # Lần chạy đầu tiên sẽ được gọi sau interval
            # Nếu muốn chạy ngay lập tức, bạn có thể gọi _run_task() ở đây trước khi set timer
            self._timer = threading.Timer(self.interval, self._run_task)
            self._timer.daemon = True
            self._timer.start()
            print("[CategoryCronTask] Đã được khởi động và sẽ chạy lần đầu sau", self.interval, "giây.")

    def stop(self):
        """Dừng scheduler."""
        self.is_running = False
        if self._timer:
            self._timer.cancel()  # Hủy timer hiện tại
        print("⏹️ [CategoryCronTask] Đã dừng.")

