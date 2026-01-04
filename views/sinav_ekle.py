"""
Kelebek Sınav Sistemi - Geliştirilmiş Sınav Ekleme
Sınıf ve salon seçimi ile detaylı sınav oluşturma
"""

import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from assets.styles import (KelebekTheme, configure_standard_button,
                           show_message, ask_confirmation, create_card_frame)
from assets.layout import setup_responsive_window
from controllers.database_manager import get_db


class SinavEkleView:
    """Gelişmiş Sınav Ekleme View"""
    
    def __init__(self, window, parent):
        self.window = window
        self.parent = parent
        self.db = get_db()
        
        # Initialize state containers
        self.sinif_checkboxes = {}
        self.soru_dosyasi_lookup = {}
        
        self.window.title(f"{KelebekTheme.ICON_EXAM} Sınav Ekleme")
        self.window.geometry("1100x750")  # Slightly wider
        self.window.minsize(900, 600)     # Set minimum size
        self.window.config(bg=KelebekTheme.BG_LIGHT)
        setup_responsive_window(self.window)
        
        # Ana konteyner (Split View)
        main_frame = tk.Frame(self.window, bg=KelebekTheme.BG_LIGHT)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # --- SOL PANEL: Formlar ---
        left_panel = tk.Frame(main_frame, bg=KelebekTheme.BG_LIGHT, width=400)
        left_panel.pack(side="left", fill="y", padx=(0, 15))
        left_panel.pack_propagate(False)

        # Temel Bilgiler Kartı (Üst)
        basic_card = create_card_frame(left_panel, "Temel Bilgiler", KelebekTheme.ICON_EDIT)
        basic_card.pack(fill="x", pady=(0, 10))
        self.create_basic_info_form(basic_card.content)

        # Sınıf Seçimi Kartı (Alt - Esnek)
        sinif_card = create_card_frame(left_panel, "Sınava Girecek Sınıflar", KelebekTheme.ICON_STUDENT)
        sinif_card.pack(fill="both", expand=True)
        self.create_sinif_selection(sinif_card.content) # İçerisinde kendi scrollbar'ı olabilir

        # --- SAĞ PANEL: Liste ---
        right_panel = tk.Frame(main_frame, bg=KelebekTheme.BG_LIGHT)
        right_panel.pack(side="right", fill="both", expand=True)

        exams_card = create_card_frame(right_panel, "Mevcut Sınavlar", KelebekTheme.ICON_EXAM)
        exams_card.pack(fill="both", expand=True)
        self.create_exam_list(exams_card.content)

        # Alt Butonlar (main_frame'in altına, window'a pack edelim)
        btn_frame = tk.Frame(self.window, bg=KelebekTheme.BG_LIGHT, height=60)
        btn_frame.pack(fill="x", side="bottom", padx=20, pady=10)
        btn_frame.pack_propagate(False)

        btn_kaydet = tk.Button(btn_frame, command=self.save_sinav)
        configure_standard_button(btn_kaydet, "success",
                                 f"{KelebekTheme.ICON_CHECK} Sınavı Oluştur")
        btn_kaydet.pack(side="right")

        btn_iptal = tk.Button(btn_frame, command=self.window.destroy)
        configure_standard_button(btn_iptal, "secondary", "İptal")
        btn_iptal.pack(side="right", padx=10)
    
    def create_basic_info_form(self, parent):
        """Temel bilgiler formu"""
        form = tk.Frame(parent, bg=KelebekTheme.BG_WHITE)
        form.pack(fill="x", padx=15, pady=15)
        
        # Grid layout
        row = 0
        
        # Sınav Adı
        tk.Label(
            form,
            text="Sınav Adı:",
            font=(KelebekTheme.FONT_FAMILY, 11, "bold"),
            bg=KelebekTheme.BG_WHITE
        ).grid(row=row, column=0, sticky="w", pady=8, padx=5)
        
        self.sinav_adi_entry = tk.Entry(
            form,
            font=(KelebekTheme.FONT_FAMILY, 11),
            width=40
        )
        self.sinav_adi_entry.grid(row=row, column=1, pady=8, padx=5, sticky="ew")
        self.sinav_adi_entry.insert(0, "Arapça")
        
        row += 1
        
        # Ders seçimi
        tk.Label(
            form,
            text="Ders:",
            font=(KelebekTheme.FONT_FAMILY, 11, "bold"),
            bg=KelebekTheme.BG_WHITE
        ).grid(row=row, column=0, sticky="w", pady=8, padx=5)
        
        self.ders_var = tk.StringVar()
        self.ders_combo = ttk.Combobox(
            form,
            textvariable=self.ders_var,
            state="readonly",
            width=38,
            font=(KelebekTheme.FONT_FAMILY, 11)
        )
        self.ders_combo.grid(row=row, column=1, pady=8, padx=5, sticky="ew")
        self.ders_combo.bind("<<ComboboxSelected>>", lambda _: self.refresh_soru_dosyasi())
        
        row += 1
        
        tk.Label(
            form,
            text="Soru Dosyası:",
            font=(KelebekTheme.FONT_FAMILY, 11, "bold"),
            bg=KelebekTheme.BG_WHITE
        ).grid(row=row, column=0, sticky="w", pady=8, padx=5)
        
        soru_frame = tk.Frame(form, bg=KelebekTheme.BG_WHITE)
        soru_frame.grid(row=row, column=1, pady=8, padx=5, sticky="ew")
        
        self.soru_dosyasi_var = tk.StringVar()
        self.soru_combo = ttk.Combobox(
            soru_frame,
            textvariable=self.soru_dosyasi_var,
            state="readonly",
            width=30
        )
        self.soru_combo.pack(side="left", fill="x", expand=True)
        
        btn_soru_refresh = tk.Button(soru_frame, command=self.refresh_soru_dosyasi)
        configure_standard_button(btn_soru_refresh, "secondary", "↻")
        btn_soru_refresh.pack(side="left", padx=4)
        
        btn_soru_manage = tk.Button(soru_frame, command=self.open_soru_bankasi)
        configure_standard_button(btn_soru_manage, "info", "Soru Bankası")
        btn_soru_manage.pack(side="left")
        
        row += 1
        self.load_dersler()
        
        # Tarih, Saat, Kaçıncı Ders alanları kaldırıldı
        
        form.columnconfigure(1, weight=1)
    
    def create_sinif_selection(self, parent):
        """Sınıf seçimi alanı - veritabanından dinamik"""
        info_frame = tk.Frame(parent, bg=KelebekTheme.BG_WHITE)
        info_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Label(
            info_frame,
            text="Bu sınava girecek sınıfları seçin:",
            font=(KelebekTheme.FONT_FAMILY, 10),
            fg=KelebekTheme.TEXT_DARK,
            bg=KelebekTheme.BG_WHITE
        ).pack(side="left")
        
        # Yenile butonu
        btn_refresh = tk.Button(info_frame, command=self.load_siniflar)
        configure_standard_button(btn_refresh, "secondary", "↻ Yenile")
        btn_refresh.pack(side="right")
        
        # Checkbox container
        self.sinif_checkbox_frame = tk.Frame(parent, bg=KelebekTheme.BG_WHITE)
        self.sinif_checkbox_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.sinif_checkboxes = {}
        
        # Sınıfları yükle
        self.load_siniflar()
        
        # Toplam label
        self.toplam_ogrenci_label = tk.Label(
            parent,
            text="Toplam: 0 öğrenci seçildi",
            font=(KelebekTheme.FONT_FAMILY, 11, "bold"),
            fg=KelebekTheme.INFO,
            bg=KelebekTheme.BG_WHITE
        )
        self.toplam_ogrenci_label.pack(pady=10)
    
    def load_siniflar(self):
        """Veritabanından sınıf-şube kombinasyonlarını yükle"""
        # Mevcut checkbox'ları temizle
        if hasattr(self, 'sinif_checkbox_frame'):
            for widget in self.sinif_checkbox_frame.winfo_children():
                widget.destroy()
        
        self.sinif_checkboxes = {}
        
        try:
            # Veritabanından benzersiz sınıf-şube kombinasyonlarını al
            kombinasyonlar = self.db.benzersiz_sinif_sube()
            
            if not kombinasyonlar:
                tk.Label(
                    self.sinif_checkbox_frame,
                    text="⚠️ Henüz öğrenci eklenmemiş. Önce öğrenci ekleyin.",
                    font=(KelebekTheme.FONT_FAMILY, 10),
                    fg=KelebekTheme.TEXT_MUTED,
                    bg=KelebekTheme.BG_WHITE
                ).pack(pady=20)
                return
            
            columns = 5  # 5 sütunlu grid
            for idx, komb in enumerate(kombinasyonlar):
                frame = tk.Frame(
                    self.sinif_checkbox_frame,
                    bg=KelebekTheme.BG_CARD,
                    relief="flat",
                    borderwidth=1,
                    highlightbackground=KelebekTheme.BORDER_COLOR,
                    highlightthickness=1
                )
                row = idx // columns
                col = idx % columns
                frame.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
                
                var = tk.BooleanVar(value=False)
                self.sinif_checkboxes[komb] = var
                
                # Sınıf-şube'yi ayır ve öğrenci sayısını al
                parts = komb.split('-', 1)
                sinif = parts[0]
                sube = parts[1] if len(parts) > 1 else ''
                ogrenci_sayisi = len(self.db.ogrencileri_listele(sinif=sinif, sube=sube))
                
                cb = tk.Checkbutton(
                    frame,
                    text=komb,
                    variable=var,
                    font=(KelebekTheme.FONT_FAMILY, 9, "bold"),
                    bg=KelebekTheme.BG_CARD,
                    fg=KelebekTheme.TEXT_DARK,
                    activebackground=KelebekTheme.BG_CARD,
                    command=self.update_sinif_info
                )
                cb.pack(anchor="center", pady=(5, 2))
                
                # Öğrenci sayısı label
                count_label = tk.Label(
                    frame,
                    text=f"{ogrenci_sayisi} öğr.",
                    font=(KelebekTheme.FONT_FAMILY, 8),
                    fg=KelebekTheme.TEXT_MUTED,
                    bg=KelebekTheme.BG_CARD
                )
                count_label.pack(anchor="center", pady=(0, 5))
                
                self.sinif_checkboxes[f"{komb}_count"] = ogrenci_sayisi
            
            for col in range(columns):
                self.sinif_checkbox_frame.columnconfigure(col, weight=1)
                
        except Exception as e:
            tk.Label(
                self.sinif_checkbox_frame,
                text=f"Sınıf yükleme hatası: {e}",
                font=(KelebekTheme.FONT_FAMILY, 10),
                fg=KelebekTheme.DANGER,
                bg=KelebekTheme.BG_WHITE
            ).pack(pady=20)
        
        self.update_sinif_info()
    
    def load_dersler(self):
        """Dersleri yükle"""
        try:
            dersler = self.db.dersleri_listele()
            
            self.ders_dict = {}
            ders_items = []
            
            for ders in dersler:
                item_text = f"{ders['ders_adi']}"
                ders_items.append(item_text)
                self.ders_dict[item_text] = ders
            
            self.ders_combo['values'] = ders_items
            
            if ders_items:
                self.ders_combo.current(0)
                self.refresh_soru_dosyasi()
        except Exception as e:
            show_message(self.window, f"Ders yükleme hatası: {e}", "error")
    
    def refresh_soru_dosyasi(self):
        """Seçili ders için soru dosyalarını listele"""
        if not hasattr(self, 'ders_dict'):
            return
        ders = self.ders_dict.get(self.ders_var.get())
        if not ders:
            self.soru_combo['values'] = ["Soru dosyası yok"]
            self.soru_combo.set("Soru dosyası yok")
            self.soru_dosyasi_lookup = {}
            return
        
        try:
            dosyalar = self.db.soru_bankasi_listele(ders_id=ders['id'])
            self.soru_dosyasi_lookup = {d['dosya_adi']: d for d in dosyalar}
            if dosyalar:
                self.soru_combo['values'] = list(self.soru_dosyasi_lookup.keys())
                self.soru_combo.current(0)
            else:
                self.soru_combo['values'] = ["Soru dosyası yok"]
                self.soru_combo.set("Soru dosyası yok")
        except Exception as e:
            show_message(self.window, f"Soru dosyaları yüklenemedi: {e}", "warning")
    
    def open_soru_bankasi(self):
        """Soru bankası penceresini aç"""
        try:
            from views.soru_bankasi import SoruBankasiView
            dialog = tk.Toplevel(self.window)
            SoruBankasiView(dialog, self)
            dialog.transient(self.window)
            dialog.grab_set()
            dialog.bind("<Destroy>", lambda _: self.refresh_soru_dosyasi())
        except ImportError as e:
            show_message(self.window, f"Soru bankası modülü yüklenemedi: {e}", "error")
    
    def create_exam_list(self, parent):
        """Mevcut sınavları listeleyen alan"""
        frame = tk.Frame(parent, bg=KelebekTheme.BG_WHITE)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        columns = ("ID", "Sınav", "Ders")
        self.exam_tree = ttk.Treeview(frame, columns=columns, show="headings", height=8)
        widths = [60, 280, 280]
        for col, width in zip(columns, widths):
            self.exam_tree.heading(col, text=col)
            self.exam_tree.column(col, width=width, anchor="center")
        self.exam_tree.pack(side="left", fill="both", expand=True)
        
        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.exam_tree.yview)
        self.exam_tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        
        btn_frame = tk.Frame(parent, bg=KelebekTheme.BG_WHITE)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        btn_delete = tk.Button(btn_frame, command=self.delete_selected_exam)
        configure_standard_button(btn_delete, "danger", f"{KelebekTheme.ICON_DELETE} Seçili Sınavı Sil")
        btn_delete.pack(side="left")
        
        self.load_existing_exams()
    
    def load_existing_exams(self):
        if not hasattr(self, 'exam_tree'):
            return
        for item in self.exam_tree.get_children():
            self.exam_tree.delete(item)
        
        try:
            exams = self.db.sinavlari_listele()
            for exam in exams:
                self.exam_tree.insert("", "end", values=(
                    exam['id'],
                    exam['sinav_adi'],
                    exam['ders_adi']
                ))
        except Exception as e:
            show_message(self.window, f"Sınav listesi yüklenemedi: {e}", "error")
    
    def delete_selected_exam(self):
        if not hasattr(self, 'exam_tree'):
            return
        selection = self.exam_tree.selection()
        if not selection:
            show_message(self.window, "Lütfen silinecek sınavı seçin!", "warning")
            return
        item = self.exam_tree.item(selection[0])
        sinav_id = item['values'][0]
        sinav_adi = item['values'][1]
        if not ask_confirmation(self.window, f"{sinav_adi} silinecek. Emin misiniz?"):
            return
        try:
            if self.db.sinav_sil(sinav_id):
                show_message(self.window, "✓ Sınav silindi!", "success")
                self.load_existing_exams()
            else:
                show_message(self.window, "Sınav silinemedi!", "error")
        except Exception as e:
            show_message(self.window, f"Silme hatası: {e}", "error")
    
    def update_sinif_info(self):
        """Sınıf bilgilerini güncelle"""
        toplam = 0
        
        # Dinamik sınıf-şube kombinasyonları üzerinden döngü
        for key, value in self.sinif_checkboxes.items():
            # '_count' ile bitenler öğrenci sayılarını tutuyor
            if key.endswith('_count'):
                continue
            
            if isinstance(value, tk.BooleanVar) and value.get():
                # Bu sınıf-şube seçili, öğrenci sayısını al
                count_key = f"{key}_count"
                if count_key in self.sinif_checkboxes:
                    toplam += self.sinif_checkboxes[count_key]
        
        if hasattr(self, 'toplam_ogrenci_label'):
            self.toplam_ogrenci_label.config(text=f"Toplam: {toplam} öğrenci seçildi")
    
    def save_sinav(self):
        """Sınavı kaydet"""
        # Validasyon
        sinav_adi = self.sinav_adi_entry.get().strip()
        if not sinav_adi:
            show_message(self.window, "Sınav adı boş bırakılamaz!", "warning")
            return
        
        ders_sec = self.ders_var.get()
        if not ders_sec:
            show_message(self.window, "Ders seçmelisiniz!", "warning")
            return
        
        # Seçili sınıfları al
        secili_siniflar = [
            sinif for sinif, var in self.sinif_checkboxes.items()
            if isinstance(var, tk.BooleanVar) and var.get()
        ]
        
        if not secili_siniflar:
            show_message(self.window, "En az bir sınıf seçmelisiniz!", "warning")
            return
        
        ogrenciler = self.db.ogrencileri_listele(siniflar=secili_siniflar)
        if not ogrenciler:
            show_message(self.window, "Seçilen sınıflarda aktif öğrenci bulunamadı!", "warning")
            return
        
        # Salon seçimi harmanlama ekranında yapılacak
        secili_salonlar = []
        
        try:
            ders = self.ders_dict[ders_sec]
            soru_secimi = self.soru_dosyasi_lookup.get(self.soru_dosyasi_var.get())
            soru_id = soru_secimi['id'] if soru_secimi else None
            
            sinav_id = self.db.sinav_ekle(
                sinav_adi,
                ders['id'],
                secili_siniflar,
                secili_salonlar,
                soru_dosyasi_id=soru_id
            )
            
            show_message(self.window, f"✅ Sınav oluşturuldu! (ID: {sinav_id})", "success")
            self.load_existing_exams()
            
            if hasattr(self.parent, 'refresh_stats'):
                self.parent.refresh_stats()
            
        except Exception as e:
            show_message(self.window, f"Kaydetme hatası: {e}", "error")
