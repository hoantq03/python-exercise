import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading
import requests
from io import BytesIO

class ProfileView(ttk.Frame):
    """
    Frame hiển thị thông tin cá nhân người dùng,
    avatar lớn phía trái và các thông tin chi tiết bên phải.
    """
    def __init__(self, master, current_user: dict, **kwargs):
        super().__init__(master, **kwargs)
        self.current_user = current_user
        self._image_cache = {}
        self._create_widgets()
        self._display_user_info()

    def _create_widgets(self):
        container = ttk.Frame(self)
        container.pack(expand=True, fill=tk.BOTH)

        # Avatar container (hiện avatar hoặc emoji)
        avatar_container = ttk.Frame(container, width=150, height=150, relief=tk.RIDGE)
        avatar_container.pack(side=tk.LEFT, padx=(20, 15), pady=20)
        avatar_container.pack_propagate(False)

        self.avatar_label = tk.Label(avatar_container, text="👤", font=("Arial", 80), bg="#ddd", relief="sunken")
        self.avatar_label.pack(fill=tk.BOTH, expand=True)

        # Thông tin cá nhân
        info_container = ttk.Frame(container)
        info_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=20)

        info_fields = {
            "Họ và tên:": self.current_user.get("name", "N/A"),
            "Tên đăng nhập:": self.current_user.get("username", "N/A"),
            "Email:": self.current_user.get("email", "N/A"),
            "Số điện thoại:": self.current_user.get("phone", "N/A"),
            "Ngày sinh:": self.current_user.get("dob", "N/A"),
            "Giới tính:": self.current_user.get("gender", "N/A"),
            "Địa chỉ:": self.current_user.get("address", "N/A"),
            "Vai trò:": str(self.current_user.get("role", "N/A")).capitalize(),
        }

        for i, (label, value) in enumerate(info_fields.items()):
            lbl_label = ttk.Label(info_container, text=label, font=("Arial", 11, "bold"))
            lbl_label.grid(row=i, column=0, sticky="w", pady=4, padx=5)
            lbl_value = ttk.Label(info_container, text=value, font=("Arial", 11), wraplength=400, justify="left")
            lbl_value.grid(row=i, column=1, sticky="w", pady=4, padx=5)

    def _display_user_info(self):
        avatar_url = self.current_user.get("avatar")
        user_id = self.current_user.get("id")
        self._load_avatar(avatar_url, user_id)

    def _load_avatar(self, url, user_id):
        if user_id in self._image_cache:
            self.avatar_label.config(image=self._image_cache[user_id], text="")
            return
        self.avatar_label.config(text="...", image="")
        threading.Thread(target=self._fetch_avatar_async, args=(url, user_id), daemon=True).start()

    def _fetch_avatar_async(self, url, user_id):
        try:
            if url and str(url).startswith("http"):
                resp = requests.get(url, timeout=5)
                resp.raise_for_status()
                img_data = BytesIO(resp.content)
            elif url:
                img_data = url
            else:
                raise ValueError("No URL or path")
            with Image.open(img_data) as img:
                img = img.convert("RGB")
                img.thumbnail((150, 150), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self._image_cache[user_id] = photo
                self.after(0, self.avatar_label.config, {"image": photo, "text": ""})
        except Exception:
            self.after(0, self.avatar_label.config, {"text": "🚫", "image": ""})
