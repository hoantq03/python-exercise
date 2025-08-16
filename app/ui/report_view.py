import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from datetime import datetime
from collections import defaultdict
import calendar


def get_most_specific_product_category(product_info):
    """
    Tìm danh mục cụ thể nhất từ list 'categories' của một sản phẩm.
    Có thể lọc bỏ các danh mục chung chung hoặc ưu tiên danh mục có tên cụ thể.
    """
    if not product_info:
        return None, None

    product_categories = product_info.get('categories', [])
    if not product_categories:
        return None, None

    # Danh sách các tên danh mục chung chung hoặc không mong muốn để báo cáo
    # Bạn có thể điều chỉnh danh sách này dựa trên dữ liệu thực tế của mình
    # Ví dụ, nếu 'Điện thoại' là một danh mục cha, bạn có thể thêm nó vào đây để loại trừ
    generic_names_to_exclude = ['root', 'điện thoại', 'phone', 'chuẩn nfc']

    # Ưu tiên các danh mục không nằm trong danh sách loại trừ
    filtered_cats = [
        cat for cat in product_categories
        if cat.get('categoryName', '').lower() not in generic_names_to_exclude
    ]

    chosen_category = None
    if filtered_cats:
        # Nếu có các danh mục đã lọc (không phải generic), lấy danh mục đầu tiên trong số đó
        chosen_category = filtered_cats[0]
    elif product_categories:
        # Nếu không có danh mục cụ thể nào (chỉ có generic), fallback về danh mục đầu tiên
        chosen_category = product_categories

    if chosen_category:
        # Sử dụng categoryId hoặc id cho ID, categoryName cho tên
        cat_id = chosen_category.get('id') or str(chosen_category.get('categoryId'))
        cat_name = chosen_category.get('categoryName')
        return cat_id, cat_name

    return None, None


