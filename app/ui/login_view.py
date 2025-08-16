import tkinter as tk
from tkinter import ttk, messagebox
import re

class LoginView(tk.Toplevel):
    UI_CFG = {
        # --- Cấu hình chung cho Font và Màu sắc ---
        "title_font": ("Arial", 23, "bold"),  # Font cho tiêu đề chính (ví dụ: "Đăng nhập")
        "title_color": "#D60000",  # Màu sắc cho tiêu đề chính (mã Hex)

        "label_font": ("Arial", 13),  # Font cho các nhãn (ví dụ: "Tên đăng nhập:", "Mật khẩu:")
        "entry_font": ("Arial", 16),  # Font cho các trường nhập liệu (Entry)

        "button_font": ("Arial", 16, "bold"),  # Font cho các nút (có thể áp dụng riêng cho từng loại nút nếu cần)

        # --- Cấu hình Padding và Khoảng cách ---
        "padx_common": 29,  # Padding ngang chung (padx) cho nhiều thành phần
        # (ví dụ: nhãn, trường nhập liệu, nút)

        "pady_title": (23, 10),  # Padding dọc (pady) cho tiêu đề chính.
        # (top_padding, bottom_padding)

        "pady_entry": (0, 16),  # Padding dọc cho các trường nhập liệu (Entry).
        # (top_padding, bottom_padding)

        "pady_button": (5, 5),  # Padding dọc cho nút đăng nhập.
        # (top_padding, bottom_padding)

        # --- Cấu hình cho phần Separator (đường phân cách) ---
        "separator_label_font": ("Arial", 13, "italic"),  # Font cho nhãn trong phần phân cách ("Hoặc đăng nhập bằng")

        "separator_padx": (29, 10),  # Padding ngang cho các đường phân cách (Separator).
        # (left_padding, right_padding) cho phần bên trái của nhãn
        # và ngược lại cho phần bên phải.

        "separator_pady": 16,  # Padding dọc cho khung chứa các đường phân cách và nhãn.

        # --- Cấu hình cho các nút cụ thể ---
        "show_pw_button_width": 3,  # Chiều rộng (width) của nút "hiện/ẩn mật khẩu" (👁).

        "social_button_width": 16,  # Chiều rộng (width) của các nút đăng nhập mạng xã hội (Google, Zalo).

        "social_button_padx": (29, 16),  # Padding ngang cho các nút đăng nhập mạng xã hội.
        # (left_padding, right_padding) cho nút Google,
        # và (right_padding, left_padding) cho nút Zalo để tạo khoảng cách đối xứng.
    }

    def __init__(self, master, auth_service, on_success):
        super().__init__(master)
        self.title("Đăng nhập")
        self.geometry("380x420")
        self.resizable(False, False)
        self.auth = auth_service
        self.on_success = on_success

        # --- Title
        ttk.Label(self, text="Đăng nhập",
                  font=self.UI_CFG["title_font"],
                  foreground=self.UI_CFG["title_color"]).pack(pady=self.UI_CFG["pady_title"])

        # --- Phone input
        ttk.Label(self, text="Tên đăng nhập:",
                  font=self.UI_CFG["label_font"]).pack(anchor="w", padx=self.UI_CFG["padx_common"])
        self.e_user = ttk.Entry(self,
                                font=self.UI_CFG["entry_font"])
        self.e_user.pack(fill="x", padx=self.UI_CFG["padx_common"], pady=self.UI_CFG["pady_entry"])

        # --- Password input + show/hide
        ttk.Label(self, text="Mật khẩu:",
                  font=self.UI_CFG["label_font"]).pack(anchor="w", padx=self.UI_CFG["padx_common"])
        pw_frame = ttk.Frame(self)
        pw_frame.pack(fill="x", padx=self.UI_CFG["padx_common"], pady=self.UI_CFG["pady_entry"])
        self.e_pass = ttk.Entry(pw_frame,
                                font=self.UI_CFG["entry_font"],
                                show="*")
        self.e_pass.pack(side=tk.LEFT, fill="x", expand=1)
        self.showing_pw = False
        show_btn = ttk.Button(pw_frame, text="👁",
                              width=self.UI_CFG["show_pw_button_width"],
                              command=self.toggle_pw)
        show_btn.pack(side=tk.LEFT, padx=4)

        # --- Đăng nhập button
        login_btn = ttk.Button(self, text="Đăng nhập",
                               # font=self.UI_CFG["button_font"], # Có thể thêm nếu muốn font riêng
                               command=self._do_login)
        login_btn.pack(fill="x", padx=self.UI_CFG["padx_common"], pady=self.UI_CFG["pady_button"])

        # --- Separator
        sep_frame = ttk.Frame(self)
        sep_frame.pack(fill="x", pady=self.UI_CFG["separator_pady"])
        sep_left = ttk.Separator(sep_frame, orient="horizontal")
        sep_left.pack(side=tk.LEFT, fill="x", expand=1, padx=self.UI_CFG["separator_padx"])
        ttk.Label(sep_frame, text="Hoặc đăng nhập bằng",
                  font=self.UI_CFG["separator_label_font"]).pack(side=tk.LEFT)
        sep_right = ttk.Separator(sep_frame, orient="horizontal")
        sep_right.pack(side=tk.LEFT, fill="x", expand=1, padx=self.UI_CFG["separator_padx"])

        # --- Social login buttons (dummy)
        social_frame = ttk.Frame(self)
        social_frame.pack(pady=(0,6)) # Giữ nguyên pady này nếu nó là cụ thể cho social frame
        ttk.Button(social_frame, text="Google",
                   width=self.UI_CFG["social_button_width"],
                   state=tk.DISABLED).pack(side=tk.LEFT, padx=self.UI_CFG["social_button_padx"])
        ttk.Button(social_frame, text="Zalo",
                   width=self.UI_CFG["social_button_width"],
                   state=tk.DISABLED).pack(side=tk.LEFT, padx=(self.UI_CFG["social_button_padx"][1], self.UI_CFG["social_button_padx"][0]))


    def toggle_pw(self):
        self.showing_pw = not self.showing_pw
        self.e_pass.config(show="" if self.showing_pw else "*")

    def _do_login(self):
        user = self.e_user.get().strip()
        pw = self.e_pass.get().strip()
        if not user or not pw:
            messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ thông tin.")
            return

        u = self.auth.login(user, pw)
        if u:
            messagebox.showinfo("Thành công", "Đăng nhập thành công")
            self.on_success(u)
            self.destroy()
        else:
            messagebox.showerror("Lỗi", "Sai số điện thoại hoặc mật khẩu.")

