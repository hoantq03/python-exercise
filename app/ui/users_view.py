from datetime import datetime
import tkinter as tk
import uuid
from tkinter import ttk, messagebox
import threading
from io import BytesIO
import requests
from PIL import Image, ImageTk
from tkcalendar import DateEntry
import re

from app.auth.user_permission import UserPermissions
from app.services.auth import hash_password

ROLES = ("admin", "staff", "viewer")
GENDERS = ("Nam", "Nữ", "Khác")


class UsersView(ttk.Frame):
    """
    Giao diện quản lý người dùng với bố cục hai khung (chi tiết và danh sách).
    """

    def __init__(self, master, storage, current_user):
        super().__init__(master)
        self.storage = storage
        self.current_user = current_user

        # --- Khởi tạo đối tượng quản lý quyền ---
        self.permissions = UserPermissions(self.current_user)

        self.selected_user_id = None
        self._image_cache = {}
        self._create_widgets()
        self.refresh()

    def _create_widgets(self):
        """Tạo các widget chính cho giao diện."""
        toolbar = ttk.Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X, pady=10, padx=10)

        self.add_btn = ttk.Button(toolbar, text="➕ Thêm tài khoản", command=self.add_user)
        self.add_btn.pack(side=tk.LEFT)

        # --- Sử dụng lớp permissions để kiểm tra ---
        if not self.permissions.can_add_user():
            self.add_btn.config(state=tk.DISABLED)

        self.edit_btn = ttk.Button(toolbar, text="✏️ Sửa thông tin", command=self.edit_user, state=tk.DISABLED)
        self.edit_btn.pack(side=tk.LEFT, padx=5)
        self.delete_btn = ttk.Button(toolbar, text="🗑️ Xóa", command=self.delete_user, state=tk.DISABLED)
        self.delete_btn.pack(side=tk.LEFT)

        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.detail_frame = ttk.LabelFrame(main_pane, text="Thông tin chi tiết", padding=15)
        main_pane.add(self.detail_frame, weight=1)
        self._create_detail_view()
        list_container = ttk.Frame(main_pane)
        main_pane.add(list_container, weight=2)
        self._create_list_view(list_container)

    def _create_detail_view(self):
        """Tạo các widget trong khung chi tiết (bên trái)."""
        avatar_container = ttk.Frame(self.detail_frame, width=200, height=200)
        avatar_container.pack(pady=10)
        avatar_container.pack_propagate(False)
        self.avatar_label = tk.Label(avatar_container, text="👤", font=("Arial", 100), bg="#e0e0e0", relief="sunken")
        self.avatar_label.pack(fill=tk.BOTH, expand=True)

        self.info_labels = {}
        info_fields = {"name": "Họ và tên:", "username": "Tên đăng nhập:", "role": "Quyền:", "email": "Email:",
                       "phone": "SĐT:", "dob": "Ngày sinh:", "gender": "Giới tính:", "address": "Địa chỉ:"}
        for key, text in info_fields.items():
            row = ttk.Frame(self.detail_frame)
            row.pack(fill="x", pady=2, padx=5)
            ttk.Label(row, text=text, font=("Arial", 10, "bold")).pack(side="left")
            self.info_labels[key] = ttk.Label(row, text="N/A", font=("Arial", 10), wraplength=250, justify=tk.LEFT)
            self.info_labels[key].pack(side="left", padx=5)
        self._show_default_detail_view()

    def _create_list_view(self, parent):
        """Tạo Treeview danh sách người dùng (bên phải)."""
        columns = ("id", "username", "role")
        self.tree = ttk.Treeview(parent, columns=columns, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.column("id", width=250, stretch=tk.NO)
        self.tree.heading("username", text="Tên đăng nhập")
        self.tree.column("username", width=150)
        self.tree.heading("role", text="Quyền")
        self.tree.column("role", width=100, anchor="center")
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_user_select)

    def refresh(self):
        """Làm mới danh sách người dùng, giữ nguyên lựa chọn hiện tại."""
        selected_iid = self.tree.selection()[0] if self.tree.selection() else None
        for item in self.tree.get_children():
            self.tree.delete(item)
        for user in self.storage.all():
            self.tree.insert("", tk.END, values=(user.get('id'), user.get('username'), user.get('role')),
                             iid=user.get('id'))
        if selected_iid and self.tree.exists(selected_iid):
            self.tree.selection_set(selected_iid)
        else:
            self._on_selection_clear()

    def _on_user_select(self, event=None):
        """Xử lý sự kiện khi một người dùng được chọn trong danh sách."""
        selected_items = self.tree.selection()
        if not selected_items:
            self._on_selection_clear()
            return
        self.selected_user_id = selected_items[0]
        user_data = next((u for u in self.storage.all() if u['id'] == self.selected_user_id), None)
        if user_data:
            self._display_user_details(user_data)
            # --- Sử dụng lớp permissions để kiểm tra ---
            self.edit_btn.config(state=tk.NORMAL)
            self.delete_btn.config(state=tk.NORMAL if self.permissions.can_delete_user(user_data) else tk.DISABLED)

    def _on_selection_clear(self):
        """Reset giao diện khi không có user nào được chọn."""
        self.selected_user_id = None
        self.edit_btn.config(state=tk.DISABLED)
        self.delete_btn.config(state=tk.DISABLED)
        self._show_default_detail_view()
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())

    def _show_default_detail_view(self):
        """Hiển thị trạng thái mặc định cho khung chi tiết."""
        self.avatar_label.config(text="👤", image='')
        self.avatar_label.image = None
        for key, label in self.info_labels.items():
            label.config(text="N/A" if key != "name" else "Vui lòng chọn người dùng")

    def _display_user_details(self, user):
        """Hiển thị thông tin chi tiết của một người dùng."""
        for key, label in self.info_labels.items():
            label.config(text=user.get(key, "N/A"))
        self._load_avatar(user.get("avatar"), user.get("id"))

    def _load_avatar(self, url, user_id):
        """Tải ảnh đại diện trong luồng nền."""
        if user_id in self._image_cache:
            self.avatar_label.config(image=self._image_cache[user_id])
            return
        self.avatar_label.config(text="...", image='')
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
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self._image_cache[user_id] = photo
                self.after(0, self.avatar_label.config, {"image": photo})
        except Exception:
            self.after(0, self.avatar_label.config, {"text": "🚫", "image": ''})

    def add_user(self):
        """Mở dialog để thêm người dùng mới, với danh sách role phù hợp."""
        creatable_roles = self.permissions.get_creatable_roles()
        if not creatable_roles:
            messagebox.showinfo("Thông báo", "Bạn không có quyền tạo người dùng mới.", parent=self)
            return
        UserDialog(self, "Tạo tài khoản mới", on_submit=self._add_user_submit, creatable_roles=creatable_roles)

    def _add_user_submit(self, user_data, pw):
        """Xử lý logic khi form thêm người dùng được gửi đi."""
        if any(u["username"] == user_data["username"] for u in self.storage.all()):
            messagebox.showerror("Lỗi", "Tên đăng nhập đã tồn tại.", parent=self)
            return
        now_iso = datetime.now().isoformat(timespec="seconds")
        new_user = {"id": str(uuid.uuid4()), "password_hash": hash_password(pw), "created_at": now_iso,
                    "updated_at": now_iso, "last_login": "", **user_data}
        self.storage.create(new_user)
        self.refresh()

    def edit_user(self):
        """Mở dialog để sửa thông tin người dùng đã chọn."""
        if not self.selected_user_id:
            messagebox.showerror("Lỗi", "Vui lòng chọn một người dùng để sửa.", parent=self)
            return
        user = next((u for u in self.storage.all() if u['id'] == self.selected_user_id), None)
        if not user:
            messagebox.showerror("Lỗi", "Không tìm thấy thông tin người dùng.", parent=self)
            return

        UserDialog(self, title="Sửa thông tin người dùng",
                   on_submit=lambda data, pw: self._edit_user_submit(self.selected_user_id, data),
                   disable_username=True, ask_password=False,
                   disable_role=not self.permissions.can_change_role(),
                   username_default=user.get("username", ""), role_default=user.get("role", "staff"),
                   name_default=user.get("name", ""), dob_default=user.get("dob"),
                   phone_default=user.get("phone", ""), email_default=user.get("email", ""),
                   address_default=user.get("address", ""), gender_default=user.get("gender", "Nam"),
                   avatar_default=user.get("avatar", ""))

    def _edit_user_submit(self, _id, user_data):
        """Xử lý logic khi form sửa người dùng được gửi đi."""
        user_data.pop("username", None)
        user_data.pop("role", None)
        patch = {**user_data, "updated_at": datetime.now().isoformat(timespec="seconds")}
        self.storage.update(_id, patch)
        self.refresh()

    def delete_user(self):
        """Xóa người dùng đã chọn."""
        if not self.selected_user_id:
            messagebox.showerror("Lỗi", "Vui lòng chọn một người dùng để xóa.", parent=self)
            return

        user = next((u for u in self.storage.all() if u['id'] == self.selected_user_id), None)
        if not self.permissions.can_delete_user(user):
            messagebox.showerror("Lỗi", "Bạn không thể tự xóa chính mình.", parent=self)
            return

        username = user.get('username', 'N/A') if user else 'N/A'
        if messagebox.askyesno("Xác nhận xóa", f"Bạn có chắc muốn xóa người dùng '{username}' không?"):
            self.storage.delete(self.selected_user_id)
            self._on_selection_clear()
            self.refresh()


