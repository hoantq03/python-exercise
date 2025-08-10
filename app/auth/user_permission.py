class UserPermissions:
    """
    Quản lý logic phân quyền (Role-Based Access Control - RBAC) cho người dùng.
    """
    def __init__(self, current_user):
        self.current_user = current_user
        self.role = self.current_user.get('role')

    def can_add_user(self):
        return self.role in ['admin', 'staff']

    def get_creatable_roles(self):
        if self.role == 'admin':
            return ['staff', 'viewer']
        if self.role == 'staff':
            return ['viewer']
        return []

    def can_delete_user(self, target_user):
        return self.role in ['admin'] and self.current_user.get('id') != target_user.get('id')

    def can_change_role(self):
        return False
