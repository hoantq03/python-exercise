from app.models.category import Category
from app.models.storage import JsonStorage
from dataclasses import asdict
from typing import Dict, List
import uuid
from datetime import datetime

class CategoryService:
    def __init__(self, storage: JsonStorage):
        self.storage = storage

    def list_all_categories(self) -> List[Dict]:
        """
        Lấy tất cả các danh mục từ storage, sắp xếp theo tên danh mục.
        """
        all_cats = self.storage.all()
        return sorted(all_cats, key=lambda x: x.get('categoryName', ''))

    def get_category_by_uri(self, uri: str) -> Dict | None:
        """
        Tìm một danh mục theo categoryUri.
        """
        for cat in self.storage.all():
            if cat.get('categoryUri') == uri:
                return cat
        return None

    def create_category(self, category_data: Dict) -> Dict:
        """
        Tạo một danh mục mới.
        """
        if "id" not in category_data:
            category_data["id"] = str(uuid.uuid4())
        now_iso = datetime.now().isoformat(timespec="seconds")
        category_data["created_at"] = now_iso
        category_data["updated_at"] = now_iso
        self.storage.create(category_data)
        print(f"Category '{category_data.get('categoryName', '')}' created.")
        return category_data

    def update_category(self, category_id: str, patch_data: Dict) -> Dict | None:
        """
        Cập nhật thông tin danh mục.
        """
        patch_data["updated_at"] = datetime.now().isoformat(timespec="seconds")
        updated_cat = self.storage.update(category_id, patch_data)
        if updated_cat:
            print(f"Category '{category_id}' updated.")
        else:
            print(f"Category '{category_id}' not found for update.")
        return updated_cat

    def delete_category(self, category_id: str) -> bool:
        """
        Xóa một danh mục.
        """
        deleted = self.storage.delete(category_id)
        if deleted:
            print(f"Category '{category_id}' deleted.")
        else:
            print(f"Category '{category_id}' not found for deletion.")
        return deleted

