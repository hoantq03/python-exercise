import uuid
from typing import Dict

from app.models.storage import JsonStorage


class CustomerService:
    def __init__(self, storage: JsonStorage):
        self.storage = storage

    def list(self, keyword: str = ""):
        data = self.storage.all()
        if keyword:
            k = keyword.lower()
            data = [c for c in data if k in c["name"].lower() or k in c["phone"]]
        return data

    def create(self, payload: dict):
        payload["id"] = str(uuid.uuid4())
        return self.storage.create(payload)

    def update(self, _id: str, payload: dict):
        return self.storage.update(_id, payload)

    def delete(self, _id: str):
        return self.storage.delete(_id)

    def find_or_create_customer(self, customer_info: dict) -> str:
        """
        Tìm khách hàng theo SĐT, nếu không có thì tạo mới.
        Luôn trả về ID của khách hàng.
        """
        phone = customer_info.get("phone")
        if not phone:
            raise ValueError("Số điện thoại là bắt buộc để tìm hoặc tạo khách hàng.")

        # Tìm khách hàng theo SĐT
        all_customers = self.storage.all()
        found_customer = next((c for c in all_customers if c.get("phone") == phone), None)

        if found_customer:
            return found_customer["id"]
        else:
            # Nếu không tìm thấy, tạo khách hàng mới
            new_customer = {
                "id": str(uuid.uuid4()),  # Cần import uuid
                "name": customer_info.get("name"),
                "phone": phone,
                "email": customer_info.get("email", ""),
                "address": customer_info.get("address", "")
            }
            self.storage.create(new_customer)
            return new_customer["id"]


    def find_by_phone(self, phone: str) -> Dict | None:
        """Tìm khách hàng theo số điện thoại."""
        all_customers = self.storage.all()
        return next((c for c in all_customers if c.get("phone") == phone), None)

