import requests
import uuid
from datetime import datetime
from dataclasses import asdict
from typing import List, Dict, Any

# Cần import BeautifulSoup để xử lý HTML trong description
from bs4 import BeautifulSoup

# Giả định các file này nằm trong đúng đường dẫn của dự án của bạn
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

    def _fetch_api_data(self) -> List[Dict[str, Any]]:
        """
        Bước 1: EXTRACT - Lấy dữ liệu thô từ API.
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
                    size: 100,
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
        """
        Bước 2: TRANSFORM - Ánh xạ một sản phẩm thô từ API sang cấu trúc của Product model.
        """
        general = api_item.get("general", {})
        filterable = api_item.get("filterable", {})
        attributes = general.get("attributes", {})

        thumbnail_path = filterable.get("thumbnail", "")
        avatar_url = f"https://cdn2.cellphones.com.vn/insecure/rs:fill:358:358/q:90/plain/https://cellphones.com.vn/media/catalog/product{thumbnail_path}" if thumbnail_path else ""

        description_html = attributes.get("key_selling_points", "")
        description_text = ""
        if description_html:
            soup = BeautifulSoup(description_html, 'html.parser')
            description_text = " | ".join(li.get_text(strip=True) for li in soup.find_all('li'))

        return {
            "name": general.get("name"),
            "sku": general.get("sku"),
            "price": float(filterable.get("special_price", 0)),
            "avatar": avatar_url,
            "description": description_text,
            "screen_size": attributes.get("display_size"),
            "screen_tech": attributes.get("mobile_type_of_display"),
            "camera_sau": attributes.get("camera_primary"),
            "camera_truoc": attributes.get("camera_secondary"),
            "chipset": attributes.get("chipset"),
            "nfc": attributes.get("mobile_nfc"),
            "ram": attributes.get("mobile_ram_filter"),
            "storage": attributes.get("storage"),
            "battery": attributes.get("iphone_pin_text") or attributes.get("mobile_cong_nghe_sac"),
            "sim": attributes.get("sim"),
            "os": attributes.get("operating_system"),
            "refresh_rate": attributes.get("mobile_tan_so_quet"),
            "main_screen_res": attributes.get("display_resolution"),
            "cpu_type": attributes.get("cpu"),
            "sub_screen_size": "", "sub_screen_res": "", "color_depth": "",
        }

    def _load_products(self, standardized_products: List[Dict[str, Any]]):
        """
        Bước 3: LOAD - Lưu danh sách sản phẩm đã được chuẩn hóa vào JsonStorage.
        Phương thức này chỉ làm nhiệm vụ lưu trữ, không mapping.
        """
        print("   Bắt đầu quá trình lưu trữ dữ liệu đã chuẩn hóa...")
        existing_products = self.product_storage.all()
        existing_products_lookup = {p['name']: p for p in existing_products}

        created_count = 0
        updated_count = 0

        for product_patch in standardized_products:
            product_name = product_patch.get("name")
            if not product_name:
                continue

            if product_name in existing_products_lookup:
                # UPDATE sản phẩm đã có
                existing_product = existing_products_lookup[product_name]
                product_patch['updated_at'] = datetime.now().isoformat()
                self.product_storage.update(existing_product['id'], product_patch)
                updated_count += 1
            else:
                # CREATE sản phẩm mới
                now_iso = datetime.now().isoformat()
                new_product = Product(
                    id=str(uuid.uuid4()),
                    stock=100,  # Giá trị mặc định khi tạo mới
                    created_at=now_iso,
                    updated_at=now_iso,
                    **product_patch
                )
                self.product_storage.create(asdict(new_product))
                created_count += 1

        print(f"   Lưu trữ hoàn tất. Đã tạo mới: {created_count}, Cập nhật: {updated_count} sản phẩm.")

    def scrape(self):
        """
        Phương thức chính: Điều phối toàn bộ quy trình ETL.
        """
        print("-> Bắt đầu quy trình cào dữ liệu cho điện thoại...")

        # Bước 1: Extract - Lấy dữ liệu thô
        raw_api_data = self._fetch_api_data()
        if not raw_api_data:
            print("   Kết thúc: Không nhận được dữ liệu từ API hoặc có lỗi xảy ra.")
            return
        print(f"   [Extract] Đã lấy được {len(raw_api_data)} sản phẩm thô từ API.")

        # Bước 2: Transform - Chuẩn hóa dữ liệu thô về model
        standardized_products = [self._transform_to_product_model(item) for item in raw_api_data]
        print(f"   [Transform] Đã chuẩn hóa {len(standardized_products)} sản phẩm.")

        # Bước 3: Load - Lưu dữ liệu đã chuẩn hóa
        self._load_products(standardized_products)

        print("-> Quy trình cào dữ liệu cho điện thoại đã hoàn tất.")
