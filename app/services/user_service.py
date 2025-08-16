import uuid
from typing import Dict, List, Any

from app.models.storage import JsonStorage

class UserService:
    def __init__(self, storage: JsonStorage):
        """
        Khởi tạo UserService.

        Args:
            storage: Một đối tượng JsonStorage để tương tác với dữ liệu người dùng.
        """
        self.storage = storage

    def list(self, keyword: str = "") -> List[Dict[str, Any]]:
        """
        Lấy danh sách tất cả người dùng, có thể lọc theo từ khóa.

        Args:
            keyword: Từ khóa để tìm kiếm trong username hoặc tên đầy đủ.

        Returns:
            Danh sách các người dùng khớp với từ khóa.
        """
        data = self.storage.all()
        if keyword:
            k = keyword.lower()
            data = [u for u in data if k in u.get("username", "").lower() or k in u.get("name", "").lower()]
        return data

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tạo một người dùng mới.

        Args:
            payload: Một dictionary chứa thông tin người dùng.
                     id sẽ được tự động tạo.

        Returns:
            Dictionary của người dùng vừa được tạo.
        """
        payload["id"] = str(uuid.uuid4())
        return self.storage.create(payload)

    def update(self, _id: str, patch: Dict[str, Any]) -> Dict[str, Any] | None:
        """
        Cập nhật thông tin của một người dùng.

        Args:
            _id: ID của người dùng cần cập nhật.
            patch: Dictionary chứa các trường và giá trị muốn cập nhật.

        Returns:
            Dictionary của người dùng sau khi cập nhật, hoặc None nếu không tìm thấy.
        """
        return self.storage.update(_id, patch)

    def delete(self, _id: str) -> bool:
        """
        Xóa một người dùng.

        Args:
            _id: ID của người dùng cần xóa.

        Returns:
            True nếu xóa thành công, False nếu không tìm thấy người dùng.
        """
        return self.storage.delete(_id)

    def find_by_username(self, username: str) -> Dict[str, Any] | None:
        """
        Tìm kiếm người dùng theo username.

        Args:
            username: Tên đăng nhập của người dùng.

        Returns:
            Dictionary của người dùng tìm thấy, hoặc None nếu không tìm thấy.
        """
        all_users = self.storage.all()
        return next((u for u in all_users if u.get("username") == username), None)

    def authenticate(self, username: str, password_hash: str) -> Dict[str, Any] | None:
        """
        Xác thực người dùng bằng username và password hash.

        Args:
            username: Tên đăng nhập.
            password_hash: Hash của mật khẩu.

        Returns:
            Dictionary của người dùng nếu xác thực thành công, hoặc None nếu thất bại.
        """
        user = self.find_by_username(username)
        if not user:
            return None
        if user.get("password_hash") == password_hash:
            return user
        return None

    def change_password(self, username: str, new_password_hash: str) -> bool:
        """
        Thay đổi mật khẩu của người dùng.

        Args:
            username: Tên đăng nhập của người dùng.
            new_password_hash: Hash của mật khẩu mới.

        Returns:
            True nếu thay đổi thành công, False nếu không tìm thấy người dùng.
        """
        user = self.find_by_username(username)
        if not user:
            return False
        return self.storage.update(user["id"], {"password_hash": new_password_hash}) is not None

    def get_user_by_id(self, user_id: str) -> Dict[str, Any] | None:
        """
        Lấy thông tin người dùng theo ID.

        Args:
            user_id: ID của người dùng.

        Returns:
            Dictionary của người dùng, hoặc None nếu không tìm thấy.
        """
        return self.storage.get_by_id(user_id)

