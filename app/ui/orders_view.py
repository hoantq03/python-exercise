import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry


class OrdersView(ttk.Frame):
    """Giao diện nâng cao để xem và quản lý lịch sử đơn hàng."""

    def __init__(self, master, order_service, customer_service, product_service, current_user, can_edit: bool,
                 initial_customer_id=None):
        super().__init__(master)
        self.order_service = order_service
        self.customer_service = customer_service
        self.product_service = product_service
        self.current_user = current_user
        self.can_edit = can_edit
        self.initial_customer_id = initial_customer_id

        # Biến cho các bộ lọc
        self.search_kw = tk.StringVar()
        self.sort_var = tk.StringVar(value="Ngày tạo (mới nhất)")

        self._search_timer = None

        # New: Sorting state for columns
        self.sort_column = None
        self.sort_direction = {}  # Stores 'asc', 'desc', or '' for each column

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

        # ---SỬ DỤNG DateEntry ---
        ttk.Label(toolbar, text="Từ ngày:").pack(side=tk.LEFT, padx=(5, 2))
        self.from_date_entry = DateEntry(
            toolbar, width=12, background='darkblue', foreground='white',
            borderwidth=2, date_pattern='y-mm-dd', locale='en_US'
        )
        self.from_date_entry.pack(side=tk.LEFT)
        self.from_date_entry.delete(0, "end")
        ttk.Button(toolbar, text="X", width=2, command=lambda: self.from_date_entry.delete(0, "end")).pack(side=tk.LEFT)

        ttk.Label(toolbar, text="Đến ngày:").pack(side=tk.LEFT, padx=(10, 2))
        self.to_date_entry = DateEntry(
            toolbar, width=12, background='darkblue', foreground='white',
            borderwidth=2, date_pattern='y-mm-dd', locale='en_US'
        )
        self.to_date_entry.pack(side=tk.LEFT)
        self.to_date_entry.delete(0, "end")
        ttk.Button(toolbar, text="X", width=2, command=lambda: self.to_date_entry.delete(0, "end")).pack(side=tk.LEFT,
                                                                                                         padx=(0, 10))

        # Sắp xếp (Existing dropdown, can be removed if column sorting is primary)
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

        # Treeview
        tree_frame = ttk.Frame(self)
        tree_frame.pack(expand=True, fill=tk.BOTH, pady=5)
        self.columns_info = {  # Store column and corresponding data key
            "customer_name": {"heading": "Khách hàng", "data_key": "customer_info.name"},
            "total_amount": {"heading": "Tổng tiền", "data_key": "total_amount"},
            "status": {"heading": "Trạng thái", "data_key": "status"},
            "order_date": {"heading": "Ngày tạo", "data_key": "order_date"},
            "user_id": {"heading": "Nhân viên tạo", "data_key": "user_id"},
        }
        columns = list(self.columns_info.keys())
        headings = [info["heading"] for info in self.columns_info.values()]

        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

        for col, head in zip(columns, headings):
            self.tree.heading(col, text=head, command=lambda c=col: self._sort_column(c))
            self.sort_direction[col] = ''  # Initialize sort direction for each column

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _bind_events(self):
        """Gán sự kiện cho các widget."""
        self.sort_var.trace_add('write', lambda *_: self.refresh())
        self.search_kw.trace_add('write', lambda *_: self._debounced_refresh())

        self.from_date_entry.bind("<<DateEntrySelected>>", lambda *_: self.refresh())
        self.to_date_entry.bind("<<DateEntrySelected>>", lambda *_: self.refresh())

        self.tree.bind("<Double-1>", lambda event: self._show_selected_detail())

    def _debounced_refresh(self):
        if self._search_timer: self.after_cancel(self._search_timer)
        self._search_timer = self.after(500, self.refresh)

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

        # Reset all other columns to default direction
        for c in self.sort_direction:
            if c != col:
                self.sort_direction[c] = ''
                self.tree.heading(c, text=self.columns_info[c]["heading"])

        self.sort_column = col
        self.sort_direction[col] = new_direction
        self.refresh()

    def refresh(self):
        all_orders = self.order_service.list_orders()
        kw = self.search_kw.get().lower()

        if self.initial_customer_id:
            all_orders = [o for o in all_orders if o.get("customer_id") == self.initial_customer_id]

        try:
            from_date_str = self.from_date_entry.get_date().strftime('%Y-%m-%d')
        except (AttributeError, ValueError):
            from_date_str = None

        try:
            to_date_str = self.to_date_entry.get_date().strftime('%Y-%m-%d')
        except (AttributeError, ValueError):
            to_date_str = None

        # Lọc dữ liệu
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

        # Sắp xếp (prioritize column header sorting if active)
        if self.sort_column and self.sort_direction[self.sort_column]:
            sort_key_path = self.columns_info[self.sort_column]["data_key"]
            reverse_sort = (self.sort_direction[self.sort_column] == 'desc')

            if "." in sort_key_path:
                key1, key2 = sort_key_path.split('.')
                filtered_orders.sort(key=lambda o: str(o.get(key1, {}).get(key2, "")).lower(), reverse=reverse_sort)
            else:
                filtered_orders.sort(key=lambda o: o.get(sort_key_path, 0), reverse=reverse_sort)

            # Update heading with arrow
            arrow = ""
            if self.sort_direction[self.sort_column] == 'asc':
                arrow = " \u25b2"  # Up arrow
            elif self.sort_direction[self.sort_column] == 'desc':
                arrow = " \u25bc"  # Down arrow
            self.tree.heading(self.sort_column, text=self.columns_info[self.sort_column]["heading"] + arrow)
        else:  # Fallback to existing sort_var if no column sorting
            sort_map = {
                "Ngày tạo (mới nhất)": ("order_date", True), "Ngày tạo (cũ nhất)": ("order_date", False),
                "Giá trị (cao-thấp)": ("total_amount", True), "Giá trị (thấp-cao)": ("total_amount", False),
                "Tên khách hàng (A-Z)": ("customer_info.name", False),
                "Tên khách hàng (Z-A)": ("customer_info.name", True),
            }
            sort_field, reverse = sort_map.get(self.sort_var.get(), ("order_date", True))
            if "." in sort_field:
                key1, key2 = sort_field.split('.')
                filtered_orders.sort(key=lambda o: str(o.get(key1, {}).get(key2, "")).lower(), reverse=reverse)
            else:
                filtered_orders.sort(key=lambda o: o.get(sort_field, 0), reverse=reverse)

            # Clear all column arrows if sorting is by dropdown
            for col in self.columns_info:
                self.tree.heading(col, text=self.columns_info[col]["heading"])

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


class OrderDetailView(tk.Toplevel):

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