class ReportFrame(ttk.Frame):
    def __init__(self, master, order_service, product_service, customer_service, user_service):
        super().__init__(master)
        self.order_service = order_service
        self.product_service = product_service
        self.customer_service = customer_service
        self.user_service = user_service

        # Biến StringVar để lưu lựa chọn cách nhóm thời gian (Tháng, Quý, Năm)
        self.group_by_var = tk.StringVar(value="Tháng")  # Mặc định là Tháng cho bộ lọc chung
        # Biến StringVar cho tháng, quý, năm
        self.month_var = tk.StringVar()
        self.quarter_var = tk.StringVar()
        self.year_var = tk.StringVar()

        # Khởi tạo các biến ngày bắt đầu và kết thúc
        self.start_date = None
        self.end_date = None

        self._create_widgets()

        # Thiết lập giá trị mặc định cho năm hiện tại và tháng hiện tại
        self.year_var.set(str(datetime.now().year))
        self.month_var.set(str(datetime.now().month))

        # Trigger lần đầu để hiện form đúng theo mặc định
        self._on_time_group_changed()
        # Gọi _apply_filters để tính toán khoảng thời gian ban đầu
        self._apply_filters()
        # Thiết lập báo cáo mặc định và hiển thị
        self.report_combo.set("Doanh thu theo thời gian")
        # No need to call _on_report_selected(None) here, as _apply_filters does it.

    def _create_widgets(self):
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill='x', padx=10, pady=5)
        filter_frame.columnconfigure(1, weight=1)

        # --- Chọn báo cáo ---
        ttk.Label(filter_frame, text="Chọn báo cáo:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.report_var = tk.StringVar()
        self.report_combo = ttk.Combobox(
            filter_frame, textvariable=self.report_var, state='readonly', values=[
                "Doanh thu theo thời gian",
                "Top sản phẩm bán chạy",
                "Báo cáo tồn kho",
                "Tổng quan khách hàng",
                "Doanh thu theo nhân viên",
                "Lợi nhuận gộp theo kỳ",
                "Khung giờ/ngày cao điểm",
                "Tăng trưởng tập khách hàng",
                "Tần suất mua và LTV khách hàng"
            ]
        )
        self.report_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.report_combo.bind('<<ComboboxSelected>>', self._on_report_selected)

        # --- Chọn nhóm thời gian ---
        ttk.Label(filter_frame, text="Nhóm thời gian:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        # values sẽ được cập nhật động trong _on_report_selected
        self.time_group_combo = ttk.Combobox(filter_frame, textvariable=self.group_by_var, state='readonly',
                                             values=["Tháng", "Quý", "Năm"])
        self.time_group_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.time_group_combo.bind('<<ComboboxSelected>>', self._on_time_group_changed)

        # --- Các ô nhập/chọn thời gian ---
        self.month_label = ttk.Label(filter_frame, text="Tháng:")
        self.month_combo = ttk.Combobox(filter_frame, textvariable=self.month_var, state='readonly',
                                        values=[str(i) for i in range(1, 13)])
        self.quarter_label = ttk.Label(filter_frame, text="Quý:")
        self.quarter_combo = ttk.Combobox(filter_frame, textvariable=self.quarter_var, state='readonly',
                                          values=[str(i) for i in range(1, 5)])
        self.year_label = ttk.Label(filter_frame, text="Năm:")
        self.year_entry = ttk.Entry(filter_frame, textvariable=self.year_var)

        # --- Nút Áp dụng ---
        self.apply_btn = ttk.Button(filter_frame, text="Áp dụng", command=self._apply_filters)
        self.apply_btn.grid(row=99, column=0, columnspan=2,
                            pady=10)  # row 99 chỉ là một số lớn để đảm bảo nó ở dưới cùng

        # --- Khung chứa biểu đồ ---
        self.canvas_frame = ttk.Frame(self)
        self.canvas_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # --- Label hiển thị thông tin thời gian báo cáo ---
        # Changed parent from self.canvas_frame to self to allow independent packing
        self.report_time_info_label = ttk.Label(self, text="", font=("Arial", 9, "italic"))
        self.report_time_info_label.pack(pady=(0, 5), padx=10, anchor='w')

    def _on_time_group_changed(self, event=None):
        """
        Xử lý khi lựa chọn Tháng/Quý/Năm thay đổi.
        Ẩn/hiện các ô nhập liệu thời gian tương ứng.
        """
        # Ẩn tất cả các input thời gian trước
        self.month_label.grid_forget()
        self.month_combo.grid_forget()
        self.quarter_label.grid_forget()
        self.quarter_combo.grid_forget()
        self.year_label.grid_forget()
        self.year_entry.grid_forget()

        # Đảm bảo các widget được enable trước khi ẩn/hiện,
        # tránh trường hợp bị disable từ báo cáo tồn kho
        self.month_combo.config(state='readonly')
        self.quarter_combo.config(state='readonly')
        self.year_entry.config(state='normal')

        group = self.group_by_var.get()
        current_row = 2

        # Hiển thị các input phù hợp và cập nhật vị trí nút "Áp dụng"
        if group == "Tháng":
            self.month_label.grid(row=current_row, column=0, padx=5, pady=5, sticky="w")
            self.month_combo.grid(row=current_row, column=1, sticky="ew", padx=5, pady=5)
            current_row += 1
            self.year_label.grid(row=current_row, column=0, padx=5, pady=5, sticky="w")
            self.year_entry.grid(row=current_row, column=1, sticky="ew", padx=5, pady=5)
            current_row += 1
        elif group == "Quý":
            self.quarter_label.grid(row=current_row, column=0, padx=5, pady=5, sticky="w")
            self.quarter_combo.grid(row=current_row, column=1, sticky="ew", padx=5, pady=5)
            current_row += 1
            self.year_label.grid(row=current_row, column=0, padx=5, pady=5, sticky="w")
            self.year_entry.grid(row=current_row, column=1, sticky="ew", padx=5, pady=5)
            current_row += 1
        elif group == "Năm":
            self.year_label.grid(row=current_row, column=0, padx=5, pady=5, sticky="w")
            self.year_entry.grid(row=current_row, column=1, sticky="ew", padx=5, pady=5)
            current_row += 1

        # Cập nhật vị trí nút "Áp dụng"
        self.apply_btn.grid(row=current_row, column=0, columnspan=2, pady=10)

    def _apply_filters(self):
        """
        Áp dụng bộ lọc thời gian và cập nhật khoảng thời gian báo cáo.
        """
        report_name = self.report_var.get()

        if report_name == "Báo cáo tồn kho":
            self.start_date = None
            self.end_date = None
            self._update_report_time_info()
            self._plot_inventory_report() # Call the specific plot function
            return

        year_str = self.year_var.get().strip()

        # Validate Năm
        if not year_str.isdigit() or int(year_str) < 1900 or int(year_str) > datetime.now().year + 5: # Allow a few years into future for planning
            messagebox.showerror("Lỗi", "Vui lòng nhập năm hợp lệ (1900 đến hiện tại + 5 năm).")
            self.start_date = None
            self.end_date = None
            self._update_report_time_info()
            return

        year = int(year_str)
        group = self.group_by_var.get()

        try:
            if group == "Tháng":
                month_str = self.month_var.get().strip()
                if not month_str.isdigit() or int(month_str) < 1 or int(month_str) > 12:
                    messagebox.showerror("Lỗi", "Vui lòng chọn tháng hợp lệ từ dropdown (1-12).")
                    self.start_date = None
                    self.end_date = None
                    self._update_report_time_info()
                    return
                month = int(month_str)
                self.start_date = datetime(year, month, 1)
                last_day = calendar.monthrange(year, month)[1]
                self.end_date = datetime(year, month, last_day, 23, 59, 59)
            elif group == "Quý":
                quarter_str = self.quarter_var.get().strip()
                if not quarter_str.isdigit() or int(quarter_str) < 1 or int(quarter_str) > 4:
                    messagebox.showerror("Lỗi", "Vui lòng chọn quý hợp lệ từ dropdown (1-4).")
                    self.start_date = None
                    self.end_date = None
                    self._update_report_time_info()
                    return
                quarter = int(quarter_str)
                month_start = (quarter - 1) * 3 + 1
                month_end = month_start + 2
                self.start_date = datetime(year, month_start, 1)
                last_day = calendar.monthrange(year, month_end)[1]
                self.end_date = datetime(year, month_end, last_day, 23, 59, 59)
            elif group == "Năm":
                self.start_date = datetime(year, 1, 1)
                self.end_date = datetime(year, 12, 31, 23, 59, 59)
        except Exception as e:
            messagebox.showerror("Lỗi ngày tháng", f"Có lỗi khi thiết lập khoảng thời gian: {e}")
            self.start_date = None
            self.end_date = None
            self._update_report_time_info()
            return

        # Update the report time info label after filters are applied
        self._update_report_time_info()

        # Tự động gọi lại báo cáo hiện tại sau khi áp dụng bộ lọc
        if self.report_var.get():
            self._on_report_selected(None)

    def _update_report_time_info(self):
        report_name = self.report_var.get()

        if report_name == "Báo cáo tồn kho":
            self.report_time_info_label.config(text="Thống kê báo cáo từ trước đến nay.",
                                               foreground='black',
                                               font=("Arial", 9, "italic"))
        else:
            if self.start_date and self.end_date:
                start_display = self.start_date.strftime("%d/%m/%Y")
                end_display = self.end_date.strftime("%d/%m/%Y")

                # Cập nhật text, màu chữ và font
                self.report_time_info_label.config(text=f"Thống kê báo cáo từ {start_display} đến {end_display}.",
                                                   foreground='red',
                                                   font=("Arial", 12, "bold"))
            else:
                self.report_time_info_label.config(text="Vui lòng chọn khoảng thời gian để báo cáo.",
                                                   foreground='black',
                                                   font=("Arial", 12, "italic"))

    def _filter_orders_by_date(self, orders):
        """
        Lọc danh sách đơn hàng dựa trên khoảng thời gian đã chọn.
        """
        # Nếu start_date hoặc end_date chưa được thiết lập (ví dụ, lỗi validation ban đầu)
        if not self.start_date or not self.end_date:
            print("Lọc: Khoảng thời gian không hợp lệ. Trả về rỗng.")
            return []  # Trả về rỗng

        filtered = []
        for o in orders:
            order_date_str = o.get('order_date')
            if not order_date_str:
                continue
            try:
                dt = datetime.strptime(order_date_str, "%Y-%m-%dT%H:%M:%S")
                if self.start_date <= dt <= self.end_date:
                    filtered.append(o)
            except ValueError:
                print(f"Lọc: Lỗi định dạng ngày cho đơn hàng ID {o.get('id', 'N/A')}: '{order_date_str}'. Bỏ qua.")
                continue
        print(f"Lọc: Đã lọc {len(filtered)}/{len(orders)} đơn hàng trong khoảng {self.start_date} - {self.end_date}")
        return filtered

    def _aggregate_orders_by_time(self, orders):
        """
        Tổng hợp dữ liệu đơn hàng (doanh thu) theo lựa chọn nhóm (Tháng, Quý, Năm).
        """
        data = defaultdict(float)
        group_by = self.group_by_var.get()

        for o in orders:
            try:
                dt = datetime.strptime(o['order_date'], "%Y-%m-%dT%H:%M:%S")
            except (KeyError, ValueError):
                continue

            key = ""
            if group_by == "Tháng":
                key = dt.strftime("%Y-%m")
            elif group_by == "Quý":
                quarter = (dt.month - 1) // 3 + 1
                key = f"{dt.year}-Q{quarter}"
            elif group_by == "Năm":
                key = str(dt.year)

            data[key] += o.get('total_amount', 0)

        # Sắp xếp dữ liệu theo khóa thời gian để biểu đồ hiển thị đúng thứ tự
        return dict(sorted(data.items()))

    def _on_group_by_changed(self, event=None):
        """
        Xử lý khi lựa chọn nhóm theo (Tháng/Quý/Năm) thay đổi.
        Cập nhật lại giao diện bộ lọc và báo cáo hiện tại.
        """
        # Cập nhật lại các ô input cho phù hợp với lựa chọn nhóm
        self._on_time_group_changed()
        if self.report_var.get():
            self._on_report_selected()

    def _on_report_selected(self, event=None):
        """
        Xử lý khi loại báo cáo được chọn từ Combobox.
        Xóa biểu đồ cũ và vẽ biểu đồ mới.
        """
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()
        plt.close('all')


        report_name = self.report_var.get()
        if not report_name:
            return

        # Update values and state for time_group_combo based on selected report
        if report_name == "Doanh thu theo thời gian":
            self.time_group_combo.config(values=["Năm", "Quý"], state='readonly')
            # If group_by_var is "Tháng", switch to "Năm"
            if self.group_by_var.get() == "Tháng":
                self.group_by_var.set("Năm")
            self.month_combo.config(state='readonly')
            self.quarter_combo.config(state='readonly')
            self.year_entry.config(state='normal')
            self.apply_btn.config(state='normal')
            self._on_time_group_changed() # Re-grid based on selected time group
        elif report_name == "Báo cáo tồn kho":
            # Disable all time filter options for inventory report
            self.time_group_combo.config(state='disabled')
            self.month_combo.config(state='disabled')
            self.quarter_combo.config(state='disabled')
            self.year_entry.config(state='disabled')
            self.apply_btn.config(state='disabled')
            # Hide the time-related labels/comboboxes
            self.month_label.grid_forget()
            self.month_combo.grid_forget()
            self.quarter_label.grid_forget()
            self.year_label.grid_forget()
            self.year_entry.grid_forget()
        elif report_name in ["Doanh thu theo nhân viên", "Lợi nhuận gộp theo kỳ", "Khung giờ/ngày cao điểm"]:
            self.time_group_combo.config(values=["Tháng", "Quý", "Năm"], state='readonly')
            self.month_combo.config(state='readonly')
            self.quarter_combo.config(state='readonly')
            self.year_entry.config(state='normal')
            self.apply_btn.config(state='normal')
            self._on_time_group_changed()
        else:  # Other reports can select Tháng, Quý, Năm
            self.time_group_combo.config(values=["Tháng", "Quý", "Năm"], state='readonly')
            self.month_combo.config(state='readonly')
            self.quarter_combo.config(state='readonly')
            self.year_entry.config(state='normal')
            self.apply_btn.config(state='normal')
            self._on_time_group_changed() # Re-grid based on selected time group


        # Update the time info label
        self._update_report_time_info()

        # Định nghĩa các phương thức vẽ biểu đồ
        plot_methods = {
            "Doanh thu theo thời gian": self._plot_revenue_over_time,
            "Top sản phẩm bán chạy": self._plot_top_products,
            "Báo cáo tồn kho": self._plot_inventory_report,
            "Tổng quan khách hàng": self._plot_customer_summary,
            "Doanh thu theo nhân viên": self._plot_sales_by_employee,
            "Lợi nhuận gộp theo kỳ": self._plot_gross_profit_over_time,
            "Khung giờ/ngày cao điểm": self._plot_peak_hours_and_days,
            "Tăng trưởng tập khách hàng": self._plot_customer_growth,
            "Tần suất mua và LTV khách hàng": self._plot_customer_ltv_and_frequency
        }

        plot_func = plot_methods.get(report_name)
        if plot_func:
            plot_func()

    def _plot_revenue_over_time(self):
        orders = self.order_service.list_orders()

        # Chỉ lọc dữ liệu trong khoảng Năm hoặc Quý đã chọn
        filtered_orders = self._filter_orders_by_date(orders)

        # Xác định năm/quý đang báo cáo
        year_to_report = int(self.year_var.get())
        group = self.group_by_var.get()

        labels = []
        values_m = []  # Doanh thu theo triệu VNĐ

        if group == "Năm":
            # Hiển thị toàn bộ 12 tháng của năm đã chọn
            all_month_keys = [datetime(year_to_report, m, 1).strftime("%Y-%m") for m in range(1, 13)]
            labels = [datetime.strptime(mk, "%Y-%m").strftime("%m/%Y") for mk in all_month_keys] # Format for display

            # Lấy doanh thu từng tháng từ dữ liệu đã lọc
            monthly_revenue = defaultdict(float)
            for o in filtered_orders:
                try:
                    dt = datetime.strptime(o['order_date'], "%Y-%m-%dT%H:%M:%S")
                    month_key = dt.strftime("%Y-%m")
                    monthly_revenue[month_key] += o.get('total_amount', 0)
                except (KeyError, ValueError):
                    pass

            values_m = [monthly_revenue.get(month_key, 0) / 1_000_000 for month_key in all_month_keys]

        elif group == "Quý":
            quarter_to_report = int(self.quarter_var.get())
            start_month_int = (quarter_to_report - 1) * 3 + 1
            end_month_int = start_month_int + 2

            # Generate month keys for the selected quarter
            all_month_keys_in_quarter = [datetime(year_to_report, m, 1).strftime("%Y-%m") for m in range(start_month_int, end_month_int + 1)]
            labels = [datetime.strptime(mk, "%Y-%m").strftime("%m/%Y") for mk in all_month_keys_in_quarter] # Format for display

            # Aggregate revenue by month within the quarter
            monthly_revenue_in_quarter = defaultdict(float)
            for o in filtered_orders:
                try:
                    dt = datetime.strptime(o['order_date'], "%Y-%m-%dT%H:%M:%S")
                    month_key = dt.strftime("%Y-%m")
                    monthly_revenue_in_quarter[month_key] += o.get('total_amount', 0)
                except (KeyError, ValueError):
                    pass

            values_m = [monthly_revenue_in_quarter.get(month_key, 0) / 1_000_000 for month_key in all_month_keys_in_quarter]

        if not values_m or all(v == 0 for v in values_m):  # Kiểm tra nếu tất cả giá trị đều là 0
            ttk.Label(self.canvas_frame,
                      text="Không có dữ liệu doanh thu để hiển thị trong khoảng thời gian đã chọn.").pack(pady=20)
            return

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(labels, values_m, marker='o')
        ax.set_title(f"Doanh thu theo {group} trong năm {year_to_report}")
        ax.set_xlabel("Thời gian")
        ax.set_ylabel("Doanh thu (triệu VNĐ)")
        ax.grid(True)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

        note_text = (
            "Biểu đồ này thể hiện xu hướng doanh thu tổng cộng trong khoảng thời gian đã chọn. "
            "Các điểm trên biểu đồ tương ứng với tổng doanh thu tích lũy của từng tháng trong năm/quý báo cáo. "
            "Giúp theo dõi hiệu suất bán hàng theo thời gian."
        )
        ttk.Label(self.canvas_frame, text=note_text, wraplength=800, justify='left',
                  font=("Arial", 12, "italic")).pack(pady=10, padx=10, anchor='w')

    def _plot_top_products(self):
        orders = self.order_service.list_orders()
        filtered_orders = self._filter_orders_by_date(orders)
        product_sales = defaultdict(float)

        for o in filtered_orders:
            for it in o.get('items', []):
                name = str(it.get('name', 'N/A'))
                product_sales[name] += it.get('quantity', 0) * it.get('price', 0)

        if not product_sales:
            ttk.Label(self.canvas_frame,
                      text="Không có dữ liệu sản phẩm bán chạy để hiển thị trong khoảng thời gian đã chọn.").pack(
                pady=20)
            return

        top_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:10]
        names = [t[0] for t in top_products]  # Extract only the name
        sales = [v / 1_000_000 for _, v in top_products]

        # Explicitly close any existing plot before creating a new one
        plt.close('all')
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.barh(range(len(names)), sales, color='skyblue')
        ax.set_yticks([])
        ax.invert_yaxis()
        ax.set_xlabel("Doanh thu (triệu VNĐ)")
        ax.set_title("Top 10 sản phẩm bán chạy theo doanh thu")
        ax.grid(True, axis='x')

        for i, bar in enumerate(bars):
            text_x = bar.get_width() / 2
            text_y = bar.get_y() + bar.get_height() / 2
            ax.text(text_x, text_y, f'{names[i]}\n{sales[i]:.1f}M', va='center', ha='center',
                    fontsize=8, color='black')

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        note_text = (
            "Biểu đồ này hiển thị danh sách các sản phẩm hàng đầu dựa trên doanh thu hoặc số lượng bán ra trong khoảng thời gian đã chọn. "
            "Nó giúp nhận diện những mặt hàng chủ lực, được khách hàng ưa chuộng, từ đó hỗ trợ quyết định về chiến lược marketing, tồn kho và phát triển sản phẩm."
        )
        ttk.Label(self.canvas_frame, text=note_text, wraplength=800, justify='left',
                  font=("Arial", 12, "italic")).pack(pady=10, padx=10, anchor='w')

    def _plot_inventory_report(self):
        products = self.product_service.list() # Assume this lists all products regardless of time
        if not products:
            ttk.Label(self.canvas_frame, text="Không có dữ liệu sản phẩm để hiển thị tồn kho.").pack(pady=20)
            return

        top_stock_products = sorted(products, key=lambda p: p.get('stock', 0), reverse=True)[:10]
        names = [str(p.get('name', 'N/A')) for p in top_stock_products]
        stocks = [p.get('stock', 0) for p in top_stock_products]

        # Explicitly close any existing plot before creating a new one
        plt.close('all')
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.barh(range(len(names)), stocks, color='mediumseagreen')
        ax.set_yticks([])
        ax.invert_yaxis()
        ax.set_xlabel("Số lượng tồn kho")
        ax.set_title("Top 10 sản phẩm tồn kho nhiều nhất")
        ax.grid(True, axis='x')

        for i, bar in enumerate(bars):
            text_x = bar.get_width() / 2
            text_y = bar.get_y() + bar.get_height() / 2
            ax.text(text_x, text_y, f'{names[i]}\n{stocks[i]}', va='center', ha='center', fontsize=8, color='white')

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        note_text = ("Báo cáo này cung cấp cái nhìn tổng quan về tình trạng tồn kho hiện tại của các sản phẩm."
                     " Nó liệt kê số lượng hàng còn lại trong kho, giúp xác định sản phẩm cần bổ sung, sản phẩm tồn đọng hoặc sản phẩm sắp hết hàng."
                     " Báo cáo này là công cụ quan trọng để quản lý chuỗi cung ứng và tránh tình trạng thiếu hụt hoặc dư thừa hàng hóa.")
        ttk.Label(self.canvas_frame, text=note_text, wraplength=800, justify='left',
                  font=("Arial", 12, "italic")).pack(pady=10, padx=10, anchor='w')

    def _plot_customer_summary(self):
        orders = self.order_service.list_orders()
        filtered_orders = self._filter_orders_by_date(orders)
        customer_purchase_value = defaultdict(float)

        for o in filtered_orders:
            customer_name = o.get('customer_info', {}).get('name', 'Khách vãng lai')
            customer_purchase_value[customer_name] += o.get('total_amount', 0)

        if not customer_purchase_value:
            ttk.Label(self.canvas_frame,
                      text="Không có dữ liệu khách hàng để hiển thị trong khoảng thời gian đã chọn.").pack(pady=20)
            return

        top_customers = sorted(customer_purchase_value.items(), key=lambda x: x[1], reverse=True)[:10]
        names = [t[0] for t in top_customers]  # Correctly extract only customer names for y-axis
        values = [v / 1_000_000 for _, v in top_customers]  # Convert to triệu đồng

        # Explicitly close any existing plot before creating a new one
        plt.close('all')
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.barh(range(len(names)), values, color='gold')

        # Set y-axis ticks and labels to display customer names
        ax.set_yticks(range(len(names)))
        ax.set_yticklabels(names)  # Use the 'names' list directly for labels

        ax.invert_yaxis()  # Keep the highest value at the top
        ax.set_xlabel("Tổng chi tiêu (triệu VNĐ)")
        ax.set_title("Top 10 khách hàng chi tiêu nhiều nhất")
        ax.grid(True, axis='x')

        for i, bar in enumerate(bars):
            # Position the text slightly to the right of the bar
            text_x = bar.get_width() + (ax.get_xlim()[1] * 0.01)  # Small offset
            text_y = bar.get_y() + bar.get_height() / 2

            # Display only the formatted monetary value on the bar
            ax.text(text_x, text_y, f'{values[i]:.1f}Triệu Đồng', va='center', ha='left', fontsize=8, color='black')

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        note_text = (
            "Báo cáo này cung cấp cái nhìn tổng quan về tập khách hàng của bạn trong một kỳ."
            " Nó có thể bao gồm tổng số khách hàng đã mua, số lượng khách hàng mới và khách hàng quay lại."
            " Báo cáo này giúp đánh giá sức khỏe của cơ sở khách hàng và hiệu quả của các chiến dịch thu hút và giữ chân khách hàng."
        )
        ttk.Label(self.canvas_frame, text=note_text, wraplength=800, justify='left',
                  font=("Arial", 12, "italic")).pack(pady=10, padx=10, anchor='w')

    def _calc_order_revenue_cogs(self, order):
        revenue = float(order.get('total_amount', 0))
        cogs = 0.0
        for it in order.get('items', []):
            qty = float(it.get('quantity', 0) or 0)
            price = float(it.get('price', 0) or 0)
            cost = it.get('cost')
            if cost is None:
                # Nếu có SKU và product_service hỗ trợ tra cost theo SKU:
                sku = it.get('sku')
                if sku and hasattr(self.product_service, 'get_cost_by_sku'):
                    cost = self.product_service.get_cost_by_sku(sku) or 0
                else:
                    # fallback: nếu không có cost, coi cost=price để tránh âm (tùy hệ thống)
                    cost = 0
            cogs += qty * float(cost or 0)
        gross_profit = revenue - cogs
        margin = (gross_profit / revenue * 100) if revenue > 0 else 0.0
        return revenue, cogs, gross_profit, margin

    def _plot_sales_by_employee(self):
        orders = self.order_service.list_orders()
        filtered_orders = self._filter_orders_by_date(orders)
        sales_by_emp = defaultdict(float)

        for o in filtered_orders:
            emp_id = o.get('user_id') or 'N/A'
            emp_name = 'N/A'

            print(f"Processing order: {o.get('order_id')}, user_id: {emp_id}")  # Debug 1

            if emp_id != 'N/A':
                user_info = self.user_service.get_user_by_id(emp_id)
                print(f"  User info retrieved for {emp_id}: {user_info}")  # Debug 2
                if user_info:
                    name = user_info.get('name')
                    if name and name.strip():
                        emp_name = name
                    else:
                        emp_name = f'ID: {emp_id}'
                        print(f"  Warning: User {emp_id} has no valid 'name' field. Using ID.")  # Debug 3
                else:
                    emp_name = f'ID: {emp_id}'
                    print(f"  Warning: User {emp_id} not found in UserService. Using ID.")  # Debug 4

            sales_by_emp[emp_name] += float(o.get('total_amount', 0) or 0)

        print(f"Final sales_by_emp content: {sales_by_emp}")

        if not sales_by_emp:
            ttk.Label(self.canvas_frame, text="Không có dữ liệu doanh thu theo nhân viên trong khoảng đã chọn.").pack(
                pady=20)
            return

        top = sorted(sales_by_emp.items(), key=lambda x: x[1], reverse=True)[:10]
        names = [t[0] for t in top]
        values = [t[1] / 1_000_000 for t in top]

        plt.close('all')
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.barh(range(len(names)), values, color='#4C78A8')
        ax.set_yticks(range(len(names)))
        ax.set_yticklabels(names)
        ax.invert_yaxis()
        ax.set_xlabel("Doanh thu (triệu VNĐ)")
        ax.set_title("Top 10 nhân viên theo doanh thu")
        ax.grid(True, axis='x')

        for i, bar in enumerate(bars):
            ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2, f'{values[i]:.1f}M', va='center',
                    ha='left', fontsize=8)

        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        note_text = (
            "Biểu đồ này minh họa tổng doanh thu mà mỗi nhân viên đã đóng góp trong khoảng thời gian đã chọn. "
            "Nó giúp đánh giá hiệu suất cá nhân của đội ngũ bán hàng, nhận diện những nhân viên có thành tích xuất sắc và hỗ trợ việc phân bổ nguồn lực hiệu quả hơn."
        )
        ttk.Label(self.canvas_frame, text=note_text, wraplength=800, justify='left',
                  font=("Arial", 12, "italic")).pack(pady=10, padx=10, anchor='w')

    def _time_key_for_dt(self, dt, group):
        if group == "Tháng":
            return dt.strftime("%Y-%m")
        elif group == "Quý":
            q = (dt.month - 1) // 3 + 1
            return f"{dt.year}-Q{q}"
        else:
            return str(dt.year)

    def _plot_gross_profit_over_time(self):
        orders = self.order_service.list_orders()
        filtered_orders = self._filter_orders_by_date(orders)
        group = self.group_by_var.get()

        agg = {}  # key -> dict(revenue, cogs)
        for o in filtered_orders:
            try:
                dt = datetime.strptime(o['order_date'], "%Y-%m-%dT%H:%M:%S")
            except (KeyError, ValueError):
                continue
            key = self._time_key_for_dt(dt, group)
            r, c, _, _ = self._calc_order_revenue_cogs(o)
            if key not in agg:
                agg[key] = {'revenue': 0.0, 'cogs': 0.0}
            agg[key]['revenue'] += r
            agg[key]['cogs'] += c

        if not agg:
            ttk.Label(self.canvas_frame, text="Không có dữ liệu lợi nhuận gộp trong khoảng đã chọn.").pack(pady=20)
            return

        # Sắp xếp theo thời gian
        def sort_key(k):
            if group == "Tháng":
                return datetime.strptime(k, "%Y-%m")
            if group == "Quý":
                y, q = k.split("-Q")
                return (int(y), int(q))
            return int(k)

        keys = sorted(agg.keys(), key=sort_key)
        rev = [agg[k]['revenue'] / 1_000_000 for k in keys]
        cogs = [agg[k]['cogs'] / 1_000_000 for k in keys]
        margin = []
        for k in keys:
            r = agg[k]['revenue']
            g = r - agg[k]['cogs']
            m = (g / r * 100) if r > 0 else 0
            margin.append(m)

        # Nhãn đẹp
        if group == "Tháng":
            labels = [datetime.strptime(k, "%Y-%m").strftime("%m/%Y") for k in keys]
        else:
            labels = keys

        plt.close('all')
        fig, ax1 = plt.subplots(figsize=(11, 6))
        x = range(len(labels))
        width = 0.35

        b1 = ax1.bar([i - width / 2 for i in x], rev, width=width, label="Doanh thu", color="#4C78A8")
        b2 = ax1.bar([i + width / 2 for i in x], cogs, width=width, label="COGS", color="#F58518")
        ax1.set_ylabel("Triệu VNĐ")
        ax1.set_xlabel("Kỳ")
        ax1.set_title(f"Lợi nhuận gộp theo {group}")
        ax1.grid(True, axis='y')
        ax1.set_xticks(list(x))
        ax1.set_xticklabels(labels, rotation=45, ha='right')

        ax2 = ax1.twinx()
        ax2.plot(x, margin, color="#54A24B", marker='o', label="Biên LN (%)")
        ax2.set_ylabel("Biên lợi nhuận (%)")

        # Chú thích
        lines = [b1, b2, ax2.lines[0]]
        labels_legend = ["Doanh thu", "COGS", "Biên LN (%)"]
        ax1.legend(lines, labels_legend, loc="upper left")

        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        note_text = (
            "Biểu đồ này hiển thị tổng lợi nhuận gộp trong các kỳ thời gian khác nhau (ví dụ: tháng, quý, năm)."
            " Lợi nhuận gộp được tính bằng tổng doanh thu trừ đi tổng giá vốn hàng bán."
            " Báo cáo này giúp đánh giá khả năng sinh lời của doanh nghiệp theo thời gian và là chỉ số quan trọng để phân tích sức khỏe tài chính."
        )
        ttk.Label(self.canvas_frame, text=note_text, wraplength=800, justify='left',
                  font=("Arial", 12, "italic")).pack(pady=10, padx=10, anchor='w')

    def _plot_peak_hours_and_days(self):
        orders = self.order_service.list_orders()
        filtered = self._filter_orders_by_date(orders)
        if not filtered:
            ttk.Label(self.canvas_frame, text="Không có dữ liệu trong khoảng đã chọn.").pack(pady=20)
            return

        revenue_by_hour = [0.0] * 24
        revenue_by_dow = [0.0] * 7  # 0=Mon ... 6=Sun

        for o in filtered:
            try:
                dt = datetime.strptime(o['order_date'], "%Y-%m-%dT%H:%M:%S")
            except (KeyError, ValueError):
                continue
            amount = float(o.get('total_amount', 0) or 0)
            revenue_by_hour[dt.hour] += amount
            revenue_by_dow[dt.weekday()] += amount

        # Scale to triệu
        rev_hour_m = [v / 1_000_000 for v in revenue_by_hour]
        rev_dow_m = [v / 1_000_000 for v in revenue_by_dow]
        dow_labels = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]

        plt.close('all')
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8))

        # Biểu đồ theo giờ
        ax1.plot(range(24), rev_hour_m, marker='o', color="#4C78A8")
        ax1.set_title("Doanh thu theo khung giờ (0-23)")
        ax1.set_xlabel("Giờ")
        ax1.set_ylabel("Doanh thu (triệu VNĐ)")
        ax1.grid(True)
        ax1.set_xticks(range(0, 24, 1))
        for x, y in enumerate(rev_hour_m):
            if y > 0:
                ax1.text(x, y, f"{y:.1f}", ha='center', va='bottom', fontsize=8)

        # Biểu đồ theo ngày trong tuần
        ax2.bar(dow_labels, rev_dow_m, color="#54A24B")
        ax2.set_title("Doanh thu theo ngày trong tuần")
        ax2.set_xlabel("Ngày")
        ax2.set_ylabel("Doanh thu (triệu VNĐ)")
        ax2.grid(True, axis='y')
        for i, v in enumerate(rev_dow_m):
            if v > 0:
                ax2.text(i, v, f"{v:.1f}", ha='center', va='bottom', fontsize=8)

        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        note_text = (
            "Biểu đồ này phân tích và hiển thị những khung giờ hoặc ngày trong tuần có hoạt động mua sắm cao điểm nhất."
            " Bằng cách nhận diện các khoảng thời gian bận rộn này, doanh nghiệp có thể tối ưu hóa việc phân bổ nhân sự, lập kế hoạch khuyến mãi và đảm bảo dịch vụ khách hàng tốt nhất."
        )
        ttk.Label(self.canvas_frame, text=note_text, wraplength=800, justify='left',
                  font=("Arial", 12, "italic")).pack(pady=10, padx=10, anchor='w')

    def _plot_customer_growth(self):
        orders = self.order_service.list_orders()
        # ... (phần còn lại của code cho báo cáo tăng trưởng khách hàng)
        filtered_orders = self._filter_orders_by_date(orders)

        first_purchase_dates = defaultdict(lambda: datetime.max)
        for o in orders:  # Lặp qua TẤT CẢ order để tìm ngày mua đầu tiên
            user_id = o.get('user_id')
            dt_str = o.get('order_date')
            if not user_id or not dt_str:
                continue
            try:
                dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
                first_purchase_dates[user_id] = min(first_purchase_dates[user_id], dt)
            except ValueError:
                continue

        new_customers = 0
        returning_customers = 0
        customers_in_period = set()

        for o in filtered_orders:  # Lặp qua order ĐÃ LỌC cho kỳ báo cáo
            user_id = o.get('user_id')
            if not user_id:
                continue
            if user_id in customers_in_period:  # Chỉ tính 1 lần mỗi khách trong kỳ
                continue
            # order_date = datetime.strptime(o.get('order_date'), "%Y-%m-%dT%H:%M:%S") # Không dùng biến này ở đây
            customers_in_period.add(user_id)
            if first_purchase_dates[user_id] >= self.start_date:  # So sánh với start_date của kỳ báo cáo
                new_customers += 1
            else:
                returning_customers += 1

        labels = ['Khách mới', 'Khách quay lại']
        counts = [new_customers, returning_customers]

        if new_customers + returning_customers == 0:
            ttk.Label(self.canvas_frame, text="Không có dữ liệu khách hàng trong khoảng thời gian đã chọn.").pack(
                pady=20)
            return

        plt.close('all')
        fig, ax = plt.subplots(figsize=(8, 5))
        bars = ax.bar(labels, counts, color=['#4C78A8', '#F58518'])
        ax.set_title('Tăng trưởng tập khách hàng')
        ax.set_ylabel('Số lượng khách hàng')

        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, height + 0.1, str(count), ha='center', va='bottom')

        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        note_text = (
            "Báo cáo này tập trung vào sự thay đổi trong cơ sở khách hàng của bạn, đặc biệt là số lượng khách hàng mới và khách hàng quay lại trong khoảng thời gian được phân tích."
            " Nó giúp đánh giá hiệu quả của các chiến lược thu hút khách hàng mới và khả năng duy trì mối quan hệ với khách hàng hiện có."
        )
        ttk.Label(self.canvas_frame, text=note_text, wraplength=800, justify='left',
                  font=("Arial", 12, "italic")).pack(pady=10, padx=10, anchor='w')

    def _plot_customer_ltv_and_frequency(self):
        orders = self.order_service.list_orders()
        filtered_orders = self._filter_orders_by_date(orders)

        customer_orders = defaultdict(lambda: {'total_amount': 0.0, 'order_dates': []})

        for o in filtered_orders:
            user_id = o.get('user_id')
            if not user_id:
                continue
            dt_str = o.get('order_date')
            try:
                dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
            except Exception:  # Nên bắt các exception cụ thể hơn như ValueError
                continue

            customer_orders[user_id]['total_amount'] += o.get('total_amount', 0)
            customer_orders[user_id]['order_dates'].append(dt)

        if not customer_orders:
            ttk.Label(self.canvas_frame, text="Không có dữ liệu để tính LTV và tần suất mua.").pack(pady=20)
            return

        labels = []
        ltvs = []
        avg_freq_days = []

        for user_id, data in customer_orders.items():
            # Sử dụng self.user_service để lấy tên khách hàng nếu cần, giống như _plot_sales_by_employee
            user_info = self.user_service.get_user_by_id(user_id)
            display_name = user_info.get('name') if user_info and user_info.get('name') else f'ID: {user_id}'

            dates_sorted = sorted(data['order_dates'])

            # Tính LTV
            ltv = data['total_amount']

            # Tính tần suất trung bình (ngày)
            if len(dates_sorted) > 1:
                intervals = [(dates_sorted[i] - dates_sorted[i - 1]).days for i in range(1, len(dates_sorted))]
                avg_days = sum(intervals) / len(intervals)
            else:
                avg_days = 0  # Chỉ mua 1 lần hoặc không có giao dịch trong kỳ

            labels.append(display_name)  # Sử dụng tên hiển thị
            ltvs.append(ltv / 1_000_000)  # Triệu VNĐ
            avg_freq_days.append(avg_days)

        # Vẽ biểu đồ LTV (Bar chart)
        plt.close('all')
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(labels, ltvs, color='#4C78A8')
        ax.set_title('Giá trị vòng đời khách hàng (LTV) theo khách hàng')
        ax.set_xlabel('Khách hàng')  # Đổi nhãn
        ax.set_ylabel('LTV (triệu VNĐ)')
        ax.grid(True, axis='y')
        plt.xticks(rotation=45, ha='right')  # Xoay nhãn để dễ đọc

        for bar, val in zip(bars, ltvs):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, height + 0.05, f'{val:.2f}', ha='center', va='bottom',
                    fontsize=8)

        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

        # Vẽ biểu đồ tần suất mua (Line chart)
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        ax2.plot(labels, avg_freq_days, marker='o', color='#F58518')
        ax2.set_title('Tần suất mua trung bình (ngày) theo khách hàng')
        ax2.set_xlabel('Khách hàng')  # Đổi nhãn
        ax2.set_ylabel('Ngày')
        ax2.grid(True)
        plt.xticks(rotation=45, ha='right')  # Xoay nhãn để dễ đọc

        plt.tight_layout()
        canvas2 = FigureCanvasTkAgg(fig2, master=self.canvas_frame)
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill='both', expand=True)
        note_text = (
            "Báo cáo này cung cấp thông tin chi tiết về hành vi mua sắm của từng khách hàng."
            " 'Tần suất mua' thể hiện mức độ thường xuyên khách hàng thực hiện giao dịch."
            " 'Giá trị vòng đời khách hàng (LTV)' ước tính tổng giá trị mà một khách hàng mang lại cho doanh nghiệp trong suốt mối quan hệ của họ."
            " Báo cáo này rất hữu ích để phân khúc khách hàng, xây dựng các chiến lược giữ chân khách hàng và cá nhân hóa trải nghiệm mua sắm."
        )
        ttk.Label(self.canvas_frame, text=note_text, wraplength=800, justify='left',
                  font=("Arial", 12, "italic")).pack(pady=10, padx=10, anchor='w')