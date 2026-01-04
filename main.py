"""
Kelebek Sınav Sistemi - Ana Program
Versiyon: 1.0
Geliştirici: İBRAHİM ERTUĞRUL
Tarih: 2025
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os

# Path ayarı
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from views.anasayfa import AnasayfaView
    from controllers.database_manager import get_db
    from assets.styles import KelebekTheme
except ImportError as e:
    print(f"❌ Import hatası: {e}")
    print("\n📁 Lütfen aşağıdaki dosya yapısının doğru olduğundan emin olun:")
    print("""
    kelebek_sinav_sistemi/
    ├── main.py
    ├── views/
    │   ├── __init__.py
    │   └── anasayfa.py
    ├── controllers/
    │   ├── __init__.py
    │   └── database_manager.py
    └── assets/
        ├── __init__.py
        └── styles.py
    """)
    input("\nDevam etmek için Enter'a basın...")
    sys.exit(1)


def check_dependencies():
    """Gerekli kütüphaneleri kontrol et"""
    missing = []
    
    required_packages = [
        ('pandas', 'pandas'),
        ('openpyxl', 'openpyxl'),
        ('PIL', 'Pillow'),
        ('reportlab', 'reportlab'),
        ('tkcalendar', 'tkcalendar')
    ]
    
    for import_name, package_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package_name)
    
    if missing:
        error_msg = f"""
❌ Eksik Kütüphaneler Tespit Edildi!

Aşağıdaki kütüphaneler yüklü değil:
{chr(10).join(f'  • {pkg}' for pkg in missing)}

Kurulum için şu komutu çalıştırın:
pip install {' '.join(missing)}

Veya:
pip install -r requirements.txt
        """
        print(error_msg)
        
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Eksik Kütüphaneler", error_msg)
        return False
    
    return True


def initialize_database():
    """Veritabanını başlat ve test et"""
    try:
        db = get_db()
        stats = db.istatistikler()
        print(f"✅ Veritabanı bağlantısı başarılı!")
        print(f"   • Öğrenci: {stats['toplam_ogrenci']}")
        print(f"   • Ders: {stats['toplam_ders']}")
        print(f"   • Salon: {stats['toplam_salon']}")
        return True
    except Exception as e:
        error_msg = f"""
❌ Veritabanı Hatası!

Hata: {str(e)}

Çözüm:
1. 'database' klasörünün var olduğundan emin olun
2. Yazma izinlerini kontrol edin
3. Disk alanının yeterli olduğundan emin olun
        """
        print(error_msg)
        
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Veritabanı Hatası", error_msg)
        return False


def splash_screen(root):
    """Splash ekranı göster"""
    splash = tk.Toplevel(root)
    splash.title("")
    splash.geometry("500x300")
    splash.overrideredirect(True)  # Başlık çubuğunu kaldır
    
    # Ekranın ortasına getir
    splash.update_idletasks()
    x = (splash.winfo_screenwidth() // 2) - (500 // 2)
    y = (splash.winfo_screenheight() // 2) - (300 // 2)
    splash.geometry(f"500x300+{x}+{y}")
    
    # Arka plan
    splash.config(bg=KelebekTheme.PRIMARY)
    
    # Logo ve metin
    tk.Label(
        splash,
        text=f"{KelebekTheme.ICON_BUTTERFLY}",
        font=(KelebekTheme.FONT_FAMILY, 80),
        bg=KelebekTheme.PRIMARY,
        fg=KelebekTheme.TEXT_WHITE
    ).pack(pady=(40, 10))
    
    tk.Label(
        splash,
        text="KELEBEK SİSTEMİ",
        font=(KelebekTheme.FONT_FAMILY, 24, "bold"),
        bg=KelebekTheme.PRIMARY,
        fg=KelebekTheme.TEXT_WHITE
    ).pack()
    
    tk.Label(
        splash,
        text="Öğrenci Yerleştirme ve Harmanlama Sistemi",
        font=(KelebekTheme.FONT_FAMILY, 12),
        bg=KelebekTheme.PRIMARY,
        fg=KelebekTheme.TEXT_LIGHT
    ).pack(pady=5)
    
    tk.Label(
        splash,
        text="Yükleniyor...",
        font=(KelebekTheme.FONT_FAMILY, 10),
        bg=KelebekTheme.PRIMARY,
        fg=KelebekTheme.TEXT_LIGHT
    ).pack(pady=(30, 10))
    
    # Progress bar
    progress_frame = tk.Frame(splash, bg=KelebekTheme.PRIMARY)
    progress_frame.pack(pady=10)
    canvas = tk.Canvas(progress_frame, width=300, height=20, bg=KelebekTheme.BG_DARK, highlightthickness=0)
    canvas.pack()
    
    def animate_progress(step=0):
        if step <= 300:
            canvas.delete("progress")
            canvas.create_rectangle(0, 0, step, 20, fill=KelebekTheme.SUCCESS, tags="progress")
            splash.after(5, lambda: animate_progress(step + 10))
        else:
            splash.after(200, lambda: splash.destroy())
    
    animate_progress()
    return splash


def main():
    """Ana fonksiyon"""
    print("=" * 60)
    print(f"{KelebekTheme.ICON_BUTTERFLY} KELEBEK SİSTEMİ")
    print("=" * 60)
    print("\n🚀 Sistem başlatılıyor...\n")
    
    print("📦 Kütüphaneler kontrol ediliyor...")
    if not check_dependencies():
        input("\nProgramdan çıkmak için Enter'a basın...")
        return
    print("✅ Tüm kütüphaneler mevcut!\n")
    
    print("💾 Veritabanı bağlantısı kontrol ediliyor...")
    if not initialize_database():
        input("\nProgramdan çıkmak için Enter'a basın...")
        return
    print()
    
    print("🎨 Arayüz başlatılıyor...\n")
    root = tk.Tk()
    root.withdraw()
    splash = splash_screen(root)
    root.wait_window(splash)
    root.deiconify()
    
    try:
        app = AnasayfaView(root)
        print("✅ Sistem hazır!\n")
        print("=" * 60)
        print("ℹ️  Programı kapatmak için pencereyi kapatın.")
        print("=" * 60)
        root.mainloop()
    except Exception as e:
        error_msg = f"""
❌ Program Hatası!

Beklenmeyen bir hata oluştu:
{str(e)}

Lütfen loglara bakın veya geliştiriciye bildirin.
        """
        print(error_msg)
        messagebox.showerror("Program Hatası", error_msg)
        import traceback
        traceback.print_exc()
    finally:
        print("\n👋 Program kapatılıyor...")
        print("Teşekkürler!\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Program kullanıcı tarafından durduruldu.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Kritik hata: {e}")
        import traceback
        traceback.print_exc()
        input("\nDevam etmek için Enter'a basın...")
        sys.exit(1)
