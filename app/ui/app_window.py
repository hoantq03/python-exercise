import tkinter as tk
from tkinter import ttk

class AppWindow(tk.Toplevel):
    def __init__(self, session_user: dict, **kwargs):
        super().__init__(**kwargs)
        self.session_user = session_user

        self.title(f"Dashboard - Xin chào, {session_user.get('username', 'user')}")
        self.geometry("1280x800")
        self.minsize(1024, 640)

        self.protocol("WM_DELETE_WINDOW", self.handle_close)

        self.view_cache = {}
        self.current_view = None

        main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        main_pane.pack(fill=tk.BOTH, expand=True)

        self.nav_frame = ttk.Frame(main_pane, width=200)
        main_pane.add(self.nav_frame, stretch="never")

        self.content_frame = ttk.Frame(main_pane)
        main_pane.add(self.content_frame, stretch="always")

    def add_nav_button(self, text, command):
        """Thêm một nút vào thanh điều hướng."""
        btn = ttk.Button(self.nav_frame, text=text, command=command)
        btn.pack(fill=tk.X, padx=10, pady=5)

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

        self.current_view.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        if hasattr(self.current_view, 'refresh') and callable(getattr(self.current_view, 'refresh')):
            print(f"⚡ Gọi refresh() cho view {view_class.__name__}")
            self.current_view.refresh()  # Bỏ `reset_page=True`

    def handle_close(self):
        """Xử lý sự kiện đóng cửa sổ và thoát ứng dụng."""
        self.destroy()
        if self.master:
            self.master.destroy()

