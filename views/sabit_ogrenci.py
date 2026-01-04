# ============================================
# Dosya: views/sabit_ogrenci.py
"""Sabit Öğrenci İşaretleme"""
import tkinter as tk
from tkinter import ttk
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from assets.styles import *
from assets.layout import setup_responsive_window
from controllers.database_manager import get_db

class SabitOgrenciView:
    def __init__(self, window, parent):
        self.window = window
        self.parent = parent
        self.db = get_db()
        self.selected_ogrenci_id = None
        self.selected_salon_id = None
        self.ogrenci_detaylari = {}
        self.salon_cache = {}
        self.salon_sira_cache = {}
        self.salon_value_map = {}
        self.sira_value_map = {}
        self.window.title(f"{KelebekTheme.ICON_PIN} Sabit Öğrenci İşaretleme")
        self.window.geometry("1100x700")
        setup_responsive_window(self.window)
        self.setup_ui()
        self.refresh_salon_cache()
        self.load_ogrenciler()
    
    def setup_ui(self):
        header = tk.Frame(self.window, bg=KelebekTheme.INFO, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=f"{KelebekTheme.ICON_PIN} SABİT ÖĞRENCİ İŞARETLEME",
                font=(KelebekTheme.FONT_FAMILY, 18, "bold"),
                fg=KelebekTheme.TEXT_WHITE, bg=KelebekTheme.INFO).pack(pady=15)
        
        info = tk.Label(self.window, text="Sabit işaretlenen öğrenciler harmanlama algoritmasına dahil edilmez.",
                       font=(KelebekTheme.FONT_FAMILY, 10), bg=KelebekTheme.BG_LIGHT)
        info.pack(pady=10)
        
        # Ana konteyner (Split V.)
        main_content = tk.Frame(self.window, bg=KelebekTheme.BG_LIGHT)
        main_content.pack(fill="both", expand=True, padx=15, pady=15)

        # --- SOL PANEL ---
        left_panel = tk.Frame(main_content, bg=KelebekTheme.BG_LIGHT, width=320)
        left_panel.pack(side="left", fill="y", padx=(0, 15))
        left_panel.pack_propagate(False)

        self.create_assignment_card(left_panel)
        
        btn_frame = tk.Frame(left_panel, bg=KelebekTheme.BG_LIGHT)
        btn_frame.pack(fill="x", pady=10)
        
        btn1 = tk.Button(btn_frame, command=lambda: self.toggle_sabit(True))
        configure_standard_button(btn1, "success", "✓ Sabit Yap")
        btn1.pack(side="top", fill="x", pady=2)
        
        btn2 = tk.Button(btn_frame, command=lambda: self.toggle_sabit(False))
        configure_standard_button(btn2, "warning", "✗ Sabit Kaldır")
        btn2.pack(side="top", fill="x", pady=2)

        # --- SAĞ PANEL ---
        right_panel = tk.Frame(main_content, bg=KelebekTheme.BG_LIGHT)
        right_panel.pack(side="right", fill="both", expand=True)

        list_card = create_card_frame(right_panel, "Öğrenci Listesi", KelebekTheme.ICON_STUDENT)
        list_card.pack(fill="both", expand=True)

        tree_frame = tk.Frame(list_card.content, bg=KelebekTheme.BG_WHITE)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        cols = ("ID", "Ad", "Soyad", "Sınıf", "Şube", "Salon", "Sabit Sıra", "Durum")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        for col in cols:
            self.tree.heading(col, text=col)
        self.tree.column("ID", width=40)
        self.tree.column("Ad", width=100)
        self.tree.column("Soyad", width=100)
        self.tree.column("Sınıf", width=50)
        self.tree.column("Şube", width=40)
        self.tree.column("Salon", width=110)
        self.tree.column("Sabit Sıra", width=100)
        self.tree.column("Durum", width=80)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_student_select)

    def create_assignment_card(self, parent):
        card = create_card_frame(parent, "Sabit Salon & Sıra", KelebekTheme.ICON_ROOM)
        card.pack(fill="x", padx=0, pady=(0, 20))
        content = card.content
        content.columnconfigure(1, weight=1)
        tk.Label(content, text="Salon Seçimi:", font=(KelebekTheme.FONT_FAMILY, 11, "bold"),
                 bg=KelebekTheme.BG_WHITE, fg=KelebekTheme.TEXT_DARK).grid(row=0, column=0, sticky="w")
        self.salon_var = tk.StringVar()
        self.salon_combo = ttk.Combobox(content, textvariable=self.salon_var, state="readonly")
        self.salon_combo.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=5)
        self.salon_combo.bind("<<ComboboxSelected>>", self.on_salon_changed)
        tk.Label(content, text="Sıra Seçimi:", font=(KelebekTheme.FONT_FAMILY, 11, "bold"),
                 bg=KelebekTheme.BG_WHITE, fg=KelebekTheme.TEXT_DARK).grid(row=1, column=0, sticky="w")
        self.sira_var = tk.StringVar()
        self.sira_combo = ttk.Combobox(content, textvariable=self.sira_var, state="readonly")
        self.sira_combo.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=5)
        self.assignment_info = tk.Label(content, text="Bir öğrenci seçerek başlayın.",
                                        font=(KelebekTheme.FONT_FAMILY, 10),
                                        bg=KelebekTheme.BG_WHITE,
                                        fg=KelebekTheme.TEXT_LIGHT)
        self.assignment_info.grid(row=2, column=0, columnspan=2, sticky="w", pady=(5, 10))
        btn_save = tk.Button(content, command=self.save_sabit_konum)
        configure_standard_button(btn_save, "primary", f"{KelebekTheme.ICON_SAVE} Konumu Kaydet")
        btn_save.grid(row=3, column=0, columnspan=2, sticky="e", pady=5)

    def refresh_salon_cache(self):
        try:
            salonlar = self.db.salonlari_listele()
            self.salon_cache = {s['id']: s for s in salonlar}
            salon_ids = list(self.salon_cache.keys())
            if salon_ids:
                sira_map = self.db.salon_sira_haritasi(salon_ids)
            else:
                sira_map = {}
            self.salon_sira_cache = {}
            for siralar in sira_map.values():
                for sira in siralar:
                    self.salon_sira_cache[sira['id']] = sira
            self.salon_value_map = {}
            salon_values = []
            for salon in salonlar:
                display = self._format_salon_value(salon)
                self.salon_value_map[display] = salon['id']
                salon_values.append(display)
            if hasattr(self, 'salon_combo'):
                self.salon_combo['values'] = salon_values
        except Exception as e:
            show_message(self.window, f"Salon verileri alınamadı: {e}", "error")

    def _format_salon_value(self, salon) -> str:
        return f"{salon['salon_adi']} (Kap: {salon['kapasite']})"

    def _salon_label_for(self, ogr) -> str:
        salon_id = ogr.get('sabit_salon_id')
        if salon_id and salon_id in self.salon_cache:
            return self.salon_cache[salon_id]['salon_adi']
        return "-"

    def _sira_label_for(self, ogr) -> str:
        sira_id = ogr.get('sabit_salon_sira_id')
        seat = self.salon_sira_cache.get(sira_id)
        if not seat:
            return "-"
        label = f"{seat['sira_no']:03d}"
        if seat.get('etiket'):
            label += f" - {seat['etiket']}"
        return label

    def _restore_selection(self):
        for item in self.tree.get_children():
            if self.tree.item(item)['values'][0] == self.selected_ogrenci_id:
                self.tree.selection_set(item)
                self.tree.focus(item)
                self.on_student_select()
                break

    def clear_assignment_form(self):
        if hasattr(self, 'salon_var'):
            self.salon_var.set("")
        if hasattr(self, 'sira_var'):
            self.sira_var.set("")
        self.selected_salon_id = None
        self.sira_value_map = {}
        if hasattr(self, 'sira_combo'):
            self.sira_combo['values'] = []
        if hasattr(self, 'assignment_info'):
            self.assignment_info.config(text="Bir öğrenci seçerek başlayın.")

    def on_student_select(self, event=None):
        selection = self.tree.selection()
        if not selection:
            self.selected_ogrenci_id = None
            self.clear_assignment_form()
            return
        item = self.tree.item(selection[0])
        ogr_id = item['values'][0]
        self.selected_ogrenci_id = ogr_id
        ogr = self.ogrenci_detaylari.get(ogr_id)
        if not ogr:
            self.clear_assignment_form()
            return
        salon_id = ogr.get('sabit_salon_id')
        if salon_id:
            self._set_salon_combo_by_id(salon_id)
            self.load_sira_options(salon_id, current_owner_id=ogr_id)
            self._set_sira_combo_by_id(ogr.get('sabit_salon_sira_id'))
            self.assignment_info.config(text="Sabit konumu güncelleyebilirsiniz.")
        else:
            self.clear_assignment_form()
            self.assignment_info.config(text="Bu öğrenci için sabit konum seçilmedi.")

    def _set_salon_combo_by_id(self, salon_id):
        self.selected_salon_id = salon_id
        for label, sid in self.salon_value_map.items():
            if sid == salon_id:
                self.salon_var.set(label)
                return
        self.salon_var.set("")

    def _set_sira_combo_by_id(self, sira_id):
        if not sira_id:
            self.sira_var.set("")
            return
        for label, seat in self.sira_value_map.items():
            if seat['id'] == sira_id:
                self.sira_var.set(label)
                return
        self.sira_var.set("")

    def on_salon_changed(self, event=None):
        display = self.salon_var.get()
        salon_id = self.salon_value_map.get(display)
        self.selected_salon_id = salon_id
        self.load_sira_options(salon_id, current_owner_id=self.selected_ogrenci_id)

    def load_sira_options(self, salon_id, current_owner_id=None):
        if not salon_id:
            self.sira_combo['values'] = []
            self.sira_var.set("")
            return
        try:
            siralar = self.db.salon_sira_durumlari(salon_id)
        except Exception as e:
            show_message(self.window, f"Sıra bilgisi alınamadı: {e}", "error")
            return
        self.sira_value_map = {}
        values = []
        for sira in siralar:
            label = f"{sira['sira_no']:03d}"
            if sira.get('etiket'):
                label += f" - {sira['etiket']}"
            if sira.get('ogrenci_id') and sira['ogrenci_id'] != current_owner_id:
                label += " (DOLU)"
            else:
                label += " (Boş)"
            self.sira_value_map[label] = sira
            values.append(label)
        self.sira_combo['values'] = values
        if not values:
            self.assignment_info.config(text="Seçilen salon için aktif sıra bulunamadı.")

    def save_sabit_konum(self):
        if not self.selected_ogrenci_id:
            show_message(self.window, "Önce listeden bir öğrenci seçin!", "warning")
            return
        salon_display = self.salon_var.get()
        salon_id = self.selected_salon_id or self.salon_value_map.get(salon_display)
        if not salon_id:
            show_message(self.window, "Sabit salon seçmelisiniz!", "warning")
            return
        sira_display = self.sira_var.get()
        seat = self.sira_value_map.get(sira_display)
        if not seat:
            show_message(self.window, "Sabit sıra seçmelisiniz!", "warning")
            return
        try:
            mevcut = self.db.salon_sira_sahibi(seat['id'], exclude_ogrenci_id=self.selected_ogrenci_id)
            if mevcut:
                show_message(self.window,
                             f"Bu sıra {mevcut['ad']} {mevcut['soyad']} tarafından kullanılıyor!",
                             "error")
                return
            self.db.ogrenci_guncelle(
                self.selected_ogrenci_id,
                sabit_mi=True,
                sabit_salon_id=salon_id,
                sabit_salon_sira_id=seat['id']
            )
            show_message(self.window, "Sabit konum güncellendi!", "success")
            self.load_ogrenciler()
        except Exception as e:
            show_message(self.window, f"Sabit konum kaydedilemedi: {e}", "error")

    def load_ogrenciler(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.ogrenci_detaylari = {}
        self.refresh_salon_cache()
        try:
            ogrenciler = self.db.ogrencileri_listele()
            for ogr in ogrenciler:
                self.ogrenci_detaylari[ogr['id']] = ogr
                durum = "🔒 Sabit" if ogr['sabit_mi'] else "🔄 Mobil"
                salon_label = self._salon_label_for(ogr)
                sira_label = self._sira_label_for(ogr)
                self.tree.insert("", "end", values=(
                    ogr['id'], ogr['ad'], ogr['soyad'],
                    ogr['sinif'], ogr['sube'], salon_label,
                    sira_label, durum
                ))
        except Exception as e:
            show_message(self.window, f"Hata: {e}", "error")
        if self.selected_ogrenci_id and self.selected_ogrenci_id in self.ogrenci_detaylari:
            self._restore_selection()
        else:
            self.selected_ogrenci_id = None
            self.clear_assignment_form()
    
    def toggle_sabit(self, sabit_mi):
        sel = self.tree.selection()
        if not sel:
            show_message(self.window, "Öğrenci seçin!", "warning")
            return
        item = self.tree.item(sel[0])
        ogr_id = item['values'][0]
        ogr = self.ogrenci_detaylari.get(ogr_id)
        updates = {}
        if sabit_mi:
            if not ogr or not ogr.get('sabit_salon_sira_id'):
                show_message(self.window,
                             "Önce sabit salon ve sırayı seçip kaydedin!",
                             "warning")
                return
            updates['sabit_mi'] = True
        else:
            updates = {
                'sabit_mi': False,
                'sabit_salon_id': None,
                'sabit_salon_sira_id': None
            }
        try:
            self.db.ogrenci_guncelle(ogr_id, **updates)
            durum = "sabit" if sabit_mi else "mobil"
            show_message(self.window, f"✓ Öğrenci {durum} yapıldı!", "success")
            if not sabit_mi and self.selected_ogrenci_id == ogr_id:
                self.clear_assignment_form()
            self.load_ogrenciler()
        except Exception as e:
            show_message(self.window, f"Hata: {e}", "error")
