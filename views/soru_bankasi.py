"""
Kelebek Sınav Sistemi - Soru Bankası Yönetimi
Ders bazlı sınav dosyalarının yönetildiği ekran
"""

import os
import sys
import shutil
import mimetypes
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog

from assets.styles import (
    KelebekTheme,
    configure_standard_button,
    show_message,
    create_card_frame,
    ScrollableFrame,
    ask_confirmation
)
from assets.layout import setup_responsive_window
from controllers.database_manager import get_db


class SoruBankasiView:
    """Soru bankası yönetim ekranı"""
    
    def __init__(self, window, parent):
        self.window = window
        self.parent = parent
        self.db = get_db()
        self.storage_dir = Path("database") / "soru_bankasi"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.selected_file_path: Path | None = None
        self.ders_lookup = {}
        self.soru_lookup = {}
        
        self.setup_ui()
        self.load_dersler()
        self.refresh_list()
    
    def setup_ui(self):
        self.window.title(f"{KelebekTheme.ICON_BOOK} Soru Bankası")
        self.window.geometry("1100x720")
        self.window.config(bg=KelebekTheme.BG_LIGHT)
        setup_responsive_window(self.window)
        
        header = tk.Frame(self.window, bg=KelebekTheme.PRIMARY, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text=f"{KelebekTheme.ICON_BOOK} SORU BANKASI",
            font=(KelebekTheme.FONT_FAMILY, 22, "bold"),
            fg=KelebekTheme.TEXT_WHITE,
            bg=KelebekTheme.PRIMARY
        ).pack(pady=18)
        
        # Ana konteyner (Split V.)
        main_frame = tk.Frame(self.window, bg=KelebekTheme.BG_LIGHT)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # --- SOL PANEL ---
        left_panel = tk.Frame(main_frame, bg=KelebekTheme.BG_LIGHT, width=380)
        left_panel.pack(side="left", fill="y", padx=(0, 15))
        left_panel.pack_propagate(False)
        
        self.create_form_section(left_panel)
        
        # --- SAĞ PANEL ---
        right_panel = tk.Frame(main_frame, bg=KelebekTheme.BG_LIGHT)
        right_panel.pack(side="right", fill="both", expand=True)
        
        self.create_list_section(right_panel)
    
    def create_form_section(self, parent):
        # Parent zaten sol panel, doğrudan doldurabiliriz
        form_frame = tk.Frame(parent, bg=KelebekTheme.BG_LIGHT)
        form_frame.pack(fill="both", expand=True)
        
        card = create_card_frame(form_frame, "Yeni Soru Dosyası", KelebekTheme.ICON_SAVE)
        card.pack(fill="both", expand=True)
        
        inner = tk.Frame(card.content, bg=KelebekTheme.BG_WHITE)
        inner.pack(fill="both", expand=True)
        
        row = 0
        tk.Label(
            inner,
            text="Ders Seç:",
            font=(KelebekTheme.FONT_FAMILY, 11, "bold"),
            bg=KelebekTheme.BG_WHITE
        ).grid(row=row, column=0, sticky="w", pady=8)
        
        self.ders_var = tk.StringVar()
        self.ders_combo = ttk.Combobox(inner, textvariable=self.ders_var, state="readonly", width=32)
        self.ders_combo.grid(row=row, column=1, sticky="ew", pady=8, padx=5)
        
        row += 1
        tk.Label(
            inner,
            text="Dosya Başlığı:",
            font=(KelebekTheme.FONT_FAMILY, 11, "bold"),
            bg=KelebekTheme.BG_WHITE
        ).grid(row=row, column=0, sticky="w", pady=8)
        
        self.dosya_adi_var = tk.StringVar()
        tk.Entry(
            inner,
            textvariable=self.dosya_adi_var,
            font=(KelebekTheme.FONT_FAMILY, 10),
            bg=KelebekTheme.BG_WHITE
        ).grid(row=row, column=1, sticky="ew", pady=8, padx=5)
        
        row += 1
        tk.Label(
            inner,
            text="Notlar:",
            font=(KelebekTheme.FONT_FAMILY, 11, "bold"),
            bg=KelebekTheme.BG_WHITE
        ).grid(row=row, column=0, sticky="nw", pady=8)
        
        self.aciklama_text = tk.Text(inner, height=4, font=(KelebekTheme.FONT_FAMILY, 10))
        self.aciklama_text.grid(row=row, column=1, sticky="ew", pady=8, padx=5)
        
        row += 1
        tk.Label(
            inner,
            text="Seçilen Dosya:",
            font=(KelebekTheme.FONT_FAMILY, 11, "bold"),
            bg=KelebekTheme.BG_WHITE
        ).grid(row=row, column=0, sticky="w", pady=8)
        
        self.file_label = tk.Label(
            inner,
            text="Henüz dosya seçilmedi",
            font=(KelebekTheme.FONT_FAMILY, 9),
            fg=KelebekTheme.TEXT_MUTED,
            bg=KelebekTheme.BG_WHITE,
            wraplength=220,
            justify="left"
        )
        self.file_label.grid(row=row, column=1, sticky="w", pady=8, padx=5)
        
        row += 1
        btn_select = tk.Button(inner, command=self.select_file)
        configure_standard_button(btn_select, "secondary", "📁 Dosya Seç")
        btn_select.grid(row=row, column=0, columnspan=2, pady=10, sticky="ew")
        
        row += 1
        btn_save = tk.Button(inner, command=self.add_question_file)
        configure_standard_button(btn_save, "success", f"{KelebekTheme.ICON_CHECK} Dosyayı Kaydet")
        btn_save.grid(row=row, column=0, columnspan=2, pady=5, sticky="ew")
        
        inner.columnconfigure(1, weight=1)
    
    def create_list_section(self, parent):
        # Parent sağ panel
        list_frame = tk.Frame(parent, bg=KelebekTheme.BG_LIGHT)
        list_frame.pack(fill="both", expand=True)
        
        filter_card = create_card_frame(list_frame, "Filtreler", KelebekTheme.ICON_SEARCH)
        filter_card.pack(fill="x", pady=(0, 8))
        
        filter_inner = tk.Frame(filter_card.content, bg=KelebekTheme.BG_WHITE)
        filter_inner.pack(fill="x")
        
        tk.Label(
            filter_inner,
            text="Ders:",
            font=(KelebekTheme.FONT_FAMILY, 10, "bold"),
            bg=KelebekTheme.BG_WHITE
        ).pack(side="left")
        
        self.filter_var = tk.StringVar(value="Tümü")
        self.filter_combo = ttk.Combobox(
            filter_inner,
            textvariable=self.filter_var,
            state="readonly",
            width=25
        )
        self.filter_combo.pack(side="left", padx=10)
        self.filter_combo.bind("<<ComboboxSelected>>", lambda _: self.refresh_list())
        
        btn_refresh = tk.Button(filter_inner, command=self.refresh_list)
        configure_standard_button(btn_refresh, "secondary", "🔄 Yenile")
        btn_refresh.pack(side="left", padx=5)
        
        list_card = create_card_frame(list_frame, "Soru Dosyaları", KelebekTheme.ICON_BOOK)
        list_card.pack(fill="both", expand=True)
        
        tree_container = tk.Frame(list_card.content, bg=KelebekTheme.BG_WHITE)
        tree_container.pack(fill="both", expand=True)
        
        columns = ("id", "ders", "dosya", "boyut", "tarih")
        self.tree = ttk.Treeview(tree_container, columns=columns, show="headings", height=15)
        headers = ["ID", "Ders", "Dosya", "Boyut", "Eklenme"]
        widths = [60, 180, 260, 80, 140]
        for col, header, width in zip(columns, headers, widths):
            self.tree.heading(col, text=header)
            self.tree.column(col, width=width, anchor="center")
        
        tree_scroll = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")
        
        btn_frame = tk.Frame(list_card.content, bg=KelebekTheme.BG_WHITE)
        btn_frame.pack(fill="x", pady=10)
        
        btn_open = tk.Button(btn_frame, command=self.open_selected)
        configure_standard_button(btn_open, "primary", "📂 Dosyayı Aç")
        btn_open.pack(side="left", padx=5)
        
        btn_delete = tk.Button(btn_frame, command=self.delete_selected)
        configure_standard_button(btn_delete, "danger", f"{KelebekTheme.ICON_DELETE} Sil")
        btn_delete.pack(side="left", padx=5)
    
    def load_dersler(self):
        try:
            dersler = self.db.dersleri_listele()
            ders_items = []
            for ders in dersler:
                ders_items.append(ders['ders_adi'])
                self.ders_lookup[ders['ders_adi']] = ders
            
            self.ders_combo['values'] = ders_items
            self.filter_combo['values'] = ["Tümü"] + ders_items
            
            if ders_items:
                self.ders_combo.current(0)
                self.filter_combo.current(0)
        except Exception as e:
            show_message(self.window, f"Ders yüklenemedi: {e}", "error")
    
    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="Sınav Dosyası Seç",
            filetypes=[("Desteklenen Dosyalar", "*.pdf *.docx *.doc *.ppt *.pptx *.zip"), ("Tüm Dosyalar", "*.*")]
        )
        if not file_path:
            # Dosya seçilmese bile pencereyi ön plana al
            self.window.lift()
            self.window.focus_force()
            return
        
        self.selected_file_path = Path(file_path)
        self.file_label.config(
            text=f"{self.selected_file_path.name}\n{self.selected_file_path.parent}"
        )
        if not self.dosya_adi_var.get():
            self.dosya_adi_var.set(self.selected_file_path.stem)
        
        # Pencereyi ön plana al
        self.window.lift()
        self.window.focus_force()
    
    def add_question_file(self):
        ders_key = self.ders_var.get()
        ders = self.ders_lookup.get(ders_key)
        if not ders:
            show_message(self.window, "Önce ders seçmelisiniz!", "warning")
            return
        
        if not self.selected_file_path:
            show_message(self.window, "Kaydedilecek dosyayı seçiniz!", "warning")
            return
        
        dosya_adi = self.dosya_adi_var.get().strip() or self.selected_file_path.stem
        aciklama = self.aciklama_text.get("1.0", "end").strip() or None
        
        hedef_klasor = self.storage_dir / f"ders_{ders['id']}"
        hedef_klasor.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hedef_dosya = hedef_klasor / f"{timestamp}_{self.selected_file_path.name}"
        
        try:
            shutil.copy2(self.selected_file_path, hedef_dosya)
            mime, _ = mimetypes.guess_type(str(hedef_dosya))
            self.db.soru_bankasi_ekle(
                ders['id'],
                dosya_adi,
                self.selected_file_path.name,
                str(hedef_dosya),
                mime,
                aciklama
            )
            show_message(self.window, "Dosya soru bankasına eklendi!", "success")
            self.selected_file_path = None
            self.file_label.config(text="Henüz dosya seçilmedi")
            self.dosya_adi_var.set("")
            self.aciklama_text.delete("1.0", "end")
            self.refresh_list()
        except Exception as e:
            show_message(self.window, f"Dosya kaydedilemedi: {e}", "error")
    
    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        filt = self.filter_var.get()
        ders = self.ders_lookup.get(filt)
        ders_id = ders['id'] if ders else None
        
        try:
            sorular = self.db.soru_bankasi_listele(ders_id=ders_id)
            self.soru_lookup = {}
            for row in sorular:
                boyut = self._format_size(row['dosya_yolu'])
                tarih = datetime.fromisoformat(row['olusturma_tarihi']).strftime("%d.%m.%Y %H:%M")
                self.tree.insert(
                    "",
                    "end",
                    values=(row['id'], row['ders_adi'], row['dosya_adi'], boyut, tarih)
                )
                self.soru_lookup[row['id']] = row
        except Exception as e:
            show_message(self.window, f"Soru dosyaları yüklenemedi: {e}", "error")
    
    def delete_selected(self):
        selection = self.tree.selection()
        if not selection:
            show_message(self.window, "Silinecek kaydı seçiniz!", "warning")
            return
        item = self.tree.item(selection[0])
        soru_id = item['values'][0]
        soru = self.soru_lookup.get(soru_id)
        if not soru:
            return
        
        if not ask_confirmation(
            self.window,
            f"\"{soru['dosya_adi']}\" dosyasını silmek istediğinize emin misiniz?"
        ):
            return
        
        try:
            dosya_path = Path(soru['dosya_yolu'])
            if dosya_path.exists():
                dosya_path.unlink()
            self.db.soru_bankasi_sil(soru_id)
            show_message(self.window, "Dosya kaldırıldı.", "success")
            self.refresh_list()
        except Exception as e:
            show_message(self.window, f"Silme hatası: {e}", "error")
    
    def open_selected(self):
        selection = self.tree.selection()
        if not selection:
            show_message(self.window, "Lütfen açılacak dosyayı seçin.", "warning")
            return
        item = self.tree.item(selection[0])
        soru_id = item['values'][0]
        soru = self.soru_lookup.get(soru_id)
        if not soru:
            return
        
        path = Path(soru['dosya_yolu'])
        if not path.exists():
            show_message(self.window, "Dosya bulunamadı. Kayıt silinmiş olabilir.", "error")
            return
        
        try:
            if os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                os.system(f"open '{path}'")
            else:
                os.system(f"xdg-open '{path}'")
        except Exception as e:
            show_message(self.window, f"Dosya açılamadı: {e}", "error")
    
    def _format_size(self, file_path: str) -> str:
        try:
            size = Path(file_path).stat().st_size
            for unit in ["B", "KB", "MB", "GB"]:
                if size < 1024:
                    return f"{size:.1f} {unit}"
                size /= 1024
            return f"{size:.1f} TB"
        except Exception:
            return "-"
