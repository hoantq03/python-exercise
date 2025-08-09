import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

class CustomersView(ttk.Frame):
    def __init__(self, master, service, can_edit: bool):
        super().__init__(master)
        self.service = service
        self.can_edit = can_edit

        top = ttk.Frame(self)
        top.pack(fill=tk.X)
        self.e_kw = ttk.Entry(top)
        self.e_kw.pack(side=tk.LEFT, padx=4, pady=4)
        ttk.Button(top, text="Tìm", command=self.refresh).pack(side=tk.LEFT, padx=4)

        if self.can_edit:
            ttk.Button(top, text="Thêm", command=self.add).pack(side=tk.LEFT, padx=4)
            ttk.Button(top, text="Sửa", command=self.edit).pack(side=tk.LEFT, padx=4)
            ttk.Button(top, text="Xóa", command=self.delete).pack(side=tk.LEFT, padx=4)

        self.tree = ttk.Treeview(self, columns=("name","phone","email","address"), show="headings")
        for c, t in zip(("name","phone","email","address"), ("Tên","Điện thoại","Email","Địa chỉ")):
            self.tree.heading(c, text=t)
        self.tree.pack(expand=True, fill=tk.BOTH)
        self.refresh()

    def refresh(self):
        kw = self.e_kw.get().strip()
        for i in self.tree.get_children():
            self.tree.delete(i)
        for c in self.service.list(kw):
            self.tree.insert("", tk.END, iid=c["id"], values=(c["name"], c["phone"], c["email"], c["address"]))

    def add(self):
        payload = {}
        payload["name"] = simpledialog.askstring("Tên","Nhập tên:")
        if not payload["name"]: return
        payload["phone"] = simpledialog.askstring("Điện thoại","")
        payload["email"] = simpledialog.askstring("Email","")
        payload["address"] = simpledialog.askstring("Địa chỉ","")
        self.service.create(payload)
        self.refresh()

    def edit(self):
        sel = self.tree.selection()
        if not sel: return
        _id = sel[0]
        current = next(x for x in self.service.list() if x["id"] == _id)
        patch = {}
        for field, label in (("name","Tên"),("phone","Điện thoại"),("email","Email"),("address","Địa chỉ")):
            val = simpledialog.askstring(label, f"{label} (hiện tại: {current[field]}):")
            if val is not None and val != "":
                patch[field] = val
        if patch:
            self.service.update(_id, patch)
            self.refresh()

    def delete(self):
        sel = self.tree.selection()
        if not sel: return
        _id = sel[0]
        if messagebox.askyesno("Xác nhận","Xóa khách hàng?"):
            self.service.delete(_id)
            self.refresh()
