"""
Kelebek Sınav Sistemi - Kaynak Yol Yönetimi

PyInstaller ile frozen uygulama ve normal Python çalıştırması için
dosya yollarını yöneten yardımcı modül.
"""

import sys
import os
from typing import Optional


def is_frozen() -> bool:
    """
    Uygulamanın PyInstaller frozen EXE olarak çalışıp çalışmadığını kontrol eder.
    
    Returns:
        bool: Frozen uygulama ise True, değilse False
    """
    return getattr(sys, 'frozen', False)


def get_base_path() -> str:
    """
    Uygulama temel dizinini döndürür.
    
    Frozen modda: _MEIPASS (geçici dizin)
    Normal modda: Proje kök dizini
    
    Returns:
        str: Temel dizin yolu
    """
    if is_frozen():
        # PyInstaller frozen uygulama - geçici dizin
        return sys._MEIPASS
    else:
        # Normal Python çalıştırması - proje kök dizini
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_resource_path(relative_path: str) -> str:
    """
    Paketlenmiş kaynak dosyalarının yolunu döndürür.
    
    Bu fonksiyon assets, views, controllers gibi uygulama ile birlikte
    dağıtılan dosyalar için kullanılır.
    
    Args:
        relative_path: Kaynağın proje köküne göre göreli yolu
                       Örn: 'assets/styles.py', 'views/anasayfa.py'
    
    Returns:
        str: Kaynağın mutlak yolu
    
    Example:
        >>> icon_path = get_resource_path('assets/kelebek.ico')
        >>> style_path = get_resource_path('assets/styles.py')
    """
    base_path = get_base_path()
    return os.path.join(base_path, relative_path)


def get_user_data_path(relative_path: str = "") -> str:
    """
    Kullanıcı verileri için yazılabilir dizin yolunu döndürür.
    
    Bu fonksiyon veritabanı, log dosyaları, kullanıcı ayarları gibi
    çalışma zamanında oluşturulan/değiştirilen dosyalar için kullanılır.
    
    Frozen modda: EXE dosyasının bulunduğu dizin
    Normal modda: Proje kök dizini
    
    Args:
        relative_path: İstenilen dosya/klasörün göreli yolu
                       Örn: 'database/kelebek.db', 'logs/app.log'
    
    Returns:
        str: Kullanıcı veri dosyasının mutlak yolu
    
    Example:
        >>> db_path = get_user_data_path('database/kelebek.db')
        >>> log_dir = get_user_data_path('logs')
    """
    if is_frozen():
        # Frozen modda executable dizini
        base_path = os.path.dirname(sys.executable)
    else:
        # Normal modda proje kök dizini
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    if relative_path:
        return os.path.join(base_path, relative_path)
    return base_path


def ensure_user_data_dir(relative_dir: str) -> str:
    """
    Kullanıcı veri dizininin var olduğundan emin olur, yoksa oluşturur.
    
    Args:
        relative_dir: Oluşturulacak dizinin göreli yolu
                      Örn: 'database', 'logs', 'exports'
    
    Returns:
        str: Oluşturulan/var olan dizinin mutlak yolu
    
    Example:
        >>> db_dir = ensure_user_data_dir('database')
        >>> log_dir = ensure_user_data_dir('logs')
    """
    dir_path = get_user_data_path(relative_dir)
    os.makedirs(dir_path, exist_ok=True)
    return dir_path


def get_app_info() -> dict:
    """
    Uygulama çalışma ortamı bilgilerini döndürür.
    
    Returns:
        dict: Uygulama bilgileri
            - frozen: bool - Frozen uygulama mı
            - base_path: str - Temel dizin
            - user_data_path: str - Kullanıcı veri dizini
            - executable: str - Çalıştırılabilir dosya yolu
    """
    return {
        'frozen': is_frozen(),
        'base_path': get_base_path(),
        'user_data_path': get_user_data_path(),
        'executable': sys.executable
    }


# Test amaçlı
if __name__ == "__main__":
    print("=" * 50)
    print("Resource Helper Test")
    print("=" * 50)
    
    info = get_app_info()
    for key, value in info.items():
        print(f"{key}: {value}")
    
    print("\nÖrnek yollar:")
    print(f"Database: {get_user_data_path('database/kelebek.db')}")
    print(f"Assets: {get_resource_path('assets')}")
