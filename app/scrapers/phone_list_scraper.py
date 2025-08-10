import requests
import uuid
from datetime import datetime
from dataclasses import asdict
from typing import List, Dict, Any
import sys
import threading
import time
from bs4 import BeautifulSoup

from app.scrapers.base_scraper import BaseScraper
from app.models.storage import JsonStorage
from app.models.product import Product


class PhoneListScraper(BaseScraper):
    """
    Cào dữ liệu điện thoại từ API GraphQL của CellphoneS, chuẩn hóa,
    và lưu vào JsonStorage theo quy trình ETL.
    """

    def __init__(self):
        super().__init__("https://api.cellphones.com.vn/v2/graphql/query")
        self.product_storage = JsonStorage("data/products.json")
        self._progress_current = 0
        self._progress_total = 0
        self._progress_created = 0
        self._progress_updated = 0
        self._loading_in_progress = False

    def _update_progress_periodically(self):
        """Hàm này chạy trong một luồng riêng để cập nhật thanh tiến trình mỗi giây."""
        while self._loading_in_progress:
            self._print_progress()
            time.sleep(1)  # Cập nhật mỗi giây

        # Đảm bảo thanh tiến trình hiển thị 100% khi kết thúc
        self._print_progress()


    def _fetch_api_data(self) -> List[Dict[str, Any]]:
        """
        EXTRACT - Lấy dữ liệu thô từ API.
        """
        graphql_query = """
            query GetProductsByCateId{
                products(
                    filter: {
                        static: {
                            categories: ["3"],
                            province_id: 30,
                            stock: { from: 0 },
                            stock_available_id: [46, 56, 152, 4920],
                            filter_price: {from:0, to:100000000}
                        },
                        dynamic: {}
                    },
                    page: 1,
                    size: 2000,
                    sort: [{view: desc}]
                )
                {
                    general{ product_id name attributes sku url_path },
                    filterable{ price special_price thumbnail }
                }
            }
        """
        payload = {"query": graphql_query, "variables": {}}
        try:
            response = requests.post(self.url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get("data", {}).get("products", [])
        except requests.exceptions.RequestException as e:
            print(f"   Lỗi khi gọi API GraphQL: {e}")
            return []

    def _transform_to_product_model(self, api_item: Dict[str, Any]) -> Dict[str, Any]:
        general = api_item.get("general", {})
        filterable = api_item.get("filterable", {})
        attributes = general.get("attributes", {})
        thumbnail_path = filterable.get("thumbnail", "")
        base_image_url_cdn = "https://cdn2.cellphones.com.vn/insecure/rs:fill:358:358/q:90/plain/https://cellphones.com.vn/media/catalog/product"
        avatar_url = f"{base_image_url_cdn}{thumbnail_path}" if thumbnail_path else ""
        description_html = attributes.get("key_selling_points", "")
        description_text = ""
        if description_html:
            soup = BeautifulSoup(description_html, 'html.parser')
            description_text = " | ".join(li.get_text(strip=True) for li in soup.find_all('li'))
        image_urls = []
        for key, value in attributes.items():
            if key.startswith("anh_") and value and value != "no_selection":
                full_image_url = f"{base_image_url_cdn}{value}"
                if full_image_url not in image_urls:
                    image_urls.append(full_image_url)
        return {
            "name": general.get("name"), "sku": general.get("sku"),
            "price": float(filterable.get("special_price", 0)),
            "avatar": avatar_url, "images": image_urls, "description": description_text,
            "screen_size": attributes.get("display_size"), "screen_tech": attributes.get("mobile_type_of_display"),
            "camera_sau": attributes.get("camera_primary"), "camera_truoc": attributes.get("camera_secondary"),
            "chipset": attributes.get("chipset"), "nfc": attributes.get("mobile_nfc"),
            "ram": attributes.get("mobile_ram_filter"), "storage": attributes.get("storage"),
            "battery": attributes.get("iphone_pin_text") or attributes.get("mobile_cong_nghe_sac"),
            "sim": attributes.get("sim"), "os": attributes.get("operating_system"),
            "refresh_rate": attributes.get("mobile_tan_so_quet"),
            "main_screen_res": attributes.get("display_resolution"),
            "cpu_type": attributes.get("cpu"), "sub_screen_size": "", "sub_screen_res": "", "color_depth": "",
        }

    def _print_progress(self):
        """Vẽ thanh tiến trình động dựa trên các biến trạng thái của instance."""
        iteration = self._progress_current
        total = self._progress_total
        if total == 0: return

        bar_length = 50
        percent = (iteration / total) * 100
        filled_length = int(bar_length * iteration // total)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)

        status_text = f"Đã tạo: {self._progress_created}, Cập nhật: {self._progress_updated}"
        progress_string = f"\r   [Load] {bar} {percent:.1f}% ({iteration}/{total}) | {status_text}"

        sys.stdout.write(progress_string.ljust(120))
        sys.stdout.flush()

    def _load_products(self, standardized_products: List[Dict[str, Any]]):
        """
        LOAD - Lưu sản phẩm trong khi một luồng khác hiển thị tiến trình.
        """
        print("   Bắt đầu quá trình lưu trữ dữ liệu...")
        existing_products = self.product_storage.all()
        existing_products_lookup = {p['name']: p for p in existing_products}

        self._progress_total = len(standardized_products)
        self._progress_current = 0
        self._progress_created = 0
        self._progress_updated = 0
        self._loading_in_progress = True

        # Tạo và bắt đầu luồng hiển thị tiến trình
        progress_thread = threading.Thread(target=self._update_progress_periodically, daemon=True)
        progress_thread.start()

        # Vòng lặp chính xử lý dữ liệu (không còn in log cho từng sản phẩm)
        for product_patch in standardized_products:
            product_name = product_patch.get("name")
            if not product_name:
                self._progress_current += 1
                continue

            if product_name in existing_products_lookup:
                existing_product = existing_products_lookup[product_name]
                product_patch['updated_at'] = datetime.now().isoformat()
                self.product_storage.update(existing_product['id'], product_patch)
                self._progress_updated += 1
            else:
                now_iso = datetime.now().isoformat()
                new_product = Product(id=str(uuid.uuid4()), stock=100, created_at=now_iso, updated_at=now_iso,
                                      **product_patch)
                self.product_storage.create(asdict(new_product))
                self._progress_created += 1

            self._progress_current += 1

        self._loading_in_progress = False
        progress_thread.join()

        print()
        print(f"   Lưu trữ hoàn tất. Tổng cộng: {self._progress_created} mới, {self._progress_updated} cập nhật.")

    def scrape(self):
        print("-> Bắt đầu quy trình cào dữ liệu cho điện thoại...")
        raw_api_data = self._fetch_api_data()
        if not raw_api_data:
            print("   Kết thúc: Không nhận được dữ liệu từ API hoặc có lỗi xảy ra.")
            return
        print(f"   [Extract] Đã lấy được {len(raw_api_data)} sản phẩm thô từ API.")
        standardized_products = [self._transform_to_product_model(item) for item in raw_api_data]
        print(f"   [Transform] Đã chuẩn hóa {len(standardized_products)} sản phẩm.")
        self._load_products(standardized_products)
        print("-> Quy trình cào dữ liệu cho điện thoại đã hoàn tất.")
