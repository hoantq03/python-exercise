class UserPermissions:
    """
    Quản lý logic phân quyền (Role-Based Access Control - RBAC) cho người dùng.
    """
    def __init__(self, current_user):
        self.current_user = current_user
        self.role = self.current_user.get('role')

    def can_add_user(self):
        """Kiểm tra xem người dùng hiện tại có thể thêm người dùng mới không."""
        return self.role in ['admin', 'staff']

    def get_creatable_roles(self):
        """Lấy danh sách các vai trò mà người dùng hiện tại có thể tạo."""
        if self.role == 'admin':
            return ['staff', 'viewer']
        if self.role == 'staff':
            return ['viewer']
        return []

    def can_delete_user(self, target_user):
        """Kiểm tra xem có thể xóa người dùng mục tiêu không (không thể tự xóa)."""
        return self.current_user.get('id') != target_user.get('id')

    def can_change_role(self):
        """Quy tắc nghiệp vụ: Không cho phép thay đổi vai trò sau khi tạo."""
        return False
