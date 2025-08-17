import uuid

from app.models.storage import JsonStorage


class ProductService:
    def __init__(self, storage: JsonStorage):
        self.storage = storage

    def list(self, keyword: str = ""):
        data = self.storage.all()
        if keyword:
            k = keyword.lower()
            data = [p for p in data if k in p["name"].lower() or k in p["sku"].lower()]
        return data

    def create(self, payload: dict):
        payload["id"] = str(uuid.uuid4())
        payload["stock"] = int(payload.get("stock", 0))
        payload["price"] = float(payload.get("price", 0))
        return self.storage.create(payload)

    def update(self, _id: str, payload: dict):
        if "stock" in payload: payload["stock"] = int(payload["stock"])
        if "price" in payload: payload["price"] = float(payload["price"])
        return self.storage.update(_id, payload)

    def delete(self, _id: str):
        return self.storage.delete(_id)

    def get_product_by_id(self, product_id: str) -> dict | None:
        """
        Tìm kiếm và trả về thông tin sản phẩm theo ID.
        Args:
            product_id: ID của sản phẩm cần tìm.
        Returns:
            Dictionary chứa thông tin sản phẩm, hoặc None nếu không tìm thấy.
        """
        # Nếu storage hỗ trợ phương thức get_by_id (cách hiệu quả hơn)
        if hasattr(self.storage, 'get_by_id'):
            product = self.storage.get_by_id(product_id)
            if product:
                return product

        # Nếu storage không có get_by_id hoặc trả về None, duyệt qua tất cả sản phẩm
        # Giả định self.storage.all() trả về danh sách tất cả sản phẩm
        all_products = self.storage.all() if hasattr(self.storage, 'all') else []
        for p in all_products:
            if p.get('id') == product_id:
                return p
        return None

    def get_category_by_id(self, category_id: str) -> dict | None:
        """
        Tìm kiếm và trả về thông tin danh mục theo ID.
        Đây là một ví dụ giả định ProductService cũng quản lý danh mục,
        hoặc có thể bạn có một CategoryService riêng.
        Args:
            category_id: ID của danh mục cần tìm.
        Returns:
            Dictionary chứa thông tin danh mục, hoặc None nếu không tìm thấy.
        """
        # Logic tương tự như get_product_by_id, tìm trong dữ liệu danh mục
        # Giả định bạn có một cách để truy cập dữ liệu danh mục từ storage
        # hoặc nếu danh mục được lưu trong cùng ProductService's storage.
        if hasattr(self.storage, 'get_by_id'):
            category = self.storage.get_by_id(category_id)  # Cần đảm bảo storage này chứa cả categories
            if category:
                return category

        # Fallback nếu storage không trực tiếp hỗ trợ hoặc category_id không phải là key chính
        # Cần điều chỉnh tùy thuộc vào cách bạn lưu trữ categories
        # Ví dụ: nếu categories là một phần của ProductService's storage hoặc một storage riêng
        all_categories = []  # Thay thế bằng cách lấy danh sách categories thực tế
        for c in all_categories:  # Ví dụ: self.storage.get_all_categories()
            if c.get('id') == category_id:
                return c
        return None

    def get_cost_by_sku(self, sku: str) -> float:
        """
        Retrieves the cost ('bought_product') of a product by its SKU.
        Returns 0 if the product or cost is not found.
        """
        if not sku:
            return 0.0

        all_products = self.list()
        for product in all_products:
            if product.get('sku') == sku:
                # The cost is stored in the 'bought_product' field
                cost = product.get('bought_product')
                # Ensure the returned value is a float, defaulting to 0.0
                return float(cost or 0.0)

        # Return 0 if no product with the given SKU is found
        return 0.0