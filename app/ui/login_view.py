import tkinter as tk
from tkinter import ttk, messagebox
import re

class LoginView(tk.Toplevel):
    def __init__(self, master, auth_service, on_success):
        super().__init__(master)
        self.title("Đăng nhập")
        self.geometry("380x420")
        self.resizable(False, False)
        self.auth = auth_service
        self.on_success = on_success

        # --- Title
        ttk.Label(self, text="Đăng nhập SMEMBER", font=("Arial", 18, "bold"), foreground="#D60000").pack(pady=(18,8))

        # --- Phone input
        ttk.Label(self, text="Số điện thoại:", font=("Arial", 10)).pack(anchor="w", padx=22)
        self.e_user = ttk.Entry(self, font=("Arial", 12))
        self.e_user.pack(fill="x", padx=22, pady=(0,12))

        # --- Password input + show/hide
        ttk.Label(self, text="Mật khẩu:", font=("Arial", 10)).pack(anchor="w", padx=22)
        pw_frame = ttk.Frame(self)
        pw_frame.pack(fill="x", padx=22, pady=(0,12))
        self.e_pass = ttk.Entry(pw_frame, font=("Arial", 12), show="*")
        self.e_pass.pack(side=tk.LEFT, fill="x", expand=1)
        self.showing_pw = False
        show_btn = ttk.Button(pw_frame, text="👁", width=2, command=self.toggle_pw)
        show_btn.pack(side=tk.LEFT, padx=4)

        # --- Đăng nhập button
        login_btn = ttk.Button(self, text="Đăng nhập", command=self._do_login)
        login_btn.pack(fill="x", padx=22, pady=(4,4))

        # --- Separator
        sep_frame = ttk.Frame(self)
        sep_frame.pack(fill="x", pady=12)
        sep_left = ttk.Separator(sep_frame, orient="horizontal")
        sep_left.pack(side=tk.LEFT, fill="x", expand=1, padx=(22,8))
        ttk.Label(sep_frame, text="Hoặc đăng nhập bằng", font=("Arial", 10, "italic")).pack(side=tk.LEFT)
        sep_right = ttk.Separator(sep_frame, orient="horizontal")
        sep_right.pack(side=tk.LEFT, fill="x", expand=1, padx=(8,22))

        # --- Social login buttons (dummy)
        social_frame = ttk.Frame(self)
        social_frame.pack(pady=(0,6))
        ttk.Button(social_frame, text="Google", width=12, state=tk.DISABLED).pack(side=tk.LEFT, padx=(22,12))
        ttk.Button(social_frame, text="Zalo", width=12, state=tk.DISABLED).pack(side=tk.LEFT, padx=(12,22))

    def toggle_pw(self):
        # Ẩn/hiện mật khẩu
        self.showing_pw = not self.showing_pw
        self.e_pass.config(show="" if self.showing_pw else "*")

    def _do_login(self):
        user = self.e_user.get().strip()
        pw = self.e_pass.get().strip()
        if not user or not pw:
            messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ thông tin.")
            return
        # Chỉ kiểm tra số điện thoại: regex tối giản
        # if not re.match(r"^(0|\+84)[0-9]{8,}$", user):
        #     messagebox.showerror("Lỗi", "Số điện thoại không hợp lệ.")
        #     return
        u = self.auth.login(user, pw)
        if u:
            messagebox.showinfo("Thành công", "Đăng nhập thành công")
            self.on_success(u)
            self.destroy()
        else:
            messagebox.showerror("Lỗi", "Sai số điện thoại hoặc mật khẩu.")
