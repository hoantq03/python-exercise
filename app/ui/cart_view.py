import tkinter as tk
from dataclasses import asdict
from tkinter import ttk, messagebox
from functools import partial
from typing import Dict

from PIL import Image, ImageTk
import io
import requests

from app.models.cart_item import CartItem
from app.services.cart_service import CartService
from app.services.customer_service import CustomerService
from app.services.order_service import OrderService


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

    def __init__(self, master, cart_service: CartService, order_service: OrderService,
                 customer_service: CustomerService, current_user: Dict):
        super().__init__(master)
        self.cart_service = cart_service
        self.order_service = order_service
        self.customer_service = customer_service
        self.current_user = current_user

        # Sử dụng StringVar để theo dõi và xác thực dữ liệu
        self.phone_var = tk.StringVar()
        self.name_var = tk.StringVar()

        # Gắn trace cho StringVar để cập nhật trạng thái nút "Tạo Đơn Hàng"
        self.phone_var.trace_add("write", self._validate_customer_info)
        self.name_var.trace_add("write", self._validate_customer_info)

        self._create_widgets()
        self.refresh()
        self._validate_customer_info()  # Gọi lần đầu để thiết lập trạng thái nút

    def _create_widgets(self):
        main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        main_pane.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(main_pane, width=650)
        self._create_cart_details_frame(left_frame)
        main_pane.add(left_frame, stretch="always")

        right_frame = ttk.Frame(main_pane, width=350)
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

        # --- Số điện thoại (Bắt buộc) ---
        ttk.Label(container, text="Số điện thoại (*):").pack(anchor='w')
        self.e_phone = ttk.Entry(container, font=("Arial", 10), textvariable=self.phone_var)
        self.e_phone.pack(fill=tk.X, pady=(0, 10))
        self.e_phone.bind("<FocusOut>", self._on_phone_focus_out)  # Gắn sự kiện FocusOut

        # --- Họ và Tên (Bắt buộc) ---
        ttk.Label(container, text="Họ và Tên (*):").pack(anchor='w')
        self.e_name = ttk.Entry(container, font=("Arial", 10), textvariable=self.name_var)
        self.e_name.pack(fill=tk.X, pady=(0, 10))
        self.name_var.set("")  # Đảm bảo tên trống ban đầu

        # --- Địa chỉ (Tùy chọn) ---
        ttk.Label(container, text="Địa chỉ giao hàng (Tùy chọn):").pack(anchor='w')
        self.e_address = tk.Text(container, height=4, font=("Arial", 10))
        self.e_address.pack(fill=tk.X)
        self.e_address.delete("1.0", "end")  # Đảm bảo địa chỉ trống ban đầu

        # --- Nút Tạo Đơn Hàng ---
        self.create_order_btn = ttk.Button(container, text="✅ Tạo Đơn Hàng", command=self._create_order,
                                           state=tk.DISABLED)
        self.create_order_btn.pack(fill=tk.X, pady=(20, 5), ipady=10)

    def _on_phone_focus_out(self, event=None):
        """
        Xử lý khi người dùng rời khỏi trường số điện thoại.
        Tìm kiếm khách hàng đã có và điền/khóa trường tên.
        """
        phone = self.phone_var.get().strip()

        # Chỉ xử lý nếu số điện thoại đã được nhập
        if not phone:
            self.name_var.set('')
            self.e_name.config(state='normal')
            self.e_address.delete("1.0", "end")
            self._validate_customer_info()  # Cập nhật trạng thái nút
            return

        customer = self.customer_service.find_by_phone(phone)

        if customer:
            # Khách hàng đã tồn tại: điền tên và vô hiệu hóa trường tên
            self.name_var.set(customer.get('name', ''))
            self.e_name.config(state='disabled')
            self.e_address.delete("1.0", "end")
            self.e_address.insert("1.0", customer.get('address', ''))
        else:
            # Khách hàng mới: cho phép nhập tên
            self.name_var.set('')
            self.e_name.config(state='normal')
            self.e_address.delete("1.0", "end")  # Đảm bảo địa chỉ trống nếu là khách mới

        self._validate_customer_info()  # Cập nhật trạng thái nút sau khi điền thông tin

    def _validate_customer_info(self, *args):
        """
        Kiểm tra tính hợp lệ của thông tin khách hàng (SĐT và Tên)
        để kích hoạt/vô hiệu hóa nút "Tạo Đơn Hàng".
        """
        # Thêm kiểm tra này để đảm bảo nút đã được tạo
        if not hasattr(self, 'create_order_btn'):
            return

        phone = self.phone_var.get().strip()
        name = self.name_var.get().strip()

        # Nút được kích hoạt nếu SĐT và Tên đều không rỗng
        if phone and name:
            self.create_order_btn.config(state='normal')
        else:
            self.create_order_btn.config(state='disabled')

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

    def _create_cart_item_widget(self, item: CartItem, index: int):
        # --- Khung chính cho mỗi sản phẩm ---
        item_frame = ttk.Frame(self.scroll_frame.scrollable_frame, padding=10)
        item_frame.pack(fill=tk.X, pady=5, padx=5)

        # Đường kẻ ngang phân cách giữa các sản phẩm
        ttk.Separator(self.scroll_frame.scrollable_frame, orient='horizontal').pack(fill='x', padx=5, pady=(0, 5))

        # Cấu hình grid để phần tên sản phẩm (cột 1) co giãn
        item_frame.columnconfigure(1, weight=1)

        # --- Khung bên trái: Ảnh và Tên sản phẩm ---
        left_frame = ttk.Frame(item_frame)
        left_frame.grid(row=0, column=0, sticky="w")

        # Tải ảnh từ URL - Đã sửa lỗi AttributeError
        avatar_url = item.avatar  # Trực tiếp truy cập thuộc tính
        photo = None
        if avatar_url and isinstance(avatar_url, str) and avatar_url.startswith('http'):
            try:
                resp = requests.get(avatar_url, timeout=10)
                resp.raise_for_status()
                img = Image.open(io.BytesIO(resp.content)).convert('RGB')
                img.thumbnail((60, 60), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img, master=self)
            except Exception as e:
                print(f"Lỗi tải ảnh: {e}")

        if photo:
            label_img = ttk.Label(left_frame, image=photo)
            label_img.image = photo
            label_img.pack(side="left", anchor="center")
        else:
            ttk.Label(left_frame, text="[Ảnh]", width=10, anchor="center").pack(side="left")

        # Tên sản phẩm - Đã sửa lỗi AttributeError
        item_name = item.name  # Trực tiếp truy cập thuộc tính
        ttk.Label(left_frame, text=item_name, wraplength=250, font=("Arial", 11)).pack(side="left", padx=15, anchor="w")

        # --- Khung bên phải: Giá, Số lượng, Thành tiền, Nút xóa ---
        right_frame = ttk.Frame(item_frame)
        right_frame.grid(row=0, column=1, sticky="e")

        # Khung giá - Đã sửa lỗi AttributeError
        price_frame = ttk.Frame(right_frame)
        price_frame.pack(side="left", padx=15, anchor="center")
        ttk.Label(price_frame, text="Giá").pack(pady=(0, 2))
        item_price = item.price  # Trực tiếp truy cập thuộc tính
        ttk.Label(price_frame, text=f"{item_price:,.0f} ₫", font=("Arial", 10, "bold")).pack()

        # Khung số lượng - Đã sửa lỗi AttributeError
        qty_frame = ttk.Frame(right_frame)
        qty_frame.pack(side="left", padx=15, anchor="center")
        ttk.Label(qty_frame, text="Số lượng").pack(pady=(0, 2))
        qty_spinbox = ttk.Spinbox(qty_frame, from_=1, to=99, width=5, justify='center')
        item_quantity = item.quantity  # Trực tiếp truy cập thuộc tính
        qty_spinbox.insert(0, str(item_quantity))
        qty_spinbox.pack()

        item_id = item.item_id  # Trực tiếp truy cập thuộc tính
        update_callback = partial(self._update_quantity, item_id, qty_spinbox)
        qty_spinbox.config(command=update_callback)
        qty_spinbox.bind("<Return>", lambda event: update_callback())
        qty_spinbox.bind("<FocusOut>", lambda event: update_callback())

        # Khung thành tiền - Đã sửa lỗi AttributeError
        subtotal_frame = ttk.Frame(right_frame)
        subtotal_frame.pack(side="left", padx=15, anchor="center")
        ttk.Label(subtotal_frame, text="Thành tiền").pack(pady=(0, 2))
        subtotal = item.get_subtotal()  # Trực tiếp gọi phương thức
        ttk.Label(subtotal_frame, text=f"{subtotal:,.0f} ₫", font=("Arial", 10, "bold"), foreground="red").pack()

        # Nút xóa
        remove_btn = ttk.Button(right_frame, text="🗑️ Xóa", style="Toolbutton",
                                command=lambda: self._remove_item(item_id))
        remove_btn.pack(side="left", padx=(25, 0), anchor="center")

    def _update_quantity(self, item_id: str, spinbox_widget: ttk.Spinbox):
        """Cập nhật số lượng sản phẩm từ widget Spinbox."""
        new_quantity_str = spinbox_widget.get()
        try:
            new_quantity = int(new_quantity_str)
            if new_quantity > 0:
                self.cart_service.update_item_quantity(item_id, new_quantity)
                self.refresh()
            else:
                spinbox_widget.set(1)
                self._remove_item(item_id)
        except (ValueError, TypeError):
            pass

    def _remove_item(self, item_id: str):
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa sản phẩm này khỏi giỏ hàng?"):
            self.cart_service.remove_item(item_id)
            self.refresh()

    def _create_order(self):
        # Lấy thông tin khách hàng từ các StringVar và Text widget
        customer_info = {
            "phone": self.phone_var.get().strip(),
            "name": self.name_var.get().strip(),
            "address": self.e_address.get("1.0", "end-1c").strip()
        }

        # Kiểm tra lại thông tin bắt buộc trước khi tạo đơn
        if not customer_info["name"] or not customer_info["phone"]:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập đầy đủ Số điện thoại và Họ và Tên.", parent=self)
            return

        cart = self.cart_service.get_cart()
        if not cart.items:
            messagebox.showwarning("Giỏ hàng trống", "Vui lòng thêm sản phẩm vào giỏ trước khi tạo đơn hàng.",
                                   parent=self)
            return

        try:
            # Service sẽ tìm khách hàng bằng SĐT, nếu không có sẽ tạo mới
            # find_or_create_customer sẽ trả về customer_id
            customer_id = self.customer_service.find_or_create_customer(customer_info)

            # Chuyển đổi danh sách CartItem objects sang dictionaries để phù hợp với Order model
            items_payload = [asdict(item) for item in cart.items]

            order_payload = {
                "customer_id": customer_id,
                "customer_info": customer_info,  # Thông tin khách hàng tại thời điểm đặt hàng
                "items": items_payload,
                "total_amount": cart.get_total(),
                "user_id": self.current_user.get("id")  # Giả định current_user là dict có 'id'
            }

            new_order = self.order_service.create_order(order_payload)
            messagebox.showinfo("Thành công", f"Đã tạo thành công đơn hàng #{new_order.get('id')}", parent=self)

            self.cart_service.clear_cart()  # Xóa giỏ hàng sau khi đặt thành công

            # Dọn dẹp các trường thông tin khách hàng và reset trạng thái
            self.phone_var.set('')
            self.name_var.set('')
            self.e_address.delete("1.0", "end")
            self.e_name.config(state='normal')  # Reset ô tên về trạng thái bình thường

            self.refresh()  # Cập nhật lại giao diện giỏ hàng
            self._validate_customer_info()  # Cập nhật trạng thái nút "Tạo Đơn Hàng" sau khi refresh

        except ValueError as e:
            messagebox.showerror("Lỗi tạo đơn hàng", f"{e}", parent=self)
        except Exception as e:
            messagebox.showerror("Lỗi tạo đơn hàng", f"Đã có lỗi xảy ra: {e}", parent=self)
            import traceback
            traceback.print_exc()