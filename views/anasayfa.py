"""
Kelebek Sınav Sistemi - Ana Sayfa
8 büyük butonlu modern dashboard
"""

import tkinter as tk
from tkinter import filedialog
import sys
import os
import webbrowser

# Path ayarı (import için)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from assets.styles import (KelebekTheme, configure_main_button, configure_standard_button,
                           show_message, AnimationHelper, ScrollableFrame)
from assets.layout import setup_responsive_window
from controllers.database_manager import get_db


def maximize_toplevel(window: tk.Toplevel, min_width: int = 800, min_height: int = 600) -> None:
    """Toplevel pencereleri tam ekran yap"""
    window.update_idletasks()
    screen_w = window.winfo_screenwidth()
    screen_h = window.winfo_screenheight()
    window.geometry(f"{screen_w}x{screen_h}+0+0")
    window.minsize(min_width, min_height)
    try:
        window.state("zoomed")
    except tk.TclError:
        pass


class AboutWindow(tk.Toplevel):
    """Hakkında sayfası - tam ekran renkli tasarım"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Hakkında - Kelebek Sınav Sistemi")
        self.configure(bg="#1a1a2e")
        maximize_toplevel(self, 900, 600)
        self.transient(parent)
        self.bind("<Escape>", lambda _: self.destroy())
        
        self._build_ui()
        self.grab_set()
        self.focus_force()
    
    def _build_ui(self):
        # Ana container
        main = tk.Frame(self, bg="#1a1a2e")
        main.pack(fill="both", expand=True, padx=50, pady=30)
        
        # Başlık
        title_frame = tk.Frame(main, bg="#16213e", pady=20)
        title_frame.pack(fill="x", pady=(0, 30))
        
        tk.Label(
            title_frame,
            text="🦋 KELEBEK SINAV SİSTEMİ",
            font=("Segoe UI", 32, "bold"),
            fg="#00d4ff",
            bg="#16213e"
        ).pack()
        
        tk.Label(
            title_frame,
            text="Sınav Yönetim ve Harmanlama Sistemi",
            font=("Segoe UI", 14),
            fg="#e94560",
            bg="#16213e"
        ).pack(pady=(5, 0))
        
        # İçerik kartları
        cards_frame = tk.Frame(main, bg="#1a1a2e")
        cards_frame.pack(fill="both", expand=True)
        
        # Okul kartı
        self._create_card(
            cards_frame,
            icon="🏫",
            title="OKUL",
            value="DUDULLU AMANETOĞLU\nİMAM HATİP LİSESİ",
            bg_color="#0f3460",
            icon_color="#00d4ff"
        ).pack(fill="x", pady=10)
        
        # Programcı kartı
        self._create_card(
            cards_frame,
            icon="👨‍💻",
            title="PROGRAMLAYAN",
            value="İBRAHİM ERTUĞRUL",
            bg_color="#533483",
            icon_color="#ff6b6b"
        ).pack(fill="x", pady=10)
        
        # Mail kartı
        self._create_card(
            cards_frame,
            icon="📧",
            title="MAİL ADRESİ",
            value="muderrisibrahim@gmail.com",
            bg_color="#e94560",
            icon_color="#ffffff",
            clickable=True,
            link="mailto:muderrisibrahim@gmail.com"
        ).pack(fill="x", pady=10)
        
        # Link kartları yan yana
        links_frame = tk.Frame(cards_frame, bg="#1a1a2e")
        links_frame.pack(fill="x", pady=10)
        
        # Instagram kartı
        instagram_card = self._create_card(
            links_frame,
            icon="📸",
            title="INSTAGRAM",
            value="@dudulluaihl",
            bg_color="#c13584",
            icon_color="#ffffff",
            clickable=True,
            link="https://www.instagram.com/dudulluaihl/"
        )
        instagram_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Web sitesi kartı
        web_card = self._create_card(
            links_frame,
            icon="🌐",
            title="WEB SİTESİ",
            value="dudulluaaihl.meb.k12.tr",
            bg_color="#00a8cc",
            icon_color="#ffffff",
            clickable=True,
            link="https://dudulluaaihl.meb.k12.tr/"
        )
        web_card.pack(side="left", fill="both", expand=True)
        
        # Alt buton
        btn_frame = tk.Frame(main, bg="#1a1a2e", pady=20)
        btn_frame.pack(fill="x")
        
        close_btn = tk.Button(
            btn_frame,
            text="✖ KAPAT",
            font=("Segoe UI", 12, "bold"),
            bg="#e94560",
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=30,
            pady=10,
            command=self.destroy
        )
        close_btn.pack()
    
    def _create_card(self, parent, icon, title, value, bg_color, icon_color,
                     clickable=False, link=None):
        card = tk.Frame(parent, bg=bg_color, padx=20, pady=15)
        
        # İkon
        tk.Label(
            card,
            text=icon,
            font=("Segoe UI", 28),
            fg=icon_color,
            bg=bg_color
        ).pack(side="left", padx=(0, 15))
        
        # Metin alanı
        text_frame = tk.Frame(card, bg=bg_color)
        text_frame.pack(side="left", fill="x", expand=True)
        
        tk.Label(
            text_frame,
            text=title,
            font=("Segoe UI", 10, "bold"),
            fg="#aaaaaa",
            bg=bg_color,
            anchor="w"
        ).pack(fill="x")
        
        value_label = tk.Label(
            text_frame,
            text=value,
            font=("Segoe UI", 14, "bold"),
            fg="white",
            bg=bg_color,
            anchor="w",
            justify="left"
        )
        value_label.pack(fill="x")
        
        if clickable and link:
            card.config(cursor="hand2")
            value_label.config(cursor="hand2")
            card.bind("<Button-1>", lambda e: webbrowser.open(link))
            value_label.bind("<Button-1>", lambda e: webbrowser.open(link))
            
            # Tıkla ipucu
            tk.Label(
                card,
                text="🔗",
                font=("Segoe UI", 16),
                fg="white",
                bg=bg_color
            ).pack(side="right")
        
        return card


class WelcomeDialog(tk.Toplevel):
    """Program açılışında gösterilen hoşgeldiniz pop-up'ı"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.title("🦋 Kelebek Sınav Sistemi'ne Hoş Geldiniz!")
        self.configure(bg=KelebekTheme.BG_WHITE)
        self.geometry("650x500")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Ortala
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 650) // 2
        y = (self.winfo_screenheight() - 500) // 2
        self.geometry(f"+{x}+{y}")
        
        self._build_ui()
        
    def _build_ui(self):
        # Başlık
        header = tk.Frame(self, bg=KelebekTheme.PRIMARY)
        header.pack(fill="x")
        
        tk.Label(
            header,
            text="🦋 OTONOM ÖZELLİKLER",
            font=(KelebekTheme.FONT_FAMILY, 18, "bold"),
            fg="white",
            bg=KelebekTheme.PRIMARY,
            pady=10
        ).pack()
        
        # İçerik bölümü
        content = tk.Frame(self, bg=KelebekTheme.BG_WHITE, padx=25, pady=20)
        content.pack(fill="both", expand=True)
        
        # Ana bilgi metni
        info_text = (
            "📝 Öğretmenlerimizden aldığımız sınav kağıtlarını harmanlamış olduğu sınav salonu oturma düzenine göre yazdırır.Yazılı kağıtlarını yazdırırken sınav salonu için bir yoklama listesi bir de oturma düzeni dosyasıda yazdırır. "
            "ve öğrencilerin bilgilerini de sınav kağıdının üst bilgisine işler.\n\n"
            "🖨️ Yazıcıdan alıp tasnif ve düzenlemeye gerek kalmadan "
            "sınav salonuna uygulayabilirsiniz.\n\n"
            "📋 Sınav sonunda öğretmenlerimiz salondaki farklı sınav kağıtlarını "
            "ayırıp ilgili kutulara bırakmalıdır."
        )
        
        tk.Label(
            content,
            text=info_text,
            font=(KelebekTheme.FONT_FAMILY, 11),
            fg=KelebekTheme.TEXT_DARK,
            bg=KelebekTheme.BG_WHITE,
            justify="left",
            wraplength=600
        ).pack(anchor="w", pady=(0, 10))
        
        # Uyarı kutusu
        warning_frame = tk.Frame(content, bg="#fff3cd", bd=1, relief="solid")
        warning_frame.pack(fill="x", pady=10)
        
        tk.Label(
            warning_frame,
            text="⚠️ ÖNEMLİ NOT",
            font=(KelebekTheme.FONT_FAMILY, 12, "bold"),
            fg="#856404",
            bg="#fff3cd",
            pady=10
        ).pack(anchor="w", padx=15)
        
        note_text = (
            "📄 Öğretmenlerimizden sınav dosyalarını WORD dosyası olarak isteyiniz "
            "ve sisteme yükleyiniz.\n"
            "⚙️ Word dosyası sayfa düzeni DAR olmamalı ve ÜST BİLGİ içermemelidir."
        )
        
        tk.Label(
            warning_frame,
            text=note_text,
            font=(KelebekTheme.FONT_FAMILY, 10),
            fg="#856404",
            bg="#fff3cd",
            justify="left",
            wraplength=560,
            pady=10
        ).pack(anchor="w", padx=15)
        
        # Kapatma butonu
        btn_frame = tk.Frame(self, bg=KelebekTheme.BG_WHITE, pady=15)
        btn_frame.pack(fill="x")
        
        close_btn = tk.Button(
            btn_frame,
            text="✅ Anladım, Devam Et",
            font=(KelebekTheme.FONT_FAMILY, 12, "bold"),
            bg=KelebekTheme.SUCCESS,
            fg="white",
            padx=30,
            pady=10,
            bd=0,
            cursor="hand2",
            command=self.destroy
        )
        close_btn.pack()


