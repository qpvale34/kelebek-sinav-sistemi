"""
Kelebek Sınav Sistemi - Geliştirilmiş Harmanlama Ekranı
Sınav seçimi, sınıf/salon filtresi ve gözetmen atama özellikleriyle
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import sys
import os
import re
import threading
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from assets.styles import (KelebekTheme, configure_standard_button,
                           show_message, ask_confirmation, create_card_frame,
                           ScrollableFrame)
from assets.layout import setup_responsive_window
from controllers.database_manager import get_db
from controllers.harmanlama_engine import HarmanlamaEngine, HarmanlamaConfig, GozetmenAtamaEngine
from controllers.excel_handler import ExcelHandler
from utils import format_sira_label
from views.visual_seating import VisualSeatingPlanWindow


class LoadingDialog(tk.Toplevel):
    """Yükleme animasyonu gösteren dialog"""
    
    def __init__(self, parent, message="Lütfen bekleyin..."):
        super().__init__(parent)
        self.title("İşlem Devam Ediyor")
        self.configure(bg=KelebekTheme.BG_DARK)
        self.geometry("300x120")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Ortala
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 300) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 120) // 2
        self.geometry(f"+{x}+{y}")
        
        # Mesaj
        self.message_label = tk.Label(
            self,
            text=message,
            font=(KelebekTheme.FONT_FAMILY, 12, "bold"),
            fg="white",
            bg=KelebekTheme.BG_DARK
        )
        self.message_label.pack(pady=(20, 10))
        
        # Animasyon
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_idx = 0
        self.spinner_label = tk.Label(
            self,
            text=self.spinner_chars[0],
            font=(KelebekTheme.FONT_FAMILY, 24),
            fg=KelebekTheme.PRIMARY,
            bg=KelebekTheme.BG_DARK
        )
        self.spinner_label.pack()
        
        self.running = True
        self._animate()
        
        # ESC ile kapatmayı engelle
        self.protocol("WM_DELETE_WINDOW", lambda: None)
    
    def _animate(self):
        if self.running:
            self.spinner_idx = (self.spinner_idx + 1) % len(self.spinner_chars)
            self.spinner_label.config(text=self.spinner_chars[self.spinner_idx])
            self.after(100, self._animate)
    
    def stop(self):
        self.running = False
        self.destroy()


class GelismisHarmanlamaView:
    """Geliştirilmiş Harmanlama ve Yerleştirme ekranı"""
    
    def __init__(self, window, parent):
        self.window = window
        self.parent = parent
        self.db = get_db()
        self.engine = HarmanlamaEngine()
        self.gozetmen_engine = GozetmenAtamaEngine()
        self.excel_handler = ExcelHandler()
        setup_responsive_window(self.window)
        
        self.yerlesim_sonuc = None
        self.secili_sinav_ids = []
        self.secili_sinav_snapshot = {}
        self.havuz_toplam_ogrenci = 0
        self.secili_sinav_id = None  # legacy alanlar için tekil kimlik
        self.son_harman_secili_sinavlar = []
        self.result_window = None
        self.salon_gozetmen_map = {}
        self.gozetmen_atamalari = []
        self.last_summary = None
        self.log_messages = []
        self.log_window = None
        self.uyumsuzluk_window = None
        self.uyumsuzluk_tree = None
        self.gozetmen_salon_var = None
        self.gozetmen_var = None
        self.gozetmen_salon_combo = None
        self.gozetmen_combo = None
        self.gozetmen_tree = None
        self.gozetmen_tree_map = {}
        
        self.setup_ui()
        self.load_sinavlar()
    
    def setup_ui(self):
        """UI oluştur"""
        self.window.title(f"{KelebekTheme.ICON_SHUFFLE} Gelişmiş Harmanlama")
        self.window.geometry("1400x800")
        self.window.config(bg=KelebekTheme.BG_LIGHT)
        
        # Header
        header = tk.Frame(self.window, bg=KelebekTheme.DANGER, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text=f"{KelebekTheme.ICON_SHUFFLE} GELİŞMİŞ HARMANLAMA SİSTEMİ",
            font=(KelebekTheme.FONT_FAMILY, 22, "bold"),
            fg=KelebekTheme.TEXT_WHITE,
            bg=KelebekTheme.DANGER
        ).pack(pady=18)

        
        # Ana container (3 kolon)
        main_frame = tk.Frame(self.window, bg=KelebekTheme.BG_LIGHT)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # --- KOLON 1: SINAV SEÇİMİ (SOL) ---
        col_exams = tk.Frame(main_frame, bg=KelebekTheme.BG_LIGHT, width=380)
        col_exams.pack(side="left", fill="y", padx=(0, 15))
        col_exams.pack_propagate(False)
        
        self._create_exam_panel(col_exams)
        
        # --- KOLON 2: SALON SEÇİMİ (ORTA) ---
        col_salons = tk.Frame(main_frame, bg=KelebekTheme.BG_LIGHT)
        col_salons.pack(side="left", fill="both", expand=True, padx=(0, 15))
        
        salon_card = create_card_frame(col_salons, "Salon Seçimi", KelebekTheme.ICON_ROOM)
        salon_card.pack(fill="both", expand=True)
        self._build_salon_panel(salon_card.content)

        # --- KOLON 3: İŞLEMLER VE LOGLAR (SAĞ) ---
        col_actions = tk.Frame(main_frame, bg=KelebekTheme.BG_LIGHT, width=320)
        col_actions.pack(side="right", fill="y")
        col_actions.pack_propagate(False)
        
        # Üst: İşlemler
        action_card = create_card_frame(col_actions, "İşlemler", KelebekTheme.ICON_SHUFFLE)
        action_card.pack(side="top", fill="x", pady=(0, 15))
        self._build_action_panel(action_card.content)
        
        # Alt: Mini Log Paneli (Yeni)
        log_card = create_card_frame(col_actions, "Son İşlemler", KelebekTheme.ICON_INFO)
        log_card.pack(side="bottom", fill="both", expand=True)
        self._build_mini_log_panel(log_card.content)

   
    
    def _create_exam_panel(self, parent):
        """Sol panel - Sınav seçimi"""
        # Sınav seçimi kartı
        sinav_card = create_card_frame(parent, "Harmanlanacak Sınavlar", KelebekTheme.ICON_EXAM)
        sinav_card.pack(fill="both", expand=True)
        
        tk.Label(
            sinav_card.content,
            text="Harmanlanmasını istediğiniz sınavları işaretleyin:",
            font=(KelebekTheme.FONT_FAMILY, 10),
            fg=KelebekTheme.TEXT_DARK,
            bg=KelebekTheme.BG_WHITE
        ).pack(anchor="w", padx=5, pady=5)
        
        checkbox_container = tk.Frame(sinav_card.content, bg=KelebekTheme.BG_WHITE)
        checkbox_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        sinav_canvas = tk.Canvas(checkbox_container, bg=KelebekTheme.BG_WHITE, highlightthickness=0)
        sinav_scroll = ttk.Scrollbar(checkbox_container, orient="vertical", command=sinav_canvas.yview)
        self.sinav_checkbox_frame = tk.Frame(sinav_canvas, bg=KelebekTheme.BG_WHITE)
        sinav_canvas.create_window((0, 0), window=self.sinav_checkbox_frame, anchor="nw")
        sinav_canvas.configure(yscrollcommand=sinav_scroll.set)
        sinav_canvas.pack(side="left", fill="both", expand=True)
        sinav_scroll.pack(side="right", fill="y")
        self._enable_mousewheel_canvas(sinav_canvas)
        
        sinav_canvas.bind(
            "<Configure>",
            lambda e: sinav_canvas.configure(scrollregion=sinav_canvas.bbox("all"))
        )
        
        self.sinav_check_vars = {}
        self.sinav_detay_label = tk.Label(
            sinav_card.content,
            text="Seçili sınav yok",
            font=(KelebekTheme.FONT_FAMILY, 9),
            fg=KelebekTheme.TEXT_MUTED,
            bg=KelebekTheme.BG_WHITE,
            justify="left",
            wraplength=350
        )
        self.sinav_detay_label.pack(anchor="w", padx=5, pady=(0, 5))
        
        self.havuz_info_label = tk.Label(
            sinav_card.content,
            text="Pota henüz oluşturulmadı.",
            font=(KelebekTheme.FONT_FAMILY, 9, "italic"),
            fg=KelebekTheme.INFO,
            bg=KelebekTheme.BG_WHITE,
            justify="left",
            wraplength=350
        )
        self.havuz_info_label.pack(anchor="w", padx=5, pady=(0, 5))

    def _enable_mousewheel_canvas(self, canvas: tk.Canvas):
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _on_mousewheel_linux(event):
            direction = -1 if event.num == 4 else 1
            canvas.yview_scroll(direction, "units")

        def _bind(_event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", _on_mousewheel_linux)
            canvas.bind_all("<Button-5>", _on_mousewheel_linux)

        def _unbind(_event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        canvas.bind("<Enter>", _bind)
        canvas.bind("<Leave>", _unbind)

    def _style_action_button(self, button, variant: str, text: str):
        palette = {
            "danger": ("#c0392b", "#e74c3c"),
            "primary": ("#1f3c88", "#27478f"),
            "info": ("#1b6ca8", "#1f78bd"),
            "muted": ("#2c3e50", "#34495e"),
            "warning": ("#d35400", "#e67e22"),
        }
        bg, hover = palette.get(variant, palette["primary"])
        button.config(
            text=text,
            font=(KelebekTheme.FONT_FAMILY, 12, "bold"),
            fg=KelebekTheme.TEXT_WHITE,
            bg=bg,
            activebackground=hover,
            activeforeground=KelebekTheme.TEXT_WHITE,
            relief="flat",
            bd=0,
            cursor="hand2",
            pady=10
        )
    
    def _build_mini_log_panel(self, parent):
        """Sağ panel altına mini log eklentisi"""
        self.mini_log_text = scrolledtext.ScrolledText(
            parent,
            font=("Consolas", 9),
            bg="#f8f9fa",
            fg="#495057",
            wrap=tk.WORD,
            state="disabled",
            height=10
        )
        self.mini_log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Butonlar
        btn_frame = tk.Frame(parent, bg=KelebekTheme.BG_WHITE)
        btn_frame.pack(fill="x", padx=5, pady=(0, 5))
        
        tk.Button(btn_frame, text="📜 Detaylı Log", 
                 font=(KelebekTheme.FONT_FAMILY, 8),
                 command=self.show_log_window).pack(side="right")

    def _build_salon_panel(self, container):
        tk.Label(
            container,
            text="Hangi salonlar kullanılacak?",
            font=(KelebekTheme.FONT_FAMILY, 10, "bold"),
            fg=KelebekTheme.TEXT_DARK,
            bg=KelebekTheme.BG_WHITE
        ).pack(anchor="w", padx=5, pady=5)

        salon_scroll_frame = tk.Frame(container, bg=KelebekTheme.BG_WHITE)
        salon_scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

        salon_canvas = tk.Canvas(salon_scroll_frame, bg=KelebekTheme.BG_WHITE,
                                highlightthickness=0)
        salon_scrollbar = ttk.Scrollbar(salon_scroll_frame, orient="vertical",
                                       command=salon_canvas.yview)
        self.salon_checkbox_frame = tk.Frame(salon_canvas, bg=KelebekTheme.BG_WHITE)

        salon_canvas.create_window((0, 0), window=self.salon_checkbox_frame, anchor="nw")
        salon_canvas.configure(yscrollcommand=salon_scrollbar.set)

        salon_canvas.pack(side="left", fill="both", expand=True)
        salon_scrollbar.pack(side="right", fill="y")
        self._enable_mousewheel_canvas(salon_canvas)

        self.salon_checkboxes = {}
        self.salon_kapasite_label = tk.Label(
            container,
            text="Toplam kapasite: 0",
            font=(KelebekTheme.FONT_FAMILY, 9),
            fg=KelebekTheme.SUCCESS,
            bg=KelebekTheme.BG_WHITE
        )
        self.salon_kapasite_label.pack(anchor="w", padx=10, pady=5)

        salon_canvas.bind('<Configure>',
                         lambda e: salon_canvas.configure(
                             scrollregion=salon_canvas.bbox("all")
                         ))

        self.load_salonlar()

    def _build_action_panel(self, container):
        buttons = [
            ("danger", f"{KelebekTheme.ICON_SHUFFLE} Harmanlamayı Başlat", self.harmanla),
            ("primary", f"{KelebekTheme.ICON_ROOM} Yerleşimi Göster", self.show_result_window),
            ("info", "🎨 Görsel Önizleme", self.open_visual_preview),
            ("warning", f"{KelebekTheme.ICON_WARNING} Uyumsuzlukları Göster", self.show_uyumsuzluklar),
            ("muted", f"{KelebekTheme.ICON_INFO} İşlem Logları", self.show_log_window),
        ]
        for variant, text, action in buttons:
            btn = tk.Button(container, command=action)
            self._style_action_button(btn, variant, text)
            btn.pack(pady=6, fill="x", padx=20)

    def _build_gozetmen_panel(self, container):
        tk.Label(
            container,
            text="Seçili sınav için manuel gözetmen atayın.",
            font=(KelebekTheme.FONT_FAMILY, 10),
            fg=KelebekTheme.TEXT_DARK,
            bg=KelebekTheme.BG_WHITE,
            wraplength=360,
            justify="left"
        ).pack(anchor="w", padx=10, pady=(5, 10))

        form = tk.Frame(container, bg=KelebekTheme.BG_WHITE)
        form.pack(fill="x", padx=10)

        tk.Label(
            form,
            text="Salon:",
            font=(KelebekTheme.FONT_FAMILY, 10, "bold"),
            fg=KelebekTheme.TEXT_DARK,
            bg=KelebekTheme.BG_WHITE
        ).grid(row=0, column=0, sticky="w", pady=4)

        self.gozetmen_salon_var = tk.StringVar()
        self.gozetmen_salon_combo = ttk.Combobox(
            form,
            textvariable=self.gozetmen_salon_var,
            state="readonly",
            width=30
        )
        self.gozetmen_salon_combo.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=4)

        tk.Label(
            form,
            text="Gözetmen:",
            font=(KelebekTheme.FONT_FAMILY, 10, "bold"),
            fg=KelebekTheme.TEXT_DARK,
            bg=KelebekTheme.BG_WHITE
        ).grid(row=1, column=0, sticky="w", pady=4)

        self.gozetmen_var = tk.StringVar()
        self.gozetmen_combo = ttk.Combobox(
            form,
            textvariable=self.gozetmen_var,
            state="readonly",
            width=30
        )
        self.gozetmen_combo.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=4)

        form.columnconfigure(1, weight=1)

        btn_frame = tk.Frame(container, bg=KelebekTheme.BG_WHITE)
        btn_frame.pack(fill="x", padx=10, pady=(5, 0))

        add_btn = tk.Button(btn_frame, command=self.assign_gozetmen_manual)
        configure_standard_button(add_btn, "success", f"{KelebekTheme.ICON_CHECK} Gözetmen Ata")
        add_btn.pack(side="left", padx=5, pady=5)

        remove_btn = tk.Button(btn_frame, command=self.remove_gozetmen_assignment)
        configure_standard_button(remove_btn, "danger", f"{KelebekTheme.ICON_DELETE} Atamayı Sil")
        remove_btn.pack(side="left", padx=5, pady=5)

        assignment_card = tk.Frame(container, bg=KelebekTheme.BG_WHITE)
        assignment_card.pack(fill="both", expand=True, padx=10, pady=(10, 5))

        columns = ("Salon", "Gözetmen", "Görev")
        self.gozetmen_tree = ttk.Treeview(
            assignment_card,
            columns=columns,
            show="headings",
            height=6
        )
        for col in columns:
            width = 120 if col == "Gözetmen" else 100
            self.gozetmen_tree.heading(col, text=col)
            self.gozetmen_tree.column(col, width=width, anchor="center")
        self.gozetmen_tree.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(assignment_card, orient="vertical", command=self.gozetmen_tree.yview)
        self.gozetmen_tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")

        self.gozetmen_tree_map = {}
        self.gozetmen_salon_map = {}
        self.gozetmen_combo_map = {}
        self.refresh_gozetmen_inputs()
        self._render_gozetmen_assignments()

    def refresh_gozetmen_inputs(self):
        """Salon ve gözetmen combobox değerlerini güncelle."""
        if not hasattr(self, "gozetmen_salon_combo") or self.gozetmen_salon_combo is None:
            return
        salon_options = []
        self.gozetmen_salon_map = {}
        if hasattr(self, "salon_checkboxes"):
            for data in self.salon_checkboxes.values():
                salon = data['salon']
                display = salon['salon_adi']
                salon_options.append(display)
                self.gozetmen_salon_map[display] = salon['id']
        self.gozetmen_salon_combo['values'] = salon_options
        if salon_options and self.gozetmen_salon_var.get() not in salon_options:
            self.gozetmen_salon_var.set(salon_options[0])
        elif not salon_options:
            self.gozetmen_salon_var.set("")

        if not hasattr(self, "gozetmen_combo") or self.gozetmen_combo is None:
            return
        try:
            gozetmenler = self.db.gozetmenleri_listele()
        except AttributeError:
            gozetmenler = []
        except Exception:
            gozetmenler = []
        options = []
        self.gozetmen_combo_map = {}
        for goz in gozetmenler:
            label = f"{goz['ad']} {goz['soyad']}"
            options.append(label)
            self.gozetmen_combo_map[label] = goz['id']
        self.gozetmen_combo['values'] = options
        if options and self.gozetmen_var.get() not in options:
            self.gozetmen_var.set(options[0])
        elif not options:
            self.gozetmen_var.set("")

    def _render_gozetmen_assignments(self):
        if not hasattr(self, "gozetmen_tree") or self.gozetmen_tree is None:
            return
        for item in self.gozetmen_tree.get_children():
            self.gozetmen_tree.delete(item)
        self.gozetmen_tree_map = {}
        if not self.gozetmen_atamalari:
            placeholder = self.gozetmen_tree.insert("", "end", values=("-", "Henüz atama yok", "-"))
            self.gozetmen_tree_map[placeholder] = None
            return
        for atama in self.gozetmen_atamalari:
            gorev = "Asıl" if atama['gorev_turu'] == 'asil' else "Yedek"
            item = self.gozetmen_tree.insert(
                "",
                "end",
                values=(atama['salon_adi'], f"{atama['ad']} {atama['soyad']}", gorev)
            )
            self.gozetmen_tree_map[item] = atama['id']

    def assign_gozetmen_manual(self):
        if len(self.secili_sinav_ids) != 1 or not self.secili_sinav_id:
            show_message(self.window, "Gözetmen atamak için tek bir sınav seçmelisiniz.", "warning")
            return
        salon_label = self.gozetmen_salon_var.get()
        goz_label = self.gozetmen_var.get()
        if not salon_label or salon_label not in self.gozetmen_salon_map:
            show_message(self.window, "Lütfen salon seçin.", "warning")
            return
        if not goz_label or goz_label not in self.gozetmen_combo_map:
            show_message(self.window, "Lütfen gözetmen seçin.", "warning")
            return
        salon_id = self.gozetmen_salon_map[salon_label]
        gozetmen_id = self.gozetmen_combo_map[goz_label]
        try:
            self.db.gozetmen_ata(self.secili_sinav_id, gozetmen_id, salon_id, 'asil')
        except AttributeError:
            show_message(self.window, "Gözetmen atama fonksiyonu bulunamadı.", "error")
            return
        except Exception as exc:
            show_message(self.window, f"Gözetmen atanamadı:\n{exc}", "error")
            return
        self.update_gozetmen_map()
        show_message(self.window, f"👨‍🏫 {goz_label} → {salon_label} atandı.", "success")
        self.log(f"👨‍🏫 {goz_label} {salon_label} salonuna atandı")

    def remove_gozetmen_assignment(self):
        if not self.gozetmen_tree_map:
            show_message(self.window, "Silinecek atama bulunamadı.", "warning")
            return
        selection = self.gozetmen_tree.selection()
        if not selection:
            show_message(self.window, "Lütfen listeden bir atama seçin.", "info")
            return
        item = selection[0]
        atama_id = self.gozetmen_tree_map.get(item)
        if not atama_id:
            show_message(self.window, "Bu satır silinebilir bir atama içermiyor.", "info")
            return
        try:
            self.db.gozetmen_atama_sil(atama_id)
        except AttributeError:
            show_message(self.window, "Atama silme fonksiyonu bulunamadı.", "error")
            return
        except Exception as exc:
            show_message(self.window, f"Atama silinemedi:\n{exc}", "error")
            return
        self.update_gozetmen_map()
        show_message(self.window, "Gözetmen ataması silindi.", "success")
    
    def load_sinavlar(self):
        """Sınavları yükle"""
        try:
            sinavlar = self.db.sinavlari_listele()
            
            self.sinav_dict = {sinav['id']: sinav for sinav in sinavlar}
            self.secili_sinav_ids = []
            self.secili_sinav_snapshot = {}
            
            for widget in self.sinav_checkbox_frame.winfo_children():
                widget.destroy()
            self.sinav_check_vars.clear()
            
            if not sinavlar:
                tk.Label(
                    self.sinav_checkbox_frame,
                    text="Henüz sınav eklenmemiş.",
                    font=(KelebekTheme.FONT_FAMILY, 10, "italic"),
                    fg=KelebekTheme.TEXT_MUTED,
                    bg=KelebekTheme.BG_WHITE
                ).pack(fill="x", padx=5, pady=5)
                self.sinav_detay_label.config(text="Seçili sınav yok")
                self.havuz_info_label.config(text="Pota henüz oluşturulmadı.")
                self.log("⚠️ Henüz sınav eklenmemiş")
                show_message(self.window, "Önce sınav eklemelisiniz!", "warning")
                return
            
            for sinav in sinavlar:
                var = tk.BooleanVar(value=False)
                self.sinav_check_vars[sinav['id']] = var
                
                card = tk.Frame(
                    self.sinav_checkbox_frame,
                    bg=KelebekTheme.BG_CARD,
                    relief="flat",
                    borderwidth=1,
                    highlightbackground=KelebekTheme.BORDER_COLOR,
                    highlightthickness=1
                )
                card.pack(fill="x", padx=4, pady=4)
                
                header = tk.Frame(card, bg=KelebekTheme.BG_CARD)
                header.pack(fill="x", padx=6, pady=4)
                
                cb = tk.Checkbutton(
                    header,
                    text=f"{sinav['sinav_adi']}",
                    variable=var,
                    font=(KelebekTheme.FONT_FAMILY, 11, "bold"),
                    bg=KelebekTheme.BG_CARD,
                    fg=KelebekTheme.TEXT_DARK,
                    activebackground=KelebekTheme.BG_CARD,
                    command=self.on_sinav_selected
                )
                cb.pack(anchor="w")
                
                # Tarih/saat/ders_no NULL olabilir
                tarih_str = sinav.get('sinav_tarihi') or ''
                saat_str = sinav.get('sinav_saati') or ''
                ders_no = sinav.get('kacinci_ders')
                
                if tarih_str and saat_str and ders_no:
                    detay_text = f"{sinav['ders_adi']} • {tarih_str} {saat_str} • {ders_no}. Ders"
                else:
                    detay_text = sinav['ders_adi']
                tk.Label(
                    card,
                    text=detay_text,
                    font=(KelebekTheme.FONT_FAMILY, 9),
                    fg=KelebekTheme.TEXT_MUTED,
                    bg=KelebekTheme.BG_CARD,
                    justify="left",
                    wraplength=300
                ).pack(anchor="w", padx=8)
                
                sinif_list = ", ".join(f"{s}.sınıf" for s in sinav['secili_siniflar']) or "Sınıf seçilmedi"
                soru_dosyasi = sinav.get('soru_dosyasi', {})
                soru_text = soru_dosyasi.get('dosya_adi', "Soru dosyası atanmadı")
                
                tk.Label(
                    card,
                    text=f"Sınıflar: {sinif_list}\nSoru Dosyası: {soru_text}",
                    font=(KelebekTheme.FONT_FAMILY, 9),
                    fg=KelebekTheme.TEXT_MUTED,
                    bg=KelebekTheme.BG_CARD,
                    justify="left",
                    wraplength=300
                ).pack(anchor="w", padx=8, pady=(0, 6))
            
            self.log(f"✅ {len(sinavlar)} sınav yüklendi")
        except Exception as e:
            self.log(f"❌ Sınav yükleme hatası: {e}")
    
    def load_salonlar(self):
        """Salonları yükle ve checkbox'ları oluştur"""
        try:
            salonlar = self.db.salonlari_listele()
            
            # Eski checkbox'ları temizle
            for widget in self.salon_checkbox_frame.winfo_children():
                widget.destroy()
            
            self.salon_checkboxes.clear()
            
            columns = 2
            for idx, salon in enumerate(salonlar):
                var = tk.BooleanVar(value=False)
                self.salon_checkboxes[salon['id']] = {
                    'var': var,
                    'salon': salon
                }
                
                salon_box = tk.Frame(
                    self.salon_checkbox_frame,
                    bg=KelebekTheme.BG_CARD,
                    relief="flat",
                    borderwidth=1,
                    highlightbackground=KelebekTheme.BORDER_COLOR,
                    highlightthickness=1
                )
                row = idx // columns
                col = idx % columns
                salon_box.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
                
                cb = tk.Checkbutton(
                    salon_box,
                    text=f"{salon['salon_adi']}",
                    variable=var,
                    font=(KelebekTheme.FONT_FAMILY, 10, "bold"),
                    bg=KelebekTheme.BG_CARD,
                    fg=KelebekTheme.TEXT_DARK,
                    activebackground=KelebekTheme.BG_CARD,
                    command=self.update_kapasite
                )
                cb.pack(anchor="w", padx=10, pady=(8, 2))
                
                info_label = tk.Label(
                    salon_box,
                    text=f"Kapasite: {salon['kapasite']}",
                    font=(KelebekTheme.FONT_FAMILY, 9),
                    fg=KelebekTheme.TEXT_MUTED,
                    bg=KelebekTheme.BG_CARD
                )
                info_label.pack(anchor="w", padx=12, pady=(0, 8))
            
            for col in range(columns):
                self.salon_checkbox_frame.columnconfigure(col, weight=1)
            
            self.update_kapasite()
            self.refresh_gozetmen_inputs()
            self.log(f"✅ {len(salonlar)} salon yüklendi")
        except Exception as e:
            self.log(f"❌ Salon yükleme hatası: {e}")
    
    def on_sinav_selected(self, event=None):
        """Sınav checkbox'ları değiştiğinde"""
        selected_ids = [sid for sid, var in self.sinav_check_vars.items() if var.get()]
        self.secili_sinav_ids = selected_ids
        self.secili_sinav_snapshot = {sid: self.sinav_dict[sid] for sid in selected_ids}
        self.secili_sinav_id = selected_ids[0] if selected_ids else None
        
        if not selected_ids:
            self.sinav_detay_label.config(text="Seçili sınav yok")
            self.havuz_info_label.config(text="Pota henüz oluşturulmadı.")
            self.havuz_toplam_ogrenci = 0
            return
        
        secili_siniflar = set()
        toplam = 0
        satirlar = []
        
        for sinav in self.secili_sinav_snapshot.values():
            secili_siniflar.update(sinav['secili_siniflar'])
            soru = sinav.get('soru_dosyasi') or {}
            soru_text = soru.get('dosya_adi', "Soru dosyası yok")
            satirlar.append(f"• {sinav['sinav_adi']} ({sinav['ders_adi']}) → {soru_text}")
            try:
                ogrenciler = self.db.ogrencileri_listele(siniflar=sinav['secili_siniflar'])
                toplam += len(ogrenciler)
            except Exception:
                pass
        
        self.havuz_toplam_ogrenci = toplam
        self.sinav_detay_label.config(text="\n".join(satirlar))
        self.havuz_info_label.config(
            text=f"{len(selected_ids)} sınav | {len(secili_siniflar)} sınıf seviyesi | Yaklaşık {toplam} öğrenci"
        )
        self.log(f"✅ {len(selected_ids)} sınav seçildi")
        self.update_gozetmen_map()
    
    def update_kapasite(self):
        """Seçili salonlara göre kapasiteyi güncelle"""
        toplam_kapasite = sum(
            data['salon']['kapasite']
            for data in self.salon_checkboxes.values()
            if data['var'].get()
        )
        
        self.salon_kapasite_label.config(text=f"Toplam kapasite: {toplam_kapasite}")
    
    def update_gozetmen_map(self):
        """Seçili sınav için gözetmen atamalarını güncelle"""
        self.salon_gozetmen_map = {}
        self.gozetmen_atamalari = []
        
        if len(self.secili_sinav_ids) != 1 or not self.secili_sinav_id:
            return
        
        try:
            atamalar = self.db.gozetmen_atamalari_listele(self.secili_sinav_id)
        except AttributeError:
            return
        
        self.gozetmen_atamalari = atamalar
        temp_map = {}
        for atama in atamalar:
            salon_id = atama['salon_id']
            gorev_text = "Asıl" if atama['gorev_turu'] == 'asil' else "Yedek"
            temp_map.setdefault(salon_id, []).append(f"{atama['ad']} {atama['soyad']} ({gorev_text})")
        
        self.salon_gozetmen_map = {sid: ", ".join(names) for sid, names in temp_map.items()}
        self._render_gozetmen_assignments()
    
    def get_exam_info_text(self):
        """Seçili sınav bilgisi"""
        if not self.secili_sinav_ids:
            return "Sınav seçilmedi"
        if len(self.secili_sinav_ids) == 1:
            sinav = self.sinav_dict.get(self.secili_sinav_ids[0])
            if not sinav:
                return "Sınav seçilmedi"
            # Tarih/saat NULL olabilir
            tarih_str = sinav.get('sinav_tarihi') or ''
            saat_str = sinav.get('sinav_saati') or ''
            if tarih_str and saat_str:
                return (f"{sinav['sinav_adi']} - {sinav['ders_adi']} | "
                        f"{tarih_str} {saat_str}")
            return f"{sinav['sinav_adi']} - {sinav['ders_adi']}"
        return (f"{len(self.secili_sinav_ids)} sınav seçildi | "
                f"Yaklaşık {self.havuz_toplam_ogrenci} öğrenci")
    
    
    def log(self, message):
        """Log mesajı ekle"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}"
        self.log_messages.append(formatted_msg)
        
        # Mini log güncelle
        if hasattr(self, 'mini_log_text') and self.mini_log_text.winfo_exists():
            self.mini_log_text.config(state='normal')
            self.mini_log_text.insert('end', formatted_msg + "\n")
            self.mini_log_text.see('end')
            self.mini_log_text.config(state='disabled')

        if self.log_window and tk.Toplevel.winfo_exists(self.log_window):
            self.update_log_window()

    def show_log_window(self):
        """İşlem loglarını ayrı pencerede göster"""
        if self.log_window and tk.Toplevel.winfo_exists(self.log_window):
            self.log_window.lift()
            self.update_log_window()
            return
        
        self.log_window = tk.Toplevel(self.window)
        self.log_window.title("İşlem Logları")
        self.log_window.geometry("500x400")
        self.log_window.config(bg=KelebekTheme.BG_LIGHT)
        
        log_card = create_card_frame(self.log_window, "İşlem Logları", KelebekTheme.ICON_INFO)
        log_card.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(
            log_card.content,
            font=(KelebekTheme.FONT_FAMILY, 9),
            bg=KelebekTheme.BG_WHITE,
            fg=KelebekTheme.TEXT_DARK,
            wrap=tk.WORD
        )
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        btn_clear = tk.Button(log_card.content,
                              command=lambda: self.clear_logs())
        configure_standard_button(btn_clear, "secondary", "Temizle")
        btn_clear.pack(pady=5)

        # Mevcut logları pencere açılır açılmaz göster
        self.update_log_window()
        
    def show_uyumsuzluklar(self):
        """Harmanlama sonrası tespit edilen uyumsuzlukları göster."""
        if not self.yerlesim_sonuc:
            show_message(self.window, "Önce harmanlama yapmalısınız.", "warning")
            return
        uyumsuzluklar = self.yerlesim_sonuc.get('uyumsuzluklar') or []
        if not uyumsuzluklar:
            show_message(self.window, "Harmanlanan öğrencilerde uyumsuzluk bulunamadı.", "success")
            return
        data = self._parse_uyumsuzluklar(uyumsuzluklar)
        if self.uyumsuzluk_window and tk.Toplevel.winfo_exists(self.uyumsuzluk_window):
            self._render_uyumsuzluk_tree(data)
            self.uyumsuzluk_window.lift()
            return
        self.uyumsuzluk_window = tk.Toplevel(self.window)
        self.uyumsuzluk_window.title("Uyumsuzluk Listesi")
        self.uyumsuzluk_window.geometry("640x320")
        self.uyumsuzluk_window.config(bg=KelebekTheme.BG_LIGHT)
        self.uyumsuzluk_window.protocol("WM_DELETE_WINDOW", self._close_uyumsuzluk_window)
        
        card = create_card_frame(self.uyumsuzluk_window, "Kurala Uymayan Yerleşimler", KelebekTheme.ICON_WARNING)
        card.pack(fill="both", expand=True, padx=10, pady=10)
        
        columns = ("Salon", "Sıra", "Detay")
        self.uyumsuzluk_tree = ttk.Treeview(card.content, columns=columns, show="headings", height=10)
        for col in columns:
            width = 100 if col != "Detay" else 380
            self.uyumsuzluk_tree.heading(col, text=col)
            self.uyumsuzluk_tree.column(col, width=width, anchor="center" if col != "Detay" else "w")
        self.uyumsuzluk_tree.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        
        scroll = ttk.Scrollbar(card.content, orient="vertical", command=self.uyumsuzluk_tree.yview)
        self.uyumsuzluk_tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y", padx=(0, 5), pady=5)
        
        self._render_uyumsuzluk_tree(data)

    def _parse_uyumsuzluklar(self, logs):
        parsed = []
        pattern = re.compile(r"(?P<salon>.+?) salonunda (?P<sira>\d+)\.")
        for text in logs:
            salon = "-"
            sira = "-"
            match = pattern.search(text)
            if match:
                salon = match.group("salon").strip()
                sira = match.group("sira")
            parsed.append({
                'salon': salon,
                'sira': sira,
                'detay': text
            })
        return parsed

    def _render_uyumsuzluk_tree(self, data):
        if not self.uyumsuzluk_tree:
            return
        for item in self.uyumsuzluk_tree.get_children():
            self.uyumsuzluk_tree.delete(item)
        for entry in data:
            self.uyumsuzluk_tree.insert(
                "",
                "end",
                values=(entry['salon'], entry['sira'], entry['detay'])
            )
    
    def _close_uyumsuzluk_window(self):
        if self.uyumsuzluk_window and tk.Toplevel.winfo_exists(self.uyumsuzluk_window):
            self.uyumsuzluk_window.destroy()
        self.uyumsuzluk_window = None
        self.uyumsuzluk_tree = None
        
        self.update_log_window()

    def update_log_window(self):
        if not self.log_window or not tk.Toplevel.winfo_exists(self.log_window):
            return
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, "\n".join(self.log_messages))
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def clear_logs(self):
        self.log_messages.clear()
        if self.log_window and tk.Toplevel.winfo_exists(self.log_window):
            self.log_text.config(state="normal")
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state="disabled")
    
    def harmanla(self):
        """Harmanlama işlemini başlat"""
        if not self.secili_sinav_ids:
            show_message(self.window, "Önce en az bir sınav seçmelisiniz!", "warning")
            return
        
        secili_salonlar = [
            data['salon'] for data in self.salon_checkboxes.values()
            if data['var'].get()
        ]
        if not secili_salonlar:
            show_message(self.window, "En az bir salon seçmelisiniz!", "warning")
            return
        
        havuz = self._hazirla_ogrenci_havuzu()
        tum_ogrenciler = havuz['tum']
        mobil_ogrenciler = havuz['mobil']
        sabit_ogrenciler = havuz['sabit']
        
        if not tum_ogrenciler:
            show_message(self.window, "Seçili sınavlarda öğrenci bulunamadı!", "warning")
            return
        
        self.log("=" * 50)
        self.log("🔄 HARMANLAMA BAŞLIYOR")
        self.log("=" * 50)
        self.log(f"🧪 Seçili sınav sayısı: {len(self.secili_sinav_ids)}")
        for ist in havuz['istatistikler']:
            self.log(f"   • {ist['sinav_adi']}: {ist['toplam']} öğrenci "
                     f"(mobil {ist['mobil']}, sabit {ist['sabit']})")
        
        self.log(f"📊 Öğrenci sayısı: {len(tum_ogrenciler)} "
                 f"(Mobil: {len(mobil_ogrenciler)}, Sabit: {len(sabit_ogrenciler)})")
        self.log(f"🏢 Salon sayısı: {len(secili_salonlar)}")
        
        toplam_kapasite = sum(s['kapasite'] for s in secili_salonlar)
        self.log(f"📦 Toplam kapasite: {toplam_kapasite}")
        
        if len(tum_ogrenciler) > toplam_kapasite:
            msg = f"Yetersiz kapasite!\nÖğrenci: {len(tum_ogrenciler)}\nKapasite: {toplam_kapasite}"
            show_message(self.window, msg, "error")
            self.log(f"❌ {msg}")
            return
        
        try:
            config = HarmanlamaConfig()
            self.engine = HarmanlamaEngine(config)
            
            self.log("⚙️ Harmanlama modu çalıştırılıyor.")
            self.log("🚀 Harmanlama algoritması çalışıyor...")
            
            # Loading dialog göster
            loading = LoadingDialog(self.window, "🔄 Harmanlama yapılıyor...")
            self.window.update()
            
            try:
                salon_sira_map = self.db.salon_sira_haritasi([s['id'] for s in secili_salonlar])
                sonuc = self.engine.harmanla(
                    tum_ogrenciler,
                    secili_salonlar,
                    sabit_ogrenciler=sabit_ogrenciler,
                    salon_sira_haritasi=salon_sira_map
                )
            finally:
                loading.stop()
            
            if not sonuc['basarili']:
                self.log("❌ HARMANLAMA BAŞARISIZ!")
                for hata in sonuc['hatalar']:
                    self.log(f"   {hata}")
                show_message(self.window, "Harmanlama başarısız! Loglara bakın.", "error")
                return
            
            self.yerlesim_sonuc = sonuc
            self.yerlesim_sonuc['secili_sinavlar'] = list(self.secili_sinav_snapshot.values())
            self.yerlesim_sonuc['havuz_istatistikler'] = havuz['istatistikler']
            self.yerlesim_sonuc['uyumsuzluklar'] = sonuc.get('uyumsuzluklar', [])
            self.yerlesim_sonuc['uyumsuzluk_var'] = sonuc.get('uyumsuzluk_var', False)
            self.son_harman_secili_sinavlar = list(self.secili_sinav_snapshot.values())
            
            try:
                self._persist_yerlesim(sonuc['yerlesim'])
                self.log("💾 Yerleşim veritabanına kaydedildi")
            except Exception as e:
                self.log(f"❌ Yerleşim kaydedilemedi: {e}")
                show_message(self.window,
                             f"Yerleşim kaydedilirken hata oluştu:\n{e}",
                             "warning")
            
            self.display_results(sonuc)
            
            uyumsuzluklar = sonuc.get('uyumsuzluklar') or []
            if uyumsuzluklar:
                self.log("⚠️ Uyumsuzluklar tespit edildi:")
                for detay in uyumsuzluklar:
                    self.log(f"   {detay}")
            
            koltuk_listesi = sonuc.get('koltuk_listesi') or []
            if koltuk_listesi:
                self.log("🪑 Koltuk Sıralaması:")
                max_satir = min(20, len(koltuk_listesi))
                for satir in koltuk_listesi[:max_satir]:
                    self.log(f"   {satir}")
                if len(koltuk_listesi) > max_satir:
                    self.log(f"   ... toplam {len(koltuk_listesi)} öğrenci")
            
            istatistikler = sonuc['istatistikler']
            self.log("=" * 50)
            self.log("✅ HARMANLAMA BAŞARILI!")
            self.log("=" * 50)
            self.log(f"📊 İstatistikler:")
            self.log(f"   • Yerleştirilen öğrenci: {istatistikler['yerlestirilen']}")
            self.log(f"   • Kullanılan salon: {istatistikler['kullanilan_salon']}/{istatistikler['toplam_salon']}")
            
            for salon_stat in istatistikler['salon_istatistikleri']:
                self.log(f"   • {salon_stat['salon_adi']}: {salon_stat['doluluk']}/"
                         f"{salon_stat['kapasite']} (%{salon_stat['oran']})")
            
            stat_text = (f"✅ {istatistikler['yerlestirilen']} öğrenci yerleştirildi | "
                         f"{istatistikler['kullanilan_salon']} salon kullanıldı")
            if uyumsuzluklar:
                stat_text += f" | ⚠️ {len(uyumsuzluklar)} uyumsuzluk"
            self.log(stat_text)
            
            if uyumsuzluklar:
                warning_text = (
                    f"Harmanlama tamamlandı ancak {len(uyumsuzluklar)} uyumsuzluk bulundu.\n"
                    "Detaylar için log ekranını inceleyin."
                )
                show_message(self.window, warning_text, "warning")
            else:
                show_message(self.window, "✅ Harmanlama başarılı!", "success")
        
        except Exception as e:
            error_msg = f"Beklenmeyen hata: {str(e)}"
            self.log(f"❌ {error_msg}")
            show_message(self.window, error_msg, "error")
            import traceback
            traceback.print_exc()
    
    def _hazirla_ogrenci_havuzu(self):
        """Seçili sınavlar için öğrenci listesini hazırla"""
        mobil, sabit = [], []
        mobil_seen, sabit_seen = set(), set()
        istatistikler = []
        
        for sinav_id in self.secili_sinav_ids:
            sinav = self.sinav_dict.get(sinav_id)
            if not sinav:
                continue
            siniflar = sinav.get('secili_siniflar', [])
            try:
                mobil_list = self.db.ogrencileri_listele(siniflar=siniflar, sabit_mi=False)
                sabit_list = self.db.ogrencileri_listele(siniflar=siniflar, sabit_mi=True)
            except Exception:
                mobil_list, sabit_list = [], []
            
            mobil_count = 0
            for ogr in mobil_list:
                if ogr['id'] in mobil_seen:
                    continue
                mobil_seen.add(ogr['id'])
                ogr_copy = dict(ogr)
                ogr_copy['sinav_id'] = sinav_id
                ogr_copy['sinav_adi'] = sinav['sinav_adi']
                mobil.append(ogr_copy)
                mobil_count += 1
            
            sabit_count = 0
            for ogr in sabit_list:
                if ogr['id'] in sabit_seen:
                    continue
                sabit_seen.add(ogr['id'])
                ogr_copy = dict(ogr)
                ogr_copy['sinav_id'] = sinav_id
                ogr_copy['sinav_adi'] = sinav['sinav_adi']
                sabit.append(ogr_copy)
                sabit_count += 1
            
            istatistikler.append({
                'sinav_id': sinav_id,
                'sinav_adi': sinav['sinav_adi'],
                'ders_adi': sinav['ders_adi'],
                'siniflar': siniflar,
                'mobil': mobil_count,
                'sabit': sabit_count,
                'toplam': mobil_count + sabit_count
            })
        
        return {
            'mobil': mobil,
            'sabit': sabit,
            'tum': mobil + sabit,
            'istatistikler': istatistikler
        }
    
    def _persist_yerlesim(self, yerlesim_listesi):
        """Yerleşim sonuçlarını tekil veya çoklu sınavlar için kaydet"""
        if not yerlesim_listesi:
            return
        
        try:
            if hasattr(self.db, 'yerlesim_toplu_kaydet') and len(self.secili_sinav_ids) > 1:
                self.db.yerlesim_toplu_kaydet(yerlesim_listesi)
            elif self.secili_sinav_ids:
                hedef_id = self.secili_sinav_ids[0]
                filtreli = [y for y in yerlesim_listesi
                            if y.get('sinav_id', hedef_id) == hedef_id]
                self.db.yerlesim_kaydet(hedef_id, filtreli)
        except AttributeError:
            self.log("⚠️ Yerleşim kaydı için gerekli yöntem bulunamadı")
    
    def gozetmen_ata(self):
        """Gözetmenleri otomatik ata (İsteğe bağlı özellik)"""
        if len(self.secili_sinav_ids) != 1 or not self.secili_sinav_id:
            show_message(self.window, "Gözetmen ataması için tek bir sınav seçmelisiniz!", "warning")
            return
        
        if not self.yerlesim_sonuc:
            show_message(self.window, "Önce harmanlama yapmalısınız!", "warning")
            return
        
        # Uyarı - isteğe bağlı özellik
        if not ask_confirmation(self.window,
                               "⚠️ Gözetmen Atama özelliği henüz geliştirme aşamasındadır.\n\n"
                               "Bu özellik sadece yedek/deneme amaçlıdır ve doğru çalışmayabilir.\n\n"
                               "Devam etmek istiyor musunuz?"):
            return
        
        self.log("=" * 50)
        self.log("👨‍🏫 GÖZETMEN ATAMA BAŞLIYOR (İsteğe bağlı)")
        self.log("=" * 50)
        
        try:
            # Kullanılan salonları bul
            kullanilan_salon_ids = set(y['salon_id'] for y in self.yerlesim_sonuc['yerlesim'])
            kullanilan_salonlar = [
                s for s in self.db.salonlari_listele()
                if s['id'] in kullanilan_salon_ids
            ]
            
            # Gözetmenleri al - method var mı kontrol et
            try:
                gozetmenler = self.db.gozetmenleri_listele()
            except AttributeError:
                self.log("❌ Gözetmen yönetimi henüz eklenmemiş")
                show_message(self.window,
                           "Gözetmen yönetimi henüz sistemde bulunmuyor.\n"
                           "Bu özellik gelecek sürümlerde eklenecektir.",
                           "info")
                return
            
            if not gozetmenler:
                show_message(self.window, "Gözetmen bulunamadı!", "warning")
                self.log("❌ Gözetmen bulunamadı!")
                return
            
            self.log(f"🏢 {len(kullanilan_salonlar)} salon için gözetmen atanacak")
            self.log(f"👥 Kullanılabilir gözetmen: {len(gozetmenler)}")
            
            # Otomatik atama
            atamalar = self.gozetmen_engine.otomatik_ata(
                kullanilan_salonlar,
                gozetmenler,
                salon_basina_gozetmen=1
            )
            
            # Mevcut atamaları temizle - method var mı kontrol et
            try:
                self.db.gozetmen_atamalarini_temizle(self.secili_sinav_id)
            except AttributeError:
                self.log("⚠️ Gözetmen atama temizleme methodu bulunamadı")
            
            # Yeni atamaları kaydet - method var mı kontrol et
            try:
                for atama in atamalar:
                    self.db.gozetmen_ata(
                        self.secili_sinav_id,
                        atama['gozetmen_id'],
                        atama['salon_id'],
                        atama['gorev_turu']
                    )
            except AttributeError:
                self.log("⚠️ Gözetmen atama kaydetme methodu bulunamadı")
                show_message(self.window,
                           "Gözetmen atama veritabanı işlemleri henüz hazır değil.\n"
                           "Atama sadece hafızada yapıldı, veritabanına kaydedilmedi.",
                           "warning")
            
            self.log(f"✅ {len(atamalar)} gözetmen ataması yapıldı")
            
            # Detayları göster - method var mı kontrol et
            try:
                atama_detaylari = self.db.gozetmen_atamalari_listele(self.secili_sinav_id)
                for atama in atama_detaylari:
                    self.log(f"   • {atama['salon_adi']}: {atama['ad']} {atama['soyad']} ({atama['gorev_turu']})")
            except AttributeError:
                self.log("⚠️ Gözetmen atama listesi methodu bulunamadı")
            
            self.update_gozetmen_map()
            if self.result_window and tk.Toplevel.winfo_exists(self.result_window):
                self.populate_result_window()
            
            show_message(self.window,
                        f"✅ {len(atamalar)} gözetmen atandı!\n\n"
                        f"⚠️ Not: Bu özellik henüz geliştirme aşamasındadır.",
                        "success")
            
        except Exception as e:
            error_msg = f"Gözetmen atama hatası: {str(e)}"
            self.log(f"❌ {error_msg}")
            show_message(self.window,
                        f"Gözetmen atama hatası:\n{str(e)}\n\n"
                        f"Bu özellik henüz tam olarak çalışmamaktadır.",
                        "error")
    
    def display_results(self, sonuc):
        """Sonuç bilgilerini kaydet"""
        yerlesim = sonuc['yerlesim']
        salonlar = sorted(set(y['salon_adi'] for y in yerlesim))
        summary_text = (f"Kullanılan salon: {len(salonlar)} | "
                        f"Yerleştirilen öğrenci: {len(yerlesim)}")
        self.last_summary = summary_text
        self.log(f"📊 {summary_text}")
        self.log("ℹ️ Detaylar için 'Yerleşimi Göster' butonunu kullanın.")
    
    def auto_assign_gozetmenler(self):
        """Her salon için otomatik gözetmen ataması yap"""
        if not self.yerlesim_sonuc:
            return
        if len(self.secili_sinav_ids) != 1 or not self.secili_sinav_id:
            self.log("ℹ️ Gözetmen ataması sadece tek sınav seçildiğinde yapılabilir.")
            return
        
        try:
            gozetmenler = self.db.gozetmenleri_listele()
        except AttributeError:
            self.log("⚠️ Gözetmen listeleme fonksiyonu bulunamadı")
            return
        
        if not gozetmenler:
            self.log("⚠️ Atanacak gözetmen bulunamadı")
            return
        
        salon_ids = []
        for yer in sorted(self.yerlesim_sonuc['yerlesim'], key=lambda x: (x['salon_id'], x['sira_no'])):
            if yer['salon_id'] not in salon_ids:
                salon_ids.append(yer['salon_id'])
        
        try:
            self.db.gozetmen_atamalarini_temizle(self.secili_sinav_id)
        except AttributeError:
            pass
        
        assignments = 0
        for salon_id in salon_ids:
            if assignments >= len(gozetmenler):
                break
            gozetmen = gozetmenler[assignments]
            try:
                self.db.gozetmen_ata(self.secili_sinav_id, gozetmen['id'], salon_id, 'asil')
                assignments += 1
            except AttributeError:
                self.log("⚠️ Gözetmen atama fonksiyonu bulunamadı")
                break
        
        if assignments < len(salon_ids):
            self.log(f"⚠️ Yetersiz gözetmen: {assignments}/{len(salon_ids)} salon")
        else:
            self.log(f"👨‍🏫 {assignments} salon için otomatik gözetmen atandı")
        
        self.update_gozetmen_map()

    def excel_export(self):
        """Excel'e aktar (gözetmen bilgileri dahil)"""
        if not self.yerlesim_sonuc:
            show_message(self.window, "Önce harmanlama yapmalısınız!", "warning")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Excel Olarak Kaydet",
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")],
            initialfile=f"yerlesim_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        )
        
        if not file_path:
            return
        
        try:
            snapshot = getattr(self, "son_harman_secili_sinavlar", [])
            if len(snapshot) == 1:
                sinav = snapshot[0]
                sinav_bilgi = {
                    'ders_adi': sinav['ders_adi'],
                    'tarih': sinav.get('sinav_tarihi') or '-',
                    'saat': sinav.get('sinav_saati') or '-',
                    'kacinci_ders': sinav.get('kacinci_ders') or '-'
                }
            elif snapshot:
                tarihler = sorted({s['sinav_tarihi'] for s in snapshot if s.get('sinav_tarihi')})
                saatler = sorted({s['sinav_saati'] for s in snapshot if s.get('sinav_saati')})
                sinav_bilgi = {
                    'ders_adi': f"{len(snapshot)} Sınav (Karma)",
                    'tarih': ", ".join(tarihler) if tarihler else "-",
                    'saat': ", ".join(saatler) if saatler else "-",
                    'kacinci_ders': "Karma Program"
                }
            else:
                sinav = self.db.sinav_getir(self.secili_sinav_id) if self.secili_sinav_id else None
                sinav_bilgi = {
                    'ders_adi': sinav['ders_adi'] if sinav else "Sınav",
                    'tarih': sinav.get('sinav_tarihi') or '-' if sinav else "-",
                    'saat': sinav.get('sinav_saati') or '-' if sinav else "-",
                    'kacinci_ders': sinav.get('kacinci_ders') or '-' if sinav else "-"
                }
            
            # Gözetmen atamalarını güncelle
            self.update_gozetmen_map()
            gozetmen_atamalari = self.gozetmen_atamalari
            salon_gozetmenleri = self.salon_gozetmen_map
            
            # Yerleşim verilerini hazırla (gözetmen bilgileri dahil)
            yerlesim_data = []
            sinav_map = {s['id']: s for s in snapshot} if snapshot else {}
            for yer in self.yerlesim_sonuc['yerlesim']:
                ogrenci = self.db.ogrenci_getir(yer['ogrenci_id'])
                if ogrenci:
                    yerlesim_data.append({
                        'salon_adi': yer['salon_adi'],
                        'sira_no': yer['sira_no'],
                        'ad': ogrenci['ad'],
                        'soyad': ogrenci['soyad'],
                        'sinif': ogrenci['sinif'],
                        'sube': ogrenci['sube'],
                        'gozetmenler': salon_gozetmenleri.get(yer['salon_id'], ""),
                        'sinav_adi': sinav_map.get(yer.get('sinav_id'), {}).get('sinav_adi', yer.get('sinav_adi', ""))
                    })
            
            # Excel'e yazdır
            if self.excel_handler.yerlesim_yazdir(file_path, sinav_bilgi, yerlesim_data):
                self.log(f"✅ Excel dosyası oluşturuldu: {file_path}")
                
                # Gözetmen bilgilerini logla
                if gozetmen_atamalari:
                    self.log("👨‍🏫 Gözetmen atamaları:")
                    for atama in gozetmen_atamalari:
                        gorev_text = "Asıl" if atama['gorev_turu'] == 'asil' else "Yedek"
                        self.log(f"   • {atama['salon_adi']}: {atama['ad']} {atama['soyad']} ({gorev_text})")
                
                show_message(self.window, f"✅ Excel dosyası oluşturuldu:\n{file_path}\n\n📋 Gözetmen atamaları da dahil edildi!", "success")
            else:
                self.log("❌ Excel dosyası oluşturulamadı")
                show_message(self.window, "Excel dosyası oluşturulamadı!\nDosya başka bir uygulamada açık olabilir.", "error")
        except Exception as e:
            error_msg = f"Excel export hatası: {e}"
            self.log(f"❌ {error_msg}")
            show_message(self.window, error_msg, "error")
            import traceback
            traceback.print_exc()


    def _ensure_yerlesim_data(self):
        """Yerleşim verisi yoksa DB'den yüklemeyi dene. Varsa True döner."""
        if self.yerlesim_sonuc:
            return True
            
        try:
            kayitli_yerlesim = self.db.tum_yerlesimleri_listele()
            if kayitli_yerlesim:
                self.log("💾 Veritabanından kayıtlı yerleşim yüklendi.")
                
                # Benzersiz sınavları bul
                sinav_ids = set(k['sinav_id'] for k in kayitli_yerlesim)
                secili_sinavlar = []
                for sid in sinav_ids:
                    sinav = self.db.sinav_getir(sid)
                    if sinav:
                        secili_sinavlar.append(sinav)
                
                self.yerlesim_sonuc = {
                    'basarili': True,
                    'yerlesim': kayitli_yerlesim,
                    'istatistikler': {
                        'yerlesen': len(kayitli_yerlesim),
                        'yerlesemeyen': 0,
                        'doluluk_orani': 0
                    },
                    'secili_sinavlar': secili_sinavlar
                }
                self.secili_sinav_snapshot = {s['id']: s for s in secili_sinavlar}
                return True
        except Exception as e:
            self.log(f"Yerleşim yüklenirken hata: {e}")
            
        return False

    def open_visual_preview(self):
        """Görsel oturma düzeni pencresini aç"""
        if not self._ensure_yerlesim_data():
            show_message(self.window, "Görüntülenecek yerleşim verisi yok! Lütfen önce harmanlama yapın.", "warning")
            return
                
        if not self.yerlesim_sonuc.get('yerlesim'):
             show_message(self.window, "Data boş!", "warning")
             return
             
        # Sınav adı (Birden fazla olabilir, birleştir)
        sinav_adlari = ", ".join([s['ders_adi'] for s in self.yerlesim_sonuc.get('secili_sinavlar', [])])
        if not sinav_adlari and self.yerlesim_sonuc.get('yerlesim'):
             # fallback
             sinav_adlari = self.yerlesim_sonuc['yerlesim'][0].get('sinav_adi', 'Sınav')
        VisualSeatingPlanWindow(self.window, self.yerlesim_sonuc['yerlesim'], sinav_adlari)

    def show_result_window(self):
        """Yerleşim sonuçlarını ayrı pencerede göster"""
        if not self._ensure_yerlesim_data():
            show_message(self.window, "Henüz harmanlama yapılmadı veya kayıtlı yerleşim bulunamadı!", "warning")
            return
            
        if self.result_window and tk.Toplevel.winfo_exists(self.result_window):
            self.result_window.lift()
            return
            self.populate_result_window()
            return
        
        self.result_window = tk.Toplevel(self.window)
        self.result_window.title("Yerleşim Sonuçları")
        self.result_window.geometry("800x500")
        self.result_window.config(bg=KelebekTheme.BG_LIGHT)
        
        header = tk.Frame(self.result_window, bg=KelebekTheme.BG_WHITE, height=60)
        header.pack(fill="x")
        tk.Label(
            header,
            text="Yerleşim Sonuçları",
            font=(KelebekTheme.FONT_FAMILY, 14, "bold"),
            bg=KelebekTheme.BG_WHITE,
            fg=KelebekTheme.TEXT_DARK
        ).pack(side="left", padx=15, pady=10)
        
        self.popup_exam_label = tk.Label(
            header,
            text=self.get_exam_info_text(),
            font=(KelebekTheme.FONT_FAMILY, 10),
            bg=KelebekTheme.BG_WHITE,
            fg=KelebekTheme.TEXT_MUTED
        )
        self.popup_exam_label.pack(side="left", padx=15)
        
        tk.Label(
            header,
            text="Salon:",
            bg=KelebekTheme.BG_WHITE,
            font=(KelebekTheme.FONT_FAMILY, 10)
        ).pack(side="left", padx=(20, 5))
        
        self.popup_salon_var = tk.StringVar(value="Tümü")
        self.popup_salon_combo = ttk.Combobox(
            header,
            textvariable=self.popup_salon_var,
            state="readonly",
            width=15
        )
        self.popup_salon_combo.pack(side="left")
        self.popup_salon_combo.bind("<<ComboboxSelected>>", lambda e: self.populate_result_window())
        
        tree_frame = tk.Frame(self.result_window, bg=KelebekTheme.BG_WHITE)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        columns = ("Sınav", "Sıra", "Ad", "Soyad", "Sınıf", "Şube", "Salon", "Gözetmenler")
        self.popup_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
        for col in columns:
            self.popup_tree.heading(col, text=col)
            width = 120
            if col == "Sıra":
                width = 60
            elif col == "Gözetmenler":
                width = 200
            elif col == "Sınav":
                width = 180
            self.popup_tree.column(col, anchor="center", width=width)
        
        popup_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.popup_tree.yview)
        self.popup_tree.configure(yscrollcommand=popup_scroll.set)
        self.popup_tree.pack(side="left", fill="both", expand=True)
        popup_scroll.pack(side="right", fill="y")
        
        self.populate_result_window()

    def populate_result_window(self):
        """Popup penceresini doldur"""
        if not self.yerlesim_sonuc or not hasattr(self, "popup_tree"):
            return
        
        self.update_gozetmen_map()
        if hasattr(self, "popup_exam_label"):
            self.popup_exam_label.config(text=self.get_exam_info_text())
        
        for item in self.popup_tree.get_children():
            self.popup_tree.delete(item)
        
        yerlesim = self.yerlesim_sonuc['yerlesim']
        salonlar = sorted(set(y['salon_adi'] for y in yerlesim))
        if hasattr(self, "popup_salon_combo"):
            current_values = ["Tümü"] + salonlar
            self.popup_salon_combo['values'] = current_values
            if self.popup_salon_var.get() not in current_values:
                self.popup_salon_var.set("Tümü")
        
        selected = self.popup_salon_var.get() if hasattr(self, "popup_salon_var") else "Tümü"
        sinav_map = {s['id']: s for s in getattr(self, "son_harman_secili_sinavlar", [])}
        for yer in sorted(yerlesim, key=lambda x: (x['salon_adi'], x['sira_no'])):
            if selected != "Tümü" and yer['salon_adi'] != selected:
                continue
            ogrenci = self.db.ogrenci_getir(yer['ogrenci_id'])
            if ogrenci:
                seat_display = format_sira_label(yer.get('sira_no'))
                sinav_adi = sinav_map.get(yer.get('sinav_id'), {}).get('sinav_adi', yer.get('sinav_adi', "-"))
                self.popup_tree.insert("", "end", values=(
                    sinav_adi,
                    seat_display,
                    ogrenci['ad'],
                    ogrenci['soyad'],
                    ogrenci['sinif'],
                    ogrenci['sube'],
                    yer['salon_adi'],
                    self.salon_gozetmen_map.get(yer['salon_id'], "")
                ))


# Alias for compatibility
HarmanlamaView = GelismisHarmanlamaView
