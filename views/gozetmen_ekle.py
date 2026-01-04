# Dosya: views/gozetmen_ekle.py
"""Gözetmen Ekleme - Excel ve Manuel"""
import tkinter as tk
from tkinter import ttk, filedialog
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from assets.styles import *
from assets.layout import setup_responsive_window
from controllers.database_manager import get_db
from controllers.excel_handler import ExcelHandler

class GozetmenEkleView:
    def __init__(self, window, parent):
        self.window = window
        self.parent = parent
        self.db = get_db()
        self.excel_handler = ExcelHandler()
        self.window.title(f"{KelebekTheme.ICON_TEACHER} Gözetmen Yönetimi")
        self.window.geometry("1100x700")
        self.window.config(bg=KelebekTheme.BG_LIGHT)
        setup_responsive_window(self.window)
        self.setup_ui()
        self.load_gozetmenler()
    
    def setup_ui(self):
        header = tk.Frame(self.window, bg=KelebekTheme.WARNING, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=f"{KelebekTheme.ICON_TEACHER} GÖZETMEN YÖNETİMİ",
                font=(KelebekTheme.FONT_FAMILY, 20, "bold"),
                fg=KelebekTheme.TEXT_WHITE, bg=KelebekTheme.WARNING).pack(pady=15)
        
        # Ana içerik container (Split View)
        main_content = tk.Frame(self.window, bg=KelebekTheme.BG_LIGHT)
        main_content.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Sol Panel: Form (Sabit genişlik)
        left_panel = tk.Frame(main_content, bg=KelebekTheme.BG_LIGHT, width=350)
        left_panel.pack(side="left", fill="y", padx=(0, 15))
        left_panel.pack_propagate(False)
        
        left_card = create_card_frame(left_panel, "Gözetmen Ekle", KelebekTheme.ICON_EDIT)
        left_card.pack(fill="both", expand=True)
        self.create_form(left_card.content)
        
        # Sağ Panel: Liste (Esnek)
        right_panel = tk.Frame(main_content, bg=KelebekTheme.BG_LIGHT)
        right_panel.pack(side="right", fill="both", expand=True)
        
        right_card = create_card_frame(right_panel, "Gözetmen Listesi", KelebekTheme.ICON_TEACHER)
        right_card.pack(fill="both", expand=True)
        self.create_list(right_card.content)
    
    def create_form(self, parent):
        form = tk.Frame(parent, bg=KelebekTheme.BG_WHITE)
        form.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Excel butonları
        btn_frame = tk.Frame(form, bg=KelebekTheme.BG_WHITE)
        btn_frame.pack(pady=10)
        btn1 = tk.Button(btn_frame, command=self.create_template)
        configure_standard_button(btn1, "secondary", "📄 Şablon İndir")
        btn1.pack(side="left", padx=5)
        btn2 = tk.Button(btn_frame, command=self.import_excel)
        configure_standard_button(btn2, "success", "📊 Excel'den Aktar")
        btn2.pack(side="left", padx=5)
        
        tk.Label(form, text="─" * 40, bg=KelebekTheme.BG_WHITE).pack(pady=10)
        
        # Manuel form
        fields = [("Ad:", "ad"), ("Soyad:", "soyad"), ("E-posta:", "email"), ("Telefon:", "telefon")]
        self.entries = {}
        for label, name in fields:
            tk.Label(form, text=label, font=(KelebekTheme.FONT_FAMILY, 10, "bold"),
                    bg=KelebekTheme.BG_WHITE).pack(anchor="w", pady=2)
            entry = tk.Entry(form, font=(KelebekTheme.FONT_FAMILY, 10), width=30)
            entry.pack(fill="x", pady=5)
            self.entries[name] = entry
        
        btn = tk.Button(form, command=self.add_gozetmen)
        configure_standard_button(btn, "success", f"{KelebekTheme.ICON_CHECK} Gözetmen Ekle")
        btn.pack(pady=15)
    
    def create_list(self, parent):
        cols = ("ID", "Ad", "Soyad", "E-posta", "Telefon")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", height=15)
        for col in cols:
            self.tree.heading(col, text=col)
        self.tree.column("ID", width=40)
        self.tree.column("Ad", width=120)
        self.tree.column("Soyad", width=120)
        self.tree.column("E-posta", width=180)
        self.tree.column("Telefon", width=120)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        btn_frame = tk.Frame(parent, bg=KelebekTheme.BG_WHITE)
        btn_frame.pack(fill="x", pady=5)
        btn = tk.Button(btn_frame, command=self.delete_selected)
        configure_standard_button(btn, "danger", f"{KelebekTheme.ICON_DELETE} Sil")
        btn.pack()
    
    def load_gozetmenler(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            gozetmenler = self.db.gozetmenleri_listele()
            for g in gozetmenler:
                self.tree.insert("", "end", values=(
                    g['id'],
                    g['ad'],
                    g['soyad'],
                    g.get('email', ''),
                    g.get('telefon', '')
                ))
        except Exception as e:
            show_message(self.window, f"Hata: {e}", "error")
    
    def add_gozetmen(self):
        ad = self.entries['ad'].get().strip()
        soyad = self.entries['soyad'].get().strip()
        if not ad or not soyad:
            show_message(self.window, "Ad ve soyad gerekli!", "warning")
            return
        try:
            self.db.gozetmen_ekle(ad, soyad, self.entries['email'].get().strip(), 
                                 self.entries['telefon'].get().strip())
            show_message(self.window, f"✓ {ad} {soyad} eklendi!", "success")
            for e in self.entries.values():
                e.delete(0, tk.END)
            self.load_gozetmenler()
            if hasattr(self.parent, 'refresh_stats'):
                self.parent.refresh_stats()
        except Exception as e:
            show_message(self.window, f"Hata: {e}", "error")
    
    def create_template(self):
        path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                           filetypes=[("Excel", "*.xlsx")],
                                           initialfile="gozetmen_sablonu.xlsx")
        if path and self.excel_handler.gozetmen_sablonu_olustur(path):
            show_message(self.window, f"✓ Şablon: {path}", "success")
    
    def import_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx *.xls")])
        if not path:
            return
        try:
            gozetmenler, hatalar = self.excel_handler.gozetmen_oku(path)
            if gozetmenler:
                eklenen = self.db.gozetmen_toplu_ekle(gozetmenler)
                show_message(self.window, f"✓ {eklenen} gözetmen eklendi!", "success")
                self.load_gozetmenler()
                if hasattr(self.parent, 'refresh_stats'):
                    self.parent.refresh_stats()
        except Exception as e:
            show_message(self.window, f"Hata: {e}", "error")
    
    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        item = self.tree.item(sel[0])
        goz_id = item['values'][0]
        if ask_confirmation(self.window, "Gözetmen silinecek?"):
            self.db.gozetmen_guncelle(goz_id, aktif_mi=False)
            self.load_gozetmenler()


