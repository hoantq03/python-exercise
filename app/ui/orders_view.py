import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from functools import partial

# --- THÊM IMPORT MỚI ---
from tkcalendar import DateEntry


# --- LỚP ORDERSVIEW ĐÃ CẬP NHẬT ---
class OrdersView(ttk.Frame):
    """Giao diện nâng cao để xem và quản lý lịch sử đơn hàng."""

    def __init__(self, master, order_service, customer_service, product_service, current_user, can_edit: bool, initial_customer_id=None):
        super().__init__(master)
        self.order_service = order_service
        self.customer_service = customer_service
        self.product_service = product_service
        self.current_user = current_user
        self.can_edit = can_edit
        self.initial_customer_id = initial_customer_id

        # Biến cho các bộ lọc
        self.search_kw = tk.StringVar()
        # Không cần StringVar cho date nữa vì DateEntry tự quản lý
        self.sort_var = tk.StringVar(value="Ngày tạo (mới nhất)")

        # Timer để tối ưu hóa việc tìm kiếm (debouncing)
        self._search_timer = None

        self._create_widgets()
        self._bind_events()
        if self.initial_customer_id:
            # tìm widget search và disable nó
            search_entry_widget = self.nametowidget(self.search_kw.get())  # Cần đặt tên cho widget
            search_entry_widget.config(state="disabled")
            search_entry_widget.insert(0, "Đang lọc theo khách hàng cụ thể")

        self.refresh()

    def _create_widgets(self):
        """Tạo các thành phần giao diện: toolbar và treeview."""
        toolbar = ttk.Frame(self, padding=5)
        toolbar.pack(fill=tk.X, side=tk.TOP)

        # Tìm kiếm
        ttk.Label(toolbar, text="Tìm tên KH:").pack(side=tk.LEFT, padx=(0, 2))
        ttk.Entry(toolbar, textvariable=self.search_kw, width=20).pack(side=tk.LEFT, padx=(0, 10))

        # --- THAY ĐỔI: SỬ DỤNG DateEntry ---
        ttk.Label(toolbar, text="Từ ngày:").pack(side=tk.LEFT, padx=(5, 2))
        self.from_date_entry = DateEntry(
            toolbar, width=12, background='darkblue', foreground='white',
            borderwidth=2, date_pattern='y-mm-dd', locale='en_US'
        )
        self.from_date_entry.pack(side=tk.LEFT)
        # Xóa ngày ban đầu để không lọc mặc định
        self.from_date_entry.delete(0, "end")
        ttk.Button(toolbar, text="X", width=2, command=lambda: self.from_date_entry.delete(0, "end")).pack(side=tk.LEFT)

        ttk.Label(toolbar, text="Đến ngày:").pack(side=tk.LEFT, padx=(10, 2))
        self.to_date_entry = DateEntry(
            toolbar, width=12, background='darkblue', foreground='white',
            borderwidth=2, date_pattern='y-mm-dd', locale='en_US'
        )
        self.to_date_entry.pack(side=tk.LEFT)
        # Xóa ngày ban đầu để không lọc mặc định
        self.to_date_entry.delete(0, "end")
        ttk.Button(toolbar, text="X", width=2, command=lambda: self.to_date_entry.delete(0, "end")).pack(side=tk.LEFT,
                                                                                                         padx=(0, 10))

        # Sắp xếp
        ttk.Label(toolbar, text="Sắp xếp:").pack(side=tk.LEFT, padx=(5, 2))
        sort_options = {
            "Ngày tạo (mới nhất)": "date_desc", "Ngày tạo (cũ nhất)": "date_asc",
            "Giá trị (cao-thấp)": "total_desc", "Giá trị (thấp-cao)": "total_asc",
            "Tên khách hàng (A-Z)": "name_az", "Tên khách hàng (Z-A)": "name_za",
        }
        ttk.Combobox(
            toolbar, textvariable=self.sort_var, values=list(sort_options.keys()),
            width=20, state="readonly"
        ).pack(side=tk.LEFT, padx=(0, 10))

        # Nút hành động
        ttk.Button(toolbar, text="🔄 Làm mới", command=self.refresh).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="👁️ Xem chi tiết", command=self._show_selected_detail).pack(side=tk.LEFT, padx=5)

        # Treeview (giữ nguyên)
        tree_frame = ttk.Frame(self)
        tree_frame.pack(expand=True, fill=tk.BOTH, pady=5)
        columns = ("customer_name", "total_amount", "status", "order_date", "user_id")
        headings = ("Khách hàng", "Tổng tiền", "Trạng thái", "Ngày tạo", "Nhân viên tạo")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        for col, head in zip(columns, headings): self.tree.heading(col, text=head)
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _bind_events(self):
        """Gán sự kiện cho các widget."""
        self.sort_var.trace_add('write', lambda *_: self.refresh())
        self.search_kw.trace_add('write', lambda *_: self._debounced_refresh())

        # --- THAY ĐỔI: Gán sự kiện cho DateEntry ---
        self.from_date_entry.bind("<<DateEntrySelected>>", lambda *_: self.refresh())
        self.to_date_entry.bind("<<DateEntrySelected>>", lambda *_: self.refresh())

        self.tree.bind("<Double-1>", lambda event: self._show_selected_detail())

    def _debounced_refresh(self):
        if self._search_timer: self.after_cancel(self._search_timer)
        self._search_timer = self.after(500, self.refresh)

    def refresh(self):
        all_orders = self.order_service.list_orders()
        kw = self.search_kw.get().lower()

        if self.initial_customer_id:
            all_orders = [o for o in all_orders if o.get("customer_id") == self.initial_customer_id]

        # --- THAY ĐỔI: Lấy ngày từ DateEntry ---
        try:
            from_date_str = self.from_date_entry.get_date().strftime('%Y-%m-%d')
        except (AttributeError, ValueError):
            from_date_str = None  # Nếu ô trống hoặc không hợp lệ

        try:
            to_date_str = self.to_date_entry.get_date().strftime('%Y-%m-%d')
        except (AttributeError, ValueError):
            to_date_str = None  # Nếu ô trống hoặc không hợp lệ

        # Lọc dữ liệu (logic giữ nguyên nhưng an toàn hơn)
        filtered_orders = []
        for order in all_orders:
            customer_name = order.get("customer_info", {}).get("name", "").lower()
            if kw and kw not in customer_name:
                continue
            order_date_str = order.get("order_date", "")[:10]
            if from_date_str and order_date_str < from_date_str:
                continue
            if to_date_str and order_date_str > to_date_str:
                continue
            filtered_orders.append(order)

        # Sắp xếp và hiển thị (giữ nguyên logic)
        sort_map = {
            "Ngày tạo (mới nhất)": ("order_date", True), "Ngày tạo (cũ nhất)": ("order_date", False),
            "Giá trị (cao-thấp)": ("total_amount", True), "Giá trị (thấp-cao)": ("total_amount", False),
            "Tên khách hàng (A-Z)": ("customer_info.name", False), "Tên khách hàng (Z-A)": ("customer_info.name", True),
        }
        sort_field, reverse = sort_map.get(self.sort_var.get(), ("order_date", True))
        if "." in sort_field:
            key1, key2 = sort_field.split('.')
            filtered_orders.sort(key=lambda o: str(o.get(key1, {}).get(key2, "")).lower(), reverse=reverse)
        else:
            filtered_orders.sort(key=lambda o: o.get(sort_field, 0), reverse=reverse)

        self.tree.delete(*self.tree.get_children())
        for order in filtered_orders:
            values = (
                order.get("customer_info", {}).get("name", "N/A"), f"{order.get('total_amount', 0):,.0f} ₫",
                order.get("status", "N/A"), order.get("order_date", "N/A"),
                order.get("user_id", "N/A")[:8] + "..."
            )
            self.tree.insert("", tk.END, iid=order["id"], values=values)

    def _show_selected_detail(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("Thông báo", "Vui lòng chọn một đơn hàng để xem.", parent=self)
            return
        order_id = selected_items[0]
        order_data = self.order_service.get_order_by_id(order_id)
        if order_data:
            OrderDetailView(self, order_data)
        else:
            messagebox.showerror("Lỗi", f"Không tìm thấy dữ liệu cho đơn hàng ID: {order_id}", parent=self)


# --- Lớp OrderDetailView giữ nguyên, không cần thay đổi ---
class OrderDetailView(tk.Toplevel):
    # ... (Giữ nguyên toàn bộ code của OrderDetailView)
    def __init__(self, master, order_data: dict):
        super().__init__(master)
        self.order_data = order_data

        self.title(f"Chi tiết đơn hàng #{order_data.get('id', '')[:8]}...")
        self.geometry("700x500")
        self.grab_set()

        self._create_widgets()

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        info_frame = ttk.LabelFrame(main_frame, text="Thông tin chung", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        self._add_info_row(info_frame, "Mã đơn hàng:", self.order_data.get("id"))
        self._add_info_row(info_frame, "Ngày đặt:", self.order_data.get("order_date"))
        self._add_info_row(info_frame, "Trạng thái:", self.order_data.get("status").upper(),
                           "red" if self.order_data.get("status") != "completed" else "green")
        self._add_info_row(info_frame, "Tổng tiền:", f"{self.order_data.get('total_amount', 0):,.0f} ₫")

        cust_frame = ttk.LabelFrame(main_frame, text="Thông tin khách hàng", padding=10)
        cust_frame.pack(fill=tk.X, pady=(0, 10))
        cust_info = self.order_data.get("customer_info", {})
        self._add_info_row(cust_frame, "Họ tên:", cust_info.get("name"))
        self._add_info_row(cust_frame, "Điện thoại:", cust_info.get("phone"))
        self._add_info_row(cust_frame, "Email:", cust_info.get("email"))
        self._add_info_row(cust_frame, "Địa chỉ:", cust_info.get("address"))

        items_frame = ttk.LabelFrame(main_frame, text="Danh sách sản phẩm", padding=10)
        items_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("name", "price", "quantity", "subtotal")
        headings = ("Tên sản phẩm", "Đơn giá", "Số lượng", "Thành tiền")

        tree = ttk.Treeview(items_frame, columns=columns, show="headings")
        for col, head in zip(columns, headings):
            tree.heading(col, text=head)
            tree.column(col, width=150)
        tree.pack(fill=tk.BOTH, expand=True)

        for item in self.order_data.get("items", []):
            subtotal = item.get("price", 0) * item.get("quantity", 0)
            values = (
                item.get("name"),
                f"{item.get('price', 0):,.0f} ₫",
                item.get("quantity"),
                f"{subtotal:,.0f} ₫"
            )
            tree.insert("", tk.END, values=values)

    def _add_info_row(self, parent, label_text, value_text, value_color=None):
        row_frame = ttk.Frame(parent)
        row_frame.pack(fill=tk.X, pady=2)
        label_widget = ttk.Label(row_frame, text=label_text, font=("Arial", 9, "bold"), width=15)
        label_widget.pack(side=tk.LEFT)
        ttk.Label(row_frame, text=value_text, foreground=value_color, wraplength=500).pack(side=tk.LEFT, padx=5)