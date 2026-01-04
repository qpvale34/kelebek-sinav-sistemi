"""
Kelebek Sınav Sistemi - Sınıf Oturma Düzeni Yoklama ve Yazdırma

"""

import tkinter as tk
from tkinter import ttk, filedialog
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from assets.styles import (KelebekTheme, configure_standard_button,
                           show_message, create_card_frame)
from controllers.database_manager import get_db
from controllers.excel_handler import ExcelHandler
from utils import format_sira_label


class SinifOturmaDuzeniView:
    """Sınıf Oturma Düzeni Yoklama Listesi"""
    
    def __init__(self, window, parent):
        self.window = window
        self.parent = parent
        self.db = get_db()
        self.excel_handler = ExcelHandler()  # Argümansız
        
        # State
        self.yerlesim_data = []
        self.salon_gozetmen_map = {}
        self.gozetmen_atamalari = []
        self.sinav_dict = {}
        self.secili_sinav = None
        self.secili_sinav_id = None
        
        # Pencere ayarları
        self.window.title("📋 Sınıf Oturma Düzeni ve Yoklama Listesi")
        self.window.config(bg=KelebekTheme.BG_LIGHT)
        
        # Ekran boyutunu al
        screen_w = self.window.winfo_screenwidth()
        screen_h = self.window.winfo_screenheight()
        
        # Büyük pencere aç (ekranın %90'ı)
        win_w = int(screen_w * 0.9)
        win_h = int(screen_h * 0.85)
        x = (screen_w - win_w) // 2
        y = (screen_h - win_h) // 4
        self.window.geometry(f"{win_w}x{win_h}+{x}+{y}")
        
        # UI oluştur
        self._build_ui()
        self._load_sinavlar()
        
        # 100ms sonra maximize et
        self.window.after(100, lambda: self.window.state('zoomed'))
    
    def _build_ui(self):
        """Ana UI yapısını oluştur"""
        # ========== HEADER ==========
        header = tk.Frame(self.window, bg=KelebekTheme.SUCCESS, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="📋 Sınıf Oturma Düzeni Yoklama Listesi",
            font=(KelebekTheme.FONT_FAMILY, 18, "bold"),
            fg=KelebekTheme.TEXT_WHITE,
            bg=KelebekTheme.SUCCESS
        ).pack(pady=20)
        
        # ========== ANA İÇERİK ==========
        content = tk.Frame(self.window, bg=KelebekTheme.BG_LIGHT)
        content.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Sol Panel - Sınav Seçimi
        left_frame = tk.Frame(content, bg=KelebekTheme.BG_WHITE, width=350)
        left_frame.pack(side="left", fill="y", padx=(0, 10))
        left_frame.pack_propagate(False)
        
        self._build_sinav_panel(left_frame)
        
        # Sağ Panel - Yerleşim Tablosu
        right_frame = tk.Frame(content, bg=KelebekTheme.BG_WHITE)
        right_frame.pack(side="right", fill="both", expand=True)
        
        self._build_yerlesim_panel(right_frame)
        
        # ========== ALT BUTONLAR ==========
        btn_frame = tk.Frame(self.window, bg=KelebekTheme.BG_LIGHT, height=150)
        btn_frame.pack(fill="x", padx=15, pady=10)
        btn_frame.pack_propagate(False)
        
        btn_excel = tk.Button(btn_frame, command=self._excel_export)
        configure_standard_button(btn_excel, "success", 
            "📊 Seçili Şubenin Oturma Düzenini Excel Olarak Kaydet")
        btn_excel.pack(side="left", padx=5, pady=10)
        
        btn_excel_all = tk.Button(btn_frame, command=self._excel_export_all)
        configure_standard_button(btn_excel_all, "info", 
            "📋 Tüm Sınıfların Oturma Düzeni Yoklama Listesi Excel OLARAK KAYDET")
        btn_excel_all.pack(side="left", padx=5, pady=10)
        
        btn_refresh = tk.Button(btn_frame, command=self._load_yerlesim)
        configure_standard_button(btn_refresh, "primary", "🔄 Yerleşimi Yenile")
        btn_refresh.pack(side="left", padx=5, pady=10)
        
        btn_close = tk.Button(btn_frame, command=self.window.destroy)
        configure_standard_button(btn_close, "danger", "✖ Kapat")
        btn_close.pack(side="right", padx=5, pady=10)
    
    def _build_sinav_panel(self, parent):
        """Sol panel - Sınav seçimi"""
        # Başlık
        header = tk.Frame(parent, bg=KelebekTheme.PRIMARY, height=45)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="📝 SINAV SEÇİMİ",
            font=(KelebekTheme.FONT_FAMILY, 12, "bold"),
            fg=KelebekTheme.TEXT_WHITE,
            bg=KelebekTheme.PRIMARY
        ).pack(pady=12)
        
        # İçerik
        inner = tk.Frame(parent, bg=KelebekTheme.BG_WHITE, padx=10, pady=10)
        inner.pack(fill="both", expand=True)
        
        tk.Label(
            inner,
            text="Görüntülenecek sınavı seçin:",
            font=(KelebekTheme.FONT_FAMILY, 10),
            fg=KelebekTheme.TEXT_DARK,
            bg=KelebekTheme.BG_WHITE
        ).pack(anchor="w", pady=(0, 5))
        
        # Sınav Listesi
        list_frame = tk.Frame(inner, bg=KelebekTheme.BG_WHITE)
        list_frame.pack(fill="both", expand=True, pady=5)
        
        self.sinav_listbox = tk.Listbox(
            list_frame,
            font=(KelebekTheme.FONT_FAMILY, 10),
            height=15,
            selectmode=tk.SINGLE,
            bg=KelebekTheme.BG_CARD,
            fg=KelebekTheme.TEXT_DARK,
            selectbackground=KelebekTheme.PRIMARY,
            selectforeground=KelebekTheme.TEXT_WHITE,
            relief="flat",
            highlightthickness=1,
            highlightbackground=KelebekTheme.BORDER_COLOR
        )
        self.sinav_listbox.pack(side="left", fill="both", expand=True)
        self.sinav_listbox.bind("<<ListboxSelect>>", self._on_sinav_selected)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.sinav_listbox.yview)
        self.sinav_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # Salon Filtresi
        filter_frame = tk.Frame(inner, bg=KelebekTheme.BG_WHITE)
        filter_frame.pack(fill="x", pady=10)
        
        tk.Label(
            filter_frame,
            text="Salon Filtresi:",
            font=(KelebekTheme.FONT_FAMILY, 10),
            fg=KelebekTheme.TEXT_DARK,
            bg=KelebekTheme.BG_WHITE
        ).pack(side="left")
        
        self.salon_var = tk.StringVar(value="Tümü")
        self.salon_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.salon_var,
            state="readonly",
            width=20
        )
        self.salon_combo.pack(side="left", padx=10)
        self.salon_combo.bind("<<ComboboxSelected>>", lambda e: self._populate_tree())
        
        # Bilgi Label
        self.info_label = tk.Label(
            inner,
            text="📌 Sınav seçilmedi",
            font=(KelebekTheme.FONT_FAMILY, 10, "italic"),
            fg=KelebekTheme.TEXT_MUTED,
            bg=KelebekTheme.BG_WHITE,
            wraplength=300,
            justify="left"
        )
        self.info_label.pack(anchor="w", pady=5)
    
    def _build_yerlesim_panel(self, parent):
        """Sağ panel - Yerleşim tablosu"""
        # Başlık
        header = tk.Frame(parent, bg=KelebekTheme.INFO, height=45)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="📋 OTURMA DÜZENİ LİSTESİ",
            font=(KelebekTheme.FONT_FAMILY, 12, "bold"),
            fg=KelebekTheme.TEXT_WHITE,
            bg=KelebekTheme.INFO
        ).pack(pady=12)
        
        # Tablo
        tree_frame = tk.Frame(parent, bg=KelebekTheme.BG_WHITE)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        columns = ("Sınav", "Sıra", "Ad", "Soyad", "Sınıf", "Şube", "Salon", "Gözetmen")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
        
        col_widths = {"Sınav": 180, "Sıra": 50, "Ad": 100, "Soyad": 100, 
                      "Sınıf": 70, "Şube": 50, "Salon": 120, "Gözetmen": 180}
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=col_widths.get(col, 100))
        
        scroll_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")
        
        # İstatistik
        self.stat_label = tk.Label(
            parent,
            text="⏳ Sınav seçin ve yerleşimi görüntüleyin",
            font=(KelebekTheme.FONT_FAMILY, 11, "bold"),
            fg=KelebekTheme.INFO,
            bg=KelebekTheme.BG_WHITE
        )
        self.stat_label.pack(anchor="w", padx=10, pady=5)
    
    def _load_sinavlar(self):
        """Sınavları yükle"""
        self.sinav_listbox.delete(0, tk.END)
        self.sinav_dict = {}
        
        try:
            sinavlar = self.db.sinavlari_listele()
            for sinav in sinavlar:
                tarih_str = sinav.get('sinav_tarihi') or ''
                display = f"{sinav['sinav_adi']} | {sinav['ders_adi']}" + (f" | {tarih_str}" if tarih_str else '')
                self.sinav_listbox.insert(tk.END, display)
                self.sinav_dict[display] = sinav
            
            if not sinavlar:
                self.info_label.config(text="⚠️ Henüz sınav eklenmemiş")
        except Exception as e:
            self.info_label.config(text=f"❌ Hata: {e}")
    
    def _on_sinav_selected(self, event=None):
        """Sınav seçildiğinde"""
        selection = self.sinav_listbox.curselection()
        if not selection:
            return
        
        display = self.sinav_listbox.get(selection[0])
        sinav = self.sinav_dict.get(display)
        
        if sinav:
            self.secili_sinav = sinav
            self.secili_sinav_id = sinav['id']
            tarih_str = sinav.get('sinav_tarihi') or ''
            saat_str = sinav.get('sinav_saati') or ''
            tarih_info = f"\n📅 Tarih: {tarih_str} {saat_str}" if tarih_str else ''
            self.info_label.config(
                text=f"✅ Seçili: {sinav['sinav_adi']}{tarih_info}\n"
                     f"📚 Ders: {sinav['ders_adi']}"
            )
            self._load_yerlesim()
    
    def _load_yerlesim(self):
        """Yerleşimi yükle"""
        if not self.secili_sinav_id:
            show_message(self.window, "Önce bir sınav seçin!", "warning")
            return
        
        try:
            yerlesim = self.db.yerlesim_listele(self.secili_sinav_id)
            
            if not yerlesim:
                self.stat_label.config(
                    text="⚠️ Bu sınav için yerleşim bulunamadı. Önce harmanlama yapın.",
                    fg=KelebekTheme.WARNING
                )
                self.yerlesim_data = []
                self._populate_tree()
                return
            
            self.yerlesim_data = yerlesim
            
            # Salon listesi
            salonlar = sorted(set(y['salon_adi'] for y in yerlesim))
            self.salon_combo['values'] = ["Tümü"] + salonlar
            self.salon_var.set("Tümü")
            
            # Gözetmen bilgileri
            self._load_gozetmenler()
            
            # Tabloyu doldur
            self._populate_tree()
            
            self.stat_label.config(
                text=f"✅ {len(yerlesim)} öğrenci | {len(salonlar)} salon",
                fg=KelebekTheme.SUCCESS
            )
            
        except Exception as e:
            show_message(self.window, f"Yerleşim yükleme hatası: {e}", "error")
    
    def _load_gozetmenler(self):
        """Gözetmen atamalarını yükle"""
        self.salon_gozetmen_map = {}
        
        if not self.secili_sinav_id:
            return
        
        try:
            atamalar = self.db.gozetmen_atamalari_listele(self.secili_sinav_id)
            temp = {}
            for a in atamalar:
                sid = a['salon_id']
                gorev = "Asıl" if a['gorev_turu'] == 'asil' else "Yedek"
                temp.setdefault(sid, []).append(f"{a['ad']} {a['soyad']} ({gorev})")
            
            self.salon_gozetmen_map = {sid: ", ".join(n) for sid, n in temp.items()}
        except Exception:
            pass
    
    def _populate_tree(self):
        """Tabloyu doldur"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not self.yerlesim_data:
            return
        
        filtre = self.salon_var.get()
        
        for yer in sorted(self.yerlesim_data, key=lambda x: (x['salon_adi'], x['sira_no'])):
            if filtre != "Tümü" and yer['salon_adi'] != filtre:
                continue
            
            ogrenci = self.db.ogrenci_getir(yer['ogrenci_id'])
            if ogrenci:
                sira = format_sira_label(yer.get('sira_no'))
                sinav_adi = self.secili_sinav.get('sinav_adi', '-') if self.secili_sinav else '-'
                
                self.tree.insert("", "end", values=(
                    sinav_adi,
                    sira,
                    ogrenci['ad'],
                    ogrenci['soyad'],
                    ogrenci['sinif'],
                    ogrenci['sube'],
                    yer['salon_adi'],
                    self.salon_gozetmen_map.get(yer['salon_id'], "")
                ))
    
    def _excel_export(self):
        """Excel'e aktar"""
        if not self.yerlesim_data:
            show_message(self.window, "Önce yerleşim yükleyin!", "warning")
            return
        
        if not self.secili_sinav:
            show_message(self.window, "Sınav seçilmedi!", "warning")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Excel Olarak Kaydet",
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")],
            initialfile=f"oturma_duzeni_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        )
        
        if not file_path:
            return
        
        try:
            sinav = self.secili_sinav
            sinav_bilgi = {
                'sinav_adi': sinav['sinav_adi'],
                'ders_adi': sinav['ders_adi'],
                'tarih': sinav.get('sinav_tarihi') or '-',
                'saat': sinav.get('sinav_saati') or '-',
                'kacinci_ders': sinav.get('kacinci_ders') or '-'
            }
            
            export_data = []
            for yer in self.yerlesim_data:
                ogrenci = self.db.ogrenci_getir(yer['ogrenci_id'])
                if ogrenci:
                    export_data.append({
                        'salon_adi': yer['salon_adi'],
                        'sira_no': yer['sira_no'],
                        'ad': ogrenci['ad'],
                        'soyad': ogrenci['soyad'],
                        'sinif': ogrenci['sinif'],
                        'sube': ogrenci['sube'],
                        'gozetmenler': self.salon_gozetmen_map.get(yer['salon_id'], ""),
                        'sinav_adi': sinav['sinav_adi']
                    })
            
            if self.excel_handler.yerlesim_yazdir(file_path, sinav_bilgi, export_data):
                show_message(self.window, 
                    f"✅ Excel oluşturuldu:\n{file_path}\n\n"
                    "🏫 Salonların dışına asılabilir.", "success")
            else:
                show_message(self.window, "Excel oluşturulamadı!", "error")
        except Exception as e:
            show_message(self.window, f"Excel hatası: {e}", "error")
    
    def _excel_export_all(self):
        """TÜM sınavların oturma düzenlerini Excel'e aktar"""
        try:
            tum_yerlesim = self.db.tum_yerlesimleri_listele()
            
            if not tum_yerlesim:
                show_message(self.window, "Hiç yerleşim verisi bulunamadı!", "warning")
                return
            
            file_path = filedialog.asksaveasfilename(
                title="Tüm Oturma Düzenlerini Kaydet",
                defaultextension=".xlsx",
                filetypes=[("Excel Files", "*.xlsx")],
                initialfile=f"Sınıf Oturma Düzeni Yoklama Listesi_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
            )
            
            if not file_path:
                return
            
            sinav_bilgi = {
                'sinav_adi': "TÜM SINAVLAR",
                'ders_adi': "TÜM SINAVLAR",
                'tarih': datetime.now().strftime("%Y-%m-%d"),
                'saat': "-",
                'kacinci_ders': "-"
            }
            
            export_data = []
            for yer in tum_yerlesim:
                export_data.append({
                    'salon_adi': yer['salon_adi'],
                    'sira_no': yer['sira_no'],
                    'ad': yer['ad'],
                    'soyad': yer['soyad'],
                    'sinif': yer['sinif'],
                    'sube': yer['sube'],
                    'gozetmenler': "",
                    'sinav_adi': yer.get('sinav_adi', '')
                })
            
            if self.excel_handler.yerlesim_yazdir(file_path, sinav_bilgi, export_data):
                show_message(self.window, 
                    f"✅ Tüm sınavların oturma düzenleri oluşturuldu:\n{file_path}\n\n"
                    f"📋 Toplam {len(export_data)} öğrenci", "success")
            else:
                show_message(self.window, "Excel oluşturulamadı!", "error")
        except Exception as e:
            show_message(self.window, f"Excel hatası: {e}", "error")


# Alias
OturmaDuzeniView = SinifOturmaDuzeniView



