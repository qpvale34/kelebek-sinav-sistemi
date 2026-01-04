"""Kelebek Sınav Sistemi genel sabitleri."""

import re

# Eski sayısal sınıf aralığı (geriye uyumluluk için)
MIN_SINIF = 5
MAX_SINIF = 12

# Öğretmen masası baz numarası
TEACHER_DESK_BASE = 900000

# CP-SAT kısıtları
CP_SAT_FORBID_SAME_GRADE_ADJACENT = True  # Aynı sınıf seviyesini yan yana oturtma yasağı

# Sınıf ismi validasyon regex'i
# Harfler, sayılar, Türkçe karakterler ve işaretler (-_) kabul eder
SINIF_ISMI_PATTERN = re.compile(r'^[a-zA-Z0-9çğıöşüÇĞİÖŞÜ\-_]+$')


def sinif_ismi_gecerli_mi(sinif_str: str) -> bool:
    """
    Sınıf isminin geçerli olup olmadığını kontrol eder.
    
    Geçerli karakterler:
    - Harfler (a-z, A-Z, Türkçe karakterler)
    - Sayılar (0-9)
    - İşaretler (-, _)
    
    Args:
        sinif_str: Kontrol edilecek sınıf ismi
        
    Returns:
        bool: Geçerliyse True, değilse False
    """
    if not sinif_str or len(sinif_str) > 50:
        return False
    return bool(SINIF_ISMI_PATTERN.match(sinif_str))

# Genişletilmiş sınıf seviyeleri (string tabanlı)
# Ortaokul, lise hazırlık ve branş sınıfları dahil
SINIF_SEVIYELERI = [
    # Ortaokul seviyeleri
    "5", "6", "7", "8",
    # Ortaokul hazırlık programları
    "ortaokulhazirlikingilizce", "ortaokulhazirlikarapca",
    # Lise hazırlık programları
    "lisehazirlikingilizce", "lisehazirlikarapca",
    # Lise 9-10. sınıflar
    "9", "10",
    # 11. sınıf branşları
    "11sayisal", "11esitağirlik", "11sozel",
    "11ingilizce", "11arapca", "11korece", "11rusca", "11cince", "11japonca",
    # 12. sınıf branşları
    "12sayisal", "12esitağirlik", "12sozel",
    "12ingilizce", "12arapca", "12korece", "12rusca", "12cince", "12japonca",
]

# Sayısal sınıfları ayıklamak için yardımcı fonksiyon
def sinif_seviyesinden_sayi(sinif_str):
    """
    Sınıf seviyesinden sayısal değer çıkar.
    Örn: "11sayisal" -> 11, "5" -> 5, "ortaokulhazirlikingilizce" -> 5
    """
    if sinif_str is None:
        return 0
    sinif_str = str(sinif_str).strip()
    # Doğrudan sayısal ise
    if sinif_str.isdigit():
        return int(sinif_str)
    # 11/12 branşları
    if sinif_str.startswith("11"):
        return 11
    if sinif_str.startswith("12"):
        return 12
    # Hazırlık sınıfları
    if sinif_str.startswith("ortaokulhazirlika") or sinif_str.startswith("ortaokulhazirliking"):
        return 8  # Ortaokul hazırlık 8. sınıf seviyesinde kabul edilir
    if sinif_str.startswith("lisehazirlik"):
        return 9  # Lise hazırlık 9. sınıf seviyesinde kabul edilir
    return 0


__all__ = [
    "MIN_SINIF",
    "MAX_SINIF",
    "SINIF_SEVIYELERI",
    "SINIF_ISMI_PATTERN",
    "TEACHER_DESK_BASE",
    "CP_SAT_FORBID_SAME_GRADE_ADJACENT",
    "sinif_seviyesinden_sayi",
    "sinif_ismi_gecerli_mi",
]

