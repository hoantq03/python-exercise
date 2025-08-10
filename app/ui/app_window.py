import tkinter as tk
from tkinter import ttk

# --- THAY ĐỔI QUAN TRỌNG ---
# AppWindow nên kế thừa từ tk.Toplevel để trở thành một cửa sổ phụ.
# Cửa sổ gốc tk.Tk() duy nhất sẽ được quản lý trong file main.py.
# Cách làm này giúp quản lý vòng đời ứng dụng đúng chuẩn hơn.
class AppWindow(tk.Toplevel):
    def __init__(self, session_user: dict, **kwargs):
        super().__init__(**kwargs)
        self.session_user = session_user

        self.title(f"Dashboard - Xin chào, {session_user.get('username', 'user')}")
        self.geometry("1280x800")
        self.minsize(1024, 640)

        # Xử lý sự kiện khi người dùng nhấn nút X để đóng cửa sổ
        self.protocol("WM_DELETE_WINDOW", self.handle_close)

        # --- Cơ chế Caching View ---
        # Dictionary để lưu các view đã được tạo
        self.view_cache = {}
        # Tham chiếu đến view đang được hiển thị
        self.current_view = None
        # -----------------------------

        # Layout chính dùng PanedWindow để có thể thay đổi kích thước panel
        main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        main_pane.pack(fill=tk.BOTH, expand=True)

        # Panel điều hướng bên trái
        self.nav_frame = ttk.Frame(main_pane, width=200)
        main_pane.add(self.nav_frame, stretch="never")

        # Panel nội dung chính bên phải
        self.content_frame = ttk.Frame(main_pane)
        main_pane.add(self.content_frame, stretch="always")

    def add_nav_button(self, text, command):
        """Thêm một nút vào thanh điều hướng."""
        btn = ttk.Button(self.nav_frame, text=text, command=command)
        btn.pack(fill=tk.X, padx=10, pady=5)

    def show_view(self, view_class, *args, **kwargs):
        """
        Hiển thị một view với cơ chế caching.
        Phương thức này chỉ tạo view một lần và tái sử dụng cho các lần gọi sau.

        Args:
            view_class: Lớp của view cần hiển thị (ví dụ: ProductsView).
            *args, **kwargs: Các tham số để truyền vào hàm tạo của view.
        """
        # 1. Ẩn view đang hiển thị (nếu có)
        if self.current_view:
            self.current_view.pack_forget()

        # 2. Kiểm tra xem view đã có trong cache chưa
        if view_class in self.view_cache:
            # Nếu có, lấy nó ra từ cache
            print(f"🔄 Lấy view từ cache: {view_class.__name__}")
            self.current_view = self.view_cache[view_class]
        else:
            # Nếu chưa có, tạo một thực thể mới...
            print(f"✨ Tạo mới view: {view_class.__name__}")
            # ...truyền `self.content_frame` làm widget cha.
            new_view = view_class(self.content_frame, *args, **kwargs)
            # ...và lưu vào cache để dùng cho lần sau.
            self.view_cache[view_class] = new_view
            self.current_view = new_view

        # 3. Hiển thị view đã chọn
        self.current_view.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # 4. (Tùy chọn) Gọi 'refresh' nếu có để đảm bảo dữ liệu luôn mới
        if hasattr(self.current_view, 'refresh') and callable(getattr(self.current_view, 'refresh')):
            self.current_view.refresh()

    def handle_close(self):
        """Xử lý sự kiện đóng cửa sổ và thoát ứng dụng."""
        # Phá hủy cửa sổ chính...
        self.destroy()
        # ...và cả cửa sổ gốc tk.Tk() đang bị ẩn đi.
        if self.master:
            self.master.destroy()

