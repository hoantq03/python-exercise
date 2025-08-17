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
from app.utils.password_utils import is_strong_password
from app.utils.phone_util import is_vietnamese_phone

ROLES = ('administrator', 'employee_manager', 'sales_manager', 'accountant', 'sales_person')
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

        # New: Sorting state for columns
        self.sort_column = None
        self.sort_direction = {}  # Stores 'asc', 'desc', or '' for each column

        # New: Search keyword variable
        self.search_kw = tk.StringVar()
        self._search_timer = None  # For debouncing search input

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

        # New: Search input
        ttk.Label(toolbar, text="Tìm kiếm (tên, email, SĐT):").pack(side=tk.LEFT, padx=(10, 2))
        self.search_entry = ttk.Entry(toolbar, textvariable=self.search_kw, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        self.search_kw.trace_add('write', self._debounced_refresh)

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
        # Define columns info for sorting (UPDATED)
        self.columns_info = {
            "name": {"heading": "Tên", "data_key": "name"},
            "email": {"heading": "Email", "data_key": "email"},
            "phone": {"heading": "Số điện thoại", "data_key": "phone"},
            "role": {"heading": "Quyền", "data_key": "role"},
        }
        columns = list(self.columns_info.keys())
        headings = [info["heading"] for info in self.columns_info.values()]

        self.tree = ttk.Treeview(parent, columns=columns, show="headings")

        for col, head in zip(columns, headings):
            self.tree.heading(col, text=head, command=lambda c=col: self._sort_column(c))
            # Set column widths and anchors (adjust as needed for better layout)
            if col == "name":
                self.tree.column(col, width=150, stretch=tk.YES)
            elif col == "email":
                self.tree.column(col, width=200, stretch=tk.YES)
            elif col == "phone":
                self.tree.column(col, width=120, stretch=tk.NO)
            elif col == "role":
                self.tree.column(col, width=80, anchor="center", stretch=tk.NO)

            self.sort_direction[col] = ''  # Initialize sort direction for each column

        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_user_select)

    def _sort_column(self, col):
        # Cycle through sort directions: '', 'asc', 'desc'
        current_direction = self.sort_direction.get(col, '')
        new_direction = ''
        if current_direction == '':
            new_direction = 'asc'
        elif current_direction == 'asc':
            new_direction = 'desc'
        else:
            new_direction = ''  # Reset to default

        # Reset all other columns to default direction and clear their arrows
        for c in self.sort_direction:
            if c != col:
                self.sort_direction[c] = ''
                self.tree.heading(c, text=self.columns_info[c]["heading"])

        self.sort_column = col
        self.sort_direction[col] = new_direction
        self.refresh()

    def _debounced_refresh(self, *args):
        # Cancel previous scheduled refresh if any
        if self._search_timer:
            self.after_cancel(self._search_timer)
        # Schedule refresh after 300ms (adjust as needed)
        self._search_timer = self.after(300, self.refresh)

    def refresh(self):
        """Làm mới danh sách người dùng, giữ nguyên lựa chọn hiện tại."""
        selected_iid = self.tree.selection()[0] if self.tree.selection() else None

        self.tree.delete(*self.tree.get_children())  # Clear existing items

        all_users = self.storage.all()
        search_keyword = self.search_kw.get().lower()

        filtered_users = []
        for user in all_users:
            # Check if keyword is in name, email, or phone
            if (not search_keyword or
                    (user.get('name', '').lower() and search_keyword in user['name'].lower()) or
                    (user.get('email', '').lower() and search_keyword in user['email'].lower()) or
                    (user.get('phone', '') and search_keyword in user['phone'])  # Phone might not be lowercased
            ):
                filtered_users.append(user)

        # Apply sorting logic
        if self.sort_column and self.sort_direction[self.sort_column]:
            sort_key = self.columns_info[self.sort_column]["data_key"]
            reverse_sort = (self.sort_direction[self.sort_column] == 'desc')

            # Special sorting for role (optional: define a custom order for roles)
            if sort_key == "role":
                # Example: Define a custom order for roles
                role_order = {"administrator": 0, "employee_manager": 1, "sales_manager": 2, "sales_person": 3, "accountant": 4}
                filtered_users.sort(key=lambda u: role_order.get(u.get(sort_key, "accountant"), 99), reverse=reverse_sort)
            else:
                filtered_users.sort(key=lambda u: str(u.get(sort_key, "")).lower(), reverse=reverse_sort)

            # Update heading with arrow
            arrow = ""
            if self.sort_direction[self.sort_column] == 'asc':
                arrow = " \u25b2"  # Up arrow
            elif self.sort_direction[self.sort_column] == 'desc':
                arrow = " \u25bc"  # Down arrow
            self.tree.heading(self.sort_column, text=self.columns_info[self.sort_column]["heading"] + arrow)
        else:
            # If no specific column is sorted, ensure all arrows are cleared
            for col in self.columns_info:
                self.tree.heading(col, text=self.columns_info[col]["heading"])
            # Default sort (e.g., by username or creation date) if no column sort is active
            filtered_users.sort(key=lambda u: str(u.get('username', '')).lower())  # Keeping a default sort

        for user in filtered_users:
            # Pass the values for the displayed columns (UPDATED)
            self.tree.insert("", tk.END,
                             values=(user.get('name'), user.get('email'), user.get('phone'), user.get('role')),
                             iid=user.get('id'))  # Keep using user['id'] as iid for uniqueness
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
        # Fetch full user data from storage using the iid (which is the user's ID)
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
        # This function needs access to `hash_password` from `app.services.auth`
        # Assuming it's imported or defined globally.
        if any(u["username"] == user_data["username"] for u in self.storage.all()):
            messagebox.showerror("Lỗi", "Tên đăng nhập đã tồn tại.", parent=self)
            return
        now_iso = datetime.now().isoformat(timespec="seconds")
        # Ensure hash_password is available or mock it for testing
        hashed_pw = hash_password(pw) if 'hash_password' in globals() else pw  # Placeholder if not imported
        new_user = {"id": str(uuid.uuid4()), "password_hash": hashed_pw, "created_at": now_iso,
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

        # Add password note label (NEW)
        if self.kwargs.get("ask_password", True):
            # Placing it at the current row 'i' (which is after the last field added)
            # You might need to adjust its grid placement depending on where 'password' field is
            # if not the last. Here it assumes password is effectively the last field added or close.
            note_label = ttk.Label(main_frame,
                                   text="Mật khẩu phải có ít nhất 8 ký tự, bao gồm chữ hoa, chữ thường, số và ký tự đặc biệt.",
                                   foreground="red", font=("Arial", 8, "italic"))
            note_label.grid(row=len(fields), column=0, columnspan=2, sticky="w", pady=(0, 5)) # Place below the last field

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=15, pady=(5, 15))
        ttk.Button(btn_frame, text="Lưu", command=self._submit).pack(side="right")
        ttk.Button(btn_frame, text="Hủy", command=self.destroy).pack(side="right", padx=5)

    def _submit(self):
        user_data = {}
        pw = None
        for key, var in self.entries.items():
            if key == 'dob':
                try:
                    value = var.get_date().isoformat()
                except AttributeError: # If DateEntry is empty
                    value = ""
            elif key == 'password':
                pw = var.get()
                is_password_required = self.kwargs.get("ask_password", True)
                if is_password_required and not pw:
                    messagebox.showerror("Lỗi", "Trường 'Mật khẩu' không được để trống.", parent=self)
                    return
                elif pw and not is_strong_password(pw):
                    messagebox.showerror("Lỗi", "Mật khẩu không đủ mạnh. Vui lòng nhập mật khẩu thỏa mãn yêu cầu: ít nhất 8 ký tự, gồm chữ hoa, chữ thường, số và ký tự đặc biệt.", parent=self)
                    return
                continue # Skip adding password to user_data directly
            else:
                value = var.get().strip()

            # --- Logic validation ---
            if key == 'email' and value and not re.match(r"[^@]+@[^@]+\.[^@]+", value):
                messagebox.showerror("Lỗi", "Định dạng email không hợp lệ.", parent=self)
                return
            if key == 'phone' and value and not is_vietnamese_phone(value):
                messagebox.showerror("Lỗi", "Số điện thoại phải bắt đầu bằng 0 và có 10 chữ số.", parent=self)
                return

            # Check for empty required fields (other than password, already handled)
            if not value and (key in ["username", "role"]):
                messagebox.showerror("Lỗi", f"Trường '{key}' không được để trống.", parent=self)
                return
            user_data[key] = value

        self.on_submit(user_data, pw)
        self.destroy()

