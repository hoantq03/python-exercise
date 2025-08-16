from functools import partial
from datetime import datetime
import uuid, math, threading
from typing import Set, List, Dict

from PIL import Image, ImageTk
import requests
from io import BytesIO
import tkinter as tk
from tkinter import ttk, messagebox


class ScrollableFrame(ttk.Frame):
    """Custom scrollable frame with mouse wheel support"""

    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)

        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.bind_mousewheel()

    def bind_mousewheel(self):
        """Bind mouse wheel scrolling"""

        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_to_mousewheel(event):
            self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_from_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>")

        self.bind('<Enter>', _bind_to_mousewheel)
        self.bind('<Leave>', _unbind_from_mousewheel)


class ProductsView(ttk.Frame):
    UI_CFG = {
        "grid": {
            "base_cols": 6,
            "min_cols": 2,
            "img_size": (160, 120),
            "card_width": 180,
            "card_height": 280,
            "img_bg_loading": "#e0e0e0",
            "img_bg_done": "#ffffff",
            "card_wrap": 150,
            "name_font": ("Arial", 10, "bold"),
            "price_font": ("Arial", 12, "bold"),
            "meta_font": ("Arial", 10),
            "price_color": "#d60000",
            "card_padx": 6,
            "card_pady": 8,
        },
        "detail": {
            "img_size": (360, 300),
            "title_wrap": 450,
            "title_font": ("Arial", 16, "bold"),
            "label_font": ("Arial", 12),
            "label_bold": ("Arial", 12, "bold"),
        },
    }

    def __init__(self, master, product_service, cart_service, category_service, can_edit: bool):
        super().__init__(master)
        self.product_service = product_service
        self.cart_service = cart_service
        self.category_service = category_service  # NEW: category_service
        self.can_edit = can_edit

        # Performance optimization variables
        self._img_cache = {}
        self._img_labels = {}
        self._refreshing = False
        self._last_items_per_page = 8
        self._resize_timer = None
        self._search_timer = None
        self._sort_timer = None
        self._last_window_size = None

        # Pagination state
        self.current_page = 1
        self.items_per_page = tk.IntVar(value=12)
        self.total_pages = 1

        # NEW: Category filter state
        self.selected_categories: Set[str] = set()  # Stores categoryUris of selected categories

        self._create_widgets()
        self._bind_events()

        # Delayed initial load to avoid lag
        self.after(200, lambda: self.refresh(reset_page=True))

    def _create_widgets(self):
        entry_width_price = 11
        entry_padx = 3

        # Hàm định dạng giá tiền
        def format_price(event, price_var):
            value = price_var.get().replace(',', '')  # Xóa bỏ dấu phẩy cũ nếu có
            if value.isdigit():  # Kiểm tra xem giá trị có phải là số không
                price_var.set('{:,}'.format(int(value)))  # Định dạng với dấu phẩy

        """Creates all widgets with optimized layout"""
        # Toolbar with fixed height
        toolbar = ttk.Frame(self, height=40)
        toolbar.pack(fill=tk.X, pady=6)
        toolbar.pack_propagate(False)

        # Search controls
        ttk.Label(toolbar, text="Tìm tên:").pack(side=tk.LEFT, padx=4)
        self.e_kw = ttk.Entry(toolbar, width=18)
        self.e_kw.pack(side=tk.LEFT, padx=2)

        # Sử dụng StringVar cho e_min_price
        self.min_price_var = tk.StringVar()
        self.e_min_price = ttk.Entry(toolbar, width=entry_width_price, textvariable=self.min_price_var)
        self.e_min_price.pack(side=tk.LEFT, padx=entry_padx)
        # Gắn sự kiện FocusOut để định dạng giá tiền khi rời khỏi trường nhập
        self.e_min_price.bind('<FocusOut>', lambda e: format_price(e, self.min_price_var))

        ttk.Label(toolbar, text="đến:").pack(side=tk.LEFT)
        # Sử dụng StringVar cho e_max_price
        self.max_price_var = tk.StringVar()
        self.e_max_price = ttk.Entry(toolbar, width=entry_width_price, textvariable=self.max_price_var)
        self.e_max_price.pack(side=tk.LEFT, padx=entry_padx)
        # Gắn sự kiện FocusOut để định dạng giá tiền khi rời khỏi trường nhập
        self.e_max_price.bind('<FocusOut>', lambda e: format_price(e, self.max_price_var))

        # NEW: Category filter button
        ttk.Button(toolbar, text="Danh mục...", command=self._open_category_filter_dialog).pack(side=tk.LEFT, padx=8)

        # Sort control with StringVar trace
        ttk.Label(toolbar, text="Sắp xếp:").pack(side=tk.LEFT, padx=4)
        self.sort_var = tk.StringVar(value="name_az")

        # Add trace to monitor StringVar changes
        self.sort_var.trace_add('write', self._on_sort_var_change)

        self.c_sort = ttk.Combobox(
            toolbar, textvariable=self.sort_var, width=16, state="readonly",
            values=["name_az - Tên A-Z", "name_za - Tên Z-A", "price_asc - Giá tăng", "price_desc - Giá giảm"]
        )
        self.c_sort.pack(side=tk.LEFT, padx=2)

        # Action buttons
        ttk.Button(toolbar, text="🔄 Làm mới",
                   command=self._manual_refresh).pack(side=tk.LEFT, padx=8)

        if self.can_edit:
            ttk.Button(toolbar, text="➕ Thêm sản phẩm",
                       command=self.add).pack(side=tk.LEFT, padx=8)

        # Scrollable grid frame
        self.scroll_frame = ScrollableFrame(self)
        self.scroll_frame.pack(expand=True, fill=tk.BOTH, padx=12, pady=10)

        # Pagination with fixed height
        pagination_frame = ttk.Frame(self, height=50)
        pagination_frame.pack(fill=tk.X, pady=(0, 10))
        pagination_frame.pack_propagate(False)

        ttk.Label(pagination_frame, text="Số mục/trang:").pack(side=tk.LEFT, padx=(10, 2))

        self.c_items_per_page = ttk.Combobox(
            pagination_frame, textvariable=self.items_per_page,
            values=[12, 18, 24], width=5, state="readonly"
        )
        self.c_items_per_page.pack(side=tk.LEFT, padx=2)

        # Spacer
        ttk.Frame(pagination_frame).pack(side=tk.LEFT, expand=True, fill=tk.X)

        # Navigation
        self.btn_prev = ttk.Button(pagination_frame, text="◀ Trước", command=self.prev_page)
        self.btn_prev.pack(side=tk.LEFT, padx=5)

        self.lbl_page_status = ttk.Label(pagination_frame, text="Trang 1 / 1",
                                         width=20, anchor="center")
        self.lbl_page_status.pack(side=tk.LEFT)

        self.btn_next = ttk.Button(pagination_frame, text="Sau ▶", command=self.next_page)
        self.btn_next.pack(side=tk.LEFT, padx=5)

    def _bind_events(self):
        """FIXED: Bind events with performance optimization and sort fix"""
        # Items per page binding
        self.c_items_per_page.bind("<<ComboboxSelected>>", self._on_items_per_page_change)
        self.c_items_per_page.bind("<Button-1>", self._on_combo_click)
        self.c_items_per_page.bind("<Return>", self._on_items_per_page_change)

        # Search events
        self.e_kw.bind("<KeyRelease>", self._on_search_change)
        self.e_min_price.bind("<KeyRelease>", self._on_price_change)
        self.e_max_price.bind("<KeyRelease>", self._on_price_change)

        # Window resize
        self.bind("<Configure>", self._on_window_resize)

        # IntVar trace
        self.items_per_page.trace_add('write', self._on_intvar_change)

    def _on_sort_var_change(self, *args):
        """
        Handles sort option changes via the StringVar trace with debouncing.
        This is the ONLY handler needed for sorting.
        """
        print(f"🎯 Sort value changed to: {self.sort_var.get()}. Scheduling refresh.")

        # Cancel any pending refresh to avoid multiple calls
        if self._sort_timer:
            self.after_cancel(self._sort_timer)

        # Schedule refresh after a short delay (debouncing)
        # We reuse _search_refresh_callback because it does exactly what we need:
        # reset the page to 1 and call refresh().
        self._sort_timer = self.after(300, self._search_refresh_callback)

    def _on_combo_click(self, event=None):
        """Handle combo click to force check value"""
        self.after(150, self._check_combo_value)

    def _check_combo_value(self):
        """Check and sync combo value with IntVar"""
        try:
            combo_text = self.c_items_per_page.get()
            intvar_val = self.items_per_page.get()

            if combo_text and combo_text.isdigit():
                combo_val = int(combo_text)
                if combo_val != intvar_val:
                    print(f"🔧 Syncing combo: {intvar_val} → {combo_val}")
                    self.items_per_page.set(combo_val)
                    self._on_items_per_page_change()
        except (ValueError, AttributeError) as e:
            print(f"⚠️ Combo sync error: {e}")

    def _on_intvar_change(self, *args):
        """Callback when IntVar changes"""
        new_value = self.items_per_page.get()
        if hasattr(self, '_last_items_per_page') and new_value != self._last_items_per_page:
            print(f"📊 Items per page: {self._last_items_per_page} → {new_value}")
            self._last_items_per_page = new_value

    def _on_items_per_page_change(self, event=None):
        """Handle items per page change with validation"""
        try:
            new_value = self.items_per_page.get()

            # Validate value
            if new_value not in [4, 8, 12, 16, 20, 24]:
                print(f"⚠️ Invalid items per page: {new_value}")
                return

            print(f"✅ Items per page changed to: {new_value}")

            # Reset page and refresh
            self.current_page = 1
            self.refresh()

        except (ValueError, AttributeError) as e:
            print(f"❌ Error changing items per page: {e}")

    def _on_search_change(self, event=None):
        """Handle search change with debouncing"""
        self._debounced_search_refresh(800)

    def _on_price_change(self, event=None):
        """Handle price filter change with debouncing"""
        self._debounced_search_refresh(1000)

    def _on_window_resize(self, event=None):
        """Handle window resize with intelligent checking"""
        if not event or event.widget != self:
            return

        current_width = event.width
        current_height = event.height
        current_size = (current_width, current_height)

        # Đảm bảo self._last_window_size được khởi tạo.
        # Nếu chưa, gán kích thước hiện tại và không làm gì thêm trong lần này.
        if not hasattr(self, '_last_window_size') or self._last_window_size is None:
            self._last_window_size = current_size
            return

        # Chỉ tính toán sự khác biệt nếu _last_window_size đã có giá trị
        width_diff = abs(current_width - self._last_window_size[0])
        height_diff = abs(current_height - self._last_window_size[1])  # <-- Lỗi được sửa tại đây

        # Chỉ refresh nếu sự thay đổi đáng kể (> 50px)
        if width_diff < 50 and height_diff < 50:
            return

        self._last_window_size = current_size
        self._debounced_resize_refresh(500)

    def _debounced_search_refresh(self, delay=800):
        """Separate debounced refresh for search"""
        if self._search_timer:
            self.after_cancel(self._search_timer)
        self._search_timer = self.after(delay, self._search_refresh_callback)

    def _debounced_resize_refresh(self, delay=500):
        """Separate debounced refresh for resize"""
        if self._resize_timer:
            self.after_cancel(self._resize_timer)
        self._resize_timer = self.after(delay, self._resize_refresh_callback)

    def _search_refresh_callback(self):
        """Callback for search refresh"""
        self.current_page = 1
        self.refresh()

    def _resize_refresh_callback(self):
        """Callback for resize refresh"""
        self.refresh()

    def _manual_refresh(self):
        """Manual refresh button"""
        print("🔄 Manual refresh triggered")
        self.refresh(reset_page=True)

    def get_filters(self):
        """Get all filters"""
        kw = self.e_kw.get().strip().lower()

        try:
            min_price = float(self.e_min_price.get()) if self.e_min_price.get().strip() else None
        except ValueError:
            min_price = None

        try:
            max_price = float(self.e_max_price.get()) if self.e_max_price.get().strip() else None
        except ValueError:
            max_price = None

        # FIXED: Ensure sort_by is a string
        sort_by_raw = self.sort_var.get()
        if isinstance(sort_by_raw, str):
            if " - " in sort_by_raw:
                sort_by = sort_by_raw.split(" - ")[0]
            else:
                sort_by = sort_by_raw  # It's already the key
        else:
            print(f"Error: sort_by_raw is not a string: {sort_by_raw}. Defaulting to 'name_az'")
            sort_by = "name_az"  # Fallback to default in case of unexpected type

        # MODIFIED: Return selected_categories as well
        return kw, min_price, max_price, sort_by, self.selected_categories

    def calculate_columns(self, items_per_page_val):
        """Calculate optimal columns"""
        gcfg = self.UI_CFG["grid"]
        base_cols = gcfg["base_cols"]
        min_cols = gcfg["min_cols"]

        if items_per_page_val <= 4:
            return max(min_cols, min(items_per_page_val, 4))
        elif items_per_page_val <= 8:
            return min(6, base_cols)
        elif items_per_page_val <= 12:
            return base_cols
        else:
            return base_cols

    def refresh(self, reset_page: bool = False):
        """Main refresh with performance optimization"""
        if self._refreshing:
            print("🔄 Refresh already in progress, skipping...")
            return

        self._refreshing = True

        try:
            if reset_page:
                self.current_page = 1

            # Clear existing widgets efficiently
            self._clear_grid()

            # Get and process data
            # MODIFIED: Get selected_categories from get_filters()
            kw, min_price, max_price, sort_by, selected_categories = self.get_filters()
            # MODIFIED: Pass selected_categories to _get_filtered_products()
            products_all = self._get_filtered_products(kw, min_price, max_price, sort_by, selected_categories)

            # Calculate pagination
            items_per_page_val = self.items_per_page.get()
            total_items = len(products_all)
            self.total_pages = max(1, math.ceil(total_items / items_per_page_val))

            # Validate current page
            self.current_page = min(max(1, self.current_page), self.total_pages)

            # Get page items
            start_idx = (self.current_page - 1) * items_per_page_val
            end_idx = start_idx + items_per_page_val
            products_to_display = products_all[start_idx:end_idx]

            # MODIFIED: Include categories in print statement
            print(
                f"📄 Page {self.current_page}/{self.total_pages}: {len(products_to_display)} items, sort: {sort_by}, categories: {self.selected_categories}")

            # Display products
            if products_to_display:
                self._display_products(products_to_display, items_per_page_val)
            else:
                self._show_empty_message()

            # Update controls
            self.update_pagination_controls()

        except Exception as e:
            print(f"❌ Refresh error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._refreshing = False

    def _clear_grid(self):
        """Efficiently clear grid"""
        for widget in self.scroll_frame.scrollable_frame.winfo_children():
            widget.destroy()
        self._img_labels.clear()

    # MODIFIED: Accept selected_categories parameter
    def _get_filtered_products(self, kw, min_price, max_price, sort_by, selected_categories: Set[str]):
        """Get and filter products with proper sorting and category filter"""
        products_all = self.product_service.list()

        # Apply keyword filter
        if kw:
            products_all = [p for p in products_all if kw in p["name"].lower()]

        # Apply price filters
        if min_price is not None:
            products_all = [p for p in products_all if float(p.get("price", 0)) >= min_price]
        if max_price is not None:
            products_all = [p for p in products_all if float(p.get("price", 0)) <= max_price]

        # NEW: Apply category filter
        if selected_categories:
            # A product is included if it has at least one category that is in selected_categories
            products_all = [
                p for p in products_all
                if any(cat.get('uri') in selected_categories for cat in p.get('categories', []))
            ]

        # ENHANCED: Apply sorting with comprehensive error handling
        try:
            if sort_by == "name_az":
                products_all.sort(key=lambda x: str(x.get("name", "")).lower())
            elif sort_by == "name_za":
                products_all.sort(key=lambda x: str(x.get("name", "")).lower(), reverse=True)
            elif sort_by == "price_asc":
                products_all.sort(key=lambda x: float(x.get("price", 0)))
            elif sort_by == "price_desc":
                products_all.sort(key=lambda x: float(x.get("price", 0)), reverse=True)
            else:
                print(f"⚠️ Unknown sort option: '{sort_by}', using default order")
        except Exception as e:
            print(f"❌ Sorting error: {e}")

        return products_all

    def _display_products(self, products, items_per_page_val):
        """Display products in scrollable grid"""
        gcfg = self.UI_CFG["grid"]
        cols = self.calculate_columns(items_per_page_val)

        for i in range(cols):
            self.scroll_frame.scrollable_frame.grid_columnconfigure(i, weight=1, uniform="col")

        for idx, product in enumerate(products):
            self._create_product_card(product, idx, cols, gcfg)

    def _create_product_card(self, product, idx, cols, gcfg):
        """Create single product card with lazy loading"""
        pid = product.get("id") or f"row{idx}"

        frame = ttk.Frame(self.scroll_frame.scrollable_frame, relief=tk.RAISED, borderwidth=1)
        row = idx // cols
        col = idx % cols

        frame.grid(row=row, column=col,
                   padx=gcfg["card_padx"], pady=gcfg["card_pady"],
                   sticky="nsew", ipadx=5, ipady=5)

        frame.grid_propagate(False)
        frame.configure(width=gcfg["card_width"], height=gcfg["card_height"])

        img_container = tk.Frame(frame, width=gcfg["img_size"][0],
                                 height=gcfg["img_size"][1], bg=gcfg["img_bg_loading"])
        img_container.pack(pady=(8, 6))
        img_container.pack_propagate(False)

        img_label = tk.Label(img_container, text="📷",
                             bg=gcfg["img_bg_loading"], anchor="center",
                             font=("Arial", 24))
        img_label.pack(fill=tk.BOTH, expand=True)
        self._img_labels[pid] = img_label

        avatar = product.get("avatar")
        if avatar:
            self.after(idx * 50, lambda p=pid, a=avatar: self._load_image(p, a, gcfg["img_size"]))
        else:
            img_label.config(text="🚫", font=("Arial", 20))

        self._create_product_info(frame, product, gcfg)

    def _load_image(self, pid, avatar, size):
        """Load image in background thread"""
        threading.Thread(target=self._fetch_image_async,
                         args=(pid, avatar, size), daemon=True).start()

    def _create_product_info(self, parent_frame, product, gcfg):
        """Create product info with compact layout"""
        info_frame = tk.Frame(parent_frame)
        info_frame.pack(fill=tk.X, padx=4)

        name = product.get("name", "")[:50] + ("..." if len(product.get("name", "")) > 50 else "")
        name_label = tk.Label(info_frame, text=name,
                              font=gcfg["name_font"], wraplength=gcfg["card_wrap"],
                              justify="center", height=2)
        name_label.pack(pady=(0, 3))

        price = product.get('price', 0)
        price_text = f"{price:,.0f}₫"
        price_label = tk.Label(info_frame, text=price_text,
                               foreground=gcfg["price_color"], font=gcfg["price_font"])
        price_label.pack()

        # sku = product.get('sku', '')
        # meta_text = f"SKU: {sku[:6]}{'...' if len(sku) > 6 else ''}"
        # tk.Label(info_frame, text=meta_text, font=gcfg["meta_font"]).pack()

        stock = product.get('stock', 0)
        stock_color = "#28a745" if stock > 10 else "#ffc107" if stock > 0 else "#dc3545"
        tk.Label(info_frame, text=f"Kho: {stock}",
                 font=gcfg["meta_font"], fg=stock_color).pack()

        self._create_action_buttons(parent_frame, product)

    def _create_action_buttons(self, parent_frame, product):
        """Create action buttons"""
        btn_frame = tk.Frame(parent_frame)
        btn_frame.pack(side=tk.BOTTOM, pady=(4, 6))

        stock = product.get('stock', 0)
        add_to_cart_btn = ttk.Button(
            btn_frame,
            text="🛒 Thêm vào giỏ",
            command=partial(self._add_to_cart, product),
            state=tk.NORMAL if stock > 0 else tk.DISABLED
        )
        add_to_cart_btn.pack(pady=2)

        ttk.Button(btn_frame, text="👁 Chi tiết",
                   command=partial(self.show_detail, product)).pack(pady=1)

        if self.can_edit:
            edit_frame = tk.Frame(btn_frame)
            edit_frame.pack(pady=1)

            ttk.Button(edit_frame, text="Sửa", width=8, command=partial(self.edit, product["id"])).pack(side=tk.LEFT, padx=1)
            ttk.Button(edit_frame, text="Xóa", width=8, command=partial(self.delete, product["id"])).pack(side=tk.LEFT, padx=1)

    def _add_to_cart(self, product):
        """Add 1 product to cart and show notification."""
        try:
            self.cart_service.add_item(product, 1)
            messagebox.showinfo(
                "Thành công",
                f"Đã thêm '{product['name']}' vào giỏ hàng.",
                parent=self
            )
            print(f"🛒 Added {product['name']} to cart.")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể thêm vào giỏ hàng: {e}", parent=self)
            print(f"❌ Error adding to cart: {e}")

    # NEW: Category filter methods
    def _open_category_filter_dialog(self):
        """Opens a dialog to select categories."""
        all_categories = self.category_service.list_all_categories()
        # Open dialog, pass category list and current selected categories
        CategoryFilterDialog(self, all_categories, self.selected_categories, self._on_categories_selected)

    def _on_categories_selected(self, selected_uris: Set[str]):
        """Callback when category selection dialog closes."""
        if self.selected_categories != selected_uris:  # Only refresh if there are changes
            self.selected_categories = selected_uris
            print(f"✅ Categories selected: {self.selected_categories}")
            self.refresh(reset_page=True)  # Reset page and refresh grid

    def _show_empty_message(self):
        """Show empty state"""
        empty_label = ttk.Label(self.scroll_frame.scrollable_frame,
                                text="🔍 Không tìm thấy sản phẩm nào",
                                font=("Arial", 14), foreground="#6c757d")
        empty_label.pack(pady=50)

    def next_page(self):
        """Next page with validation"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            print(f"➡️ Page: {self.current_page}")
            self.refresh()

    def prev_page(self):
        """Previous page with validation"""
        if self.current_page > 1:
            self.current_page -= 1
            print(f"⬅️ Page: {self.current_page}")
            self.refresh()

    def update_pagination_controls(self):
        """Update pagination UI"""
        items_per_page_val = self.items_per_page.get()

        # Calculate filtered total
        # MODIFIED: Get selected_categories from get_filters()
        kw, min_price, max_price, sort_by, selected_categories = self.get_filters()
        # MODIFIED: Pass selected_categories to _get_filtered_products()
        products_all = self._get_filtered_products(kw, min_price, max_price, sort_by, selected_categories)
        filtered_total = len(products_all)

        # Update status
        if filtered_total > 0:
            start_item = (self.current_page - 1) * items_per_page_val + 1
            end_item = min(self.current_page * items_per_page_val, filtered_total)
            # FIXED: sort_by is already a string here
            sort_display_text = sort_by.replace('_', ' ').title()
            status_text = f"Trang {self.current_page}/{self.total_pages} • {start_item}-{end_item}/{filtered_total} • {sort_display_text}"
        else:
            status_text = f"Trang {self.current_page}/{self.total_pages} • 0/0"

        self.lbl_page_status.config(text=status_text)

        # Update buttons
        self.btn_prev.config(state=tk.DISABLED if self.current_page <= 1 else tk.NORMAL)
        self.btn_next.config(state=tk.DISABLED if self.current_page >= self.total_pages else tk.NORMAL)

    def _fetch_image_async(self, pid, url_or_path, size):
        """Async image loading with caching"""
        try:
            # Check cache first
            if pid in self._img_cache:
                self.after(0, self._update_image_label, pid, self._img_cache[pid])
                return

            # Load image
            if str(url_or_path).startswith("http"):
                resp = requests.get(url_or_path, timeout=5)
                resp.raise_for_status()
                img = Image.open(BytesIO(resp.content))
            else:
                img = Image.open(url_or_path)

            # Process image
            img = img.convert("RGB")
            img.thumbnail(size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img, master=self)

            # Cache image
            self._img_cache[pid] = photo

            # Update UI
            self.after(0, self._update_image_label, pid, photo)

        except Exception as e:
            print(f"📷 Image load error for {pid}: {e}")
            self.after(0, lambda: self._safe_label_update(pid, error=True))

    def _update_image_label(self, pid, photo_image):
        """Update image label safely"""
        label = self._img_labels.get(pid)
        if label and label.winfo_exists():
            label.image = photo_image
            label.config(image=photo_image, text="", bg=self.UI_CFG["grid"]["img_bg_done"])

    def _safe_label_update(self, pid, error=False):
        """Safe label update on error"""
        label = self._img_labels.get(pid)
        if label and label.winfo_exists():
            if error:
                label.config(text="❌", bg="#ffe6e6", image="", font=("Arial", 16))
                label.image = None

    # CRUD Operations - keep from previous code
    def show_detail(self, product):
        """Show product detail, pass cart_service as well"""
        ProductDetailView(self, self.cart_service, product)

    def add(self):
        """Add new product"""
        # MODIFIED: Pass all_categories to ProductDialog
        ProductDialog(self, "Thêm sản phẩm", on_submit=self._add_submit,
                      all_categories=self.category_service.list_all_categories())

    def _add_submit(self, payload):
        """Handle add submit"""
        payload['id'] = str(uuid.uuid4())
        now_iso = datetime.now().isoformat(timespec="seconds")
        payload['created_at'] = now_iso
        payload['updated_at'] = now_iso

        # Kiểm tra và chuyển đổi định dạng cho trường 'categories'
        if 'categories' in payload and isinstance(payload['categories'], list):
            # Lấy tất cả danh mục một lần và tạo một map để tra cứu hiệu quả
            all_categories_map = {
                cat['categoryUri']: cat for cat in self.category_service.list_all_categories()
            }

            processed_categories = []
            for cat_uri in payload['categories']:  # payload['categories'] hiện là list các categoryUri
                cat_data = all_categories_map.get(cat_uri)
                if cat_data:
                    # Chuyển đổi định dạng mong muốn: categoryId, name, uri
                    processed_categories.append({
                        "categoryId": cat_data.get('categoryId'),
                        "name": cat_data.get('categoryName'),  # Đổi tên từ categoryName thành name
                        "uri": cat_data.get('categoryUri')
                    })
            payload['categories'] = processed_categories  # Gán lại danh sách đã xử lý

        self.product_service.create(payload)
        self.refresh(reset_page=True)

    def edit(self, product_id):
        """Edit product"""
        try:
            product = next(x for x in self.product_service.list() if x["id"] == product_id)
            # MODIFIED: Pass all_categories to ProductDialog
            ProductDialog(self, "Sửa sản phẩm", product=product,
                          on_submit=partial(self._edit_submit, product_id),
                          all_categories=self.category_service.list_all_categories())
        except StopIteration:
            messagebox.showerror("Lỗi", "Không tìm thấy sản phẩm để sửa.")

    def _edit_submit(self, product_id, patch):
        """Handle edit submit"""
        patch['updated_at'] = datetime.now().isoformat(timespec="seconds")

        # Kiểm tra và chuyển đổi định dạng cho trường 'categories'
        if 'categories' in patch and isinstance(patch['categories'], list):
            # Lấy tất cả danh mục một lần và tạo một map để tra cứu hiệu quả
            all_categories_map = {
                cat['categoryUri']: cat for cat in self.category_service.list_all_categories()
            }

            processed_categories = []
            for cat_uri in patch['categories']:  # patch['categories'] hiện là list các categoryUri
                cat_data = all_categories_map.get(cat_uri)
                if cat_data:
                    # Chuyển đổi định dạng mong muốn: categoryId, name, uri
                    processed_categories.append({
                        "categoryId": cat_data.get('categoryId'),
                        "name": cat_data.get('categoryName'),  # Đổi tên từ categoryName thành name
                        "uri": cat_data.get('categoryUri')
                    })
            patch['categories'] = processed_categories  # Gán lại danh sách đã xử lý

        self.product_service.update(product_id, patch)
        self.refresh()

    def delete(self, product_id):
        """Delete product"""
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa sản phẩm này?"):
            self.product_service.delete(product_id)
            self.refresh()


class ProductDialog(tk.Toplevel):
    """Optimized product dialog"""

    # MODIFIED: Add all_categories parameter
    def __init__(self, master, title, on_submit, product=None, all_categories=None):
        super().__init__(master)
        self.title(title)
        self.grab_set()
        self.resizable(True, True)  # Allow resize
        self.geometry("600x700")
        self.on_submit = on_submit
        self.product = product or {}
        self.all_categories = all_categories or []  # NEW

        self.entries = {}
        self.category_vars = {}  # NEW: To store StringVar for Checkbuttons
        self._create_form()

    def _create_form(self):
        """Create optimized form"""
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=15)

        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True)

        basic_tab = ttk.Frame(notebook)
        notebook.add(basic_tab, text="Thông tin cơ bản")

        specs_tab = ttk.Frame(notebook)
        notebook.add(specs_tab, text="Thông số kỹ thuật")

        # NEW: Categories tab
        categories_tab = ttk.Frame(notebook)
        notebook.add(categories_tab, text="Danh mục")

        self._create_basic_fields(basic_tab)
        self._create_spec_fields(specs_tab)
        self._create_category_fields(categories_tab)  # NEW

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(btn_frame, text="💾 Lưu", command=self._submit).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="❌ Hủy", command=self.destroy).pack(side=tk.RIGHT)

    def _create_basic_fields(self, parent):
        """Create basic fields"""
        fields = [
            ("Tên sản phẩm*", "name", "entry"),
            ("SKU*", "sku", "entry"),
            ("Giá (VNĐ)", "price", "entry"),
            ("Giá Nhập (VNĐ)", "bought_price", "entry"),
            ("Tồn kho", "stock", "entry"),
            ("Link ảnh", "avatar", "entry"),
            ("Mô tả", "description", "text")
        ]

        for label, key, widget_type in fields:
            self._create_field(parent, label, key, widget_type)

    def _create_spec_fields(self, parent):
        """Create specification fields"""
        specs = [
            ("Kích thước màn hình", "screen_size"),
            ("Công nghệ màn hình", "screen_tech"),
            ("Camera sau", "camera_sau"),
            ("Camera trước", "camera_truoc"),
            ("Chipset", "chipset"),
            ("RAM", "ram"),
            ("Bộ nhớ trong", "storage"),
            ("Pin", "battery"),
            ("Hệ điều hành", "os"),
            ("NFC", "nfc")
        ]

        for label, key in specs:
            self._create_field(parent, label, key, "entry")

    def _create_category_fields(self, parent):
        """Create category selection fields using checkbuttons in a scrollable frame."""
        if not self.all_categories:
            ttk.Label(parent, text="Không có danh mục nào để chọn.").pack(pady=20)
            return

        scroll_frame = ScrollableFrame(parent)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Get existing product categories (as uris)
        existing_product_category_uris = {
            cat.get('uri') for cat in self.product.get('categories', []) if cat.get('uri')
        }

        for category in self.all_categories:
            category_uri = category['categoryUri']
            category_name = category['categoryName']
            # Create an IntVar for each checkbox, default to 1 if already selected for this product
            var = tk.IntVar(value=1 if category_uri in existing_product_category_uris else 0)

            self.category_vars[category_uri] = var

            cb = ttk.Checkbutton(scroll_frame.scrollable_frame, text=category_name, variable=var)
            cb.pack(anchor="w", padx=5, pady=2)

    def _create_field(self, parent, label, key, widget_type):
        """Create individual field"""
        frame = ttk.Frame(parent)
        frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame, text=label + ":").pack(anchor="w")

        if widget_type == "text":
            entry = tk.Text(frame, height=4, font=("Arial", 11))
            entry.pack(fill="x", pady=(0, 5))
            entry.insert("1.0", str(self.product.get(key, "")))
        else:
            entry = ttk.Entry(frame, font=("Arial", 11))
            entry.pack(fill="x", pady=(0, 5))
            entry.insert(0, str(self.product.get(key, "")))

        self.entries[key] = entry

    def _submit(self):
        """Handle form submission"""
        payload = {}

        for key, entry in self.entries.items():
            if isinstance(entry, tk.Text):
                val = entry.get("1.0", tk.END).strip()
            else:
                val = entry.get().strip()

            # Type conversion
            if key in ["price", "bought_price", "stock"]:
                try:
                    val = float(val) if key == "price" or "bought_price" else int(val)
                except (ValueError, TypeError):
                    val = 0

            payload[key] = val

        # NEW: Add selected categories to payload
        selected_category_uris = []
        for uri, var in self.category_vars.items():
            if var.get() == 1:
                selected_category_uris.append(uri)
        payload['categories'] = selected_category_uris

        # Validation
        if not payload.get("name") or not payload.get("sku"):
            messagebox.showerror("Lỗi", "Tên sản phẩm và SKU không được để trống!", parent=self)
            return

        self.on_submit(payload)
        self.destroy()


class ProductDetailView(tk.Toplevel):
    """Optimized product detail view"""

    def __init__(self, master, cart_service, product):
        super().__init__(master)
        self.title(f"Chi tiết: {product.get('name', '')}")
        self.geometry("600x800")
        self.resizable(True, True)
        self.grab_set()
        self.product = product
        self.cart_service = cart_service

        self._create_detail_view()

    def _create_detail_view(self):
        """Create detail view with scroll support"""
        scroll_frame = ScrollableFrame(self)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=15)

        content = scroll_frame.scrollable_frame

        self._create_image_section(content)

        title_frame = ttk.Frame(content)
        title_frame.pack(fill="x", pady=(10, 20))

        ttk.Label(title_frame, text=self.product.get("name", ""),
                  font=("Arial", 18, "bold"), foreground="#2c3e50").pack()

        self._create_detail_sections(content)

        btn_frame = ttk.Frame(content)
        btn_frame.pack(fill="x", pady=(20, 0))

        stock = self.product.get('stock', 0)
        add_to_cart_btn = ttk.Button(
            btn_frame,
            text="🛒 Thêm vào giỏ",
            command=self._add_to_cart,
            state=tk.NORMAL if stock > 0 else tk.DISABLED
        )
        add_to_cart_btn.pack(side=tk.LEFT, padx=(0, 10), expand=True, fill=tk.X)

        ttk.Button(btn_frame, text="🚪 Đóng", command=self.destroy).pack(side=tk.RIGHT, expand=True, fill=tk.X)

    def _create_image_section(self, parent):
        """Create image section"""
        img_frame = ttk.Frame(parent)
        img_frame.pack(pady=(0, 15))

        avatar_path = self.product.get("avatar", "")
        if avatar_path:
            try:
                if str(avatar_path).startswith("http"):
                    resp = requests.get(avatar_path, timeout=10)
                    resp.raise_for_status()
                    img = Image.open(BytesIO(resp.content))
                else:
                    img = Image.open(avatar_path)

                img = img.convert("RGB")
                img.thumbnail((400, 300), Image.Resampling.LANCZOS)
                self._detail_img = ImageTk.PhotoImage(img, master=self)

                img_label = tk.Label(img_frame, image=self._detail_img,
                                     bg="white", relief=tk.RAISED, bd=1)
                img_label.image = self._detail_img
                img_label.pack()

            except Exception as ex:
                print(f"Detail image error: {ex}")
                ttk.Label(img_frame, text="📷 Không thể tải ảnh",
                          foreground="#6c757d").pack(pady=20)

    def _create_detail_sections(self, parent):
        """Create organized detail sections"""
        sections = {
            "Thông tin cơ bản": [
                ("Giá bán", "price", "price"),
                ("Giá nhập", "bought_product", "price"),
                ("Tồn kho", "stock", "number"),
                ("SKU", "sku", "text")
            ],
            "Mô tả": [
                ("Mô tả sản phẩm", "description", "long_text")
            ],
            "Thông số kỹ thuật": [
                ("Kích thước màn hình", "screen_size", "text"),
                ("Công nghệ màn hình", "screen_tech", "text"),
                ("Camera sau", "camera_sau", "text"),
                ("Camera trước", "camera_truoc", "text"),
                ("Chipset", "chipset", "text"),
                ("RAM", "ram", "text"),
                ("Bộ nhớ trong", "storage", "text"),
                ("Pin", "battery", "text"),
                ("Hệ điều hành", "os", "text"),
                ("NFC", "nfc", "text")
            ],
            # NEW: Add Categories section
            "Danh mục": [
                ("Danh mục", "categories", "categories_list")
            ]
        }

        for section_title, fields in sections.items():
            has_data = False
            for _, key, data_type in fields:
                if data_type == "categories_list":  # Special handling for categories
                    if self.product.get(key):
                        has_data = True
                        break
                elif key == "description":
                    if self.product.get(key) and str(self.product.get(key)).strip():
                        has_data = True
                        break
                else:
                    if self.product.get(key) is not None and str(self.product.get(key)).strip():
                        has_data = True
                        break

            if not has_data and section_title != "Thông tin cơ bản":
                continue

            section_frame = ttk.LabelFrame(parent, text=section_title, padding=15)
            section_frame.pack(fill="x", pady=(0, 15))

            for title, key, data_type in fields:
                value = self.product.get(key)
                if value is not None and str(value).strip() or data_type == "categories_list":
                    self._add_detail_row(section_frame, title, value, data_type)

    def _add_detail_row(self, parent, title, value, data_type):
        """Add detail row with formatting"""
        row_frame = ttk.Frame(parent)
        row_frame.pack(fill="x", pady=3)

        if data_type == "price":
            formatted_value = f"{value:,.0f}₫"
            color = "#28a745"
        elif data_type == "number":
            formatted_value = f"{value:,}"
            color = "#17a2b8" if value > 0 else "#dc3545"
        elif data_type == "long_text":
            formatted_value = str(value)[:200] + ("..." if len(str(value)) > 200 else "")
            color = "#495057"
        elif data_type == "categories_list":  # NEW: Handle categories list
            if isinstance(value, list) and value:
                formatted_value = ", ".join([cat.get('name', '') for cat in value if cat.get('name')])
            else:
                formatted_value = "N/A"
            color = "#495057"
        else:
            formatted_value = str(value)
            color = "#495057"

        ttk.Label(row_frame, text=f"{title}:",
                  font=("Arial", 10, "bold")).pack(anchor="w")

        value_label = tk.Label(row_frame, text=formatted_value,
                               font=("Arial", 10), fg=color,
                               wraplength=500, justify="left")
        value_label.pack(anchor="w", padx=(20, 0))

    def _add_to_cart(self):
        """Add 1 product to cart from ProductDetailView."""
        try:
            self.cart_service.add_item(self.product, 1)
            messagebox.showinfo(
                "Thành công",
                f"Đã thêm '{self.product['name']}' vào giỏ hàng.",
                parent=self
            )
            print(f"🛒 Added {self.product['name']} to cart from detail view.")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể thêm vào giỏ hàng: {e}", parent=self)
            print(f"❌ Error adding to cart from detail view: {e}")

class CategoryFilterDialog(tk.Toplevel):
    def __init__(self, master, all_categories: List[Dict], current_selected_uris: Set[str], on_apply_callback):
        super().__init__(master)
        self.title("Chọn Danh mục")
        self.grab_set()  # Make it modal
        self.resizable(False, False)
        self.geometry("400x500")

        self.all_categories = all_categories
        self.on_apply_callback = on_apply_callback
        self.checkbox_vars: Dict[str, tk.IntVar] = {}  # Stores tk.IntVar for each category

        # Biến lưu keyword search
        self.search_var = tk.StringVar()
        self.current_selected_uris = current_selected_uris  # lưu lại selected để không mất khi search

        self._create_widgets(current_selected_uris)

    def _create_widgets(self, current_selected_uris: Set[str]):
        """Create search box and checkboxes for categories."""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        # Ô tìm kiếm
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(search_frame, text="Tìm kiếm:").pack(side="left", padx=(0, 5))
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side="left", fill="x", expand=True)
        search_entry.bind("<KeyRelease>", lambda e: self._filter_categories())

        # Khung cuộn chứa checkbox
        self.scroll_frame = ScrollableFrame(main_frame)
        self.scroll_frame.pack(fill="both", expand=True, pady=(0, 10))

        self._render_categories(current_selected_uris)

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", side="bottom")

        ttk.Button(btn_frame, text="Áp dụng", command=self._apply_selection).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Hủy", command=self.destroy).pack(side="right")
        ttk.Button(btn_frame, text="Chọn tất cả", command=self._select_all).pack(side="left")
        ttk.Button(btn_frame, text="Bỏ chọn tất cả", command=self._deselect_all).pack(side="left", padx=5)

    def _render_categories(self, selected_uris: Set[str]):
        """Render checkboxes for categories (filtered if needed)."""

        # Clear frame trước khi render lại
        for widget in self.scroll_frame.scrollable_frame.winfo_children():
            widget.destroy()

        keyword = self.search_var.get().strip().lower()
        categories_to_show = [
            c for c in self.all_categories
            if keyword in c['categoryName'].lower()
        ] if keyword else self.all_categories

        if not categories_to_show:
            ttk.Label(self.scroll_frame.scrollable_frame, text="Không tìm thấy danh mục nào.").pack(pady=20)
            return

        for category in categories_to_show:
            category_uri = category['categoryUri']
            category_name = category['categoryName']

            if category_uri not in self.checkbox_vars:
                self.checkbox_vars[category_uri] = tk.IntVar(value=1 if category_uri in selected_uris else 0)

            var = self.checkbox_vars[category_uri]

            cb = ttk.Checkbutton(self.scroll_frame.scrollable_frame, text=category_name, variable=var)
            cb.pack(anchor="w", padx=5, pady=2)

    def _filter_categories(self):
        """Filter categories when typing in search box."""
        self._render_categories(self.current_selected_uris)

    def _apply_selection(self):
        """Collect selected categories and pass to callback."""
        selected_uris = {uri for uri, var in self.checkbox_vars.items() if var.get() == 1}
        self.on_apply_callback(selected_uris)
        self.destroy()

    def _select_all(self):
        """Select all checkboxes."""
        for var in self.checkbox_vars.values():
            var.set(1)

    def _deselect_all(self):
        """Deselect all checkboxes."""
        for var in self.checkbox_vars.values():
            var.set(0)
