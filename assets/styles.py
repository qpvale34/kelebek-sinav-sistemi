"""
Kelebek Sınav Sistemi - UI Stil ve Tema Yöneticisi
Modern, profesyonel görünüm için renk paleti ve stil sabitleri
"""

import tkinter as tk
from tkinter import font as tkfont, ttk


class KelebekTheme:
    """Modern UI Tema Sabitleri"""
    
    # Ana Renkler
    PRIMARY = "#2C3E50"          # Koyu Lacivert
    SECONDARY = "#3498DB"        # Parlak Mavi
    ACCENT = "#E74C3C"           # Kırmızı (Vurgu)
    SUCCESS = "#27AE60"          # Yeşil
    WARNING = "#F39C12"          # Turuncu
    DANGER = "#C0392B"           # Koyu Kırmızı
    INFO = "#16A085"             # Turkuaz
    
    # Arka Plan Renkleri
    BG_DARK = "#34495E"          # Koyu gri
    BG_LIGHT = "#ECF0F1"         # Açık gri
    BG_WHITE = "#FFFFFF"         # Beyaz
    BG_CARD = "#F8F9FA"          # Kart arka planı
    
    # Text Renkleri
    TEXT_DARK = "#2C3E50"        # Koyu text
    TEXT_LIGHT = "#7F8C8D"       # Açık text
    TEXT_WHITE = "#FFFFFF"       # Beyaz text
    TEXT_MUTED = "#95A5A6"       # Soluk text
    
    # Hover Renkleri (Buton üzerine gelindiğinde)
    PRIMARY_HOVER = "#1A252F"
    SECONDARY_HOVER = "#2980B9"
    SUCCESS_HOVER = "#229954"
    DANGER_HOVER = "#A93226"
    
    # Border ve Gölge
    BORDER_COLOR = "#BDC3C7"
    SHADOW_COLOR = "#95A5A6"
    
    # Font Boyutları
    FONT_TITLE = 24
    FONT_HEADER = 18
    FONT_SUBHEADER = 14
    FONT_BODY = 11
    FONT_SMALL = 9
    
    # Font Aileleri
    FONT_FAMILY = "Segoe UI"
    FONT_FAMILY_ALT = "Arial"
    
    # Boşluklar
    PADDING_SMALL = 5
    PADDING_MEDIUM = 10
    PADDING_LARGE = 20
    PADDING_XLARGE = 30
    
    # Border Radius (köşe yuvarlaklığı)
    RADIUS_SMALL = 5
    RADIUS_MEDIUM = 10
    RADIUS_LARGE = 15
    
    # Buton Boyutları
    BUTTON_HEIGHT = 45
    BUTTON_WIDTH_SMALL = 100
    BUTTON_WIDTH_MEDIUM = 150
    BUTTON_WIDTH_LARGE = 200
    
    # Ana Buton Boyutları (Anasayfa için)
    MAIN_BUTTON_WIDTH = 280
    MAIN_BUTTON_HEIGHT = 100
    
    # İkonlar (Unicode karakterler)
    ICON_STUDENT = "👨‍🎓"
    ICON_BOOK = "📚"
    ICON_EXAM = "📝"
    ICON_ROOM = "🏫"
    ICON_TEACHER = "👨‍🏫"
    ICON_SHUFFLE = "🔀"
    ICON_PIN = "📌"
    ICON_PRINT = "🖨️"
    ICON_CHECK = "✅"
    ICON_CROSS = "❌"
    ICON_WARNING = "⚠️"
    ICON_INFO = "ℹ️"
    ICON_EXCEL = "📊"
    ICON_SAVE = "💾"
    ICON_EDIT = "✏️"
    ICON_DELETE = "🗑️"
    ICON_SEARCH = "🔍"
    ICON_CALENDAR = "📅"
    ICON_CLOCK = "🕐"
    ICON_SETTINGS = "⚙️"
    ICON_BUTTERFLY = "🦋"