class GuideWindow(tk.Toplevel):
    """Kullanım Kılavuzu sayfası - tam ekran scroll edilebilir"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Kullanım Kılavuzu - Kelebek Sınav Sistemi")
        self.configure(bg="#0a192f")
        maximize_toplevel(self, 1000, 700)
        self.transient(parent)
        self.bind("<Escape>", lambda _: self.destroy())
        
        self._build_ui()
        self.grab_set()
        self.focus_force()
    
    def _build_ui(self):
        # Başlık
        header = tk.Frame(self, bg="#112240", pady=15)
        header.pack(fill="x")
        
        tk.Label(
            header,
            text="📖 KULLANIM KILAVUZU",
            font=("Segoe UI", 28, "bold"),
            fg="#64ffda",
            bg="#112240"
        ).pack()
        
        tk.Label(
            header,
            text="Adım adım sınav sistemi kullanımı",
            font=("Segoe UI", 12),
            fg="#8892b0",
            bg="#112240"
        ).pack()
        
        # Scroll edilebilir içerik
        canvas_frame = tk.Frame(self, bg="#0a192f")
        canvas_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        canvas = tk.Canvas(canvas_frame, bg="#0a192f", highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg="#0a192f")
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Canvas genişliğini scrollable frame'e bağla
        def _on_canvas_configure(event):
            canvas.itemconfig(window_id, width=event.width)
        
        window_id = canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Kılavuz adımları
        steps = [
            ("1.ADIM ""👥", "ÖĞRENCİ EKLE", "#e74c3c",
             "E-Okul'dan Excel toplu liste indirin, şablona uyarlayıp sisteme yükleyin."),
            ("2.ADIM ""🏫", "SALON EKLE", "#3498db",
             "Okulda sınav düzenlenecek sınıfları şube isimleriyle beraber oluşturun."),
            ("3.ADIM ""📌", "SABİT ÖĞRENCİLERİ EKLE", "#9b59b6",
             "Başka sınıfa gidemeyecek durumda olan öğrencilerimizi kendi sırasına sabitleme özelliğidir."),
            ("4.ADIM ""📕", "TÜM DERSLERİ EKLE", "#e67e22",
             "Okulunuzda yazılı sınav yapılan tüm dersleri ekleyiniz."),
            ("5.ADIM ""📄", "YAZILI KAĞITLARINI EKLE", "#2ecc71",
             "Yazılı kağıtlarını eklediğiniz dersleri seçerek sisteme yükleyiniz."),
            ("6.ADIM ""🗓️", "SINAVLARI OLUŞTUR", "#f39c12",
             "Eklediğiniz dersleri seçerek sınavları oluşturunuz."),
            ("7.ADIM ""🔀", "HARMANLAMA", "#e74c3c",
             "Sınavı seçin → İlgili salonları seçin → Harmanlamayı başlatın.\n"
             "⚠️ Uyumsuzluk oluşursa bazı öğrencileri ÖĞRETMEN MASASINA atama yapar."),
            ("8.ADIM ""🖨️", "HARMANLANMIŞ SINAV KAĞITLARINI KAYDET", "#3498db",
             "Bilgisayara klasör şeklinde sınav salonlarına göre ve harmanlanmış oturma düzenine göre yazılı kağıtlarını yazdırır ek olarak bir kapak sayfası bir yoklama listesi bir de oturma düzeni dosyası yazdırır .\n"
             "✅ Program sınav kağıdının üzerine ÖĞRENCİ BİLGİLERİNİ YAZAR."),
            ("9.ADIM ""📊", "SINAV YERLERİ BİLGİSİ", "#9b59b6",
             "Sınıflara göndermek veya kat panolarına asmak için dosyaları kaydeder, yazdırıp kullanabilirsiniz."),
            ("10.ADIM ""📋", "YOKLAMA / SALON OTURMA DÜZENİ", "#1abc9c",
             "Bu dosya o şubede kimlerin sınava gireceğini gösterir."),
            ("11.ADIM ""🖨️", "TOPLU YAZICIYA GÖNDERME", "#e67e22",
             "Tüm belgeleri klasör sırasına göre yazıcıya gönderir.\n"
             "📝 Listede başarılı ve başarısız gönderimler gösterilir.\n"
             "⚠️ ÇIKTIYI OTURMA SIRASINA GÖRE VERİR.ALIP DİREK SINIFA UYGULAYABİLİRSİNİZ.")
        ]
        
        for icon, title, color, desc in steps:
            self._create_step(scrollable, icon, title, color, desc)
        
        # Alt buton
        btn_frame = tk.Frame(self, bg="#0a192f", pady=15)
        btn_frame.pack(fill="x")
        
        close_btn = tk.Button(
            btn_frame,
            text="✖ KAPAT",
            font=("Segoe UI", 12, "bold"),
            bg="#64ffda",
            fg="#0a192f",
            relief="flat",
            cursor="hand2",
            padx=30,
            pady=8,
            command=self.destroy
        )
        close_btn.pack()
    
    def _create_step(self, parent, icon, title, color, desc):
        step_frame = tk.Frame(parent, bg=color, padx=15, pady=12)
        step_frame.pack(fill="x", pady=8, padx=10)
        
        # Sol: numara ve ikon
        left = tk.Frame(step_frame, bg=color)
        left.pack(side="left", padx=(0, 15))
        
        tk.Label(
            left,
            text=icon,
            font=("Segoe UI", 22),
            fg="white",
            bg=color
        ).pack()
        
        # Sağ: başlık ve açıklama
        right = tk.Frame(step_frame, bg=color)
        right.pack(side="left", fill="x", expand=True)
        
        tk.Label(
            right,
            text=title,
            font=("Segoe UI", 13, "bold"),
            fg="white",
            bg=color,
            anchor="w"
        ).pack(fill="x")
        
        tk.Label(
            right,
            text=desc,
            font=("Segoe UI", 10),
            fg="#000000",
            bg=color,
            anchor="w",
            justify="left",
            wraplength=800
        ).pack(fill="x", pady=(5, 0))



class AnasayfaView:
    """Ana sayfa sınıfı - 1366x768 optimize"""
    
    def __init__(self, root):
        self.root = root
        self.db = get_db()
        setup_responsive_window(self.root)
        self.setup_ui()
        self.setup_keyboard_shortcuts()
    
    def setup_ui(self):
        """UI bileşenlerini oluştur"""
        self.root.title(f"{KelebekTheme.ICON_BUTTERFLY} Kelebek Sınav Sistemi")
        self.root.config(bg=KelebekTheme.BG_LIGHT)
        
        # Header oluştur
        self.create_header()
        
        # İstatistik paneli
        self.create_stats_panel()
        
        # Ana buton grid
        self.create_main_buttons()
        
        # Footer
        self.create_footer()
        
        # Hoşgeldiniz pop-up'ını göster
        self.root.after(500, self.show_welcome_popup)
    
    def setup_keyboard_shortcuts(self):
        """Klavye kısayolları"""
        shortcuts = [
            ("<F1>", self.open_ogrenci_ekle),      # 1) Öğrenci
            ("<F2>", self.open_salon_ayarla),      # 2) Salon
            ("<F3>", self.open_sabit_ogrenci),     # 3) Sabit
            ("<F4>", self.open_gozetmen_ekle),     # 4) Gözetmen
            ("<F5>", self.open_ders_ekle),         # 5) Ders
            ("<F6>", self.open_soru_bankasi),      # 6) Soru Bankası
            ("<F7>", self.open_sinav_ekle),        # 7) Sınav
            ("<F8>", self.open_harmanlama),        # 8) Harmanla
            ("<F9>", self.open_yazdir),            # 9) Yazdırma
            ("<Control-h>", self.open_harmanlama), # Ctrl+H = Harmanla
            ("<Control-q>", lambda e: self.root.quit()),  # Ctrl+Q = Çıkış
        ]
        for key, func in shortcuts:
            self.root.bind(key, lambda e, f=func: f())
    
    def create_header(self):
        """Üst başlık bölümü - 1366x768 optimize"""
        header = tk.Frame(self.root, bg=KelebekTheme.PRIMARY, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        # Logo ve başlık
        title_frame = tk.Frame(header, bg=KelebekTheme.PRIMARY)
        title_frame.pack(expand=True)
        
        tk.Label(
            title_frame,
            text=f"{KelebekTheme.ICON_BUTTERFLY} KELEBEK SINAV SİSTEMİ",
            font=(KelebekTheme.FONT_FAMILY, 22, "bold"),
            fg=KelebekTheme.TEXT_WHITE,
            bg=KelebekTheme.PRIMARY
        ).pack(side="left", padx=15)
        
        # Versiyon
        tk.Label(
            title_frame,
            text="v1.0",
            font=(KelebekTheme.FONT_FAMILY, 9),
            fg=KelebekTheme.TEXT_LIGHT,
            bg=KelebekTheme.PRIMARY
        ).pack(side="left")
        
        # Kısayol bilgisi
       
    def create_stats_panel(self):
        """İstatistik paneli - öğrenci, salon, ders sayıları"""
        stats_frame = tk.Frame(self.root, bg=KelebekTheme.BG_WHITE, height=35)
        stats_frame.pack(fill="x", padx=15, pady=(8, 0))
        
        try:
            stats = self.db.istatistikler()
            items = [
                (KelebekTheme.ICON_STUDENT, f"Öğrenci: {stats.get('toplam_ogrenci', 0)}"),
                (KelebekTheme.ICON_ROOM, f"Salon: {stats.get('toplam_salon', 0)}"),
                (KelebekTheme.ICON_BOOK, f"Ders: {stats.get('toplam_ders', 0)}"),
               
            ]
            for icon, text in items:
                tk.Label(
                    stats_frame,
                    text=f"{icon} {text}",
                    font=(KelebekTheme.FONT_FAMILY, 9, "bold"),
                    fg=KelebekTheme.TEXT_DARK,
                    bg=KelebekTheme.BG_WHITE,
                    padx=12
                ).pack(side="left")
        except Exception:
            pass

 
        """(Kullanılmıyor)"""
        pass
    
    def create_main_buttons(self):
        """Ana butonları oluştur (3x4 grid) - 1366x768 optimize"""
        # Ana container
        button_container = tk.Frame(self.root, bg=KelebekTheme.BG_LIGHT)
        button_container.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Buton tanımları
        buttons_config = [
            (KelebekTheme.ICON_STUDENT, "1.ADIM\nÖĞRENCİ EKLE", "primary", self.open_ogrenci_ekle),
            (KelebekTheme.ICON_ROOM, "2.ADIM\nSALON EKLE", "primary", self.open_salon_ayarla),
            (KelebekTheme.ICON_PIN, "3.ADIM\nSABİT ÖĞRENCİLER", "info", self.open_sabit_ogrenci),
            (KelebekTheme.ICON_BOOK, "4.ADIM\nTÜM DERSLERİ EKLE", "secondary", self.open_ders_ekle),
            ("🗂️", "5.ADIM\nYAZILI KAĞITLARINI SİSTEME YÜKLE", "info", self.open_soru_bankasi),
            (KelebekTheme.ICON_EXAM, "6.ADIM\nSINAV OLUŞTUR-YAPILACAK SINAVLARI EKLE", "warning", self.open_sinav_ekle),
            (KelebekTheme.ICON_SHUFFLE, "7.ADIM\nOTURMA DÜZENİNİ HARMANLA", "danger", self.open_harmanlama),
            (KelebekTheme.ICON_PRINT, "8.ADIM\nYAZILI KAĞITLARINI YAZDIRMAYA HAZIR OLARAK KLASÖRE KAYDET", "secondary", self.open_yazdir),
            ("📅", "9.ADIM\nBİLGİLENDİRME / KİM NEREDE BİLGİSİNİ KLASÖRE KAYDET", "primary", self.open_takvim),
            ("📋", "10.ADIM\nYOKLAMA / SALON OTURMA DÜZENLERİNİ KLASÖRE KAYDET", "success", self.open_sinif_oturma_duzeni),
            ("🖨️", "11.ADIM\nTOPLU YAZICIYA GÖNDERME", "warning", self.open_toplu_yazdir),
            ("📖", "KULLANIM KILAVUZU", "info", self.open_guide)
        ]
        
        # Butonları yerleştir (3 satır x 4 sütun)
        for idx, (icon, text, style, command) in enumerate(buttons_config):
            row = idx // 4
            col = idx % 4
            
            btn = tk.Button(button_container, command=command)
            configure_main_button(btn, style, icon, text)
            btn.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        # Grid yapılandırması (eşit boyut)
        columns = 4
        total_rows = (len(buttons_config) + columns - 1) // columns
        for i in range(columns):
            button_container.columnconfigure(i, weight=1, uniform="button")
        for i in range(total_rows):
            button_container.rowconfigure(i, weight=1, uniform="button")
    
    def create_footer(self):
        """Alt bilgi çubuğu"""
        footer = tk.Frame(self.root, bg=KelebekTheme.BG_DARK, height=40)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)
        
        # Sol taraf - telif
        tk.Label(
            footer,
            text="© 2024 Kelebek Sınav Sistemi | Tüm hakları saklıdır",
            font=(KelebekTheme.FONT_FAMILY, 9),
            fg=KelebekTheme.TEXT_LIGHT,
            bg=KelebekTheme.BG_DARK
        ).pack(side="left", padx=20)
        
        # Sağ taraf - durum ve Hakkında butonu
        right_frame = tk.Frame(footer, bg=KelebekTheme.BG_DARK)
        right_frame.pack(side="right", padx=20)
        
        # Hakkında butonu
        about_btn = tk.Button(
            right_frame,
            text="ℹ️ Hakkında",
            font=(KelebekTheme.FONT_FAMILY, 9, "bold"),
            bg="#0f3460",
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=2,
            command=self.open_about
        )
        about_btn.pack(side="right", padx=(10, 0))
        
        # Kullanım Kılavuzu butonu kaldırıldı - ana grid'e taşındı
        
        self.status_label = tk.Label(
            right_frame,
            text="✓ Sistem Hazır",
            font=(KelebekTheme.FONT_FAMILY, 9),
            fg=KelebekTheme.SUCCESS,
            bg=KelebekTheme.BG_DARK
        )
        self.status_label.pack(side="right")
    def update_status(self, message, status_type="success"):
        """Durum mesajını güncelle"""
        colors = {
            "success": KelebekTheme.SUCCESS,
            "error": KelebekTheme.DANGER,
            "warning": KelebekTheme.WARNING,
            "info": KelebekTheme.INFO
        }
        self.status_label.config(text=message, fg=colors.get(status_type, KelebekTheme.SUCCESS))
    
    # ==================== BUTON FONKSİYONLARI ====================
    
    def open_ogrenci_ekle(self):
        """Öğrenci ekleme ekranını aç"""
        self.update_status("Öğrenci ekleme ekranı açılıyor...", "info")
        try:
            from views.ogrenci_ekle import OgrenciEkleView
            OgrenciEkleView(tk.Toplevel(self.root), self)
        except ImportError as e:
            show_message(self.root, f"Modül yüklenemedi: {e}", "error")
    
    def open_ders_ekle(self):
        """Ders ekleme ekranını aç"""
        self.update_status("Ders ekleme ekranı açılıyor...", "info")
        try:
            from views.ders_ekle import DersEkleView
            DersEkleView(tk.Toplevel(self.root), self)
        except ImportError as e:
            show_message(self.root, f"Modül yüklenemedi: {e}", "error")
    
    def open_sabit_ogrenci(self):
        """Sabit öğrenci ekranını aç"""
        self.update_status("Sabit öğrenci ekranı açılıyor...", "info")
        try:
            from views.sabit_ogrenci import SabitOgrenciView
            SabitOgrenciView(tk.Toplevel(self.root), self)
        except ImportError as e:
            show_message(self.root, f"Modül yüklenemedi: {e}", "error")
    
    def open_gozetmen_ekle(self):
        """Gözetmen ekleme ekranını aç"""
        self.update_status("Gözetmen ekleme ekranı açılıyor...", "info")
        try:
            from views.gozetmen_ekle import GozetmenEkleView
            GozetmenEkleView(tk.Toplevel(self.root), self)
        except ImportError as e:
            show_message(self.root, f"Modül yüklenemedi: {e}", "error")
    
    def open_sinav_ekle(self):
        """Sınav ekleme ekranını aç"""
        self.update_status("Sınav ekleme ekranı açılıyor...", "info")
        try:
            from views.sinav_ekle import SinavEkleView
            SinavEkleView(tk.Toplevel(self.root), self)
        except ImportError as e:
            show_message(self.root, f"Modül yüklenemedi: {e}", "error")
    
    def open_salon_ayarla(self):
        """Salon ayarlama ekranını aç"""
        self.update_status("Salon ayarlama ekranı açılıyor...", "info")
        try:
            from views.salon_ekle import SalonEkleView
            SalonEkleView(tk.Toplevel(self.root), self)
        except ImportError as e:
            show_message(self.root, f"Modül yüklenemedi: {e}", "error")
    
    def open_harmanlama(self):
        """Harmanlama ekranını aç"""
        self.update_status("Harmanlama ekranı açılıyor...", "info")
        try:
            from views.harmanlama_view import HarmanlamaView
            HarmanlamaView(tk.Toplevel(self.root), self)
        except ImportError as e:
            show_message(self.root, f"Modül yüklenemedi: {e}", "error")
    
    def open_soru_bankasi(self):
        """Soru bankası ekranını aç"""
        self.update_status("Soru bankası açılıyor...", "info")
        try:
            from views.soru_bankasi import SoruBankasiView
            SoruBankasiView(tk.Toplevel(self.root), self)
        except ImportError as e:
            show_message(self.root, f"Modül yüklenemedi: {e}", "error")
    
    def open_yazdir(self):
        """Yazdırma ekranını aç"""
        self.update_status("Yazdırma merkezi açılıyor...", "info")
        try:
            from views.yazdirma_view import YazdirmaView
            YazdirmaView(tk.Toplevel(self.root), self)
        except ImportError as e:
            show_message(self.root, f"Modül yüklenemedi: {e}", "error")

    def open_takvim(self):
        """Sınıflara göre sınav yerleri bilgilendirmesi"""
        self.update_status("Sınıflara göre sınav yerleri bilgisi açılıyor...", "info")
        try:
            from views.sinif_bilgilendirme import SinifBilgilendirmeView
            SinifBilgilendirmeView(tk.Toplevel(self.root), self)
        except ImportError as e:
            show_message(self.root, f"Modül yüklenemedi: {e}", "error")

    def open_sinif_oturma_duzeni(self):
        """Sınıf şubelerinin dışına asılacak oturma düzeni sayfası"""
        self.update_status("Sınıf oturma düzeni sayfası açılıyor...", "info")
        try:
            from views.sinif_oturma_duzeni import SinifOturmaDuzeniView
            window = tk.Toplevel(self.root)
            window.transient(self.root)
            SinifOturmaDuzeniView(window, self)
            window.focus_force()
        except Exception as e:
            import traceback
            traceback.print_exc()
            show_message(self.root, f"Sayfa açılamadı: {e}", "error")

    def open_toplu_yazdir(self):
        """Toplu yazdırma sayfası"""
        self.update_status("Toplu yazdırma sayfası açılıyor...", "info")
        try:
            from views.word_print_gui import WordPrinterApp
            window = tk.Toplevel(self.root)
            window.transient(self.root)
            WordPrinterApp(window)
            window.focus_force()
        except Exception as e:
            import traceback
            traceback.print_exc()
            show_message(self.root, f"Sayfa açılamadı: {e}", "error")
    
    def open_about(self):
        """Hakkında sayfasını aç"""
        self.update_status("Hakkında sayfası açılıyor...", "info")
        AboutWindow(self.root)
    
    def show_welcome_popup(self):
        """Program açılışında hoşgeldiniz pop-up'ını göster"""
        WelcomeDialog(self.root)
    
    def open_guide(self):
        """Kullanım kılavuzunu aç"""
        self.update_status("Kullanım kılavuzu açılıyor...", "info")
        GuideWindow(self.root)
    
    def refresh_stats(self):
        """İstatistik paneli kullanılmadığından güncellenecek içerik yok."""
        return


def main():
    """Ana fonksiyon"""
    root = tk.Tk()
    app = AnasayfaView(root)
    root.mainloop()


if __name__ == "__main__":
    main()
