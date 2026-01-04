"""
Kelebek Sınav Sistemi - Model Sınıfları
Her varlık için nesne yönelimli yapı
"""

from typing import List, Optional, Dict
from dataclasses import dataclass, field
from datetime import datetime, date, time
import json

from utils import MIN_SINIF, MAX_SINIF, SINIF_SEVIYELERI


@dataclass
class Ogrenci:
    """Öğrenci model sınıfı"""
    ad: str
    soyad: str
    sinif: int  # 5-12 arası
    sube: str
    tc_no: Optional[str] = None
    sabit_mi: bool = False
    sabit_salon_id: Optional[int] = None
    sabit_salon_sira_id: Optional[int] = None
    aktif_mi: bool = True
    id: Optional[int] = None
    olusturma_tarihi: Optional[datetime] = None
    
    def __post_init__(self):
        """Validasyon ve normalizasyon"""
        self.ad = self.ad.strip().title()
        self.soyad = self.soyad.strip().upper()
        self.sube = self.sube.upper()
        
        if not MIN_SINIF <= self.sinif <= MAX_SINIF:
            raise ValueError(f"Sınıf {MIN_SINIF}-{MAX_SINIF} arasında olmalı!")
        
        if self.tc_no and len(self.tc_no) != 11:
            raise ValueError("TC No 11 haneli olmalı!")
    
    @property
    def tam_ad(self) -> str:
        """Tam ad döndür"""
        return f"{self.ad} {self.soyad}"
    
    @property
    def sinif_sube(self) -> str:
        """Sınıf-Şube formatı"""
        return f"{self.sinif}/{self.sube}"
    
    def to_dict(self) -> Dict:
        """Dictionary'e çevir (DB için)"""
        return {
            'id': self.id,
            'ad': self.ad,
            'soyad': self.soyad,
            'sinif': self.sinif,
            'sube': self.sube,
            'tc_no': self.tc_no,
            'sabit_mi': self.sabit_mi,
            'sabit_salon_id': self.sabit_salon_id,
            'sabit_salon_sira_id': self.sabit_salon_sira_id,
            'aktif_mi': self.aktif_mi
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Ogrenci':
        """Dictionary'den oluştur (DB'den okuma için)"""
        return cls(
            id=data.get('id'),
            ad=data['ad'],
            soyad=data['soyad'],
            sinif=data['sinif'],
            sube=data['sube'],
            tc_no=data.get('tc_no'),
            sabit_mi=bool(data.get('sabit_mi', False)),
            sabit_salon_id=data.get('sabit_salon_id'),
            sabit_salon_sira_id=data.get('sabit_salon_sira_id'),
            aktif_mi=bool(data.get('aktif_mi', True)),
            olusturma_tarihi=data.get('olusturma_tarihi')
        )
    
    def __str__(self) -> str:
        durum = "🔒 Sabit" if self.sabit_mi else "🔄 Mobil"
        return f"{self.tam_ad} ({self.sinif_sube}) - {durum}"
    
    def __repr__(self) -> str:
        return f"Ogrenci(id={self.id}, ad='{self.ad}', sinif={self.sinif}, sube='{self.sube}')"


@dataclass
class Ders:
    """Ders model sınıfı"""
    ders_adi: str
    sinif_seviyeleri: List[int]  # [5-12 arası]
    aktif_mi: bool = True
    id: Optional[int] = None
    olusturma_tarihi: Optional[datetime] = None
    
    def __post_init__(self):
        """Validasyon"""
        self.ders_adi = self.ders_adi.strip()
        
        if not self.sinif_seviyeleri:
            raise ValueError("En az bir sınıf seviyesi seçilmeli!")
        
        for sinif in self.sinif_seviyeleri:
            if not MIN_SINIF <= sinif <= MAX_SINIF:
                raise ValueError(f"Geçersiz sınıf seviyesi: {sinif}")
    
    @property
    def sinif_listesi_str(self) -> str:
        """Sınıf listesini string olarak döndür"""
        return ", ".join(map(str, sorted(self.sinif_seviyeleri)))
    
    def sinif_alabilir_mi(self, sinif: int) -> bool:
        """Belirtilen sınıf bu dersi alabiliyor mu?"""
        return sinif in self.sinif_seviyeleri
    
    def to_dict(self) -> Dict:
        """Dictionary'e çevir"""
        return {
            'id': self.id,
            'ders_adi': self.ders_adi,
            'sinif_seviyeleri': json.dumps(self.sinif_seviyeleri),
            'aktif_mi': self.aktif_mi
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Ders':
        """Dictionary'den oluştur"""
        sinif_seviyeleri = data['sinif_seviyeleri']
        if isinstance(sinif_seviyeleri, str):
            sinif_seviyeleri = json.loads(sinif_seviyeleri)
        
        return cls(
            id=data.get('id'),
            ders_adi=data['ders_adi'],
            sinif_seviyeleri=sinif_seviyeleri,
            aktif_mi=bool(data.get('aktif_mi', True)),
            olusturma_tarihi=data.get('olusturma_tarihi')
        )
    
    def __str__(self) -> str:
        return f"{self.ders_adi} (Sınıflar: {self.sinif_listesi_str})"
    
    def __repr__(self) -> str:
        return f"Ders(id={self.id}, ders_adi='{self.ders_adi}')"


@dataclass
class Sinav:
    """Sınav model sınıfı"""
    ders_id: int
    sinav_tarihi: date
    sinav_saati: time
    kacinci_ders: int
    ders_adi: Optional[str] = None  # JOIN için
    aktif_mi: bool = True
    id: Optional[int] = None
    olusturma_tarihi: Optional[datetime] = None
    
    def __post_init__(self):
        """Validasyon"""
        if not 1 <= self.kacinci_ders <= 10:
            raise ValueError("Ders numarası 1-10 arasında olmalı!")
        
        # String'leri uygun tiplere çevir
        if isinstance(self.sinav_tarihi, str):
            self.sinav_tarihi = datetime.strptime(self.sinav_tarihi, '%Y-%m-%d').date()
        
        if isinstance(self.sinav_saati, str):
            self.sinav_saati = datetime.strptime(self.sinav_saati, '%H:%M:%S').time()
    
    @property
    def tarih_str(self) -> str:
        """Tarih formatı"""
        return self.sinav_tarihi.strftime('%d.%m.%Y')
    
    @property
    def saat_str(self) -> str:
        """Saat formatı"""
        return self.sinav_saati.strftime('%H:%M')
    
    @property
    def tam_bilgi(self) -> str:
        """Sınav tam bilgisi"""
        ders = self.ders_adi or f"Ders#{self.ders_id}"
        return f"{ders} - {self.tarih_str} {self.saat_str} ({self.kacinci_ders}. Ders)"
    
    def to_dict(self) -> Dict:
        """Dictionary'e çevir"""
        return {
            'id': self.id,
            'ders_id': self.ders_id,
            'sinav_tarihi': self.sinav_tarihi.strftime('%Y-%m-%d'),
            'sinav_saati': self.sinav_saati.strftime('%H:%M:%S'),
            'kacinci_ders': self.kacinci_ders,
            'aktif_mi': self.aktif_mi
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Sinav':
        """Dictionary'den oluştur"""
        return cls(
            id=data.get('id'),
            ders_id=data['ders_id'],
            sinav_tarihi=data['sinav_tarihi'],
            sinav_saati=data['sinav_saati'],
            kacinci_ders=data['kacinci_ders'],
            ders_adi=data.get('ders_adi'),
            aktif_mi=bool(data.get('aktif_mi', True)),
            olusturma_tarihi=data.get('olusturma_tarihi')
        )
    
    def __str__(self) -> str:
        return self.tam_bilgi
    
    def __repr__(self) -> str:
        return f"Sinav(id={self.id}, ders_id={self.ders_id}, tarih={self.tarih_str})"


@dataclass
class Salon:
    """Salon model sınıfı"""
    salon_adi: str
    kapasite: int
    aktif_mi: bool = True
    id: Optional[int] = None
    olusturma_tarihi: Optional[datetime] = None
    
    def __post_init__(self):
        """Validasyon"""
        self.salon_adi = self.salon_adi.strip()
        
        if self.kapasite <= 0:
            raise ValueError("Kapasite 0'dan büyük olmalı!")
    
    def dolu_mu(self, mevcut_ogrenci_sayisi: int) -> bool:
        """Salon dolu mu?"""
        return mevcut_ogrenci_sayisi >= self.kapasite
    
    def kalan_kapasite(self, mevcut_ogrenci_sayisi: int) -> int:
        """Kalan kapasite"""
        return max(0, self.kapasite - mevcut_ogrenci_sayisi)
    
    def to_dict(self) -> Dict:
        """Dictionary'e çevir"""
        return {
            'id': self.id,
            'salon_adi': self.salon_adi,
            'kapasite': self.kapasite,
            'aktif_mi': self.aktif_mi
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Salon':
        """Dictionary'den oluştur"""
        return cls(
            id=data.get('id'),
            salon_adi=data['salon_adi'],
            kapasite=data['kapasite'],
            aktif_mi=bool(data.get('aktif_mi', True)),
            olusturma_tarihi=data.get('olusturma_tarihi')
        )
    
    def __str__(self) -> str:
        return f"{self.salon_adi} (Kapasite: {self.kapasite})"
    
    def __repr__(self) -> str:
        return f"Salon(id={self.id}, salon_adi='{self.salon_adi}', kapasite={self.kapasite})"


@dataclass
class SalonSira:
    """Salon sıra objesi"""
    salon_id: int
    sira_no: int
    id: Optional[int] = None
    etiket: Optional[str] = None
    aktif_mi: bool = True
    salon_adi: Optional[str] = None
    olusturma_tarihi: Optional[datetime] = None
    ogrenci_id: Optional[int] = None  # opsiyonel - JOIN için
    ogrenci_ad: Optional[str] = None
    ogrenci_soyad: Optional[str] = None

    @property
    def display_label(self) -> str:
        """Kullanıcıya gösterilecek sıra etiketi"""
        label = self.etiket.strip() if self.etiket else ""
        text = f"{self.sira_no:03d}"
        if label:
            text += f" - {label}"
        if self.ogrenci_ad and self.ogrenci_soyad:
            text += f" ({self.ogrenci_ad} {self.ogrenci_soyad})"
        return text

    @classmethod
    def from_dict(cls, data: Dict) -> 'SalonSira':
        return cls(
            id=data.get('id'),
            salon_id=data['salon_id'],
            sira_no=data['sira_no'],
            etiket=data.get('etiket'),
            aktif_mi=bool(data.get('aktif_mi', True)),
            salon_adi=data.get('salon_adi'),
            olusturma_tarihi=data.get('olusturma_tarihi'),
            ogrenci_id=data.get('ogrenci_id'),
            ogrenci_ad=data.get('ogrenci_ad'),
            ogrenci_soyad=data.get('ogrenci_soyad')
        )


@dataclass
class SabitOgrenciKonum:
    """Sabit öğrencinin salon ve sıra bilgisi"""
    ogrenci_id: int
    salon_id: int
    sira_no: int
    salon_adi: Optional[str] = None
    sira_id: Optional[int] = None
    sira_etiket: Optional[str] = None

    @property
    def display(self) -> str:
        salon = self.salon_adi or f"Salon#{self.salon_id}"
        etiket = f" - {self.sira_etiket}" if self.sira_etiket else ""
        return f"{salon} / Sıra {self.sira_no:03d}{etiket}"

@dataclass
class Gozetmen:
    """Gözetmen model sınıfı"""
    ad: str
    soyad: str
    email: Optional[str] = None
    telefon: Optional[str] = None
    aktif_mi: bool = True
    id: Optional[int] = None
    olusturma_tarihi: Optional[datetime] = None
    
    def __post_init__(self):
        """Validasyon ve normalizasyon"""
        self.ad = self.ad.strip().title()
        self.soyad = self.soyad.strip().upper()
    
    @property
    def tam_ad(self) -> str:
        """Tam ad döndür"""
        return f"{self.ad} {self.soyad}"
    
    @property
    def iletisim_bilgisi(self) -> str:
        """İletişim bilgisi"""
        bilgiler = []
        if self.email:
            bilgiler.append(f"📧 {self.email}")
        if self.telefon:
            bilgiler.append(f"📞 {self.telefon}")
        return " | ".join(bilgiler) if bilgiler else "İletişim bilgisi yok"
    
    def to_dict(self) -> Dict:
        """Dictionary'e çevir"""
        return {
            'id': self.id,
            'ad': self.ad,
            'soyad': self.soyad,
            'email': self.email,
            'telefon': self.telefon,
            'aktif_mi': self.aktif_mi
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Gozetmen':
        """Dictionary'den oluştur"""
        return cls(
            id=data.get('id'),
            ad=data['ad'],
            soyad=data['soyad'],
            email=data.get('email'),
            telefon=data.get('telefon'),
            aktif_mi=bool(data.get('aktif_mi', True)),
            olusturma_tarihi=data.get('olusturma_tarihi')
        )
    
    def __str__(self) -> str:
        return f"{self.tam_ad} - {self.iletisim_bilgisi}"
    
    def __repr__(self) -> str:
        return f"Gozetmen(id={self.id}, ad='{self.ad}', soyad='{self.soyad}')"


@dataclass
class SinavYerlesim:
    """Sınav yerleşim model sınıfı"""
    sinav_id: int
    ogrenci_id: int
    salon_id: int
    sira_no: int
    id: Optional[int] = None
    
    # JOIN için ek bilgiler
    ogrenci_ad: Optional[str] = None
    ogrenci_soyad: Optional[str] = None
    ogrenci_sinif: Optional[int] = None
    ogrenci_sube: Optional[str] = None
    salon_adi: Optional[str] = None
    
    @property
    def ogrenci_tam_ad(self) -> str:
        """Öğrenci tam adı"""
        if self.ogrenci_ad and self.ogrenci_soyad:
            return f"{self.ogrenci_ad} {self.ogrenci_soyad}"
        return f"Öğrenci#{self.ogrenci_id}"
    
    @property
    def konum_bilgisi(self) -> str:
        """Konum bilgisi"""
        salon = self.salon_adi or f"Salon#{self.salon_id}"
        return f"{salon} - Sıra: {self.sira_no}"
    
    def to_dict(self) -> Dict:
        """Dictionary'e çevir"""
        return {
            'id': self.id,
            'sinav_id': self.sinav_id,
            'ogrenci_id': self.ogrenci_id,
            'salon_id': self.salon_id,
            'sira_no': self.sira_no
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SinavYerlesim':
        """Dictionary'den oluştur"""
        return cls(
            id=data.get('id'),
            sinav_id=data['sinav_id'],
            ogrenci_id=data['ogrenci_id'],
            salon_id=data['salon_id'],
            sira_no=data['sira_no'],
            ogrenci_ad=data.get('ad'),
            ogrenci_soyad=data.get('soyad'),
            ogrenci_sinif=data.get('sinif'),
            ogrenci_sube=data.get('sube'),
            salon_adi=data.get('salon_adi')
        )
    
    def __str__(self) -> str:
        return f"{self.ogrenci_tam_ad} → {self.konum_bilgisi}"
    
    def __repr__(self) -> str:
        return f"SinavYerlesim(sinav_id={self.sinav_id}, ogrenci_id={self.ogrenci_id}, salon_id={self.salon_id})"


@dataclass
class SinifSube:
    """Belirli sınıf seviyesindeki tek bir şube."""
    sinif: int
    sube: str
    ogrenciler: List[Dict] = field(default_factory=list)

    def add_ogrenci(self, ogrenci: Dict) -> None:
        self.ogrenciler.append(ogrenci)

    @property
    def ogrenci_sayisi(self) -> int:
        return len(self.ogrenciler)


@dataclass
class SinifSeviye:
    """Belirli sınıf seviyesinin bütün şubelerini temsil eder."""
    sinif: int
    subeler: Dict[str, SinifSube] = field(default_factory=dict)

    def get_or_create_sube(self, sube: str) -> SinifSube:
        sube = sube.upper()
        if sube not in self.subeler:
            self.subeler[sube] = SinifSube(self.sinif, sube)
        return self.subeler[sube]

    def add_ogrenci(self, ogrenci: Dict) -> None:
        hedef = self.get_or_create_sube(ogrenci.get('sube', '?'))
        hedef.add_ogrenci(ogrenci)

    @property
    def toplam_sube(self) -> int:
        return len(self.subeler)

    @property
    def toplam_ogrenci(self) -> int:
        return sum(s.ogrenci_sayisi for s in self.subeler.values())


# Model Fabrika Fonksiyonları
def ogrenci_olustur(**kwargs) -> Ogrenci:
    """Öğrenci oluştur - helper fonksiyon"""
    return Ogrenci(**kwargs)

def ders_olustur(**kwargs) -> Ders:
    """Ders oluştur - helper fonksiyon"""
    return Ders(**kwargs)

def sinav_olustur(**kwargs) -> Sinav:
    """Sınav oluştur - helper fonksiyon"""
    return Sinav(**kwargs)

def salon_olustur(**kwargs) -> Salon:
    """Salon oluştur - helper fonksiyon"""
    return Salon(**kwargs)

def gozetmen_olustur(**kwargs) -> Gozetmen:
    """Gözetmen oluştur - helper fonksiyon"""
    return Gozetmen(**kwargs)


if __name__ == "__main__":
    # Test kodu
    print("🧪 Model Sınıfları Test Ediliyor...\n")
    
    # Öğrenci testi
    ogr = Ogrenci(ad="Ahmet", soyad="yılmaz", sinif=10, sube="a", tc_no="12345678901")
    print(f"✅ Öğrenci: {ogr}")
    print(f"   Tam Ad: {ogr.tam_ad}")
    print(f"   Sınıf/Şube: {ogr.sinif_sube}\n")
    
    # Ders testi
    ders = Ders(ders_adi="Matematik", sinif_seviyeleri=SINIF_SEVIYELERI)
    print(f"✅ Ders: {ders}")
    print(f"   11. sınıf alabilir mi? {ders.sinif_alabilir_mi(11)}\n")
    
    # Salon testi
    salon = Salon(salon_adi="A-101", kapasite=30)
    print(f"✅ Salon: {salon}")
    print(f"   Kalan kapasite (15 öğrenci var): {salon.kalan_kapasite(15)}\n")
    
    # Gözetmen testi
    goz = Gozetmen(ad="ayşe", soyad="demir", email="ayse@okul.com", telefon="555-1234")
    print(f"✅ Gözetmen: {goz}")
    print(f"   İletişim: {goz.iletisim_bilgisi}\n")
    
    print("🎉 Tüm model sınıfları başarıyla çalışıyor!")
