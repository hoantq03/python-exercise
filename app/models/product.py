from dataclasses import dataclass

@dataclass
class Product:
    id: str
    name: str
    sku: str
    price: float
    stock: int
    description: str = ""
    avatar: str = ""               # link hoặc path ảnh sản phẩm
    screen_size: str = ""          # Kích thước màn hình
    screen_tech: str = ""          # Công nghệ màn hình
    camera_sau: str = ""           # Camera sau
    camera_truoc: str = ""         # Camera trước
    chipset: str = ""
    nfc: str = ""
    ram: str = ""
    storage: str = ""
    battery: str = ""
    sim: str = ""                  # Loại SIM
    os: str = ""                   # Hệ điều hành
    refresh_rate: str = ""         # Tần số quét màn hình
    main_screen_res: str = ""      # Độ phân giải chính
    sub_screen_size: str = ""      # Kích thước màn phụ (nếu có)
    sub_screen_res: str = ""       # Độ phân giải màn phụ
    color_depth: str = ""          # Độ sâu màu
    cpu_type: str = ""             # Loại CPU
    created_at: str = ""
    updated_at: str = ""