class StyleHelper:
    """Stil yardımcı fonksiyonları"""
    
    @staticmethod
    def get_button_style(style_type="primary"):
        """
        Buton stili döndür
        Types: primary, secondary, success, danger, warning
        """
        styles = {
            "primary": {
                "bg": KelebekTheme.PRIMARY,
                "fg": KelebekTheme.TEXT_WHITE,
                "hover": KelebekTheme.PRIMARY_HOVER
            },
            "secondary": {
                "bg": KelebekTheme.SECONDARY,
                "fg": KelebekTheme.TEXT_WHITE,
                "hover": KelebekTheme.SECONDARY_HOVER
            },
            "success": {
                "bg": KelebekTheme.SUCCESS,
                "fg": KelebekTheme.TEXT_WHITE,
                "hover": KelebekTheme.SUCCESS_HOVER
            },
            "danger": {
                "bg": KelebekTheme.DANGER,
                "fg": KelebekTheme.TEXT_WHITE,
                "hover": KelebekTheme.DANGER_HOVER
            },
            "warning": {
                "bg": KelebekTheme.WARNING,
                "fg": KelebekTheme.TEXT_WHITE,
                "hover": "#D68910"
            }
        }
        return styles.get(style_type, styles["primary"])
    
    @staticmethod
    def create_shadow_effect():
        """Gölge efekti parametreleri"""
        return {
            "relief": "flat",
            "borderwidth": 0,
            "highlightthickness": 0
        }
    
    @staticmethod
    def get_entry_style():
        """Input field stili"""
        return {
            "bg": KelebekTheme.BG_WHITE,
            "fg": KelebekTheme.TEXT_DARK,
            "relief": "solid",
            "borderwidth": 1,
            "highlightthickness": 1,
            "highlightbackground": KelebekTheme.BORDER_COLOR,
            "highlightcolor": KelebekTheme.SECONDARY,
            "insertbackground": KelebekTheme.TEXT_DARK
        }
    
    @staticmethod
    def get_frame_style():
        """Frame stili"""
        return {
            "bg": KelebekTheme.BG_WHITE,
            "relief": "flat",
            "borderwidth": 0
        }
    
    @staticmethod
    def get_label_style(style_type="normal"):
        """
        Label stili
        Types: title, header, normal, muted
        """
        styles = {
            "title": {
                "font": (KelebekTheme.FONT_FAMILY, KelebekTheme.FONT_TITLE, "bold"),
                "fg": KelebekTheme.TEXT_DARK,
                "bg": KelebekTheme.BG_WHITE
            },
            "header": {
                "font": (KelebekTheme.FONT_FAMILY, KelebekTheme.FONT_HEADER, "bold"),
                "fg": KelebekTheme.TEXT_DARK,
                "bg": KelebekTheme.BG_WHITE
            },
            "normal": {
                "font": (KelebekTheme.FONT_FAMILY, KelebekTheme.FONT_BODY),
                "fg": KelebekTheme.TEXT_DARK,
                "bg": KelebekTheme.BG_WHITE
            },
            "muted": {
                "font": (KelebekTheme.FONT_FAMILY, KelebekTheme.FONT_SMALL),
                "fg": KelebekTheme.TEXT_MUTED,
                "bg": KelebekTheme.BG_WHITE
            }
        }
        return styles.get(style_type, styles["normal"])


class AnimationHelper:
    """Animasyon yardımcıları"""
    
    @staticmethod
    def fade_color(widget, start_color, end_color, duration=200, steps=10):
        """Renk geçişi animasyonu (gelecekte kullanım için)"""
        pass
    
    @staticmethod
    def button_hover_effect(event):
        """Buton hover efekti"""
        widget = event.widget
        if hasattr(widget, 'hover_color'):
            widget.config(bg=widget.hover_color)
    
    @staticmethod
    def button_leave_effect(event):
        """Buton hover bitişi efekti"""
        widget = event.widget
        if hasattr(widget, 'original_color'):
            widget.config(bg=widget.original_color)
    
    @staticmethod
    def button_press_effect(event):
        """Buton basma efekti"""
        widget = event.widget
        widget.config(relief="sunken")
    
    @staticmethod
    def button_release_effect(event):
        """Buton bırakma efekti"""
        widget = event.widget
        widget.config(relief="flat")


