import tkinter as tk
from tkinter import ttk, messagebox


class CustomerPurchaseHistoryView(tk.Toplevel):
    """
    Cửa sổ Toplevel mới, chuyên hiển thị lịch sử mua hàng
    của một khách hàng cụ thể.
    """

    def __init__(self, master, order_service, customer_data: dict):
        super().__init__(master)
        self.order_service = order_service
        self.customer_data = customer_data

        customer_name = self.customer_data.get('name', 'N/A')
        self.title(f"Lịch sử mua hàng của: {customer_name}")
        self.geometry("900x500")
        self.grab_set()

        self._create_widgets()
        self.refresh()

    def _create_widgets(self):
        """Tạo TreeView để hiển thị danh sách đơn hàng."""
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("order_date", "total_amount", "status", "order_id")
        headings = ("Ngày đặt hàng", "Tổng tiền", "Trạng thái", "Mã đơn hàng")

        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings")
        for col, head in zip(columns, headings):
            self.tree.heading(col, text=head)

        # Thêm scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def refresh(self):
        """Lấy tất cả đơn hàng, lọc theo SĐT của khách hàng và hiển thị."""
        all_orders = self.order_service.list_orders()
        customer_phone = self.customer_data.get("phone")

        if not customer_phone:
            messagebox.showerror("Lỗi dữ liệu", "Khách hàng không có số điện thoại.", parent=self)
            self.destroy()
            return

        # Lọc các đơn hàng thuộc về khách hàng này
        customer_orders = [
            order for order in all_orders
            if order.get("customer_info", {}).get("phone") == customer_phone
        ]

        # Sắp xếp theo ngày mới nhất
        customer_orders.sort(key=lambda o: o.get("order_date", ""), reverse=True)

        # Hiển thị lên Treeview
        self.tree.delete(*self.tree.get_children())
        for order in customer_orders:
            values = (
                order.get("order_date"),
                f"{order.get('total_amount', 0):,.0f} ₫",
                order.get("status", "N/A"),
                order.get("id")
            )
            self.tree.insert("", tk.END, values=values)


class CustomersView(ttk.Frame):
    """View quản lý khách hàng, đã cập nhật tính năng xem lịch sử."""

    # --- Sửa __init__ để nhận order_service ---
    def __init__(self, master, customer_service, order_service, can_edit: bool):
        super().__init__(master)
        self.customer_service = customer_service
        self.order_service = order_service  # Service mới được thêm vào
        self.can_edit = can_edit

        self._create_widgets()
        self.refresh()

    def _create_widgets(self):
        toolbar = ttk.Frame(self, padding=5)
        toolbar.pack(fill=tk.X)
        ttk.Label(toolbar, text="Tìm kiếm (tên hoặc SĐT):").pack(side=tk.LEFT)
        self.search_entry = ttk.Entry(toolbar)
        self.search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh())

        self.history_button = ttk.Button(
            toolbar, text="Xem Lịch sử Mua hàng",
            command=self._show_purchase_history, state="disabled"
        )
        self.history_button.pack(side=tk.RIGHT, padx=5)

        self.tree = ttk.Treeview(self, columns=("name", "phone", "email", "address"), show="headings")
        self.tree.heading("name", text="Họ và Tên")
        self.tree.heading("phone", text="Số điện thoại")
        self.tree.heading("email", text="Email")
        self.tree.heading("address", text="Địa chỉ")
        self.tree.pack(expand=True, fill=tk.BOTH, pady=5)
        self.tree.bind("<<TreeviewSelect>>", self._on_customer_select)

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        keyword = self.search_entry.get().lower()
        all_customers = self.customer_service.list()

        for customer in all_customers:
            if keyword in customer.get("name", "").lower() or keyword in customer.get("phone", ""):
                values = (
                    customer.get("name"), customer.get("phone"),
                    customer.get("email"), customer.get("address")
                )
                self.tree.insert("", tk.END, iid=customer["id"], values=values)

        self._on_customer_select()

    def _on_customer_select(self, event=None):
        if self.tree.selection():
            self.history_button.config(state="normal")
        else:
            self.history_button.config(state="disabled")

    def _show_purchase_history(self):
        """
        Sửa lại để lấy thông tin khách hàng và mở cửa sổ
        CustomerPurchaseHistoryView.
        """
        selected_items = self.tree.selection()
        if not selected_items:
            return

        customer_id = selected_items[0]
        item_values = self.tree.item(customer_id, "values")

        # Tạo một dictionary chứa thông tin khách hàng từ dòng đã chọn
        customer_data = {
            "id": customer_id,
            "name": item_values[0],
            "phone": item_values[1],
            "email": item_values[2],
            "address": item_values[3],
        }

        # Gọi cửa sổ xem lịch sử
        CustomerPurchaseHistoryView(self, self.order_service, customer_data)
