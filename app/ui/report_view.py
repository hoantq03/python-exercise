import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from datetime import datetime
from collections import defaultdict
import calendar


class ReportFrame(ttk.Frame):
    def __init__(self, master, order_service, product_service, customer_service):
        super().__init__(master)
        self.order_service = order_service
        self.product_service = product_service
        self.customer_service = customer_service

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
        self._on_report_selected(None)

    def _create_widgets(self):
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill='x', padx=10, pady=5)
        filter_frame.columnconfigure(1, weight=1)

        # --- Chọn báo cáo ---
        ttk.Label(filter_frame, text="Chọn báo cáo:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.report_var = tk.StringVar()
        self.report_combo = ttk.Combobox(filter_frame, textvariable=self.report_var, state='readonly', values=[
            "Doanh thu theo thời gian",
            "Top sản phẩm bán chạy",
            "Báo cáo tồn kho",
            "Tổng quan khách hàng"
        ])
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
            self.report_time_info_label.config(text="Thống kê báo cáo từ trước đến nay.")
        else:
            if self.start_date and self.end_date:
                start_display = self.start_date.strftime("%d/%m/%Y")
                end_display = self.end_date.strftime("%d/%m/%Y")
                self.report_time_info_label.config(text=f"Thống kê báo cáo từ {start_display} đến {end_display}.")
            else:
                self.report_time_info_label.config(text="Vui lòng chọn khoảng thời gian để báo cáo.")


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
            self.quarter_combo.grid_forget()
            self.year_label.grid_forget()
            self.year_entry.grid_forget()
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
            "Tổng quan khách hàng": self._plot_customer_summary
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
            all_months = [f"{year_to_report}-{str(m).zfill(2)}" for m in range(1, 13)]
            labels = all_months

            # Lấy doanh thu từng tháng từ dữ liệu đã lọc
            monthly_revenue = defaultdict(float)
            for o in filtered_orders:
                try:
                    dt = datetime.strptime(o['order_date'], "%Y-%m-%dT%H:%M:%S")
                    if dt.year == year_to_report:  # Đảm bảo chỉ lấy dữ liệu của năm được chọn
                        month_key = dt.strftime("%Y-%m")
                        monthly_revenue[month_key] += o.get('total_amount', 0)
                except (KeyError, ValueError):
                    pass

            values_m = [monthly_revenue.get(month_key, 0) / 1_000_000 for month_key in all_months]

        elif group == "Quý":
            quarter_to_report = int(self.quarter_var.get())
            start_month = (quarter_to_report - 1) * 3 + 1
            end_month = start_month + 2

            all_months_in_quarter = [f"{year_to_report}-{str(m).zfill(2)}" for m in range(start_month, end_month + 1)]
            labels = all_months_in_quarter

            # Lấy doanh thu từng tháng trong quý
            monthly_revenue_in_quarter = defaultdict(float)
            for o in filtered_orders:
                try:
                    dt = datetime.strptime(o['order_date'], "%Y-%m-%dT%H:%M:%S")
                    month_key = dt.strftime("%Y-%m")
                    monthly_revenue_in_quarter[month_key] += o.get('total_amount', 0)
                except (KeyError, ValueError):
                    pass

            values_m = [monthly_revenue_in_quarter.get(month_key, 0) / 1_000_000 for month_key in all_months_in_quarter]

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

    def _plot_inventory_report(self):
        products = self.product_service.list() # Assume this lists all products regardless of time
        if not products:
            ttk.Label(self.canvas_frame, text="Không có dữ liệu sản phẩm để hiển thị tồn kho.").pack(pady=20)
            return

        top_stock_products = sorted(products, key=lambda p: p.get('stock', 0), reverse=True)[:10]
        names = [str(p.get('name', 'N/A')) for p in top_stock_products]
        stocks = [p.get('stock', 0) for p in top_stock_products]

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
        names = [t for t in top_customers]
        values = [v / 1_000_000 for _, v in top_customers]

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.barh(range(len(names)), values, color='gold')
        ax.set_yticks([])
        ax.invert_yaxis()
        ax.set_xlabel("Tổng chi tiêu (triệu VNĐ)")
        ax.set_title("Top 10 khách hàng chi tiêu nhiều nhất")
        ax.grid(True, axis='x')

        for i, bar in enumerate(bars):
            text_x = bar.get_width() / 2
            text_y = bar.get_y() + bar.get_height() / 2
            ax.text(text_x, text_y, f'{names[i]}\n{values[i]:.1f}M', va='center', ha='center', fontsize=8,
                    color='black')

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
