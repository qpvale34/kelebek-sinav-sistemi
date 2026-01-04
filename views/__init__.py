# ============================================
# Dosya: views/__init__.py
"""Kelebek Sınav Sistemi - Views Paketi"""

from .anasayfa import AnasayfaView
from .ogrenci_ekle import OgrenciEkleView
from .ders_ekle import DersEkleView
from .salon_ekle import SalonEkleView
from .gozetmen_ekle import GozetmenEkleView
from .sabit_ogrenci import SabitOgrenciView
from .sinav_ekle import SinavEkleView
from .soru_bankasi import SoruBankasiView
from .harmanlama_view import HarmanlamaView
from .sinif_bilgilendirme import SinifBilgilendirmeView

__all__ = [
    'AnasayfaView',
    'OgrenciEkleView',
    'DersEkleView',
    'SalonEkleView',
    'GozetmenEkleView',
    'SabitOgrenciView',
    'SinavEkleView',
    'SoruBankasiView',
    'HarmanlamaView',
    'SinifBilgilendirmeView'
]
