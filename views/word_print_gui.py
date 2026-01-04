import threading
import queue
import os
import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# Bu uygulama Word / Excel COM otomasyonu ve Windows kabuk yazdırması ile
# .doc/.docx, .xls/.xlsx/.csv, PDF ve resim dosyalarını toplu yazdırır.
# Gereksinimler: Python 3, pywin32, Microsoft Word ve Excel (Windows).


class WordPrinterApp:
    def __init__(self, root) -> None:
        """Toplu yazdırma uygulaması - Tk veya Toplevel penceresinde çalışır"""
        self.root = root
        self.root.title("Toplu Yazdırma")
        self.root.geometry("820x600")
        style = ttk.Style()
        style.theme_use("clam")
        # Renk paleti (sea foam) ve butonlar için turuncu vurgu
        sea_bg = "#e6fff5"
        sea_accent = "#b4f3de"
        btn_orange = "#f97316"  # turuncu
        btn_orange_active = "#ea580c"

        self.root.configure(bg=sea_bg)
        style.configure("TFrame", background=sea_bg)
        style.configure("TLabel", background=sea_bg, foreground="#1a3a2f")
        style.configure("TCheckbutton", background=sea_bg, foreground="#1a3a2f")
        style.configure("TLabelframe", background=sea_bg, foreground="#1a3a2f")
        style.configure("TLabelframe.Label", background=sea_bg, foreground="#1a3a2f")
        style.configure(
            "TButton",
            background=btn_orange,
            foreground="white",
            padding=6,
            borderwidth=0,
        )
        style.map(
            "TButton",
            background=[("active", btn_orange_active), ("pressed", btn_orange_active)],
            foreground=[("disabled", "#dddddd")],
        )
        style.configure(
            "Horizontal.TProgressbar",
            background=sea_accent,
            troughcolor="#d1efe4",
            bordercolor=sea_bg,
            lightcolor=sea_accent,
            darkcolor=sea_accent,
        )

        self.folder_var = tk.StringVar(value=str(Path.cwd()))
        self.status_var = tk.StringVar(value="Hazır")
        self.progress_var = tk.IntVar(value=0)
        self.type_vars = {
            "word": tk.BooleanVar(value=True),
            "excel": tk.BooleanVar(value=True),
            "pdf": tk.BooleanVar(value=False),
            "image": tk.BooleanVar(value=False),
        }

        self.log_queue: queue.Queue = queue.Queue()
        self.ui_queue: queue.Queue = queue.Queue()
        self.cancel_event = threading.Event()
        self.worker_thread: threading.Thread | None = None
        self.total_files = 0
        self.success = 0
        self.failed = 0

        self._build_ui()
        self._poll_queues()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        header = ttk.Frame(self.root, padding=10)
        header.pack(fill="x")
        ttk.Label(
            header,
            text="📄 Toplu Yazdırma Aracı",
            font=("Segoe UI", 14, "bold"),
        ).pack(side="left")
        ttk.Button(header, text="ℹ️ Hakkında", command=self._show_about).pack(side="right")

        frm_top = ttk.Frame(self.root, padding=10)
        frm_top.pack(fill="x")

        ttk.Label(frm_top, text="🟧📂 Klasör:", font=("Segoe UI", 10, "bold")).pack(side="left")
        entry = ttk.Entry(frm_top, textvariable=self.folder_var)
        entry.pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(frm_top, text="🟠 Seç", command=self._choose_folder).pack(side="left")

        frm_buttons = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        frm_buttons.pack(fill="x")
        self.btn_start = ttk.Button(frm_buttons, text="🟧🚀 Yazdırmayı Başlat", command=self._start_print)
        self.btn_start.pack(side="left")
        self.btn_cancel = ttk.Button(frm_buttons, text="🟧⏹ İptal", command=self._cancel_print, state="disabled")
        self.btn_cancel.pack(side="left", padx=5)

        frm_types = ttk.LabelFrame(self.root, text="Yazdırılacak türler", padding=(10, 5, 10, 5))
        frm_types.pack(fill="x", padx=10, pady=(0, 8))
        ttk.Checkbutton(frm_types, text="📘 Word (.doc/.docx)", variable=self.type_vars["word"]).pack(side="left", padx=4)
        ttk.Checkbutton(frm_types, text="📗 Excel (.xls/.xlsx/.csv)", variable=self.type_vars["excel"]).pack(side="left", padx=4)
        ttk.Checkbutton(frm_types, text="📕 PDF", variable=self.type_vars["pdf"]).pack(side="left", padx=4)
        ttk.Checkbutton(frm_types, text="🖼️ Resim (.png/.jpg/.tiff)", variable=self.type_vars["image"]).pack(side="left", padx=4)

        frm_progress = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        frm_progress.pack(fill="x")
        self.progress = ttk.Progressbar(frm_progress, maximum=1, variable=self.progress_var)
        self.progress.pack(fill="x")
        self.lbl_status = ttk.Label(frm_progress, textvariable=self.status_var, font=("Segoe UI", 9, "bold"))
        self.lbl_status.pack(anchor="w", pady=4)

        frm_log = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        frm_log.pack(fill="both", expand=True)
        self.txt_log = scrolledtext.ScrolledText(
            frm_log,
            height=20,
            state="disabled",
            wrap="word",
            background="#f5fff9",
            foreground="#123327",
            insertbackground="#123327",
            borderwidth=1,
            relief="solid",
        )
        self.txt_log.pack(fill="both", expand=True)

    def _choose_folder(self) -> None:
        path = filedialog.askdirectory(initialdir=self.folder_var.get() or str(Path.cwd()))
        if path:
            self.folder_var.set(path)

    def _start_print(self) -> None:
        if self.worker_thread and self.worker_thread.is_alive():
            messagebox.showinfo("Bilgi", "Zaten çalışıyor.")
            return

        # pywin32 kontrolü (pythoncom / win32com)
        try:
            import importlib

            importlib.import_module("pythoncom")
            importlib.import_module("win32com.client")
        except ImportError:
            messagebox.showerror(
                "Eksik Bağımlılık",
                "pywin32 kurulmalı: py -m pip install pywin32\n"
                "Kurulumdan sonra uygulamayı yeniden başlatın.",
            )
            return

        folder = Path(self.folder_var.get()).expanduser()
        if not folder.is_dir():
            messagebox.showerror("Hata", "Geçerli bir klasör seçin.")
            return

        selected_types = [k for k, v in self.type_vars.items() if v.get()]
        if not selected_types:
            messagebox.showwarning("Uyarı", "En az bir dosya türü seçin.")
            return

        files = self._gather_files(folder, selected_types)
        if not files:
            messagebox.showwarning("Uyarı", "Seçilen türlerde dosya bulunamadı.")
            return

        self.total_files = len(files)
        self.success = 0
        self.failed = 0
        self.progress["maximum"] = self.total_files
        self.progress_var.set(0)
        self.status_var.set(f"{self.total_files} dosya bulundu. Yazdırma başlıyor...")
        self._log(f"Klasör: {folder}")
        label_map = {
            "word": "Word",
            "excel": "Excel/CSV",
            "pdf": "PDF",
            "image": "Resim",
        }
        chosen = ", ".join(label_map[k] for k in selected_types)
        self._log(f"Seçilen türler: {chosen}")
        self._log(f"Toplam {self.total_files} dosya bulundu.")

        self.cancel_event.clear()
        self.btn_start.config(state="disabled")
        self.btn_cancel.config(state="normal")

        self.worker_thread = threading.Thread(
            target=self._worker_print,
            args=(files,),
            daemon=True,
        )
        self.worker_thread.start()

    def _gather_files(self, folder: Path, selected_types: list[str]) -> list[Path]:
        patterns: dict[str, tuple[str, ...]] = {
            "word": ("*.doc", "*.docx"),
            "excel": ("*.xls", "*.xlsx", "*.xlsm", "*.xlsb", "*.csv"),
            "pdf": ("*.pdf",),
            "image": ("*.png", "*.jpg", "*.jpeg", "*.bmp", "*.tif", "*.tiff"),
        }

        files: list[Path] = []
        for key in selected_types:
            for pattern in patterns.get(key, ()):
                files.extend(folder.rglob(pattern))
        # Yinelenenleri kaldır (ilk bulunanı koru) ve klasör bazında sırala
        deduped = list(dict.fromkeys(files))
        ordered = sorted(deduped, key=lambda p: (str(p.parent).lower(), p.name.lower()))
        return ordered

    def _cancel_print(self) -> None:
        self.cancel_event.set()
        self._log("İptal isteği gönderildi. Mevcut dosya tamamlandıktan sonra duracak.")

    def _worker_print(self, files: list[Path]) -> None:
        try:
            import pythoncom
            import win32com.client as win32
            import win32api
        except ImportError as exc:  # Güvenli fallback
            self._log(f"pywin32 eksik: {exc}")
            self.ui_queue.put(("done", None))
            return

        pythoncom.CoInitialize()
        word = None
        excel = None
        try:
            for idx, path in enumerate(files, start=1):
                if self.cancel_event.is_set():
                    self._log("İptal edildi.")
                    break

                ext = path.suffix.lower()
                self._log(f"[{idx}/{self.total_files}] Açılıyor: {path.name}")

                try:
                    if ext in (".doc", ".docx"):
                        if not word:
                            word = win32.DispatchEx("Word.Application")
                            word.Visible = False
                        ok = self._print_word(word, path)
                    elif ext in (".xls", ".xlsx", ".xlsm", ".xlsb", ".csv"):
                        if not excel:
                            excel = win32.DispatchEx("Excel.Application")
                            excel.Visible = False
                        ok = self._print_excel(excel, path)
                    elif ext in (".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"):
                        ok = self._print_shell(win32api, path)
                    else:
                        self._log("  ⚠ Desteklenmeyen tür, atlandı.")
                        ok = False

                    if ok:
                        self.success += 1
                    else:
                        self.failed += 1
                except Exception as exc:  # noqa: BLE001
                    self.failed += 1
                    self._log(f"  ✗ Hata: {exc}")

                self.ui_queue.put(("progress", idx))

            if self.cancel_event.is_set():
                summary = f"İptal edildi. Başarılı: {self.success}, Hatalı: {self.failed}, Kalan: {self.total_files - (self.success + self.failed)}"
            else:
                summary = f"Bitti. Başarılı: {self.success}, Hatalı: {self.failed}"
            self._log(summary)
        finally:
            try:
                if word:
                    word.Quit()
            except Exception:
                pass
            try:
                if excel:
                    excel.Quit()
            except Exception:
                pass
            pythoncom.CoUninitialize()
            self.ui_queue.put(("done", None))

    def _print_word(self, word, path: Path) -> bool:
        doc = None
        try:
            doc = word.Documents.Open(str(path))
            pages = doc.ComputeStatistics(2)
            self._log(f"  Sayfa sayısı: {pages}")
            doc.PrintOut(
                Background=False,
                Append=False,
                Range=0,  # wdPrintAllDocument
                OutputFileName="",
                From="",
                To="",
                Item=0,
                Copies=1,
                Pages="",
                PageType=0,  # wdPrintAllPages
                PrintToFile=False,
                Collate=True,
                ActivePrinterMacGX="",
                ManualDuplexPrint=True,  # çift yüz için yönergeli yazdırma
                PrintZoomColumn=0,
                PrintZoomRow=0,
                PrintZoomPaperWidth=0,
                PrintZoomPaperHeight=0,
            )
            self._log("  ✓ Word: Yazıcıya gönderildi.")
            return True
        finally:
            try:
                if doc:
                    doc.Close(False)
            except Exception:
                pass

    def _print_excel(self, excel, path: Path) -> bool:
        book = None
        try:
            book = excel.Workbooks.Open(str(path))
            sheet_count = book.Sheets.Count
            self._log(f"  Sayfa (sheet) sayısı: {sheet_count}")
            book.PrintOut(
                Copies=1,
                Collate=True,
                IgnorePrintAreas=False,
            )
            self._log("  ✓ Excel: Yazıcıya gönderildi.")
            return True
        finally:
            try:
                if book:
                    book.Close(False)
            except Exception:
                pass

    def _print_shell(self, win32api, path: Path) -> bool:
        # Varsayılan uygulama ile yazdırır (PDF ve resimler). Duplex/ayarlar yazıcıya bağlı.
        win32api.ShellExecute(0, "print", str(path), None, str(path.parent), 0)
        time.sleep(1.5)  # Gönderme tamamlanabilsin
        self._log("  ✓ Varsayılan uygulama ile yazdırma komutu gönderildi.")
        return True

    def _poll_queues(self) -> None:
        # Log kuyruğu
        while not self.log_queue.empty():
            msg = self.log_queue.get_nowait()
            self._append_log(msg)

        # UI güncellemeleri
        while not self.ui_queue.empty():
            kind, payload = self.ui_queue.get_nowait()
            if kind == "progress":
                idx = payload
                self.progress_var.set(idx)
                self.status_var.set(
                    f"İlerleme: {idx}/{self.total_files} | Başarılı: {self.success} | Hatalı: {self.failed}"
                )
            elif kind == "done":
                self.btn_start.config(state="normal")
                self.btn_cancel.config(state="disabled")
                if not self.cancel_event.is_set():
                    self.status_var.set("Tamamlandı.")
                else:
                    self.status_var.set("İptal edildi.")
        self.root.after(150, self._poll_queues)

    def _show_about(self) -> None:
        info = (
            "Toplu Yazdırma Aracı\n"
            "Programlayan: İbrahim Ertuğrul\n"
            "E-posta: muderrisibrahim@gmail.com\n"
            "\n"
            "Desteklenen türler:\n"
            "• Word (.doc/.docx)\n"
            "• Excel (.xls/.xlsx/.csv)\n"
            "• PDF\n"
            "• Resim (.png/.jpg/.bmp/.tif)\n"
        )
        messagebox.showinfo("Hakkında", info)

    def _log(self, message: str) -> None:
        self.log_queue.put(message)

    def _append_log(self, message: str) -> None:
        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", message + "\n")
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")

    def _on_close(self) -> None:
        if self.worker_thread and self.worker_thread.is_alive():
            if messagebox.askyesno("Devam Eden İşlem", "Yazdırma sürüyor. İptal edip çıkmak istiyor musunuz?"):
                self.cancel_event.set()
                self.root.after(500, self.root.destroy)
            else:
                return
        else:
            self.root.destroy()


def main() -> None:
    root = tk.Tk()
    app = WordPrinterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
