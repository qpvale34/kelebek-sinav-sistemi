"""
Kelebek Sınav Sistemi - Constants Modülü Unit Testleri
pytest ile çalıştırılır: python -m pytest tests/ -v
"""

import pytest
import sys
import os

# Path ayarı
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.constants import (
    SINIF_SEVIYELERI,
    SINIF_ISMI_PATTERN,
    MIN_SINIF,
    MAX_SINIF,
    sinif_ismi_gecerli_mi,
    sinif_seviyesinden_sayi
)


class TestSinifSeviyeleri:
    """SINIF_SEVIYELERI listesi testleri"""
    
    def test_sinif_seviyeleri_count(self):
        """Toplam sınıf seviyesi sayısı"""
        assert len(SINIF_SEVIYELERI) == 28
    
    def test_temel_siniflar_mevcut(self):
        """Temel sınıflar (5-12) listede mevcut"""
        for sinif in ["5", "6", "7", "8", "9", "10"]:
            assert sinif in SINIF_SEVIYELERI
    
    def test_brans_siniflari_mevcut(self):
        """Branş sınıfları listede mevcut"""
        branslar = ["11sayisal", "11sozel", "12sayisal", "12esitağirlik"]
        for brans in branslar:
            assert brans in SINIF_SEVIYELERI
    
    def test_hazirlik_siniflari_mevcut(self):
        """Hazırlık sınıfları listede mevcut"""
        hazirliklar = [
            "ortaokulhazirlikingilizce",
            "ortaokulhazirlikarapca",
            "lisehazirlikingilizce",
            "lisehazirlikarapca"
        ]
        for hazirlik in hazirliklar:
            assert hazirlik in SINIF_SEVIYELERI


class TestSinifIsmiGecerliMi:
    """sinif_ismi_gecerli_mi() fonksiyonu testleri"""
    
    def test_gecerli_sayisal_siniflar(self):
        """Sayısal sınıflar geçerli"""
        assert sinif_ismi_gecerli_mi("5") is True
        assert sinif_ismi_gecerli_mi("10") is True
        assert sinif_ismi_gecerli_mi("12") is True
    
    def test_gecerli_brans_siniflari(self):
        """Branş sınıfları geçerli"""
        assert sinif_ismi_gecerli_mi("11sayisal") is True
        assert sinif_ismi_gecerli_mi("12sozel") is True
        assert sinif_ismi_gecerli_mi("11esitağirlik") is True
    
    def test_gecerli_ozel_karakterler(self):
        """Tire ve alt çizgi geçerli"""
        assert sinif_ismi_gecerli_mi("hazirlik-ingilizce") is True
        assert sinif_ismi_gecerli_mi("lise_hazirlik") is True
        assert sinif_ismi_gecerli_mi("11-sayisal_A") is True
    
    def test_gecerli_turkce_karakterler(self):
        """Türkçe karakterler geçerli"""
        assert sinif_ismi_gecerli_mi("öğrenci") is True
        assert sinif_ismi_gecerli_mi("11şözel") is True
        assert sinif_ismi_gecerli_mi("çince") is True
    
    def test_gecersiz_bos_string(self):
        """Boş string geçersiz"""
        assert sinif_ismi_gecerli_mi("") is False
        assert sinif_ismi_gecerli_mi(None) is False
    
    def test_gecersiz_ozel_karakterler(self):
        """Özel karakterler geçersiz"""
        assert sinif_ismi_gecerli_mi("sinif@test") is False
        assert sinif_ismi_gecerli_mi("11#sayisal") is False
        assert sinif_ismi_gecerli_mi("5/A") is False
        assert sinif_ismi_gecerli_mi("sinif test") is False  # Boşluk
    
    def test_gecersiz_uzun_isim(self):
        """50 karakterden uzun isimler geçersiz"""
        uzun_isim = "a" * 51
        assert sinif_ismi_gecerli_mi(uzun_isim) is False
        
        # Tam 50 karakter geçerli
        sinir_isim = "a" * 50
        assert sinif_ismi_gecerli_mi(sinir_isim) is True


class TestSinifSeviyesindenSayi:
    """sinif_seviyesinden_sayi() fonksiyonu testleri"""
    
    def test_sayisal_siniflar(self):
        """Sayısal sınıflar doğru çevrilir"""
        assert sinif_seviyesinden_sayi("5") == 5
        assert sinif_seviyesinden_sayi("8") == 8
        assert sinif_seviyesinden_sayi("10") == 10
    
    def test_brans_siniflari(self):
        """Branş sınıfları doğru çevrilir"""
        assert sinif_seviyesinden_sayi("11sayisal") == 11
        assert sinif_seviyesinden_sayi("11sozel") == 11
        assert sinif_seviyesinden_sayi("12esitağirlik") == 12
    
    def test_hazirlik_siniflari(self):
        """Hazırlık sınıfları doğru çevrilir"""
        assert sinif_seviyesinden_sayi("ortaokulhazirlikingilizce") == 8
        assert sinif_seviyesinden_sayi("lisehazirlikingilizce") == 9
    
    def test_none_ve_bos(self):
        """None ve boş değerler 0 döner"""
        assert sinif_seviyesinden_sayi(None) == 0
        assert sinif_seviyesinden_sayi("") == 0


class TestMinMaxSinif:
    """MIN_SINIF ve MAX_SINIF sabitleri testleri"""
    
    def test_min_sinif_degeri(self):
        """MIN_SINIF doğru değer"""
        assert MIN_SINIF == 5
    
    def test_max_sinif_degeri(self):
        """MAX_SINIF doğru değer"""
        assert MAX_SINIF == 12


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
