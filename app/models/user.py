from dataclasses import dataclass

@dataclass
class User:
    id: str
    username: str
    password_hash: str
    role: str  # admin | staff | viewer
    name: str = ""              # Tên đầy đủ, max 50 ký tự
    dob: str = ""               # Ngày sinh, ISO 8601 yyyy-mm-dd string
    phone: str = ""             # Số điện thoại
    email: str = ""             # Email
    address: str = ""           # Địa chỉ, max 255 ký tự
    gender: str = ""            # Giới tính, ví dụ "Nam", "Nữ", "Khác"
    avatar: str = ""            # Đường dẫn ảnh đại diện
    created_at: str = ""        # ISO timestamp tài khoản tạo
    updated_at: str = ""        # ISO timestamp cập nhật cuối
    last_login: str = ""        # ISO timestamp đăng nhập cuối
