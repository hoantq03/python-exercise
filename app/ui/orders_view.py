import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

class OrdersView(ttk.Frame):
    def __init__(self, master, order_service, customer_service, product_service, current_user, can_edit: bool):
        super().__init__(master)
        self.order_service = order_service
        self.customer_service = customer_service
        self.product_service = product_service
        self.current_user = current_user
        self.can_edit = can_edit

        top = ttk.Frame(self)
        top.pack(fill=tk.X)
        self.e_kw = ttk.Entry(top)
        self.e_kw.pack(side=tk.LEFT, padx=4, pady=4)
        ttk.Button(top, text="Tìm", command=self.refresh).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Làm mới", command=self.refresh).pack(side=tk.LEFT, padx=4)

        if self.can_edit:
            ttk.Button(top, text="Tạo đơn", command=self.create_order).pack(side=tk.LEFT, padx=4)
            ttk.Button(top, text="Thanh toán (PAID)", command=self.mark_paid).pack(side=tk.LEFT, padx=4)
            ttk.Button(top, text="Hủy (CANCELED)", command=self.mark_canceled).pack(side=tk.LEFT, padx=4)
            ttk.Button(top, text="Xóa", command=self.delete).pack(side=tk.LEFT, padx=4)

        self.tree = ttk.Treeview(self, columns=("customer_id","total","status","created_at","created_by"), show="headings")
        for c, t in zip(("customer_id","total","status","created_at","created_by"), ("Khách hàng","Tổng","Trạng thái","Tạo lúc","Người tạo")):
            self.tree.heading(c, text=t)
        self.tree.pack(expand=True, fill=tk.BOTH)
        self.refresh()

    def refresh(self):
        kw = self.e_kw.get().strip()
        for i in self.tree.get_children():
            self.tree.delete(i)
        for o in self.order_service.list(keyword=kw):
            self.tree.insert("", tk.END, iid=o["id"], values=(o["customer_id"], o["total"], o["status"], o["created_at"], o["created_by"]))

    def create_order(self):
        customers = self.customer_service.list()
        if not customers:
            messagebox.showerror("Lỗi","Chưa có khách hàng")
            return
        cust_id = simpledialog.askstring("Khách hàng", f"Nhập customer_id ({', '.join([c['id'][:8] for c in customers])}...):")
        if not cust_id: return
        # nhập items nhanh: product_id:qty;product_id:qty
        raw = simpledialog.askstring("Items", "Nhập dạng product_id:qty; ...")
        if not raw: return
        items = []
        try:
            for seg in raw.split(";"):
                seg = seg.strip()
                if not seg: continue
                pid, q = seg.split(":")
                items.append({"product_id": pid.strip(), "qty": int(q)})
            order = self.order_service.create(cust_id, items, self.current_user["username"])
            messagebox.showinfo("OK", f"Tạo đơn thành công: {order['id']}")
            self.refresh()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def mark_paid(self):
        sel = self.tree.selection()
        if not sel: return
        oid = sel[0]
        try:
            self.order_service.fulfill_and_update_stock(oid)
            self.refresh()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def mark_canceled(self):
        sel = self.tree.selection()
        if not sel: return
        oid = sel[0]
        self.order_service.update_status(oid, "CANCELED")
        self.refresh()

    def delete(self):
        sel = self.tree.selection()
        if not sel: return
        oid = sel[0]
        if messagebox.askyesno("Xác nhận","Xóa đơn hàng?"):
            self.order_service.delete(oid)
            self.refresh()