class UserDialog(tk.Toplevel):
    """Dialog được tối ưu hóa để thêm/sửa người dùng."""

    def __init__(self, master, title, on_submit, **kwargs):
        super().__init__(master)
        self.title(title)
        self.grab_set()
        self.resizable(False, False)
        self.transient(master)
        self.on_submit = on_submit
        self.kwargs = kwargs
        self.entries = {}
        self._create_form()

    def _create_form(self):
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill="both", expand=True)
        creatable_roles = self.kwargs.get("creatable_roles", ROLES)

        fields = [("Tên đăng nhập:", "username", "entry",
                   {"state": tk.DISABLED if self.kwargs.get("disable_username") else tk.NORMAL}),
                  ("Tên đầy đủ:", "name", "entry"), ("Ngày sinh:", "dob", "date"), ("Số điện thoại:", "phone", "entry"),
                  ("Email:", "email", "entry"), ("Địa chỉ:", "address", "entry"), ("Giới tính:", "gender", "radio"),
                  ("Phân quyền:", "role", "combo",
                   {"state": tk.DISABLED if self.kwargs.get("disable_role") else "readonly",
                    "values": creatable_roles}),
                  ("Ảnh đại diện (URL):", "avatar", "entry")]
        if self.kwargs.get("ask_password", True):
            fields.append(("Mật khẩu:", "password", "entry", {"show": "*"}))

        for i, (label_text, key, widget_type, *options) in enumerate(fields):
            ttk.Label(main_frame, text=label_text).grid(row=i, column=0, sticky="w", pady=4)
            opts = options[0] if options else {}
            if widget_type == "entry":
                var = tk.StringVar(value=self.kwargs.get(f"{key}_default", ""))
                entry = ttk.Entry(main_frame, textvariable=var, **opts)
                entry.grid(row=i, column=1, sticky="ew", pady=4, padx=5)
                self.entries[key] = var
            elif widget_type == "date":
                entry = DateEntry(main_frame, date_pattern="yyyy-mm-dd", **opts)
                if self.kwargs.get("dob_default"):
                    try:
                        entry.set_date(self.kwargs.get("dob_default"))
                    except Exception as e:
                        print(f"Không thể đặt ngày: {e}")
                entry.grid(row=i, column=1, sticky="ew", pady=4, padx=5)
                self.entries[key] = entry
            elif widget_type == "combo":
                default_role = self.kwargs.get("role_default", creatable_roles[0] if creatable_roles else "viewer")
                var = tk.StringVar(value=default_role)
                entry = ttk.Combobox(main_frame, textvariable=var, **opts)
                entry.grid(row=i, column=1, sticky="ew", pady=4, padx=5)
                self.entries[key] = var
            elif widget_type == "radio":
                radio_frame = ttk.Frame(main_frame)
                var = tk.StringVar(value=self.kwargs.get("gender_default", "Nam"))
                for g in GENDERS:
                    ttk.Radiobutton(radio_frame, text=g, value=g, variable=var).pack(side=tk.LEFT, padx=2)
                radio_frame.grid(row=i, column=1, sticky="w", pady=4, padx=5)
                self.entries[key] = var

        main_frame.grid_columnconfigure(1, weight=1)
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=15, pady=(5, 15))
        ttk.Button(btn_frame, text="Lưu", command=self._submit).pack(side="right")
        ttk.Button(btn_frame, text="Hủy", command=self.destroy).pack(side="right", padx=5)

    def _submit(self):
        user_data = {}
        pw = None
        for key, var in self.entries.items():
            if key == 'dob':
                value = var.get_date().isoformat()
            elif key == 'password':
                pw = var.get()
                continue
            else:
                value = var.get().strip()

            # --- Logic validation ---
            if key == 'email' and value and not re.match(r"[^@]+@[^@]+\.[^@]+", value):
                messagebox.showerror("Lỗi", "Định dạng email không hợp lệ.", parent=self)
                return
            if key == 'phone' and value and not re.match(r"^0\d{9}$", value):
                messagebox.showerror("Lỗi", "Số điện thoại phải bắt đầu bằng 0 và có 10 chữ số.", parent=self)
                return

            is_password_required = self.kwargs.get("ask_password", True)
            if not value and (key in ["username", "role"] or (key == 'password' and is_password_required)):
                messagebox.showerror("Lỗi", f"Trường '{key}' không được để trống.", parent=self)
                return
            user_data[key] = value
        self.on_submit(user_data, pw)
        self.destroy()