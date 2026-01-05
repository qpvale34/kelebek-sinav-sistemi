"""
Kelebek Sınav Sistemi - Öğrenci Ekleme Ekranı
Excel ile toplu veya manuel tek tek öğrenci ekleme
"""

import tkinter as tk
from tkinter import ttk, filedialog
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from assets.styles import (KelebekTheme, StyleHelper, configure_standard_button,
                           show_message, ask_confirmation, create_card_frame,
                           ScrollableFrame)
from assets.layout import setup_responsive_window
from controllers.database_manager import get_db
from controllers.excel_handler import ExcelHandler
from utils import SINIF_SEVIYELERI


class OgrenciEkleView:
    """Öğrenci ekleme ve yönetim ekranı"""
    
    def __init__(self, window, parent):
        self.window = window
        self.parent = parent
        self.db = get_db()
        self.excel_handler = ExcelHandler()
        setup_responsive_window(self.window)
        
        # Pagination state
        self._page_size = 50
        self._current_offset = 0
        self._total_count = 0
        self._loading = False
        
        self.setup_ui()
        self.load_ogrenciler()
    
    def setup_ui(self):
        """UI oluştur"""
        self.window.title(f"{KelebekTheme.ICON_STUDENT} Öğrenci Yönetimi")
        self.window.geometry("1100x700") # Genişletilmiş
        self.window.config(bg=KelebekTheme.BG_LIGHT)
        
        # Header
        self.create_header()
        
        # Ana içerik (Split View)
        content_frame = tk.Frame(self.window, bg=KelebekTheme.BG_LIGHT)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Sol panel - Ekleme işlemleri (Sabit genişlik)
        self.create_left_panel(content_frame)
        
        # Sağ panel - Öğrenci listesi (Esnek)
        self.create_right_panel(content_frame)
    
    def create_header(self):
        """Başlık"""
        header = tk.Frame(self.window, bg=KelebekTheme.SECONDARY, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text=f"{KelebekTheme.ICON_STUDENT} ÖĞRENCİ YÖNETİMİ",
            font=(KelebekTheme.FONT_FAMILY, 20, "bold"),
            fg=KelebekTheme.TEXT_WHITE,
            bg=KelebekTheme.SECONDARY
        ).pack(pady=15)
    
    def create_left_panel(self, parent):
        """Sol panel - Ekleme işlemleri"""
        left_frame = tk.Frame(parent, bg=KelebekTheme.BG_LIGHT, width=380)
        left_frame.pack(side="left", fill="y", padx=(0, 10))
        left_frame.pack_propagate(False) # Genişliği sabitle
        
        # Excel ile ekleme card
        excel_card = create_card_frame(left_frame, "Excel ile Toplu Ekleme", KelebekTheme.ICON_EXCEL)
        excel_card.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            excel_card.content,
            text="Excel dosyasından toplu öğrenci ekleyin",
            font=(KelebekTheme.FONT_FAMILY, 10),
            fg=KelebekTheme.TEXT_MUTED,
            bg=KelebekTheme.BG_WHITE
        ).pack(pady=5)
        
        btn_frame1 = tk.Frame(excel_card.content, bg=KelebekTheme.BG_WHITE)
        btn_frame1.pack(pady=10)
        
        btn_sablon = tk.Button(btn_frame1, command=self.create_excel_template)
        configure_standard_button(btn_sablon, "secondary", "📄 Şablon İndir")
        btn_sablon.pack(side="left", padx=5)
        
        btn_excel = tk.Button(btn_frame1, command=self.import_from_excel)
        configure_standard_button(btn_excel, "success", "📂 Çoklu Excel Aktar")
        btn_excel.pack(side="left", padx=5)
        
        # Manuel ekleme card
        manual_card = create_card_frame(left_frame, "Manuel Öğrenci Ekle", KelebekTheme.ICON_EDIT)
        manual_card.pack(fill="both", expand=True)
        
        self.create_manual_form(manual_card.content)
    
    def create_manual_form(self, parent):
        """Manuel ekleme formu"""
        form_frame = tk.Frame(parent, bg=KelebekTheme.BG_WHITE)
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Form alanları
        fields = [
            ("Ad:", "ad"),
            ("Soyad:", "soyad"),
            ("TC No:", "tc_no"),
        ]
        
        self.entries = {}
        
        for i, (label_text, field_name) in enumerate(fields):
            tk.Label(
                form_frame,
                text=label_text,
                font=(KelebekTheme.FONT_FAMILY, 11, "bold"),
                fg=KelebekTheme.TEXT_DARK,
                bg=KelebekTheme.BG_WHITE
            ).grid(row=i, column=0, sticky="w", pady=8, padx=5)
            
            entry = tk.Entry(form_frame, **StyleHelper.get_entry_style(),
                           font=(KelebekTheme.FONT_FAMILY, 11), width=25)
            entry.grid(row=i, column=1, pady=8, padx=5, sticky="ew")
            self.entries[field_name] = entry
        
        # Sınıf seçimi
        tk.Label(
            form_frame,
            text="Sınıf:",
            font=(KelebekTheme.FONT_FAMILY, 11, "bold"),
            fg=KelebekTheme.TEXT_DARK,
            bg=KelebekTheme.BG_WHITE
        ).grid(row=3, column=0, sticky="w", pady=8, padx=5)
        
        self.sinif_var = tk.StringVar(value=str(SINIF_SEVIYELERI[0]))
        sinif_combo = ttk.Combobox(form_frame, textvariable=self.sinif_var,
                                   values=[str(s) for s in SINIF_SEVIYELERI],
                                   state="readonly", width=23)
        sinif_combo.grid(row=3, column=1, pady=8, padx=5, sticky="ew")
        
        # Şube seçimi
        tk.Label(
            form_frame,
            text="Şube:",
            font=(KelebekTheme.FONT_FAMILY, 11, "bold"),
            fg=KelebekTheme.TEXT_DARK,
            bg=KelebekTheme.BG_WHITE
        ).grid(row=4, column=0, sticky="w", pady=8, padx=5)
        
        self.sube_var = tk.StringVar(value="A")
        sube_combo = ttk.Combobox(form_frame, textvariable=self.sube_var,
                                  values=["A", "B", "C", "D", "E", "F"],
                                  state="readonly", width=23)
        sube_combo.grid(row=4, column=1, pady=8, padx=5, sticky="ew")
        
        # Sabit öğrenci checkbox
        self.sabit_var = tk.BooleanVar()
        tk.Checkbutton(
            form_frame,
            text="Sabit Öğrenci (Yer değiştirmez)",
            variable=self.sabit_var,
            font=(KelebekTheme.FONT_FAMILY, 10),
            bg=KelebekTheme.BG_WHITE,
            fg=KelebekTheme.TEXT_DARK
        ).grid(row=5, column=0, columnspan=2, pady=10, sticky="w", padx=5)
        
        # Ekle butonu
        btn_ekle = tk.Button(form_frame, command=self.add_ogrenci_manual)
        configure_standard_button(btn_ekle, "success", f"{KelebekTheme.ICON_CHECK} Öğrenci Ekle")
        btn_ekle.grid(row=6, column=0, columnspan=2, pady=15)
        
        form_frame.columnconfigure(1, weight=1)
    
    def create_right_panel(self, parent):
        """Sağ panel - Öğrenci listesi"""
        right_frame = tk.Frame(parent, bg=KelebekTheme.BG_LIGHT)
        right_frame.pack(side="right", fill="both", expand=True)
        
        # Başlık ve filtreler
        filter_frame = tk.Frame(right_frame, bg=KelebekTheme.BG_WHITE)
        filter_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            filter_frame,
            text="Öğrenci Listesi",
            font=(KelebekTheme.FONT_FAMILY, 14, "bold"),
            fg=KelebekTheme.TEXT_DARK,
            bg=KelebekTheme.BG_WHITE
        ).pack(side="left", padx=10, pady=10)
        
        # Filtre - Sınıf
        tk.Label(filter_frame, text="Sınıf:", bg=KelebekTheme.BG_WHITE,
                font=(KelebekTheme.FONT_FAMILY, 10)).pack(side="left", padx=(20, 5))
        
        self.filter_sinif = tk.StringVar(value="Tümü")
        ttk.Combobox(filter_frame, textvariable=self.filter_sinif,
                    values=["Tümü"] + [str(s) for s in SINIF_SEVIYELERI],
                    state="readonly", width=8).pack(side="left", padx=5)
        
        tk.Label(filter_frame, text="Şube:", bg=KelebekTheme.BG_WHITE,
                font=(KelebekTheme.FONT_FAMILY, 10)).pack(side="left", padx=(20, 5))
        
        self.filter_sube = tk.StringVar(value="Tümü")
        ttk.Combobox(filter_frame, textvariable=self.filter_sube,
                    values=["Tümü", "A", "B", "C", "D", "E", "F"],
                    state="readonly", width=6).pack(side="left", padx=5)
        
        # Filtrele butonu
        btn_filter = tk.Button(filter_frame, command=self.load_ogrenciler)
        configure_standard_button(btn_filter, "secondary", "🔍 Filtrele")
        btn_filter.pack(side="left", padx=10)
        
        # Treeview için frame
        tree_frame = tk.Frame(right_frame, bg=KelebekTheme.BG_WHITE)
        tree_frame.pack(fill="both", expand=True)
        
        # Treeview oluştur
        columns = ("No", "ID", "Ad", "Soyad", "Sınıf", "Şube", "Sabit")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
        
        # Kolonları yapılandır
        widths = [60, 60, 140, 140, 80, 80, 100]
        for col, width in zip(columns, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor="center")
        
        # Scrollbar with lazy loading binding
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self._on_scroll_update)
        self._scrollbar = scrollbar
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Butonlar
        btn_frame = tk.Frame(right_frame, bg=KelebekTheme.BG_LIGHT)
        btn_frame.pack(fill="x", pady=10)
        
        btn_delete = tk.Button(btn_frame, command=self.delete_selected)
        configure_standard_button(btn_delete, "danger", f"{KelebekTheme.ICON_DELETE} Seçileni Sil")
        btn_delete.pack(side="left", padx=5)
        
        btn_refresh = tk.Button(btn_frame, command=self.load_ogrenciler)
        configure_standard_button(btn_refresh, "secondary", "🔄 Yenile")
        btn_refresh.pack(side="left", padx=5)
        
        btn_delete_all = tk.Button(btn_frame, command=self.delete_all_students)
        configure_standard_button(btn_delete_all, "danger", "🗑️ Tümünü Sil")
        btn_delete_all.pack(side="right", padx=5)
    
    def _on_scroll_update(self, first, last):
        """Scrollbar güncelleme callback'i - lazy loading tetikler"""
        self._scrollbar.set(first, last)
        # %90'dan fazla scroll edildiyse daha fazla yükle
        if float(last) >= 0.9:
            self._on_tree_scroll()
    
    def load_ogrenciler(self, append: bool = False):
        """Öğrencileri yükle (lazy loading destekli)
        
        Args:
            append: True ise mevcut listeye ekle, False ise listeyi sıfırla
        """
        if self._loading:
            return
        
        self._loading = True
        
        try:
            # Filtre uygula (string tabanlı sınıf seviyeleri)
            sinif_filter = None if self.filter_sinif.get() == "Tümü" else self.filter_sinif.get()
            sube_filter = None if self.filter_sube.get() == "Tümü" else self.filter_sube.get()
            
            if not append:
                # Liste sıfırlanıyor
                for item in self.tree.get_children():
                    self.tree.delete(item)
                self._current_offset = 0
                self._total_count = self.db.ogrenci_sayisi(sinif=sinif_filter, sube=sube_filter)
            
            # Daha fazla veri var mı kontrol et
            if self._current_offset >= self._total_count:
                self._loading = False
                return
            
            ogrenciler = self.db.ogrencileri_listele(
                sinif=sinif_filter, 
                sube=sube_filter,
                limit=self._page_size,
                offset=self._current_offset
            )
            
            start_index = self._current_offset + 1
            for index, ogr in enumerate(ogrenciler, start=start_index):
                sabit = "✓ Sabit" if ogr['sabit_mi'] else ""
                self.tree.insert("", "end", values=(
                    index,
                    ogr['id'],
                    ogr['ad'],
                    ogr['soyad'],
                    ogr['sinif'],
                    ogr['sube'],
                    sabit
                ))
            
            self._current_offset += len(ogrenciler)
            
        except Exception as e:
            show_message(self.window, f"Yükleme hatası: {e}", "error")
        finally:
            self._loading = False
    
    def _on_tree_scroll(self, *args):
        """Treeview scroll olayını yakala ve gerekirse daha fazla veri yükle"""
        # Scrollbar pozisyonunu kontrol et
        if self.tree.yview()[1] >= 0.9:  # %90'dan fazla scroll edildi
            if self._current_offset < self._total_count:
                self.load_ogrenciler(append=True)
    
    def add_ogrenci_manual(self):
        """Manuel öğrenci ekle"""
        # Verileri al
        ad = self.entries['ad'].get().strip()
        soyad = self.entries['soyad'].get().strip()
        tc_no = self.entries['tc_no'].get().strip()
        sinif = self.sinif_var.get()  # String olarak sakla
        sube = self.sube_var.get()
        sabit_mi = self.sabit_var.get()
        
        # Validasyon
        if not ad or not soyad:
            show_message(self.window, "Ad ve soyad boş bırakılamaz!", "warning")
            return
        
        if tc_no and len(tc_no) != 11:
            show_message(self.window, "TC No 11 haneli olmalıdır!", "warning")
            return
        
        try:
            # Veritabanına ekle
            ogr_id = self.db.ogrenci_ekle(ad, soyad, sinif, sube, 
                                         tc_no if tc_no else None, sabit_mi)
            
            show_message(self.window, 
                        f"✓ {ad} {soyad} başarıyla eklendi! (ID: {ogr_id})", 
                        "success")
            
            # Formu temizle
            for entry in self.entries.values():
                entry.delete(0, tk.END)
            self.sabit_var.set(False)
            
            # Listeyi yenile
            self.load_ogrenciler()
            
            # Ana sayfadaki istatistikleri güncelle
            if hasattr(self.parent, 'refresh_stats'):
                self.parent.refresh_stats()
                
        except Exception as e:
            show_message(self.window, f"Ekleme hatası: {e}", "error")
    
    def import_from_excel(self):
        """Excel'den toplu öğrenci aktar (birden fazla dosya)"""
        file_paths = filedialog.askopenfilenames(
            title="Excel Dosyaları Seç",
            filetypes=[("Excel Files", "*.xlsx *.xls")],
        )
        
        if not file_paths:
            return
        
        toplam_kayit = []
        hata_loglari = []
        dosya_ozetleri = []
        
        try:
            for path in file_paths:
                ogrenciler, hatalar = self.excel_handler.ogrenci_oku(path)
                basename = os.path.basename(path)
                
                if ogrenciler:
                    toplam_kayit.extend(ogrenciler)
                    dosya_ozetleri.append(f"{basename}: {len(ogrenciler)} kayıt")
                
                for hata in hatalar:
                    hata_loglari.append(f"{basename}: {hata}")
            
            if not toplam_kayit:
                show_message(self.window, "Excel dosyalarında geçerli öğrenci bulunamadı!", "error")
                if hata_loglari:
                    show_message(self.window, "\n".join(hata_loglari[:5]), "warning")
                return
            
            detay_mesaj = "Seçilen dosyalar:\n" + "\n".join(dosya_ozetleri)
            detay_mesaj += f"\n\nToplam {len(toplam_kayit)} öğrenci eklenecek."
            
            if not ask_confirmation(self.window, f"{detay_mesaj}\nDevam edilsin mi?"):
                return
            
            eklenen = self.db.ogrenci_toplu_ekle(toplam_kayit)
            
            bilgi_mesaj = f"✓ {eklenen} öğrenci başarıyla eklendi!"
            if hata_loglari:
                bilgi_mesaj += f"\n⚠️ {len(hata_loglari)} uyarı bulundu. İlk kayıtlar:\n" + "\n".join(hata_loglari[:5])
            show_message(self.window, bilgi_mesaj, "success")
            
            self.load_ogrenciler()
            
            if hasattr(self.parent, 'refresh_stats'):
                self.parent.refresh_stats()
        except Exception as e:
            show_message(self.window, f"Import hatası: {e}", "error")
    
    def create_excel_template(self):
        """Excel şablonu oluştur"""
        file_path = filedialog.asksaveasfilename(
            title="Şablon Kaydet",
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")],
            initialfile="ogrenci_sablonu.xlsx"
        )
        
        if not file_path:
            return
        
        try:
            if self.excel_handler.ogrenci_sablonu_olustur(file_path):
                show_message(self.window, 
                            f"✓ Şablon oluşturuldu:\n{file_path}", 
                            "success")
        except Exception as e:
            show_message(self.window, f"Şablon oluşturma hatası: {e}", "error")
    
    def delete_selected(self):
        """Seçili öğrenciyi sil"""
        selected = self.tree.selection()
        if not selected:
            show_message(self.window, "Lütfen silinecek öğrenciyi seçin!", "warning")
            return
        
        item = self.tree.item(selected[0])
        ogr_id = item['values'][1]
        ogr_ad = f"{item['values'][2]} {item['values'][3]}"
        
        if not ask_confirmation(self.window, 
                               f"{ogr_ad} silinecek. Emin misiniz?"):
            return
        
        try:
            if self.db.ogrenci_sil(ogr_id):
                show_message(self.window, "✓ Öğrenci silindi!", "success")
                self.load_ogrenciler()
                
                if hasattr(self.parent, 'refresh_stats'):
                    self.parent.refresh_stats()
        except Exception as e:
            show_message(self.window, f"Silme hatası: {e}", "error")
    
    def delete_all_students(self):
        """Tüm öğrencileri toplu olarak sil"""
        mevcut = len(self.tree.get_children())
        if mevcut == 0:
            show_message(self.window, "Silinecek aktif öğrenci bulunamadı.", "info")
            return
        
        mesaj = (
            "Tüm aktif öğrenciler silinecek ve bu işlem geri alınamaz.\n\n"
            "Devam etmek istediğinize emin misiniz?"
        )
        if not ask_confirmation(self.window, mesaj):
            return
        
        try:
            silinen = self.db.ogrencileri_toplu_sil()
            if silinen == 0:
                show_message(self.window, "Zaten silinecek öğrenci yok.", "info")
                return
            show_message(self.window, f"✓ {silinen} öğrenci başarıyla silindi!", "success")
            self.load_ogrenciler()
            if hasattr(self.parent, 'refresh_stats'):
                self.parent.refresh_stats()
        except Exception as e:
            show_message(self.window, f"Toplu silme hatası: {e}", "error")


# Test
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    window = tk.Toplevel(root)
    
    class MockParent:
        def refresh_stats(self):
            pass
    
    app = OgrenciEkleView(window, MockParent())
    root.mainloop()
