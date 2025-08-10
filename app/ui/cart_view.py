# Thêm vào file views.py hoặc file mới ví dụ: app/ui/cart_view.py

import tkinter as tk
from tkinter import ttk, messagebox
from functools import partial


# Giả định ScrollableFrame đã có trong file này hoặc được import
# (Code cho ScrollableFrame được đính kèm ở cuối nếu cần)

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
        """Tạo layout chính với 2 khung trái-phải."""
        # PanedWindow cho phép thay đổi kích thước 2 khung
        main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        main_pane.pack(fill=tk.BOTH, expand=True)

        # --- Khung bên trái: Chi tiết giỏ hàng ---
        left_frame = ttk.Frame(main_pane, width=600)
        self._create_cart_details_frame(left_frame)
        main_pane.add(left_frame, stretch="always")

        # --- Khung bên phải: Thông tin khách hàng ---
        right_frame = ttk.Frame(main_pane, width=300)
        self._create_customer_info_frame(right_frame)
        main_pane.add(right_frame, stretch="never")

    def _create_cart_details_frame(self, parent):
        """Tạo khung hiển thị danh sách sản phẩm trong giỏ."""
        container = ttk.LabelFrame(parent, text="Chi tiết giỏ hàng", padding=10)
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Frame chứa danh sách sản phẩm có thể cuộn
        self.scroll_frame = ScrollableFrame(container)
        self.scroll_frame.pack(fill=tk.BOTH, expand=True)

        # Frame tổng kết ở dưới
        summary_frame = ttk.LabelFrame(parent, text="Tổng quan", padding=10)
        summary_frame.pack(fill=tk.X, padx=5, pady=5)

        self.lbl_total_items = ttk.Label(summary_frame, text="Tổng số sản phẩm: 0", font=("Arial", 10, "bold"))
        self.lbl_total_items.pack(anchor='w')

        self.lbl_total_price = ttk.Label(summary_frame, text="Tổng tiền: 0 ₫", font=("Arial", 12, "bold"),
                                         foreground="red")
        self.lbl_total_price.pack(anchor='w', pady=(5, 0))

    def _create_customer_info_frame(self, parent):
        """Tạo khung nhập thông tin khách hàng và nút tạo đơn hàng."""
        container = ttk.LabelFrame(parent, text="Thông tin giao hàng", padding=15)
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        fields = {
            "name": "Họ và Tên",
            "phone": "Số điện thoại",
            "email": "Email",
            "address": "Địa chỉ giao hàng"
        }

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

        # Nút tạo đơn hàng
        create_order_btn = ttk.Button(container, text="✅ Tạo Đơn Hàng", command=self._create_order,
                                      style="Accent.TButton")
        create_order_btn.pack(fill=tk.X, pady=(20, 5), ipady=10)

    def refresh(self):
        """Tải lại dữ liệu giỏ hàng và cập nhật giao diện."""
        self._clear_cart_items()

        cart = self.cart_service.get_cart()

        if not cart.items:
            self._show_empty_message()
        else:
            for i, item in enumerate(cart.items):
                self._create_cart_item_widget(item, i)

        # Cập nhật thông tin tổng kết
        total_items = cart.get_item_count()
        total_price = cart.get_total()

        self.lbl_total_items.config(text=f"Tổng số sản phẩm: {total_items}")
        self.lbl_total_price.config(text=f"Tổng tiền: {total_price:,.0f} ₫")

    def _clear_cart_items(self):
        """Xóa các widget sản phẩm cũ khỏi view."""
        for widget in self.scroll_frame.scrollable_frame.winfo_children():
            widget.destroy()

    def _show_empty_message(self):
        """Hiển thị thông báo khi giỏ hàng trống."""
        ttk.Label(
            self.scroll_frame.scrollable_frame,
            text="🛒\nGiỏ hàng của bạn đang trống.",
            font=("Arial", 14),
            justify="center",
            foreground="#6c757d"
        ).pack(pady=50, expand=True)

    def _create_cart_item_widget(self, item, index):
        """Tạo widget cho một sản phẩm trong giỏ."""
        item_frame = ttk.Frame(self.scroll_frame.scrollable_frame, padding=10, relief="solid", borderwidth=1)
        item_frame.pack(fill=tk.X, pady=5, padx=5)

        # Cấu hình grid
        item_frame.columnconfigure(0, weight=4)  # Tên sản phẩm
        item_frame.columnconfigure(1, weight=2)  # Giá
        item_frame.columnconfigure(2, weight=2)  # Số lượng
        item_frame.columnconfigure(3, weight=2)  # Thành tiền
        item_frame.columnconfigure(4, weight=1)  # Nút xóa

        # Tên sản phẩm
        ttk.Label(item_frame, text=item.name, wraplength=300).grid(row=0, column=0, sticky="w", rowspan=2)

        # Giá
        ttk.Label(item_frame, text="Giá:").grid(row=0, column=1, sticky="w")
        ttk.Label(item_frame, text=f"{item.price:,.0f} ₫").grid(row=1, column=1, sticky="w")

        # Số lượng (dùng Spinbox để dễ dàng thay đổi)
        ttk.Label(item_frame, text="Số lượng:").grid(row=0, column=2, sticky="w")
        qty_var = tk.StringVar(value=str(item.quantity))
        qty_spinbox = ttk.Spinbox(
            item_frame, from_=1, to=99, width=5, textvariable=qty_var,
            command=lambda: self._update_quantity(item.item_id, qty_spinbox.get())
        )
        qty_spinbox.grid(row=1, column=2, sticky="w")

        # Thành tiền
        ttk.Label(item_frame, text="Thành tiền:").grid(row=0, column=3, sticky="w")
        subtotal = item.get_subtotal()
        ttk.Label(item_frame, text=f"{subtotal:,.0f} ₫", font=("Arial", 10, "bold")).grid(row=1, column=3, sticky="w")

        # Nút xóa
        remove_btn = ttk.Button(item_frame, text="🗑️ Xóa", command=lambda: self._remove_item(item.item_id))
        remove_btn.grid(row=0, column=4, rowspan=2, sticky="e")

    def _update_quantity(self, item_id, new_quantity_str):
        """Cập nhật số lượng sản phẩm và tải lại view."""
        try:
            new_quantity = int(new_quantity_str)
            if new_quantity > 0:
                self.cart_service.update_item_quantity(item_id, new_quantity)
                self.refresh()
        except (ValueError, TypeError):
            messagebox.showerror("Lỗi", "Số lượng không hợp lệ.", parent=self)

    def _remove_item(self, item_id):
        """Xóa sản phẩm khỏi giỏ hàng."""
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa sản phẩm này khỏi giỏ hàng?"):
            self.cart_service.remove_item(item_id)
            self.refresh()

    def _create_order(self):
        """Thu thập thông tin và gọi service để tạo đơn hàng."""
        # 1. Thu thập thông tin khách hàng từ form
        customer_info = {key: entry.get("1.0", "end-1c") if isinstance(entry, tk.Text) else entry.get()
                         for key, entry in self.customer_entries.items()}

        # 2. Validation cơ bản
        if not customer_info['name'] or not customer_info['phone']:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập Họ tên và Số điện thoại.", parent=self)
            return

        # 3. Lấy thông tin giỏ hàng
        cart = self.cart_service.get_cart()
        if not cart.items:
            messagebox.showwarning("Giỏ hàng trống", "Vui lòng thêm sản phẩm vào giỏ trước khi tạo đơn hàng.",
                                   parent=self)
            return

        customer_id = self.customer_service.find_or_create_customer(customer_info)

        # 4. Tạo payload cho đơn hàng (bạn có thể điều chỉnh cấu trúc này cho phù hợp với OrderService)
        order_payload = {
            "customer_id": customer_id,  # Thêm trường này
            "customer_info": customer_info,
            "items": [item.__dict__ for item in cart.items],
            "total_amount": cart.get_total(),
            "user_id": self.current_user.get("id")
        }
        # 5. Gọi OrderService để tạo đơn hàng
        try:
            # Giả định OrderService có phương thức create_order(payload)
            new_order = self.order_service.create_order(order_payload)
            # Lấy customer_id thay vì chỉ truyền thông tin thô
            customer_id = self.customer_service.find_or_create_customer(customer_info)
            # Tạo payload cho đơn hàng với customer_id

            messagebox.showinfo("Thành công", f"Đã tạo thành công đơn hàng #{new_order.get('id')}", parent=self)

            # 6. Xóa giỏ hàng sau khi tạo đơn thành công
            self.cart_service.clear_cart()

            # Xóa thông tin khách đã nhập
            for entry in self.customer_entries.values():
                entry.delete("1.0", "end") if isinstance(entry, tk.Text) else entry.delete(0, "end")

            # 7. Tải lại view
            self.refresh()

        except Exception as e:
            messagebox.showerror("Lỗi tạo đơn hàng", f"Đã có lỗi xảy ra: {e}", parent=self)
            import traceback
            traceback.print_exc()


# --- Dán lớp ScrollableFrame ở đây nếu nó chưa có trong file views.py ---
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
