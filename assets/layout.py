"""
Ortak layout yardımcıları - 1366x768 ekran optimizasyonu
"""

import tkinter as tk

# 1366x768 ekran için optimize edilmiş minimum boyutlar
DEFAULT_MIN_WIDTH = 1000
DEFAULT_MIN_HEIGHT = 650

# Toplevel pencereler için
TOPLEVEL_MIN_WIDTH = 900
TOPLEVEL_MIN_HEIGHT = 550


def setup_responsive_window(window: tk.Tk, min_width: int = DEFAULT_MIN_WIDTH,
                            min_height: int = DEFAULT_MIN_HEIGHT) -> None:
    """
    Ana pencereyi tam ekran/responsive yap.
    1366x768 ekran boyutuna optimize edilmiş.
    """
    window.update_idletasks()
    try:
        window.state("zoomed")
    except tk.TclError:
        screen_w = window.winfo_screenwidth()
        screen_h = window.winfo_screenheight()
        window.geometry(f"{screen_w}x{screen_h}+0+0")
    window.minsize(min_width, min_height)
    window.grid_rowconfigure(0, weight=1)
    window.grid_columnconfigure(0, weight=1)


def setup_toplevel_window(window: tk.Toplevel, min_width: int = TOPLEVEL_MIN_WIDTH,
                          min_height: int = TOPLEVEL_MIN_HEIGHT) -> None:
    """
    Toplevel pencerelerini tam ekran/responsive yap.
    1366x768 ekran boyutuna optimize edilmiş.
    """
    window.update_idletasks()
    try:
        window.state("zoomed")
    except tk.TclError:
        screen_w = window.winfo_screenwidth()
        screen_h = window.winfo_screenheight()
        window.geometry(f"{screen_w}x{screen_h}+0+0")
    window.minsize(min_width, min_height)
    
    # ESC ile kapatma
    window.bind("<Escape>", lambda _: window.destroy())
    
    # Odak ve ön plana getirme
    window.focus_force()
    window.lift()


def make_responsive_grid(container: tk.Misc, rows: int = 1, columns: int = 1) -> None:
    """Grid kullanılan container'ı duyarlı hale getir."""
    for r in range(rows):
        container.grid_rowconfigure(r, weight=1)
    for c in range(columns):
        container.grid_columnconfigure(c, weight=1)


def get_screen_size() -> tuple:
    """Ekran boyutlarını döndür."""
    temp = tk.Tk()
    temp.withdraw()
    width = temp.winfo_screenwidth()
    height = temp.winfo_screenheight()
    temp.destroy()
    return width, height


def is_small_screen() -> bool:
    """1366x768 veya daha küçük ekran mı kontrol et."""
    w, h = get_screen_size()
    return w <= 1400 or h <= 800

