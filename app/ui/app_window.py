import tkinter as tk
from tkinter import ttk


class AppWindow(tk.Toplevel):
    def __init__(self, master, session_user: dict, **kwargs):  # Added 'master' parameter
        super().__init__(master, **kwargs)  # Pass master to super
        self.master = master  # Store master
        self.session_user = session_user

        # Gọi phương thức cấu hình UI
        self._setup_ui_config()

        self.title(f"Dashboard - Xin chào, {session_user.get('username', 'user')}")
        self.geometry(self.config['window_geometry'])
        self.minsize(self.config['min_window_size'][0], self.config['min_window_size'][1])

        self.protocol("WM_DELETE_WINDOW", self.handle_close)

        self.view_cache = {}
        self.current_view = None

        # New: Store references to navigation buttons and track active button
        self.nav_buttons_map = {}  # Maps view_class to its button widget
        self.active_nav_button = None  # Stores the currently highlighted button widget

        # New: Define custom styles for navigation buttons
        self.style = ttk.Style(self)
        self.style.configure("NavButton.TButton",
                             background=self.config['nav_button_default_bg'],
                             foreground=self.config['nav_button_default_fg'],
                             font=(
                             self.config['nav_button_font_family'], self.config['nav_button_font_size'], "normal"),
                             padding=[self.config['nav_button_padx_style'], self.config['nav_button_pady_style']])
        self.style.map("NavButton.TButton",
                       background=[('active', self.config['nav_button_active_bg']),
                                   ('pressed', self.config['nav_button_pressed_bg'])])

        self.style.configure("Selected.NavButton.TButton",
                             background=self.config['nav_button_selected_bg'],
                             foreground=self.config['nav_button_selected_fg'],
                             font=(self.config['nav_button_font_family'], self.config['nav_button_font_size'], "bold"),
                             padding=[self.config['nav_button_padx_style'], self.config['nav_button_pady_style']])
        self.style.map("Selected.NavButton.TButton",
                       background=[('active', self.config['nav_button_selected_active_bg']),
                                   ('pressed', self.config['nav_button_selected_pressed_bg'])])

        main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        main_pane.pack(fill=tk.BOTH, expand=True)

        self.nav_frame = ttk.Frame(main_pane, width=self.config['nav_frame_width'])
        self.nav_frame.pack_propagate(False)  # Prevent nav_frame from shrinking based on content
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
            "min_window_size": (1331, 832),  # Kích thước tối thiểu của cửa sổ (chiều rộng, chiều cao)
            "window_title_prefix": "Dashboard - Xin chào, ",  # Tiền tố tiêu đề cửa sổ

            # Cấu hình thanh điều hướng (navigation bar)
            "nav_frame_width": 260,  # Chiều rộng cố định của khung điều hướng
            "nav_button_padx": 13,  # Khoảng đệm ngang cho các nút điều hướng
            "nav_button_pady": 7,  # Khoảng đệm dọc cho các nút điều hướng
            "nav_button_padx_style": 10,  # Padding for button style
            "nav_button_pady_style": 10,  # Padding for button style

            # Button styles (new)
            "nav_button_font_family": "Arial",
            "nav_button_font_size": 10,
            "nav_button_default_bg": "#e0e0e0",
            "nav_button_default_fg": "black",
            "nav_button_active_bg": "#33A1E0",
            "nav_button_pressed_bg": "#33A1E0",
            "nav_button_selected_bg": "#33A1E0",  # A distinct color for selected
            "nav_button_selected_fg": "#33A1E0",
            "nav_button_selected_active_bg": "#33A1E0",
            "nav_button_selected_pressed_bg": "#33A1E0",

            # Cấu hình khung nội dung (content frame)
            "content_padding": 13  # Khoảng đệm xung quanh nội dung hiển thị trong content_frame
        }

    def add_nav_button(self, text, view_class=None, *args, **kwargs):
        """
        Thêm một nút vào thanh điều hướng.
        :param text: Văn bản hiển thị trên nút.
        :param view_class: Lớp view để hiển thị khi nút được nhấn. Nếu là None, command sẽ được gọi trực tiếp.
        :param args: Các đối số truyền cho view_class constructor.
        :param kwargs: Các đối số từ khóa truyền cho view_class constructor.
        """
        button = ttk.Button(self.nav_frame, text=text, style="NavButton.TButton")
        button.pack(fill=tk.X, padx=self.config['nav_button_padx'], pady=self.config['nav_button_pady'])

        def command_wrapper():
            self._select_button_style(button)  # Update button style
            if view_class:
                self.show_view(view_class, *args, **kwargs)  # Show view using caching mechanism
            else:
                # If no view_class, it's a direct command (e.g., logout)
                # In this case, we don't clear previously selected button style
                # as it's not a view change. You might want to adjust this.
                if 'command' in kwargs:  # Check if a direct command was passed via kwargs
                    kwargs['command']()  # Execute direct command

        button.config(command=command_wrapper)

        # Store button reference for view_class if applicable
        if view_class:
            self.nav_buttons_map[view_class] = button

        return button  # Return the button object for initial selection if needed

    def _select_button_style(self, button_to_select):
        """Updates the style of navigation buttons."""
        # Reset the style of the previously active button
        if self.active_nav_button and self.active_nav_button != button_to_select:
            self.active_nav_button.config(style="NavButton.TButton")

        # Set the style of the newly active button
        button_to_select.config(style="Selected.NavButton.TButton")
        self.active_nav_button = button_to_select

    def show_view(self, view_class, *args, **kwargs):
        """Hiển thị một view với cơ chế caching và cập nhật button style."""
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

        # Ensure the correct button is highlighted when show_view is called directly
        # (e.g., initial view, or if a view is shown without clicking its button)
        if view_class in self.nav_buttons_map:
            self._select_button_style(self.nav_buttons_map[view_class])

    def handle_close(self):
        """Xử lý sự kiện đóng cửa sổ và thoát ứng dụng."""
        self.destroy()
        if self.master:
            self.master.destroy()

