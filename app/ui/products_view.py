from functools import partial
from datetime import datetime
import uuid, math, threading
from PIL import Image, ImageTk
import requests
from io import BytesIO
import tkinter as tk
from tkinter import ttk, messagebox


class ScrollableFrame(ttk.Frame):
    """Custom scrollable frame với mouse wheel support"""

    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)

        # Create canvas và scrollbar
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # Create window in canvas
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Pack elements
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Bind mouse wheel
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
            "base_cols": 8,
            "min_cols": 2,
            "img_size": (160, 120),
            "card_width": 180,
            "card_height": 280,
            "img_bg_loading": "#e0e0e0",
            "img_bg_done": "#ffffff",
            "card_wrap": 150,
            "name_font": ("Arial", 9, "bold"),
            "price_font": ("Arial", 8, "bold"),
            "meta_font": ("Arial", 7),
            "price_color": "#d60000",
            "card_padx": 6,
            "card_pady": 8,
        },
        "detail": {
            "img_size": (360, 300),
            "title_wrap": 450,
            "title_font": ("Arial", 16, "bold"),
            "label_font": ("Arial", 11),
            "label_bold": ("Arial", 11, "bold"),
        },
    }

    def __init__(self, master, service, can_edit: bool):
        super().__init__(master)
        self.service = service
        self.can_edit = can_edit

        # **Performance optimization variables**
        self._img_cache = {}
        self._img_labels = {}
        self._refreshing = False
        self._last_items_per_page = 8
        self._resize_timer = None
        self._search_timer = None  # **Separate timer for search**
        self._last_window_size = None

        # Pagination state
        self.current_page = 1
        self.items_per_page = tk.IntVar(value=8)
        self.total_pages = 1

        self._create_widgets()
        self._bind_events()

        # **Delayed initial load để tránh lag**
        self.after(200, lambda: self.refresh(reset_page=True))

    def _create_widgets(self):
        """Tạo tất cả widgets với layout tối ưu"""
        # **Toolbar với fixed height**
        toolbar = ttk.Frame(self, height=40)
        toolbar.pack(fill=tk.X, pady=6)
        toolbar.pack_propagate(False)  # Ngăn auto-resize

        # Search controls
        ttk.Label(toolbar, text="Tìm tên:").pack(side=tk.LEFT, padx=4)
        self.e_kw = ttk.Entry(toolbar, width=18)
        self.e_kw.pack(side=tk.LEFT, padx=2)

        ttk.Label(toolbar, text="Giá từ:").pack(side=tk.LEFT, padx=4)
        self.e_min_price = ttk.Entry(toolbar, width=8)
        self.e_min_price.pack(side=tk.LEFT, padx=2)

        ttk.Label(toolbar, text="đến:").pack(side=tk.LEFT)
        self.e_max_price = ttk.Entry(toolbar, width=8)
        self.e_max_price.pack(side=tk.LEFT, padx=2)

        # Sort control
        ttk.Label(toolbar, text="Sắp xếp:").pack(side=tk.LEFT, padx=4)
        self.sort_var = tk.StringVar(value="name_az")
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

        # **Scrollable grid frame**
        self.scroll_frame = ScrollableFrame(self)
        self.scroll_frame.pack(expand=True, fill=tk.BOTH, padx=12, pady=10)

        # **Pagination với fixed height**
        pagination_frame = ttk.Frame(self, height=50)
        pagination_frame.pack(fill=tk.X, pady=(0, 10))
        pagination_frame.pack_propagate(False)

        ttk.Label(pagination_frame, text="Số mục/trang:").pack(side=tk.LEFT, padx=(10, 2))

        self.c_items_per_page = ttk.Combobox(
            pagination_frame, textvariable=self.items_per_page,
            values=[4, 8, 12, 16, 20, 24], width=5, state="readonly"
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
        """Bind events với performance optimization - FIX SORT BUG"""
        # **Items per page binding với multiple methods**
        self.c_items_per_page.bind("<<ComboboxSelected>>", self._on_items_per_page_change)
        self.c_items_per_page.bind("<Button-1>", self._on_combo_click)
        self.c_items_per_page.bind("<Return>", self._on_items_per_page_change)

        # **FIXED: Sort change - không duplicate binding**
        self.c_sort.bind("<<ComboboxSelected>>", self._on_sort_change)

        # **Search với separate timers**
        self.e_kw.bind("<KeyRelease>", self._on_search_change)
        self.e_min_price.bind("<KeyRelease>", self._on_price_change)
        self.e_max_price.bind("<KeyRelease>", self._on_price_change)

        # **Window resize với intelligent checking**
        self.bind("<Configure>", self._on_window_resize)

        # IntVar trace
        self.items_per_page.trace_add('write', self._on_intvar_change)

    def _on_sort_change(self, event=None):
        """FIXED: Handle sort change immediately"""
        try:
            sort_value = self.sort_var.get()
            print(f"🔀 Sort changed to: {sort_value}")

            # **Immediate refresh for sort change**
            self.current_page = 1  # Reset to first page when sorting
            self.refresh()

        except Exception as e:
            print(f"❌ Sort change error: {e}")

    def _on_combo_click(self, event=None):
        """Handle combo click để force check value"""
        self.after(150, self._check_combo_value)

    def _check_combo_value(self):
        """Check và sync combo value với IntVar"""
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
        """Callback khi IntVar thay đổi"""
        new_value = self.items_per_page.get()
        if hasattr(self, '_last_items_per_page') and new_value != self._last_items_per_page:
            print(f"📊 Items per page: {self._last_items_per_page} → {new_value}")
            self._last_items_per_page = new_value

    def _on_items_per_page_change(self, event=None):
        """Handle items per page change với validation"""
        try:
            new_value = self.items_per_page.get()

            # Validate value
            if new_value not in [4, 8, 12, 16, 20, 24]:
                print(f"⚠️ Invalid items per page: {new_value}")
                return

            print(f"✅ Items per page changed to: {new_value}")

            # Reset page và refresh
            self.current_page = 1
            self.refresh()

        except (ValueError, AttributeError) as e:
            print(f"❌ Error changing items per page: {e}")

    def _on_search_change(self, event=None):
        """Handle search change với debouncing"""
        self._debounced_search_refresh(800)

    def _on_price_change(self, event=None):
        """Handle price filter change với debouncing"""
        self._debounced_search_refresh(1000)

    def _on_window_resize(self, event=None):
        """Handle window resize với intelligent checking"""
        if not event or event.widget != self:
            return

        # **Chỉ resize khi thay đổi đáng kể**
        current_size = (event.width, event.height)
        if self._last_window_size:
            width_diff = abs(current_size[0] - self._last_window_size[0])
            height_diff = abs(current_size[1] - self._last_window_size[1])

            # Chỉ refresh nếu thay đổi > 50px
            if width_diff < 50 and height_diff < 50:
                return

        self._last_window_size = current_size
        self._debounced_resize_refresh(500)

    def _debounced_search_refresh(self, delay=800):
        """FIXED: Separate debounced refresh for search"""
        if self._search_timer:
            self.after_cancel(self._search_timer)
        self._search_timer = self.after(delay, self._search_refresh_callback)

    def _debounced_resize_refresh(self, delay=500):
        """FIXED: Separate debounced refresh for resize"""
        if self._resize_timer:
            self.after_cancel(self._resize_timer)
        self._resize_timer = self.after(delay, self._resize_refresh_callback)

    def _search_refresh_callback(self):
        """Callback for search refresh"""
        self.current_page = 1  # Reset to first page when searching
        self.refresh()

    def _resize_refresh_callback(self):
        """Callback for resize refresh"""
        self.refresh()

    def _manual_refresh(self):
        """Manual refresh button"""
        print("🔄 Manual refresh triggered")
        self.refresh(reset_page=True)

    def get_filters(self):
        """Get tất cả filters"""
        kw = self.e_kw.get().strip().lower()

        try:
            min_price = float(self.e_min_price.get()) if self.e_min_price.get().strip() else None
        except ValueError:
            min_price = None

        try:
            max_price = float(self.e_max_price.get()) if self.e_max_price.get().strip() else None
        except ValueError:
            max_price = None

        sort_by = self.sort_var.get().split(" ")[0]
        return kw, min_price, max_price, sort_by

    def calculate_columns(self, items_per_page_val):
        """Calculate optimal columns"""
        gcfg = self.UI_CFG["grid"]
        base_cols = gcfg["base_cols"]
        min_cols = gcfg["min_cols"]

        if items_per_page_val <= 4:
            return max(min_cols, min(items_per_page_val, 4))
        elif items_per_page_val <= 8:
            return min(6, base_cols)  # Max 6 cho readability
        elif items_per_page_val <= 12:
            return base_cols
        else:
            return base_cols

    def refresh(self, reset_page: bool = False):
        """Main refresh với performance optimization"""
        if self._refreshing:
            print("🔄 Refresh already in progress, skipping...")
            return

        self._refreshing = True

        try:
            if reset_page:
                self.current_page = 1

            # **Clear existing widgets efficiently**
            self._clear_grid()

            # Get và process data
            kw, min_price, max_price, sort_by = self.get_filters()
            products_all = self._get_filtered_products(kw, min_price, max_price, sort_by)

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

            print(f"📄 Page {self.current_page}/{self.total_pages}: {len(products_to_display)} items, sort: {sort_by}")

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

    def _get_filtered_products(self, kw, min_price, max_price, sort_by):
        """FIXED: Get và filter products với proper sorting"""
        products_all = self.service.list()

        # Apply filters
        if kw:
            products_all = [p for p in products_all if kw in p["name"].lower()]
        if min_price is not None:
            products_all = [p for p in products_all if float(p.get("price", 0)) >= min_price]
        if max_price is not None:
            products_all = [p for p in products_all if float(p.get("price", 0)) <= max_price]

        # **FIXED: Apply sorting với proper error handling**
        try:
            if sort_by == "name_az":
                products_all.sort(key=lambda x: str(x.get("name", "")).lower())
                print(f"🔤 Sorted by name A-Z: {len(products_all)} items")
            elif sort_by == "name_za":
                products_all.sort(key=lambda x: str(x.get("name", "")).lower(), reverse=True)
                print(f"🔤 Sorted by name Z-A: {len(products_all)} items")
            elif sort_by == "price_asc":
                products_all.sort(key=lambda x: float(x.get("price", 0)))
                print(f"💰 Sorted by price ascending: {len(products_all)} items")
            elif sort_by == "price_desc":
                products_all.sort(key=lambda x: float(x.get("price", 0)), reverse=True)
                print(f"💰 Sorted by price descending: {len(products_all)} items")
            else:
                print(f"⚠️ Unknown sort option: {sort_by}")
        except Exception as e:
            print(f"❌ Sorting error: {e}")

        return products_all

    def _display_products(self, products, items_per_page_val):
        """Display products trong scrollable grid"""
        gcfg = self.UI_CFG["grid"]
        cols = self.calculate_columns(items_per_page_val)

        # Configure grid columns
        for i in range(cols):
            self.scroll_frame.scrollable_frame.grid_columnconfigure(i, weight=1, uniform="col")

        # Create product cards
        for idx, product in enumerate(products):
            self._create_product_card(product, idx, cols, gcfg)

    def _create_product_card(self, product, idx, cols, gcfg):
        """Create single product card với lazy loading"""
        pid = product.get("id") or f"row{idx}"

        # Card frame
        frame = ttk.Frame(self.scroll_frame.scrollable_frame, relief=tk.RAISED, borderwidth=1)
        row = idx // cols
        col = idx % cols

        frame.grid(row=row, column=col,
                   padx=gcfg["card_padx"], pady=gcfg["card_pady"],
                   sticky="nsew", ipadx=5, ipady=5)

        # **Fixed size để consistency**
        frame.grid_propagate(False)
        frame.configure(width=gcfg["card_width"], height=gcfg["card_height"])

        # Image container
        img_container = tk.Frame(frame, width=gcfg["img_size"][0],
                                 height=gcfg["img_size"][1], bg=gcfg["img_bg_loading"])
        img_container.pack(pady=(8, 6))
        img_container.pack_propagate(False)

        # Image label với placeholder
        img_label = tk.Label(img_container, text="📷",
                             bg=gcfg["img_bg_loading"], anchor="center",
                             font=("Arial", 24))
        img_label.pack(fill=tk.BOTH, expand=True)
        self._img_labels[pid] = img_label

        # **Lazy load image**
        avatar = product.get("avatar")
        if avatar:
            # Delay image loading để tránh lag
            self.after(idx * 50, lambda p=pid, a=avatar: self._load_image(p, a, gcfg["img_size"]))
        else:
            img_label.config(text="🚫", font=("Arial", 20))

        # Product info
        self._create_product_info(frame, product, gcfg)

    def _load_image(self, pid, avatar, size):
        """Load image trong background thread"""
        threading.Thread(target=self._fetch_image_async,
                         args=(pid, avatar, size), daemon=True).start()

    def _create_product_info(self, parent_frame, product, gcfg):
        """Create product info với compact layout"""
        info_frame = tk.Frame(parent_frame)
        info_frame.pack(fill=tk.X, padx=4)

        # Product name
        name = product.get("name", "")[:50] + ("..." if len(product.get("name", "")) > 50 else "")
        name_label = tk.Label(info_frame, text=name,
                              font=gcfg["name_font"], wraplength=gcfg["card_wrap"],
                              justify="center", height=2)
        name_label.pack(pady=(0, 3))

        # Price
        price = product.get('price', 0)
        price_text = f"{price:,.0f}₫" if price < 1000000 else f"{price / 1000000:.1f}M₫"
        price_label = tk.Label(info_frame, text=price_text,
                               foreground=gcfg["price_color"], font=gcfg["price_font"])
        price_label.pack()

        # Compact meta info
        sku = product.get('sku', '')
        meta_text = f"SKU: {sku[:6]}{'...' if len(sku) > 6 else ''}"
        tk.Label(info_frame, text=meta_text, font=gcfg["meta_font"]).pack()

        stock = product.get('stock', 0)
        stock_color = "#28a745" if stock > 10 else "#ffc107" if stock > 0 else "#dc3545"
        tk.Label(info_frame, text=f"Kho: {stock}",
                 font=gcfg["meta_font"], fg=stock_color).pack()

        # Action buttons
        self._create_action_buttons(parent_frame, product)

    def _create_action_buttons(self, parent_frame, product):
        """Create action buttons"""
        btn_frame = tk.Frame(parent_frame)
        btn_frame.pack(side=tk.BOTTOM, pady=(4, 6))

        ttk.Button(btn_frame, text="👁 Chi tiết",
                   command=partial(self.show_detail, product)).pack(pady=1)

        if self.can_edit:
            edit_frame = tk.Frame(btn_frame)
            edit_frame.pack(pady=1)

            ttk.Button(edit_frame, text="✏️", width=4,
                       command=partial(self.edit, product["id"])).pack(side=tk.LEFT, padx=1)
            ttk.Button(edit_frame, text="🗑️", width=4,
                       command=partial(self.delete, product["id"])).pack(side=tk.LEFT, padx=1)

    def _show_empty_message(self):
        """Show empty state"""
        empty_label = ttk.Label(self.scroll_frame.scrollable_frame,
                                text="🔍 Không tìm thấy sản phẩm nào",
                                font=("Arial", 14), foreground="#6c757d")
        empty_label.pack(pady=50)

    def next_page(self):
        """Next page với validation"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            print(f"➡️ Page: {self.current_page}")
            self.refresh()

    def prev_page(self):
        """Previous page với validation"""
        if self.current_page > 1:
            self.current_page -= 1
            print(f"⬅️ Page: {self.current_page}")
            self.refresh()

    def update_pagination_controls(self):
        """Update pagination UI"""
        items_per_page_val = self.items_per_page.get()

        # Calculate filtered total
        kw, min_price, max_price, sort_by = self.get_filters()
        products_all = self._get_filtered_products(kw, min_price, max_price, sort_by)
        filtered_total = len(products_all)

        # Update status
        if filtered_total > 0:
            start_item = (self.current_page - 1) * items_per_page_val + 1
            end_item = min(self.current_page * items_per_page_val, filtered_total)
            status_text = f"Trang {self.current_page}/{self.total_pages} • {start_item}-{end_item}/{filtered_total}"
        else:
            status_text = f"Trang {self.current_page}/{self.total_pages} • 0/0"

        self.lbl_page_status.config(text=status_text)

        # Update buttons
        self.btn_prev.config(state=tk.DISABLED if self.current_page <= 1 else tk.NORMAL)
        self.btn_next.config(state=tk.DISABLED if self.current_page >= self.total_pages else tk.NORMAL)

    def _fetch_image_async(self, pid, url_or_path, size):
        """Async image loading với caching"""
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
            img.thumbnail(size, Image.Resampling.LANCZOS)  # Use thumbnail for better performance
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

    # CRUD Operations (giữ nguyên nhưng tối ưu)
    def show_detail(self, product):
        """Show product detail"""
        ProductDetailView(self, product)

    def add(self):
        """Add new product"""
        ProductDialog(self, "Thêm sản phẩm", on_submit=self._add_submit)

    def _add_submit(self, payload):
        """Handle add submit"""
        payload['id'] = str(uuid.uuid4())
        now_iso = datetime.now().isoformat(timespec="seconds")
        payload['created_at'] = now_iso
        payload['updated_at'] = now_iso
        self.service.create(payload)
        self.refresh(reset_page=True)

    def edit(self, product_id):
        """Edit product"""
        try:
            product = next(x for x in self.service.list() if x["id"] == product_id)
            ProductDialog(self, "Sửa sản phẩm", product=product,
                          on_submit=partial(self._edit_submit, product_id))
        except StopIteration:
            messagebox.showerror("Lỗi", "Không tìm thấy sản phẩm để sửa.")

    def _edit_submit(self, product_id, patch):
        """Handle edit submit"""
        patch['updated_at'] = datetime.now().isoformat(timespec="seconds")
        self.service.update(product_id, patch)
        self.refresh()

    def delete(self, product_id):
        """Delete product"""
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa sản phẩm này?"):
            self.service.delete(product_id)
            self.refresh()


# Giữ nguyên ProductDialog và ProductDetailView classes từ code cũ...
class ProductDialog(tk.Toplevel):
    """Optimized product dialog"""

    def __init__(self, master, title, on_submit, product=None):
        super().__init__(master)
        self.title(title)
        self.grab_set()
        self.resizable(True, True)  # Allow resize
        self.geometry("600x700")
        self.on_submit = on_submit
        self.product = product or {}

        self.entries = {}
        self._create_form()

    def _create_form(self):
        """Create optimized form"""
        # Main container với scrollbar
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=15)

        # Notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True)

        # Basic info tab
        basic_tab = ttk.Frame(notebook)
        notebook.add(basic_tab, text="Thông tin cơ bản")

        # Specs tab
        specs_tab = ttk.Frame(notebook)
        notebook.add(specs_tab, text="Thông số kỹ thuật")

        # Create fields
        self._create_basic_fields(basic_tab)
        self._create_spec_fields(specs_tab)

        # Save button
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
            if key in ["price", "stock"]:
                try:
                    val = float(val) if key == "price" else int(val)
                except (ValueError, TypeError):
                    val = 0

            payload[key] = val

        # Validation
        if not payload.get("name") or not payload.get("sku"):
            messagebox.showerror("Lỗi", "Tên sản phẩm và SKU không được để trống!", parent=self)
            return

        self.on_submit(payload)
        self.destroy()


class ProductDetailView(tk.Toplevel):
    """Optimized product detail view"""

    def __init__(self, master, product):
        super().__init__(master)
        self.title(f"Chi tiết: {product.get('name', '')}")
        self.geometry("600x800")
        self.resizable(True, True)
        self.grab_set()
        self.product = product

        self._create_detail_view()

    def _create_detail_view(self):
        """Create detail view với scroll support"""
        # Create scrollable frame
        scroll_frame = ScrollableFrame(self)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=15)

        content = scroll_frame.scrollable_frame

        # Product image
        self._create_image_section(content)

        # Product title
        title_frame = ttk.Frame(content)
        title_frame.pack(fill="x", pady=(10, 20))

        ttk.Label(title_frame, text=self.product.get("name", ""),
                  font=("Arial", 18, "bold"), foreground="#2c3e50").pack()

        # Product details in organized sections
        self._create_detail_sections(content)

        # Close button
        btn_frame = ttk.Frame(content)
        btn_frame.pack(fill="x", pady=(20, 0))
        ttk.Button(btn_frame, text="🚪 Đóng", command=self.destroy).pack()

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
            ]
        }

        for section_title, fields in sections.items():
            # Check if section has any data
            has_data = any(self.product.get(key) for _, key, _ in fields if key != "description")
            if not has_data and section_title != "Thông tin cơ bản":
                continue

            # Create section
            section_frame = ttk.LabelFrame(parent, text=section_title, padding=15)
            section_frame.pack(fill="x", pady=(0, 15))

            for title, key, data_type in fields:
                value = self.product.get(key)
                if value is not None and str(value).strip():
                    self._add_detail_row(section_frame, title, value, data_type)

    def _add_detail_row(self, parent, title, value, data_type):
        """Add detail row với formatting"""
        row_frame = ttk.Frame(parent)
        row_frame.pack(fill="x", pady=3)

        # Format value based on type
        if data_type == "price":
            formatted_value = f"{value:,.0f}₫"
            color = "#28a745"
        elif data_type == "number":
            formatted_value = f"{value:,}"
            color = "#17a2b8" if value > 0 else "#dc3545"
        elif data_type == "long_text":
            formatted_value = str(value)[:200] + ("..." if len(str(value)) > 200 else "")
            color = "#495057"
        else:
            formatted_value = str(value)
            color = "#495057"

        # Title label
        ttk.Label(row_frame, text=f"{title}:",
                  font=("Arial", 10, "bold")).pack(anchor="w")

        # Value label
        value_label = tk.Label(row_frame, text=formatted_value,
                               font=("Arial", 10), fg=color,
                               wraplength=500, justify="left")
        value_label.pack(anchor="w", padx=(20, 0))
