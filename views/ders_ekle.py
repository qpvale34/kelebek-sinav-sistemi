"""
Kelebek Sınav Sistemi - Ders Ekleme ve Yönetim Ekranı
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from assets.styles import (KelebekTheme, configure_standard_button,
                           show_message, ask_confirmation, create_card_frame,
                           ScrollableFrame)
from assets.layout import setup_responsive_window
from controllers.database_manager import get_db


class DersEkleView:
    """Ders ekleme ve yönetim ekranı"""
    
    def __init__(self, window, parent):
        self.window = window
        self.parent = parent
        self.db = get_db()
        self.sinif_vars = {}
        self.checkbox_frame = None
        setup_responsive_window(self.window)
        
        self.setup_ui()
        self.load_dersler()
    
    def setup_ui(self):
        """UI oluştur"""
        self.window.title(f"{KelebekTheme.ICON_BOOK} Ders Yönetimi")
        self.window.geometry("900x600")
        self.window.config(bg=KelebekTheme.BG_LIGHT)
        
        # Header
        header = tk.Frame(self.window, bg=KelebekTheme.SUCCESS, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text=f"{KelebekTheme.ICON_BOOK} DERS YÖNETİMİ",
            font=(KelebekTheme.FONT_FAMILY, 20, "bold"),
            fg=KelebekTheme.TEXT_WHITE,
            bg=KelebekTheme.SUCCESS
        ).pack(pady=15)

        # Ana Layout
        main_layout = tk.Frame(self.window, bg=KelebekTheme.BG_LIGHT)
        main_layout.pack(fill="both", expand=True, padx=15, pady=15)
        
        # --- SOL PANEL (FORM) ---
        left_sidebar = tk.Frame(main_layout, bg=KelebekTheme.BG_LIGHT, width=320)
        left_sidebar.pack(side="left", fill="y", padx=(0, 15))
        left_sidebar.pack_propagate(False)
        
        left_card = create_card_frame(left_sidebar, "Yeni Ders Ekle", KelebekTheme.ICON_EDIT)
        left_card.pack(fill="both", expand=True) # Checkbox listesi uzayabilir
        
        self.create_form(left_card.content)
        
        # --- SAĞ PANEL (LİSTE) ---
        right_content = tk.Frame(main_layout, bg=KelebekTheme.BG_LIGHT)
        right_content.pack(side="right", fill="both", expand=True)
        
        right_card = create_card_frame(right_content, "Ders Listesi", KelebekTheme.ICON_BOOK)
        right_card.pack(fill="both", expand=True)
        
        self.create_list(right_card.content)
    
    def create_form(self, parent):
        """Ders ekleme formu"""
        form_frame = tk.Frame(parent, bg=KelebekTheme.BG_WHITE)
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Ders adı
        tk.Label(
            form_frame,
            text="Ders Adı:",
            font=(KelebekTheme.FONT_FAMILY, 11, "bold"),
            fg=KelebekTheme.TEXT_DARK,
            bg=KelebekTheme.BG_WHITE
        ).pack(anchor="w", pady=(10, 5))
        
        self.ders_adi_entry = tk.Entry(
            form_frame,
            font=(KelebekTheme.FONT_FAMILY, 11),
            width=30
        )
        self.ders_adi_entry.pack(fill="x", pady=(0, 10))
        
        # Sınıf seçimi başlık
        sinif_header = tk.Frame(form_frame, bg=KelebekTheme.BG_WHITE)
        sinif_header.pack(fill="x", pady=(10, 5))
        
        tk.Label(
            sinif_header,
            text="Bu dersi hangi sınıflar alıyor?",
            font=(KelebekTheme.FONT_FAMILY, 11, "bold"),
            fg=KelebekTheme.TEXT_DARK,
            bg=KelebekTheme.BG_WHITE
        ).pack(side="left")
        
        # Yenile butonu
        btn_refresh = tk.Button(sinif_header, command=self.load_siniflar)
        configure_standard_button(btn_refresh, "secondary", "↻ Yenile")
        btn_refresh.pack(side="right")
        
        # Checkbox container
        self.checkbox_frame = tk.Frame(form_frame, bg=KelebekTheme.BG_WHITE)
        self.checkbox_frame.pack(fill="both", expand=True, pady=10)
        
        # Sınıfları yükle
        self.load_siniflar()
        
        # Ekle butonu
        btn_ekle = tk.Button(form_frame, command=self.add_ders)
        configure_standard_button(btn_ekle, "success", f"{KelebekTheme.ICON_CHECK} Ders Ekle")
        btn_ekle.pack(pady=20)
    
    def load_siniflar(self):
        """Veritabanından öğrenci sınıf-şube kombinasyonlarını yükle"""
        # Mevcut checkbox'ları temizle
        if self.checkbox_frame:
            for widget in self.checkbox_frame.winfo_children():
                widget.destroy()
        
        self.sinif_vars = {}
        
        try:
            # Veritabanından benzersiz sınıf-şube kombinasyonlarını al
            kombinasyonlar = self.db.benzersiz_sinif_sube()
            
            if not kombinasyonlar:
                tk.Label(
                    self.checkbox_frame,
                    text="⚠️ Henüz öğrenci eklenmemiş.\nÖnce öğrenci ekleyip sınıf tanımlayın.",
                    font=(KelebekTheme.FONT_FAMILY, 10),
                    fg=KelebekTheme.TEXT_MUTED,
                    bg=KelebekTheme.BG_WHITE,
                    justify="center"
                ).pack(pady=20)
                return
            
            columns = 5  # 5 sütunlu grid (daha fazla kombinasyon olabilir)
            for idx, komb in enumerate(kombinasyonlar):
                var = tk.BooleanVar()
                self.sinif_vars[komb] = var
                
                box = tk.Frame(
                    self.checkbox_frame,
                    bg=KelebekTheme.BG_CARD,
                    relief="flat",
                    borderwidth=1,
                    highlightbackground=KelebekTheme.BORDER_COLOR,
                    highlightthickness=1
                )
                row = idx // columns
                col = idx % columns
                box.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
                
                tk.Checkbutton(
                    box,
                    text=komb,
                    variable=var,
                    font=(KelebekTheme.FONT_FAMILY, 9, "bold"),
                    bg=KelebekTheme.BG_CARD,
                    fg=KelebekTheme.TEXT_DARK,
                    activebackground=KelebekTheme.BG_CARD
                ).pack(anchor="w", padx=6, pady=4)
            
            for col in range(columns):
                self.checkbox_frame.columnconfigure(col, weight=1)
                
        except Exception as e:
            tk.Label(
                self.checkbox_frame,
                text=f"Sınıf yükleme hatası: {e}",
                font=(KelebekTheme.FONT_FAMILY, 10),
                fg=KelebekTheme.DANGER,
                bg=KelebekTheme.BG_WHITE
            ).pack(pady=20)
    
    def create_list(self, parent):
        """Ders listesi"""
        # Treeview
        columns = ("ID", "Ders Adı", "Sınıflar")
        self.tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.tree.heading(col, text=col)
        
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Ders Adı", width=200)
        self.tree.column("Sınıflar", width=150, anchor="center")
        
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")
        
        # Sil butonu
        btn_frame = tk.Frame(parent, bg=KelebekTheme.BG_WHITE)
        btn_frame.pack(fill="x", pady=10)
        
        btn_delete = tk.Button(btn_frame, command=self.delete_selected)
        configure_standard_button(btn_delete, "danger", f"{KelebekTheme.ICON_DELETE} Sil")
        btn_delete.pack()
    
    def load_dersler(self):
        """Dersleri yükle"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            dersler = self.db.dersleri_listele()
            for ders in dersler:
                sinif_str = ", ".join(map(str, sorted(ders['sinif_seviyeleri'])))
                self.tree.insert("", "end", values=(
                    ders['id'],
                    ders['ders_adi'],
                    sinif_str
                ))
        except Exception as e:
            show_message(self.window, f"Yükleme hatası: {e}", "error")
    
    def add_ders(self):
        """Ders ekle"""
        ders_adi = self.ders_adi_entry.get().strip()
        
        if not ders_adi:
            show_message(self.window, "Ders adı boş bırakılamaz!", "warning")
            return
        
        # Seçili sınıfları al
        siniflar = [sinif for sinif, var in self.sinif_vars.items() if var.get()]
        
        if not siniflar:
            show_message(self.window, "En az bir sınıf seçmelisiniz!", "warning")
            return
        
        try:
            ders_id = self.db.ders_ekle(ders_adi, siniflar)
            show_message(self.window, f"✓ {ders_adi} eklendi!", "success")
            
            # Formu temizle
            self.ders_adi_entry.delete(0, tk.END)
            for var in self.sinif_vars.values():
                var.set(False)
            
            self.load_dersler()
            
            if hasattr(self.parent, 'refresh_stats'):
                self.parent.refresh_stats()
                
        except Exception as e:
            show_message(self.window, f"Ekleme hatası: {e}", "error")
    
    def delete_selected(self):
        """Seçili dersi sil"""
        selected = self.tree.selection()
        if not selected:
            show_message(self.window, "Lütfen silinecek dersi seçin!", "warning")
            return
        
        item = self.tree.item(selected[0])
        ders_id = item['values'][0]
        ders_adi = item['values'][1]
        
        if not ask_confirmation(self.window, f"{ders_adi} silinecek. Emin misiniz?"):
            return
        
        try:
            self.db.ders_sil(ders_id)
            show_message(self.window, "✓ Ders silindi!", "success")
            self.load_dersler()
            
            if hasattr(self.parent, 'refresh_stats'):
                self.parent.refresh_stats()
        except Exception as e:
            show_message(self.window, f"Silme hatası: {e}", "error")
