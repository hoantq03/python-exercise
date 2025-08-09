import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import uuid

from app.services.auth import hash_password

ROLES = ("admin", "staff", "viewer")
GENDERS = ("Nam", "Nữ", "Khác")

class UsersView(ttk.Frame):
    def __init__(self, master, storage, current_user):
        super().__init__(master)
        self.storage = storage
        self.current_user = current_user

        # Toolbar
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, pady=4)
        ttk.Button(toolbar, text="➕ Thêm tài khoản", command=self.add_user).pack(side=tk.LEFT, padx=6)
        ttk.Button(toolbar, text="✏️ Sửa thông tin", command=self.edit_user).pack(side=tk.LEFT, padx=6)
        ttk.Button(toolbar, text="🗑️ Xóa", command=self.delete_user).pack(side=tk.LEFT, padx=6)

        # Treeview bảng người dùng
        self.tree = ttk.Treeview(self, columns=(
            "username", "role", "name", "dob", "phone", "email", "address", "gender", "avatar"
        ), show="headings", height=15)

        self.tree.heading("username", text="Tên đăng nhập")
        self.tree.heading("role", text="Quyền")
        self.tree.heading("name", text="Tên đầy đủ")
        self.tree.heading("dob", text="Ngày sinh")
        self.tree.heading("phone", text="SĐT")
        self.tree.heading("email", text="Email")
        self.tree.heading("address", text="Địa chỉ")
        self.tree.heading("gender", text="Giới tính")
        self.tree.heading("avatar", text="Ảnh đại diện")

        # Định dạng width cột, căn giữa cho 1 số cột
        self.tree.column("username", width=120)
        self.tree.column("role", width=80, anchor="center")
        self.tree.column("name", width=150)
        self.tree.column("dob", width=90, anchor="center")
        self.tree.column("phone", width=100)
        self.tree.column("email", width=140)
        self.tree.column("address", width=200)
        self.tree.column("gender", width=80, anchor="center")
        self.tree.column("avatar", width=150)

        self.tree.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        self.refresh()

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for u in self.storage.all():
            self.tree.insert("", tk.END, iid=u["id"], values=(
                u.get("username",""),
                u.get("role",""),
                u.get("name",""),
                u.get("dob",""),
                u.get("phone",""),
                u.get("email",""),
                u.get("address",""),
                u.get("gender",""),
                u.get("avatar",""),
            ))

    def add_user(self):
        UserDialog(self, "Tạo tài khoản", on_submit=self._add_user_submit)

    def _add_user_submit(self, user_data, pw):
        if any(u["username"] == user_data["username"] for u in self.storage.all()):
            messagebox.showerror("Lỗi", "Tên đăng nhập đã tồn tại")
            return
        now_iso = datetime.now().isoformat(timespec="seconds")
        self.storage.create({
            "id": str(uuid.uuid4()),
            "username": user_data["username"],
            "password_hash": hash_password(pw),
            "role": user_data["role"],
            "name": user_data["name"],
            "dob": user_data["dob"],
            "phone": user_data["phone"],
            "email": user_data["email"],
            "address": user_data["address"],
            "gender": user_data["gender"],
            "avatar": user_data["avatar"],
            "created_at": now_iso,
            "updated_at": now_iso,
            "last_login": "",
        })
        self.refresh()

    def edit_user(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showerror("Lỗi", "Chưa chọn người dùng để sửa")
            return
        _id = sel[0]
        user = self.storage.get_by_id(_id)
        UserDialog(
            self,
            title="Sửa thông tin người dùng",
            username_default=user.get("username",""),
            role_default=user.get("role","staff"),
            name_default=user.get("name",""),
            dob_default=user.get("dob", None),
            phone_default=user.get("phone",""),
            email_default=user.get("email",""),
            address_default=user.get("address",""),
            gender_default=user.get("gender","Nam"),
            avatar_default=user.get("avatar",""),
            disable_username=True,
            ask_password=False,
            on_submit=lambda user_data, pw: self._edit_user_submit(_id, user_data)
        )

    def _edit_user_submit(self, _id, user_data):
        patch = {
            "role": user_data["role"],
            "name": user_data["name"],
            "dob": user_data["dob"],
            "phone": user_data["phone"],
            "email": user_data["email"],
            "address": user_data["address"],
            "gender": user_data["gender"],
            "avatar": user_data["avatar"],
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        self.storage.update(_id, patch)
        self.refresh()

    def delete_user(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showerror("Lỗi", "Chưa chọn người dùng để xóa")
            return
        _id = sel[0]
        if _id == self.current_user["id"]:
            messagebox.showerror("Lỗi", "Không thể xóa chính bạn")
            return
        if messagebox.askyesno("Xác nhận", "Xóa người dùng này?"):
            self.storage.delete(_id)
            self.refresh()



class UserDialog(tk.Toplevel):
    def __init__(
        self, master, title, on_submit,
        username_default="", role_default="staff",
        name_default="", dob_default=None,
        phone_default="", email_default="", address_default="",
        gender_default="Nam", avatar_default="",
        disable_username=False, ask_password=True
    ):
        super().__init__(master)
        self.title(title)
        self.grab_set()
        self.resizable(False, False)
        self.on_submit = on_submit

        padx = 18
        pady = 6

        # Username
        ttk.Label(self, text="Tên đăng nhập:", font=("Arial", 10)).pack(anchor="w", padx=padx, pady=(pady,2))
        self.e_user = ttk.Entry(self, font=("Arial", 11))
        self.e_user.insert(0, username_default)
        self.e_user.configure(state=tk.DISABLED if disable_username else tk.NORMAL)
        self.e_user.pack(padx=padx, fill="x")

        # Name (max 50 char)
        ttk.Label(self, text="Tên (max 50 ký tự):", font=("Arial", 10)).pack(anchor="w", padx=padx, pady=(pady,2))
        self.e_name = ttk.Entry(self, font=("Arial", 11))
        self.e_name.insert(0, name_default)
        self.e_name.pack(padx=padx, fill="x")

        # DOB calendar
        from tkcalendar import DateEntry
        ttk.Label(self, text="Ngày sinh:", font=("Arial", 10)).pack(anchor="w", padx=padx, pady=(pady,2))
        self.e_dob = DateEntry(self, date_pattern="yyyy-mm-dd")
        if dob_default:
            try:
                self.e_dob.set_date(dob_default)
            except Exception:
                pass
        self.e_dob.pack(padx=padx, fill="x")

        # Phone
        ttk.Label(self, text="Số điện thoại:", font=("Arial", 10)).pack(anchor="w", padx=padx, pady=(pady,2))
        self.e_phone = ttk.Entry(self, font=("Arial", 11))
        self.e_phone.insert(0, phone_default)
        self.e_phone.pack(padx=padx, fill="x")

        # Email
        ttk.Label(self, text="Email:", font=("Arial", 10)).pack(anchor="w", padx=padx, pady=(pady,2))
        self.e_email = ttk.Entry(self, font=("Arial", 11))
        self.e_email.insert(0, email_default)
        self.e_email.pack(padx=padx, fill="x")

        # Address (max 255 char)
        ttk.Label(self, text="Địa chỉ (max 255 ký tự):", font=("Arial", 10)).pack(anchor="w", padx=padx, pady=(pady,2))
        self.e_address = ttk.Entry(self, font=("Arial", 11))
        self.e_address.insert(0, address_default)
        self.e_address.pack(padx=padx, fill="x")

        # Gender (radio)
        ttk.Label(self, text="Giới tính:", font=("Arial", 10)).pack(anchor="w", padx=padx, pady=(pady,0))
        self.gender_var = tk.StringVar(value=gender_default)
        gender_frame = ttk.Frame(self)
        gender_frame.pack(anchor="w", padx=padx, pady=(0,pady))
        for g in GENDERS:
            ttk.Radiobutton(gender_frame, text=g, value=g, variable=self.gender_var).pack(side=tk.LEFT, padx=4)

        # Role combobox
        ttk.Label(self, text="Phân quyền:", font=("Arial", 10)).pack(anchor="w", padx=padx, pady=(pady,2))
        self.c_role = ttk.Combobox(self, values=ROLES, state="readonly", font=("Arial", 11))
        self.c_role.set(role_default)
        self.c_role.pack(padx=padx, fill="x")

        # Avatar (string path)
        ttk.Label(self, text="Ảnh đại diện (đường dẫn):", font=("Arial", 10)).pack(anchor="w", padx=padx, pady=(pady,2))
        self.e_avatar = ttk.Entry(self, font=("Arial", 11))
        self.e_avatar.insert(0, avatar_default)
        self.e_avatar.pack(padx=padx, fill="x")

        # Password
        self.pw_value = tk.StringVar()
        if ask_password:
            ttk.Label(self, text="Mật khẩu:", font=("Arial", 10)).pack(anchor="w", padx=padx, pady=(pady,2))
            self.e_pass = ttk.Entry(self, font=("Arial", 11), textvariable=self.pw_value, show="*")
            self.e_pass.pack(padx=padx, fill="x")
        else:
            self.e_pass = None

        ttk.Button(self, text="Lưu", command=self._submit).pack(pady=12)

    def _submit(self):
        username = self.e_user.get().strip()
        name = self.e_name.get().strip()
        dob = self.e_dob.get_date()
        phone = self.e_phone.get().strip()
        email = self.e_email.get().strip()
        address = self.e_address.get().strip()
        gender = self.gender_var.get()
        role = self.c_role.get()
        avatar = self.e_avatar.get().strip()
        pw = self.e_pass.get() if self.e_pass else None

        print(f"DEBUG: pw = '{pw}'")  # Thêm dòng này để kiểm tra

        # Validate length
        if len(name) > 50:
            messagebox.showerror("Lỗi", "Tên không được vượt quá 50 ký tự")
            return
        if len(address) > 255:
            messagebox.showerror("Lỗi", "Địa chỉ không được vượt quá 255 ký tự")
            return
        if not username:
            messagebox.showerror("Lỗi", "Tên đăng nhập không được để trống")
            return
        if not role:
            messagebox.showerror("Lỗi", "Chọn phân quyền (Role)")
            return
        if self.e_pass and not pw:
            messagebox.showerror("Lỗi", "Nhập mật khẩu!")
            return

        user_data = {
            "username": username,
            "name": name,
            "dob": dob.isoformat(),
            "phone": phone,
            "email": email,
            "address": address,
            "gender": gender,
            "role": role,
            "avatar": avatar,
        }
        self.on_submit(user_data, pw)
        self.destroy()
