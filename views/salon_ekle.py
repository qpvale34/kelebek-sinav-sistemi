# views/salon_ekle.py
"""Salon Ekleme Ekranı"""
import tkinter as tk
from tkinter import ttk, simpledialog
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from assets.styles import *
from assets.layout import setup_responsive_window
from controllers.database_manager import get_db

class SalonEkleView:
    def __init__(self, window, parent):
        self.window = window
        self.parent = parent
        self.db = get_db()
        self.selected_salon_id = None
        self.selected_salon_name = ""
        self.selected_seat_id = None
        self.seat_records = {}
        setup_responsive_window(self.window)
        self.setup_ui()
        self.load_salonlar()
    
    def setup_ui(self):
        self.window.title(f"{KelebekTheme.ICON_ROOM} Salon Yönetimi")
        self.window.geometry("1100x750")
        self.window.config(bg=KelebekTheme.BG_LIGHT)
        
        # Header
        header = tk.Frame(self.window, bg=KelebekTheme.PRIMARY, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=f"{KelebekTheme.ICON_ROOM} SALON YÖNETİMİ",
                font=(KelebekTheme.FONT_FAMILY, 20, "bold"),
                fg=KelebekTheme.TEXT_WHITE, bg=KelebekTheme.PRIMARY).pack(pady=15)
        
        # Ana Container - ScrollableFrame yerine direkt Frame kullanıyoruz ki liste uzayabilsin
        main_layout = tk.Frame(self.window, bg=KelebekTheme.BG_LIGHT)
        main_layout.pack(fill="both", expand=True, padx=15, pady=15)
        
        # --- SOL PANEL (FORM) ---
        left_sidebar = tk.Frame(main_layout, bg=KelebekTheme.BG_LIGHT, width=320)
        left_sidebar.pack(side="left", fill="y", padx=(0, 15))
        left_sidebar.pack_propagate(False) # Sabit genişlik
        
        left_card = create_card_frame(left_sidebar, "Yeni Salon Ekle", KelebekTheme.ICON_EDIT)
        left_card.pack(fill="x", anchor="n") # Sadece yukarıda dursun, tüm boyu kaplamasına gerek yok
        self.create_form(left_card.content)
        
        # --- SAĞ PANEL (LİSTE + DETAY) ---
        right_content = tk.Frame(main_layout, bg=KelebekTheme.BG_LIGHT)
        right_content.pack(side="right", fill="both", expand=True)
        
        # Üst Kısım: Salon Listesi (%50)
        list_container = tk.Frame(right_content, bg=KelebekTheme.BG_LIGHT)
        list_container.pack(side="top", fill="both", expand=True, pady=(0, 15))
        
        right_card = create_card_frame(list_container, "Salon Listesi", KelebekTheme.ICON_ROOM)
        right_card.pack(fill="both", expand=True)
        self.create_list(right_card.content)
        
        # Alt Kısım: Sıra Yönetimi (%50)
        details_container = tk.Frame(right_content, bg=KelebekTheme.BG_LIGHT)
        details_container.pack(side="bottom", fill="both", expand=True)
        self.create_seat_manager_container(details_container)
    
    def create_form(self, parent):
        form_frame = tk.Frame(parent, bg=KelebekTheme.BG_WHITE)
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        tk.Label(form_frame, text="Salon Adı:", font=(KelebekTheme.FONT_FAMILY, 11, "bold"),
                fg=KelebekTheme.TEXT_DARK, bg=KelebekTheme.BG_WHITE).pack(anchor="w", pady=(10,5))
        self.salon_adi_entry = tk.Entry(form_frame, font=(KelebekTheme.FONT_FAMILY, 11), width=25)
        self.salon_adi_entry.pack(fill="x", pady=(0,20))
        
        tk.Label(form_frame, text="Kapasite:", font=(KelebekTheme.FONT_FAMILY, 11, "bold"),
                fg=KelebekTheme.TEXT_DARK, bg=KelebekTheme.BG_WHITE).pack(anchor="w", pady=(10,5))
        self.kapasite_entry = tk.Entry(form_frame, font=(KelebekTheme.FONT_FAMILY, 11), width=25)
        self.kapasite_entry.pack(fill="x", pady=(0,20))
        
        btn_ekle = tk.Button(form_frame, command=self.add_salon)
        configure_standard_button(btn_ekle, "success", f"{KelebekTheme.ICON_CHECK} Salon Ekle")
        btn_ekle.pack(pady=20)
    
    def create_list(self, parent):
        columns = ("ID", "Salon Adı", "Kapasite")
        self.tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)
        for col in columns:
            self.tree.heading(col, text=col)
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Salon Adı", width=200)
        self.tree.column("Kapasite", width=100, anchor="center")
        
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_salon_select)
        
        btn_frame = tk.Frame(parent, bg=KelebekTheme.BG_WHITE)
        btn_frame.pack(fill="x", pady=10)
        btn_delete = tk.Button(btn_frame, command=self.delete_selected)
        configure_standard_button(btn_delete, "danger", f"{KelebekTheme.ICON_DELETE} Sil")
        btn_delete.pack(side="right", padx=5)
        btn_update = tk.Button(btn_frame, command=self.update_capacity)
        configure_standard_button(btn_update, "primary", f"{KelebekTheme.ICON_SAVE} Kapasite Güncelle")
        btn_update.pack(side="right", padx=5)

    def create_seat_manager_container(self, parent):
        card = create_card_frame(parent, "Salon Sıraları", KelebekTheme.ICON_PIN)
        card.pack(fill="both", expand=True) # Container zaten padding veriyor
        content = card.content
        content.columnconfigure(0, weight=1)
        self.selected_salon_label = tk.Label(
            content,
            text="Salon seçilmedi",
            font=(KelebekTheme.FONT_FAMILY, 12, "bold"),
            bg=KelebekTheme.BG_WHITE,
            fg=KelebekTheme.TEXT_DARK
        )
        self.selected_salon_label.pack(anchor="w", pady=(0, 5))
        columns = ("Sıra No", "Etiket", "Durum", "Atanan")
        self.seat_tree = ttk.Treeview(content, columns=columns, show="headings", height=8)
        for col in columns:
            self.seat_tree.heading(col, text=col)
        self.seat_tree.column("Sıra No", width=80, anchor="center")
        self.seat_tree.column("Etiket", width=160)
        self.seat_tree.column("Durum", width=120, anchor="center")
        self.seat_tree.column("Atanan", width=200)
        self.seat_tree.pack(fill="both", expand=True)
        self.seat_tree.bind("<<TreeviewSelect>>", self.on_seat_select)
        self.seat_info_label = tk.Label(
            content,
            text="Bir salon seçerek sıra listesine ulaşın.",
            font=(KelebekTheme.FONT_FAMILY, 10),
            bg=KelebekTheme.BG_WHITE,
            fg=KelebekTheme.TEXT_LIGHT
        )
        self.seat_info_label.pack(anchor="w", pady=5)
        form = tk.Frame(content, bg=KelebekTheme.BG_WHITE)
        form.pack(fill="x", pady=5)
        tk.Label(form, text="Sıra Etiketi:", font=(KelebekTheme.FONT_FAMILY, 11, "bold"),
                 bg=KelebekTheme.BG_WHITE, fg=KelebekTheme.TEXT_DARK).grid(row=0, column=0, sticky="w")
        self.seat_label_entry = tk.Entry(form, font=(KelebekTheme.FONT_FAMILY, 11), width=30)
        self.seat_label_entry.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        form.columnconfigure(1, weight=1)
        btn_update = tk.Button(form, command=self.update_seat_label)
        configure_standard_button(btn_update, "primary", f"{KelebekTheme.ICON_SAVE} Etiketi Kaydet")
        btn_update.grid(row=0, column=2, padx=10)
    
    def load_salonlar(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        selected = self.selected_salon_id
        select_item = None
        try:
            salonlar = self.db.salonlari_listele()
            for salon in salonlar:
                item_id = self.tree.insert("", "end",
                                          values=(salon['id'], salon['salon_adi'], salon['kapasite']))
                if selected and salon['id'] == selected:
                    select_item = item_id
        except Exception as e:
            show_message(self.window, f"Yükleme hatası: {e}", "error")
        if select_item:
            self.tree.selection_set(select_item)
            self.tree.focus(select_item)
            self.load_salon_siralar(selected)
        else:
            self.selected_salon_id = None
            self.selected_salon_name = ""
            self.load_salon_siralar(None)
    
    def add_salon(self):
        salon_adi = self.salon_adi_entry.get().strip()
        kapasite_str = self.kapasite_entry.get().strip()
        
        if not salon_adi or not kapasite_str:
            show_message(self.window, "Tüm alanları doldurun!", "warning")
            return
        
        try:
            kapasite = int(kapasite_str)
            if kapasite <= 0:
                raise ValueError("Kapasite pozitif olmalı")
            
            self.db.salon_ekle(salon_adi, kapasite)
            show_message(self.window, f"✓ {salon_adi} eklendi!", "success")
            self.salon_adi_entry.delete(0, tk.END)
            self.kapasite_entry.delete(0, tk.END)
            self.load_salonlar()
            if hasattr(self.parent, 'refresh_stats'):
                self.parent.refresh_stats()
        except Exception as e:
            show_message(self.window, f"Hata: {e}", "error")

    def on_salon_select(self, event=None):
        selection = self.tree.selection()
        if not selection:
            self.selected_salon_id = None
            self.selected_salon_name = ""
            self.load_salon_siralar(None)
            return
        item = self.tree.item(selection[0])
        self.selected_salon_id = item['values'][0]
        self.selected_salon_name = item['values'][1]
        self.load_salon_siralar(self.selected_salon_id)

    def load_salon_siralar(self, salon_id):
        if hasattr(self, 'seat_tree'):
            for item in self.seat_tree.get_children():
                self.seat_tree.delete(item)
        self.seat_records = {}
        if not salon_id:
            if hasattr(self, 'selected_salon_label'):
                self.selected_salon_label.config(text="Salon seçilmedi")
            if hasattr(self, 'seat_info_label'):
                self.seat_info_label.config(text="Bir salon seçerek sıra listesine ulaşın.")
            return
        if hasattr(self, 'selected_salon_label'):
            self.selected_salon_label.config(text=f"Seçilen Salon: {self.selected_salon_name}")
        try:
            siralar = self.db.salon_sira_durumlari(salon_id)
        except Exception as e:
            show_message(self.window, f"Sıralar yüklenemedi: {e}", "error")
            return
        for sira in siralar:
            if not sira.get('aktif_mi'):
                durum = "Pasif"
            elif sira.get('ogrenci_id'):
                durum = "Dolu"
            else:
                durum = "Boş"
            atanan = "-"
            if sira.get('ogrenci_id'):
                ad = sira.get('ogrenci_ad') or ""
                soyad = sira.get('ogrenci_soyad') or ""
                atanan = f"{ad} {soyad}".strip()
            etiket = sira.get('etiket') or "-"
            item_id = self.seat_tree.insert(
                "", "end",
                values=(sira['sira_no'], etiket, durum, atanan)
            )
            self.seat_records[item_id] = sira
        if hasattr(self, 'seat_info_label'):
            self.seat_info_label.config(text=f"Toplam {len(siralar)} sıra listelendi.")
        self.selected_seat_id = None
        if hasattr(self, 'seat_label_entry'):
            self.seat_label_entry.delete(0, tk.END)

    def on_seat_select(self, event=None):
        selection = self.seat_tree.selection()
        if not selection:
            self.selected_seat_id = None
            self.seat_label_entry.delete(0, tk.END)
            return
        item = selection[0]
        seat = self.seat_records.get(item)
        if not seat:
            return
        self.selected_seat_id = seat['id']
        self.seat_label_entry.delete(0, tk.END)
        if seat.get('etiket'):
            self.seat_label_entry.insert(0, seat['etiket'])
        self.seat_info_label.config(text=f"{seat['sira_no']}. sıra seçildi")

    def update_seat_label(self):
        if not self.selected_seat_id:
            show_message(self.window, "Etiket güncellemek için sıra seçin!", "warning")
            return
        yeni_etiket = self.seat_label_entry.get().strip()
        try:
            self.db.salon_sira_guncelle(
                self.selected_seat_id,
                etiket=yeni_etiket if yeni_etiket else None
            )
            show_message(self.window, "Sıra etiketi güncellendi!", "success")
            self.load_salon_siralar(self.selected_salon_id)
        except Exception as e:
            show_message(self.window, f"Etiket kaydedilemedi: {e}", "error")

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            show_message(self.window, "Lütfen salon seçin!", "warning")
            return
        item = self.tree.item(selected[0])
        salon_id = item['values'][0]
        salon_adi = item['values'][1]
        if not ask_confirmation(self.window, f"{salon_adi} silinecek. Emin misiniz?"):
            return
        try:
            self.db.salon_guncelle(salon_id, aktif_mi=False)
            show_message(self.window, "✓ Salon silindi!", "success")
            self.load_salonlar()
            if hasattr(self.parent, 'refresh_stats'):
                self.parent.refresh_stats()
        except Exception as e:
            show_message(self.window, f"Hata: {e}", "error")

    def update_capacity(self):
        """Seçili salonun kapasitesini güncelle"""
        selected = self.tree.selection()
        if not selected:
            show_message(self.window, "Lütfen kapasitesi güncellenecek salonu seçin!", "warning")
            return
        item = self.tree.item(selected[0])
        salon_id = item['values'][0]
        salon_adi = item['values'][1]
        current_capacity = int(item['values'][2])
        
        yeni_kapasite = simpledialog.askinteger(
            "Kapasite Güncelle",
            f"{salon_adi} için yeni kapasiteyi girin:",
            parent=self.window,
            initialvalue=current_capacity,
            minvalue=1
        )
        if yeni_kapasite is None:
            return
        if yeni_kapasite == current_capacity:
            show_message(self.window, "Kapasite aynı kaldı.", "info")
            return
        try:
            self.db.salon_guncelle(salon_id, kapasite=yeni_kapasite)
            show_message(self.window, f"{salon_adi} kapasitesi {yeni_kapasite} olarak güncellendi!", "success")
            self.selected_salon_id = salon_id
            self.load_salonlar()
            if hasattr(self.parent, 'refresh_stats'):
                self.parent.refresh_stats()
        except Exception as e:
            show_message(self.window, f"Kapasite güncellenemedi: {e}", "error")