class ScrollableFrame(tk.Frame):
    """Dikey kaydırılabilir genel amaçlı container"""
    
    def __init__(self, parent, height: int | None = None, **kwargs):
        bg_color = kwargs.get("bg", KelebekTheme.BG_LIGHT)
        super().__init__(parent, bg=bg_color)
        
        self.canvas = tk.Canvas(
            self,
            bg=bg_color,
            highlightthickness=0,
            height=height
        )
        self.scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview
        )
        self.inner = tk.Frame(self.canvas, bg=bg_color)
        
        self.inner.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        self._bind_mousewheel(self.canvas)
    
    @property
    def content(self):
        """İçerik frame referansı"""
        return self.inner
    
    def _bind_mousewheel(self, widget):
        def _on_enter(_event):
            widget.bind_all("<MouseWheel>", self._on_mousewheel)
            widget.bind_all("<Button-4>", self._on_mousewheel_linux)
            widget.bind_all("<Button-5>", self._on_mousewheel_linux)
        
        def _on_leave(_event):
            widget.unbind_all("<MouseWheel>")
            widget.unbind_all("<Button-4>")
            widget.unbind_all("<Button-5>")
        
        widget.bind("<Enter>", _on_enter)
        widget.bind("<Leave>", _on_leave)
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def _on_mousewheel_linux(self, event):
        direction = -1 if event.num == 4 else 1
        self.canvas.yview_scroll(direction, "units")


def configure_main_button(button, button_style="primary", icon="", text=""):
    """
    Ana buton yapılandırması (anasayfa butonları için)
    1366x768 ekran için optimize edilmiş
    """
    style = StyleHelper.get_button_style(button_style)
    
    button.config(
        text=f"{icon}\n{text}",
        font=(KelebekTheme.FONT_FAMILY, 14, "bold"),  # Font küçültüldü
        bg=style["bg"],
        fg=style["fg"],
        relief="flat",
        borderwidth=0,
        cursor="hand2",
        activebackground=style["hover"],
        activeforeground=KelebekTheme.TEXT_WHITE,
        width=15,   # Genişlik küçültüldü
        height=3,   # Yükseklik küçültüldü
        wraplength=200  # Wrap küçültüldü
    )
    
    # Hover efekti için renkleri sakla
    button.original_color = style["bg"]
    button.hover_color = style["hover"]
    
    # Event bindings
    button.bind("<Enter>", AnimationHelper.button_hover_effect)
    button.bind("<Leave>", AnimationHelper.button_leave_effect)
    button.bind("<ButtonPress-1>", AnimationHelper.button_press_effect)
    button.bind("<ButtonRelease-1>", AnimationHelper.button_release_effect)


def configure_standard_button(button, button_style="primary", text=""):
    """
    Standart buton yapılandırması
    """
    style = StyleHelper.get_button_style(button_style)
    
    button.config(
        text=text,
        font=(KelebekTheme.FONT_FAMILY, KelebekTheme.FONT_BODY, "bold"),
        bg=style["bg"],
        fg=style["fg"],
        relief="flat",
        borderwidth=0,
        cursor="hand2",
        activebackground=style["hover"],
        activeforeground=KelebekTheme.TEXT_WHITE,
        padx=KelebekTheme.PADDING_MEDIUM,
        pady=KelebekTheme.PADDING_SMALL
    )
    
    button.original_color = style["bg"]
    button.hover_color = style["hover"]
    
    button.bind("<Enter>", AnimationHelper.button_hover_effect)
    button.bind("<Leave>", AnimationHelper.button_leave_effect)


