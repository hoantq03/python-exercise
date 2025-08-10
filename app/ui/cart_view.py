import tkinter as tk
from tkinter import ttk, messagebox
from functools import partial


class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.bind_mousewheel()

    def bind_mousewheel(self):
        def _on_mousewheel(event): self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_to_mousewheel(event): self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_from_mousewheel(event): self.canvas.unbind_all("<MouseWheel>")

        self.bind('<Enter>', _bind_to_mousewheel)
        self.bind('<Leave>', _unbind_from_mousewheel)


class CartView(ttk.Frame):
    """Giao diện quản lý giỏ hàng và tạo đơn hàng."""

    def __init__(self, master, cart_service, order_service, customer_service, current_user):
        super().__init__(master)
        self.cart_service = cart_service
        self.order_service = order_service
        self.customer_service = customer_service
        self.current_user = current_user
        self.customer_entries = {}
        self._create_widgets()
        self.refresh()

    def _create_widgets(self):
        main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        main_pane.pack(fill=tk.BOTH, expand=True)
        left_frame = ttk.Frame(main_pane, width=600)
        self._create_cart_details_frame(left_frame)
        main_pane.add(left_frame, stretch="always")
        right_frame = ttk.Frame(main_pane, width=300)
        self._create_customer_info_frame(right_frame)
        main_pane.add(right_frame, stretch="never")

    def _create_cart_details_frame(self, parent):
        container = ttk.LabelFrame(parent, text="Chi tiết giỏ hàng", padding=10)
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.scroll_frame = ScrollableFrame(container)
        self.scroll_frame.pack(fill=tk.BOTH, expand=True)
        summary_frame = ttk.LabelFrame(parent, text="Tổng quan", padding=10)
        summary_frame.pack(fill=tk.X, padx=5, pady=5)
        self.lbl_total_items = ttk.Label(summary_frame, text="Tổng số sản phẩm: 0", font=("Arial", 10, "bold"))
        self.lbl_total_items.pack(anchor='w')
        self.lbl_total_price = ttk.Label(summary_frame, text="Tổng tiền: 0 ₫", font=("Arial", 12, "bold"),
                                         foreground="red")
        self.lbl_total_price.pack(anchor='w', pady=(5, 0))

    def _create_customer_info_frame(self, parent):
        container = ttk.LabelFrame(parent, text="Thông tin giao hàng", padding=15)
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        fields = {"name": "Họ và Tên", "phone": "Số điện thoại", "email": "Email", "address": "Địa chỉ giao hàng"}
        for key, label_text in fields.items():
            row_frame = ttk.Frame(container)
            row_frame.pack(fill=tk.X, pady=4)
            ttk.Label(row_frame, text=label_text + ":").pack(anchor='w')
            if key == "address":
                entry = tk.Text(row_frame, height=4, font=("Arial", 10))
            else:
                entry = ttk.Entry(row_frame, font=("Arial", 10))
            entry.pack(fill=tk.X)
            self.customer_entries[key] = entry
        create_order_btn = ttk.Button(container, text="✅ Tạo Đơn Hàng", command=self._create_order)
        create_order_btn.pack(fill=tk.X, pady=(20, 5), ipady=10)

    def refresh(self):
        self._clear_cart_items()
        cart = self.cart_service.get_cart()
        if not cart.items:
            self._show_empty_message()
        else:
            for i, item in enumerate(cart.items):
                self._create_cart_item_widget(item, i)
        total_items = cart.get_item_count()
        total_price = cart.get_total()
        self.lbl_total_items.config(text=f"Tổng số sản phẩm: {total_items}")
        self.lbl_total_price.config(text=f"Tổng tiền: {total_price:,.0f} ₫")

    def _clear_cart_items(self):
        for widget in self.scroll_frame.scrollable_frame.winfo_children():
            widget.destroy()

    def _show_empty_message(self):
        ttk.Label(self.scroll_frame.scrollable_frame, text="🛒\nGiỏ hàng của bạn đang trống.", font=("Arial", 14),
                  justify="center", foreground="#6c757d").pack(pady=50, expand=True)

    def _create_cart_item_widget(self, item, index):
        item_frame = ttk.Frame(self.scroll_frame.scrollable_frame, padding=10, relief="solid", borderwidth=1)
        item_frame.pack(fill=tk.X, pady=5, padx=5)
        item_frame.columnconfigure(0, weight=4)
        item_frame.columnconfigure(1, weight=2)
        item_frame.columnconfigure(2, weight=2)
        item_frame.columnconfigure(3, weight=2)
        item_frame.columnconfigure(4, weight=1)
        ttk.Label(item_frame, text=item.name, wraplength=300).grid(row=0, column=0, sticky="w", rowspan=2)
        ttk.Label(item_frame, text="Giá:").grid(row=0, column=1, sticky="w")
        ttk.Label(item_frame, text=f"{item.price:,.0f} ₫").grid(row=1, column=1, sticky="w")
        ttk.Label(item_frame, text="Số lượng:").grid(row=0, column=2, sticky="w")

        # 1. Tạo Spinbox mà không cần textvariable
        qty_spinbox = ttk.Spinbox(item_frame, from_=1, to=99, width=5)
        qty_spinbox.insert(0, str(item.quantity))  # Đặt giá trị ban đầu
        qty_spinbox.grid(row=1, column=2, sticky="w")

        # 2. Tạo một hàm callback duy nhất để xử lý mọi thay đổi
        #    partial giúp cố định các tham số cần thiết cho hàm callback
        update_callback = partial(self._update_quantity, item.item_id, qty_spinbox)

        # 3. Gán callback này cho cả 3 sự kiện
        qty_spinbox.config(command=update_callback)  # Sự kiện nhấn nút tăng/giảm
        qty_spinbox.bind("<Return>", lambda event: update_callback())  # Sự kiện nhấn Enter
        qty_spinbox.bind("<FocusOut>", lambda event: update_callback())  # Sự kiện click ra ngoài
        # --- KẾT THÚC PHẦN SỬA LỖI ---

        ttk.Label(item_frame, text="Thành tiền:").grid(row=0, column=3, sticky="w")
        subtotal = item.get_subtotal()
        ttk.Label(item_frame, text=f"{subtotal:,.0f} ₫", font=("Arial", 10, "bold")).grid(row=1, column=3, sticky="w")
        remove_btn = ttk.Button(item_frame, text="🗑️ Xóa", command=lambda: self._remove_item(item.item_id))
        remove_btn.grid(row=0, column=4, rowspan=2, sticky="e")

    # --- SỬA LỖI VÀ CẢI TIẾN TẠI ĐÂY ---
    def _update_quantity(self, item_id, spinbox_widget):
        """Cập nhật số lượng sản phẩm từ widget Spinbox."""
        # Lấy giá trị mới nhất từ chính widget
        new_quantity_str = spinbox_widget.get()
        try:
            new_quantity = int(new_quantity_str)
            if new_quantity > 0:
                print(f"Updating item {item_id} to quantity {new_quantity}")
                self.cart_service.update_item_quantity(item_id, new_quantity)
                self.refresh()
            else:  # Nếu người dùng nhập số <= 0, coi như xóa
                spinbox_widget.set(1)  # Đặt lại giá trị spinbox về 1 để tránh lỗi
                self._remove_item(item_id)
        except (ValueError, TypeError):
            # Không làm gì nếu giá trị không hợp lệ (ví dụ: người dùng đang gõ chữ)
            pass

    def _remove_item(self, item_id):
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa sản phẩm này khỏi giỏ hàng?"):
            self.cart_service.remove_item(item_id)
            self.refresh()

    def _create_order(self):
        customer_info = {key: entry.get("1.0", "end-1c") if isinstance(entry, tk.Text) else entry.get() for key, entry
                         in self.customer_entries.items()}
        if not customer_info['name'] or not customer_info['phone']:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập Họ tên và Số điện thoại.", parent=self)
            return
        cart = self.cart_service.get_cart()
        if not cart.items:
            messagebox.showwarning("Giỏ hàng trống", "Vui lòng thêm sản phẩm vào giỏ trước khi tạo đơn hàng.",
                                   parent=self)
            return

        try:
            # Lấy customer_id trước khi tạo payload
            customer_id = self.customer_service.find_or_create_customer(customer_info)

            order_payload = {
                "customer_id": customer_id,
                "customer_info": customer_info,
                "items": [item.__dict__ for item in cart.items],
                "total_amount": cart.get_total(),
                "user_id": self.current_user.get("id")
            }

            # Gọi OrderService để tạo đơn hàng
            new_order = self.order_service.create_order(order_payload)

            messagebox.showinfo("Thành công", f"Đã tạo thành công đơn hàng #{new_order.get('id')}", parent=self)

            self.cart_service.clear_cart()
            for entry in self.customer_entries.values():
                entry.delete("1.0", "end") if isinstance(entry, tk.Text) else entry.delete(0, "end")

            self.refresh()
        except Exception as e:
            messagebox.showerror("Lỗi tạo đơn hàng", f"Đã có lỗi xảy ra: {e}", parent=self)
            import traceback
            traceback.print_exc()
