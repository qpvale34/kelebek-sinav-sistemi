"""
Kelebek Sınav Sistemi - EXE Derleme Scripti

Bu script PyInstaller kullanarak uygulamayı tek dosya EXE'ye dönüştürür.
Kullanım: python build_exe.py

Gereksinimler:
- PyInstaller: pip install pyinstaller
- Tüm proje bağımlılıkları: pip install -r requirements.txt
"""

import subprocess
import sys
import os
import shutil
from datetime import datetime


def check_pyinstaller():
    """PyInstaller'ın yüklü olup olmadığını kontrol et."""
    try:
        import PyInstaller
        print(f"✅ PyInstaller {PyInstaller.__version__} bulundu")
        return True
    except ImportError:
        print("❌ PyInstaller bulunamadı!")
        print("   Yüklemek için: pip install pyinstaller")
        return False


def check_dependencies():
    """Gerekli bağımlılıkları kontrol et."""
    required = [
        ('pandas', 'pandas'),
        ('openpyxl', 'openpyxl'),
        ('PIL', 'Pillow'),
        ('reportlab', 'reportlab'),
        ('tkcalendar', 'tkcalendar'),
        ('ortools', 'ortools'),
        ('pypdf', 'pypdf'),
        ('docx', 'python-docx'),
    ]
    
    missing = []
    for import_name, package_name in required:
        try:
            __import__(import_name)
            print(f"  ✓ {package_name}")
        except ImportError:
            print(f"  ✗ {package_name} (EKSİK)")
            missing.append(package_name)
    
    if missing:
        print(f"\n❌ Eksik paketler: {', '.join(missing)}")
        print(f"   Yüklemek için: pip install {' '.join(missing)}")
        return False
    
    print("✅ Tüm bağımlılıklar mevcut")
    return True


def clean_build():
    """Önceki build dosyalarını temizle."""
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"  Temizleniyor: {dir_name}/")
            shutil.rmtree(dir_name, ignore_errors=True)
    print("✅ Temizlik tamamlandı")


def build_exe():
    """PyInstaller ile EXE oluştur."""
    spec_file = 'kelebek_sinav_sistemi.spec'
    
    if not os.path.exists(spec_file):
        print(f"❌ Spec dosyası bulunamadı: {spec_file}")
        return False
    
    print(f"\n🔨 Derleme başlıyor...")
    print(f"   Spec dosyası: {spec_file}")
    print("-" * 50)
    
    # PyInstaller'ı çalıştır
    result = subprocess.run(
        [sys.executable, '-m', 'PyInstaller', spec_file, '--clean', '--noconfirm'],
        capture_output=False,
        text=True
    )
    
    if result.returncode != 0:
        print(f"\n❌ Derleme başarısız! (Çıkış kodu: {result.returncode})")
        return False
    
    # Sonucu kontrol et
    exe_path = os.path.join('dist', 'Kelebek_Sinav_Sistemi.exe')
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"\n✅ Derleme başarılı!")
        print(f"   Dosya: {os.path.abspath(exe_path)}")
        print(f"   Boyut: {size_mb:.2f} MB")
        return True
    else:
        print(f"\n❌ EXE dosyası oluşturulamadı!")
        return False


def copy_database():
    """Mevcut veritabanını dist klasörüne kopyala."""
    src_db = os.path.join('database', 'kelebek.db')
    dst_dir = os.path.join('dist', 'database')
    dst_db = os.path.join(dst_dir, 'kelebek.db')
    
    if os.path.exists(src_db):
        os.makedirs(dst_dir, exist_ok=True)
        shutil.copy2(src_db, dst_db)
        print(f"✅ Veritabanı kopyalandı: {dst_db}")
        return True
    else:
        print(f"ℹ️  Mevcut veritabanı bulunamadı, yeni oluşturulacak")
        return True


def main():
    """Ana fonksiyon."""
    print("=" * 60)
    print("🦋 KELEBEK SINAV SİSTEMİ - EXE DERLEYİCİ")
    print("=" * 60)
    print(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Proje dizinine geç
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"📂 Çalışma dizini: {os.getcwd()}")
    print()
    
    # Kontroller
    print("📋 Bağımlılıklar kontrol ediliyor...")
    if not check_pyinstaller():
        return 1
    
    print()
    if not check_dependencies():
        return 1
    
    print()
    print("🧹 Önceki build temizleniyor...")
    clean_build()
    
    # Derleme
    if not build_exe():
        return 1
    
    # Veritabanı kopyalama
    print()
    print("📦 Veritabanı hazırlanıyor...")
    copy_database()
    
    # Tamamlandı
    print()
    print("=" * 60)
    print("🎉 İŞLEM TAMAMLANDI!")
    print("=" * 60)
    print(f"\nÇalıştırmak için: dist\\Kelebek_Sinav_Sistemi.exe")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
