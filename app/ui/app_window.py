import tkinter as tk
from tkinter import ttk

class AppWindow(tk.Toplevel):
    def __init__(self, session_user: dict, **kwargs):
        super().__init__(**kwargs)
        self.session_user = session_user

        # Gọi phương thức cấu hình UI
        self._setup_ui_config()

        self.title(f"Dashboard - Xin chào, {session_user.get('username', 'user')}")
        self.geometry(self.config['window_geometry'])
        self.minsize(self.config['min_window_size'][0], self.config['min_window_size'][1])

        self.protocol("WM_DELETE_WINDOW", self.handle_close)

        self.view_cache = {}
        self.current_view = None

        main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        main_pane.pack(fill=tk.BOTH, expand=True)

        self.nav_frame = ttk.Frame(main_pane, width=self.config['nav_frame_width'])
        main_pane.add(self.nav_frame, stretch="never")

        self.content_frame = ttk.Frame(main_pane)
        main_pane.add(self.content_frame, stretch="always")

    def _setup_ui_config(self):
        """
        Gom cấu hình UI của ứng dụng tại đây.
        Sử dụng self.config để lưu trữ các giá trị cấu hình.
        """
        self.config = {
            # Cấu hình cửa sổ chính
            "window_geometry": "1664x1040",  # Kích thước ban đầu của cửa sổ (chiều rộng x chiều cao)
            "min_window_size": (1331, 832), # Kích thước tối thiểu của cửa sổ (chiều rộng, chiều cao)
            "window_title_prefix": "Dashboard - Xin chào, ", # Tiền tố tiêu đề cửa sổ

            # Cấu hình thanh điều hướng (navigation bar)
            "nav_frame_width": 260,         # Chiều rộng cố định của khung điều hướng
            "nav_button_padx": 13,          # Khoảng đệm ngang cho các nút điều hướng
            "nav_button_pady": 7,           # Khoảng đệm dọc cho các nút điều hướng

            # Cấu hình khung nội dung (content frame)
            "content_padding": 13           # Khoảng đệm xung quanh nội dung hiển thị trong content_frame
        }

    def add_nav_button(self, text, command):
        """Thêm một nút vào thanh điều hướng."""
        btn = ttk.Button(self.nav_frame, text=text, command=command)
        btn.pack(fill=tk.X, padx=self.config['nav_button_padx'], pady=self.config['nav_button_pady'])

    def show_view(self, view_class, *args, **kwargs):
        """Hiển thị một view với cơ chế caching."""
        if self.current_view:
            self.current_view.pack_forget()

        if view_class in self.view_cache:
            print(f"🔄 Lấy view từ cache: {view_class.__name__}")
            self.current_view = self.view_cache[view_class]
        else:
            print(f"✨ Tạo mới view: {view_class.__name__}")
            new_view = view_class(self.content_frame, *args, **kwargs)
            self.view_cache[view_class] = new_view
            self.current_view = new_view

        self.current_view.pack(expand=True, fill=tk.BOTH,
                               padx=self.config['content_padding'],
                               pady=self.config['content_padding'])

        if hasattr(self.current_view, 'refresh') and callable(getattr(self.current_view, 'refresh')):
            print(f"⚡ Gọi refresh() cho view {view_class.__name__}")
            self.current_view.refresh()

    def handle_close(self):
        """Xử lý sự kiện đóng cửa sổ và thoát ứng dụng."""
        self.destroy()
        if self.master:
            self.master.destroy()