def create_card_frame(parent, title="", icon=""):
    """
    Kart stili frame oluştur (modern UI için)
    """
    import tkinter as tk
    
    # Ana card frame
    card = tk.Frame(
        parent,
        bg=KelebekTheme.BG_CARD,
        relief="flat",
        borderwidth=1,
        highlightbackground=KelebekTheme.BORDER_COLOR,
        highlightthickness=1
    )
    
    # Başlık varsa ekle
    if title or icon:
        header = tk.Frame(card, bg=KelebekTheme.PRIMARY)
        header.pack(fill="x", padx=2, pady=2)
        
        label_text = f"{icon} {title}" if icon else title
        tk.Label(
            header,
            text=label_text,
            font=(KelebekTheme.FONT_FAMILY, KelebekTheme.FONT_HEADER, "bold"),
            fg=KelebekTheme.TEXT_WHITE,
            bg=KelebekTheme.PRIMARY,
            pady=KelebekTheme.PADDING_MEDIUM
        ).pack()
    
    # İçerik alanı
    content = tk.Frame(card, bg=KelebekTheme.BG_WHITE)
    content.pack(fill="both", expand=True, padx=KelebekTheme.PADDING_MEDIUM, 
                 pady=KelebekTheme.PADDING_MEDIUM)
    
    card.content = content
    return card


def show_message(parent, message, message_type="info"):
    """
    Bilgi mesajı göster
    Types: info, success, warning, error
    """
    import tkinter as tk
    from tkinter import messagebox
    
    icons = {
        "info": KelebekTheme.ICON_INFO,
        "success": KelebekTheme.ICON_CHECK,
        "warning": KelebekTheme.ICON_WARNING,
        "error": KelebekTheme.ICON_CROSS
    }
    
    titles = {
        "info": "Bilgi",
        "success": "Başarılı",
        "warning": "Uyarı",
        "error": "Hata"
    }
    
    message_text = f"{icons.get(message_type, '')} {message}"
    
    if message_type == "error":
        messagebox.showerror(titles[message_type], message_text, parent=parent)
    elif message_type == "warning":
        messagebox.showwarning(titles[message_type], message_text, parent=parent)
    elif message_type == "success":
        messagebox.showinfo(titles[message_type], message_text, parent=parent)
    else:
        messagebox.showinfo(titles[message_type], message_text, parent=parent)


def ask_confirmation(parent, message, title="Onay"):
    """Onay dialogu göster"""
    from tkinter import messagebox
    return messagebox.askyesno(
        title,
        f"{KelebekTheme.ICON_WARNING} {message}",
        parent=parent
    )


# Test kodu
if __name__ == "__main__":
    import tkinter as tk
    
    root = tk.Tk()
    root.title("Stil Test")
    root.geometry("800x600")
    root.config(bg=KelebekTheme.BG_LIGHT)
    
    # Başlık
    tk.Label(
        root,
        text=f"{KelebekTheme.ICON_BUTTERFLY} Kelebek Tema Test",
        **StyleHelper.get_label_style("title")
    ).pack(pady=20)
    
    # Buton örnekleri
    button_frame = tk.Frame(root, bg=KelebekTheme.BG_LIGHT)
    button_frame.pack(pady=20)
    
    for i, (style, text) in enumerate([
        ("primary", "Primary"),
        ("secondary", "Secondary"),
        ("success", "Success"),
        ("danger", "Danger"),
        ("warning", "Warning")
    ]):
        btn = tk.Button(button_frame)
        configure_standard_button(btn, style, text)
        btn.grid(row=0, column=i, padx=5)
    
    # Card örneği
    card = create_card_frame(root, "Örnek Card", KelebekTheme.ICON_INFO)
    card.pack(pady=20, padx=50, fill="both", expand=True)
    
    tk.Label(
        card.content,
        text="Bu bir card örneğidir. İçerik buraya gelir.",
        **StyleHelper.get_label_style("normal")
    ).pack(pady=20)
    
    root.mainloop()
