import tkinter as tk
from tkinter import ttk, messagebox

class AppWindow(tk.Tk):
    def __init__(self, session_user: dict):
        super().__init__()
        self.title("Quản lý mua bán hàng - Tkinter + JSON")
        self.geometry("1024x640")
        self.session_user = session_user

        self.nav = ttk.Frame(self)
        self.nav.pack(side=tk.LEFT, fill=tk.Y)

        self.content = ttk.Frame(self)
        self.content.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        self._views = {}  # name -> frame builder
        self._current = None

    def add_nav_button(self, text, command):
        btn = ttk.Button(self.nav, text=text, command=command)
        btn.pack(fill=tk.X, padx=6, pady=4)

    def show_view(self, frame: tk.Frame):
        if self._current:
            self._current.pack_forget()
        self._current = frame
        self._current.pack(expand=True, fill=tk.BOTH)
