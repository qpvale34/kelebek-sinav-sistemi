"""
Kelebek Sınav Sistemi - Geliştirilmiş Database Manager
Gözetmen atama ve gelişmiş sınav yönetimi
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any, Set
from contextlib import contextmanager
import os

from utils import MIN_SINIF, MAX_SINIF, get_user_data_path, ensure_user_data_dir
from models import SinifSeviye


class DatabaseManager:
    """Veritabanı bağlantılarını ve CRUD işlemlerini yöneten merkezi sınıf"""
    
    def __init__(self, db_path: str = None):
        # Frozen uygulama veya normal çalışma için doğru yolu belirle
        if db_path is None:
            self.db_path = get_user_data_path("database/kelebek.db")
        else:
            self.db_path = db_path
        self._ensure_database_directory()
        self._initialize_database()
        self._run_migrations()
    
    def _ensure_database_directory(self):
        """Database klasörünün var olduğundan emin ol"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

    
    @contextmanager
    def get_connection(self):
        """Context manager ile güvenli bağlantı yönetimi"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _initialize_database(self):
        """Tüm tabloları oluştur"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Öğrenciler Tablosu - sinif TEXT olarak (string sınıf desteği)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ogrenciler (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ad TEXT NOT NULL,
                    soyad TEXT NOT NULL,
                    sinif TEXT NOT NULL,
                    sube TEXT NOT NULL,
                    tc_no TEXT UNIQUE,
                    sabit_mi BOOLEAN DEFAULT 0,
                    aktif_mi BOOLEAN DEFAULT 1,
                    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Dersler Tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dersler (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ders_adi TEXT NOT NULL UNIQUE,
                    sinif_seviyeleri TEXT NOT NULL,
                    aktif_mi BOOLEAN DEFAULT 1,
                    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Sınavlar Tablosu (GÜNCELLENDİ - tarih/saat/ders_no artık zorunlu değil)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sinavlar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sinav_adi TEXT NOT NULL,
                    ders_id INTEGER NOT NULL,
                    sinav_tarihi DATE,
                    sinav_saati TIME,
                    kacinci_ders INTEGER,
                    secili_siniflar TEXT NOT NULL,
                    secili_salonlar TEXT NOT NULL,
                    soru_dosyasi_id INTEGER,
                    aktif_mi BOOLEAN DEFAULT 1,
                    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ders_id) REFERENCES dersler(id) ON DELETE CASCADE,
                    FOREIGN KEY (soru_dosyasi_id) REFERENCES soru_bankasi(id) ON DELETE SET NULL
                )
            """)
            
            # Salonlar Tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS salonlar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    salon_adi TEXT NOT NULL UNIQUE,
                    kapasite INTEGER NOT NULL,
                    aktif_mi BOOLEAN DEFAULT 1,
                    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CHECK (kapasite > 0)
                )
            """)

            # Salon Sıra Tanımları
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS salon_sira (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    salon_id INTEGER NOT NULL,
                    sira_no INTEGER NOT NULL,
                    etiket TEXT,
                    aktif_mi BOOLEAN DEFAULT 1,
                    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (salon_id) REFERENCES salonlar(id) ON DELETE CASCADE,
                    UNIQUE(salon_id, sira_no)
                )
            """)
            
            # Gözetmenler Tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gozetmenler (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ad TEXT NOT NULL,
                    soyad TEXT NOT NULL,
                    email TEXT,
                    telefon TEXT,
                    aktif_mi BOOLEAN DEFAULT 1,
                    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Sınav Yerleşim Tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sinav_yerlesim (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sinav_id INTEGER NOT NULL,
                    ogrenci_id INTEGER NOT NULL,
                    salon_id INTEGER NOT NULL,
                    sira_no INTEGER NOT NULL,
                    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sinav_id) REFERENCES sinavlar(id) ON DELETE CASCADE,
                    FOREIGN KEY (ogrenci_id) REFERENCES ogrenciler(id) ON DELETE CASCADE,
                    FOREIGN KEY (salon_id) REFERENCES salonlar(id) ON DELETE CASCADE,
                    UNIQUE(sinav_id, ogrenci_id),
                    UNIQUE(sinav_id, salon_id, sira_no)
                )
            """)
            
            # Gözetmen Atama Tablosu (GÜNCELLENDİ)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gozetmen_atama (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sinav_id INTEGER NOT NULL,
                    gozetmen_id INTEGER NOT NULL,
                    salon_id INTEGER NOT NULL,
                    gorev_turu TEXT DEFAULT 'asil',
                    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sinav_id) REFERENCES sinavlar(id) ON DELETE CASCADE,
                    FOREIGN KEY (gozetmen_id) REFERENCES gozetmenler(id) ON DELETE CASCADE,
                    FOREIGN KEY (salon_id) REFERENCES salonlar(id) ON DELETE CASCADE,
                    CHECK (gorev_turu IN ('asil', 'yedek'))
                )
            """)
            
            # Soru Bankası Tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS soru_bankasi (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ders_id INTEGER NOT NULL,
                    dosya_adi TEXT NOT NULL,
                    orjinal_dosya TEXT NOT NULL,
                    mime_tipi TEXT,
                    dosya_yolu TEXT NOT NULL,
                    aciklama TEXT,
                    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ders_id) REFERENCES dersler(id) ON DELETE CASCADE
                )
            """)
            
            # Eski veritabanları için kolon kontrolü
            self._ensure_column(cursor, "sinavlar", "soru_dosyasi_id", "INTEGER")
            self._ensure_column(cursor, "ogrenciler", "sabit_salon_id", "INTEGER")
            self._ensure_column(cursor, "ogrenciler", "sabit_salon_sira_id", "INTEGER")
            
            # İndeksler
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ogrenci_sinif ON ogrenciler(sinif, sube)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sinav_tarih ON sinavlar(sinav_tarihi)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_yerlesim_sinav ON sinav_yerlesim(sinav_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_gozetmen_sinav ON gozetmen_atama(sinav_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_salon_sira_salon ON salon_sira(salon_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ogrenci_sabit_salon ON ogrenciler(sabit_salon_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ogrenci_sabit_sira ON ogrenciler(sabit_salon_sira_id)")

            self._ensure_salon_siralari(cursor)
            
            conn.commit()

    def _ensure_column(self, cursor, table: str, column: str, definition: str):
        """Var olmayan kolonları tabloya ekle"""
        cursor.execute(f"PRAGMA table_info({table})")
        existing = [row[1] if isinstance(row, tuple) else row['name'] for row in cursor.fetchall()]
        if column not in existing:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def _ensure_salon_siralari(self, cursor):
        """Tüm salonlar için sıra kayıtlarının oluşturulduğundan emin ol"""
        cursor.execute("SELECT id, kapasite FROM salonlar")
        salonlar = cursor.fetchall()
        for salon in salonlar:
            salon_id = salon['id'] if isinstance(salon, sqlite3.Row) else salon[0]
            kapasite = salon['kapasite'] if isinstance(salon, sqlite3.Row) else salon[1]
            if not kapasite:
                continue
            self._sync_salon_sira_for(cursor, salon_id, kapasite)

    def _sync_salon_sira_for(self, cursor, salon_id: int, kapasite: int):
        """Belirli salon için sıra kayıtlarını kapasite ile senkronize et"""
        if kapasite <= 0:
            return
        cursor.execute("SELECT id, sira_no, aktif_mi FROM salon_sira WHERE salon_id = ?", (salon_id,))
        mevcut = cursor.fetchall()
        mevcut_map = {}
        for row in mevcut:
            row_id = row['id'] if isinstance(row, sqlite3.Row) else row[0]
            sira_no = row['sira_no'] if isinstance(row, sqlite3.Row) else row[1]
            aktif_mi = row['aktif_mi'] if isinstance(row, sqlite3.Row) else row[2]
            mevcut_map[sira_no] = {'id': row_id, 'aktif_mi': aktif_mi}
        cursor.execute("""
            SELECT sabit_salon_sira_id FROM ogrenciler
            WHERE sabit_salon_id = ? AND sabit_salon_sira_id IS NOT NULL
        """, (salon_id,))
        dolu_sira_ids = {row['sabit_salon_sira_id'] if isinstance(row, sqlite3.Row) else row[0]
                         for row in cursor.fetchall()}
        # Eksik sırayı ekle veya pasif olanı aktifleştir
        for sira_no in range(1, kapasite + 1):
            mevcut_kayit = mevcut_map.get(sira_no)
            if mevcut_kayit:
                if not mevcut_kayit['aktif_mi']:
                    cursor.execute("UPDATE salon_sira SET aktif_mi = 1 WHERE id = ?",
                                   (mevcut_kayit['id'],))
                continue
            cursor.execute("""
                INSERT INTO salon_sira (salon_id, sira_no, aktif_mi)
                VALUES (?, ?, 1)
            """, (salon_id, sira_no))
        # Kapasite dışındaki sırayı pasifleştir (boşta ise)
        for sira_no, data in mevcut_map.items():
            if sira_no <= kapasite:
                continue
            if data['id'] in dolu_sira_ids:
                continue
            cursor.execute("UPDATE salon_sira SET aktif_mi = 0 WHERE id = ?", (data['id'],))

    def _run_migrations(self):
        """Şema güncellemelerini uygula"""
        self._migrate_sinif_to_text()  # ÖNCE: sinif kolonunu TEXT yap
        self._migrate_ogrenci_sinif_kisit()
        self._repair_sinav_yerlesim_fk()
    
    def _migrate_sinif_to_text(self):
        """
        Mevcut veritabanındaki sinif kolonunu INTEGER'dan TEXT'e dönüştür.
        CHECK kısıtını kaldırır - string sınıf isimleri desteklenir.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sql FROM sqlite_master
                WHERE type='table' AND name='ogrenciler'
            """)
            row = cursor.fetchone()
            if not row or not row['sql']:
                return
            
            tablo_sql = row['sql']
            
            # Zaten TEXT ise veya CHECK yoksa atla
            if 'sinif TEXT' in tablo_sql and 'CHECK' not in tablo_sql:
                return
            
            # INTEGER veya CHECK varsa migration yap
            if 'sinif INTEGER' in tablo_sql or 'CHECK' in tablo_sql:
                try:
                    cursor.execute("PRAGMA foreign_keys=off;")
                    
                    # Geçici tablo oluştur
                    cursor.execute("ALTER TABLE ogrenciler RENAME TO ogrenciler_backup;")
                    
                    # Yeni tablo - sinif TEXT, CHECK yok
                    cursor.execute("""
                        CREATE TABLE ogrenciler (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            ad TEXT NOT NULL,
                            soyad TEXT NOT NULL,
                            sinif TEXT NOT NULL,
                            sube TEXT NOT NULL,
                            tc_no TEXT UNIQUE,
                            sabit_mi BOOLEAN DEFAULT 0,
                            aktif_mi BOOLEAN DEFAULT 1,
                            olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            sabit_salon_id INTEGER,
                            sabit_salon_sira_id INTEGER
                        )
                    """)
                    
                    # Verileri aktar (sinif'i TEXT'e çevir)
                    cursor.execute("""
                        INSERT INTO ogrenciler 
                        (id, ad, soyad, sinif, sube, tc_no, sabit_mi, aktif_mi, olusturma_tarihi)
                        SELECT id, ad, soyad, CAST(sinif AS TEXT), sube, tc_no, sabit_mi, aktif_mi, olusturma_tarihi
                        FROM ogrenciler_backup
                    """)
                    
                    # Eski tabloyu sil
                    cursor.execute("DROP TABLE ogrenciler_backup;")
                    
                    # Sequence'i gücelle
                    cursor.execute("SELECT MAX(id) AS max_id FROM ogrenciler")
                    max_row = cursor.fetchone()
                    if max_row and max_row['max_id'] is not None:
                        cursor.execute("""
                            INSERT OR REPLACE INTO sqlite_sequence(name, seq)
                            VALUES ('ogrenciler', ?)
                        """, (max_row['max_id'],))
                    
                    # İndeks oluştur
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ogrenci_sinif ON ogrenciler(sinif, sube)")
                    
                    print("✅ Veritabanı migrated: sinif kolonu TEXT yapıldı, CHECK kısıtı kaldırıldı")
                finally:
                    cursor.execute("PRAGMA foreign_keys=on;")

    def _migrate_ogrenci_sinif_kisit(self):
        """
        Eski migration - artık kullanılmıyor (_migrate_sinif_to_text yerine geçti)
        Geriye uyumluluk için boş bırakıldı.
        """
        pass

    def _repair_sinav_yerlesim_fk(self):
        """Sinav yerleşim tablosundaki ogrenciler_old veya ogrenciler_backup referansını düzelt"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sql FROM sqlite_master
                WHERE type='table' AND name='sinav_yerlesim'
            """)
            row = cursor.fetchone()
            if not row or not row['sql']:
                return
            tablo_sql = row['sql']
            
            # Hem ogrenciler_old hem de ogrenciler_backup referanslarını kontrol et
            needs_repair = 'ogrenciler_old' in tablo_sql or 'ogrenciler_backup' in tablo_sql
            if not needs_repair:
                return
            
            try:
                cursor.execute("PRAGMA foreign_keys=off;")
                cursor.execute("ALTER TABLE sinav_yerlesim RENAME TO sinav_yerlesim_temp;")
                cursor.execute("""
                    CREATE TABLE sinav_yerlesim (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sinav_id INTEGER NOT NULL,
                        ogrenci_id INTEGER NOT NULL,
                        salon_id INTEGER NOT NULL,
                        sira_no INTEGER NOT NULL,
                        olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (sinav_id) REFERENCES sinavlar(id) ON DELETE CASCADE,
                        FOREIGN KEY (ogrenci_id) REFERENCES ogrenciler(id) ON DELETE CASCADE,
                        FOREIGN KEY (salon_id) REFERENCES salonlar(id) ON DELETE CASCADE,
                        UNIQUE(sinav_id, ogrenci_id),
                        UNIQUE(sinav_id, salon_id, sira_no)
                    )
                """)
                cursor.execute("""
                    INSERT INTO sinav_yerlesim (id, sinav_id, ogrenci_id, salon_id, sira_no, olusturma_tarihi)
                    SELECT id, sinav_id, ogrenci_id, salon_id, sira_no, olusturma_tarihi
                    FROM sinav_yerlesim_temp
                """)
                cursor.execute("DROP TABLE sinav_yerlesim_temp;")
                print("✅ sinav_yerlesim tablosu tamir edildi")
            finally:
                cursor.execute("PRAGMA foreign_keys=on;")
    
    # ==================== ÖĞRENCİ İŞLEMLERİ ====================
    
    def ogrenci_ekle(self, ad: str, soyad: str, sinif: str, sube: str, 
                     tc_no: Optional[str] = None, sabit_mi: bool = False) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ogrenciler (ad, soyad, sinif, sube, tc_no, sabit_mi)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (ad.strip().title(), soyad.strip().upper(), sinif, sube.strip(), tc_no, sabit_mi))
            return cursor.lastrowid
    
    def ogrenci_toplu_ekle(self, ogrenci_listesi: List[Dict]) -> int:
        eklenen = 0
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for ogr in ogrenci_listesi:
                try:
                    cursor.execute("""
                        INSERT INTO ogrenciler (ad, soyad, sinif, sube, tc_no, sabit_mi)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        ogr['ad'].strip().title(),
                        ogr['soyad'].strip().upper(),
                        ogr['sinif'],  # String olarak sakla
                        ogr['sube'].strip(),  # Olduğu gibi sakla
                        ogr.get('tc_no'),
                        ogr.get('sabit_mi', False)
                    ))
                    eklenen += 1
                except sqlite3.IntegrityError:
                    continue
        return eklenen
    
    def ogrenci_guncelle(self, ogrenci_id: int, **kwargs) -> bool:
        allowed_fields = ['ad', 'soyad', 'sinif', 'sube', 'tc_no', 'sabit_mi', 'aktif_mi',
                          'sabit_salon_id', 'sabit_salon_sira_id']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return False
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [ogrenci_id]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE ogrenciler SET {set_clause} WHERE id = ?", values)
            return cursor.rowcount > 0
    
    def ogrenci_sil(self, ogrenci_id: int) -> bool:
        return self.ogrenci_guncelle(ogrenci_id, aktif_mi=False)
    
    def ogrencileri_toplu_sil(self) -> int:
        """Tüm aktif öğrencileri pasife al"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM ogrenciler WHERE aktif_mi = 1")
            aktif_sayisi = cursor.fetchone()[0] or 0
            if aktif_sayisi == 0:
                return 0
            cursor.execute("""
                UPDATE ogrenciler
                SET aktif_mi = 0,
                    sabit_salon_id = NULL,
                    sabit_salon_sira_id = NULL
                WHERE aktif_mi = 1
            """)
            return aktif_sayisi
    
    def ogrenci_getir(self, ogrenci_id: int) -> Optional[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ogrenciler WHERE id = ? AND aktif_mi = 1", (ogrenci_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def ogrencileri_listele(self, sinif: Optional[int] = None, sube: Optional[str] = None,
                           sabit_mi: Optional[bool] = None, siniflar: Optional[List[int]] = None,
                           limit: Optional[int] = None, offset: int = 0) -> List[Dict]:
        """Öğrencileri filtreli listele - sinif-sube formatını da destekler
        
        Args:
            sinif: Tek bir sınıf seviyesi filtresi
            sube: Şube filtresi
            sabit_mi: Sabit öğrenci filtresi
            siniflar: Çoklu sınıf listesi (örn: ["5", "6-A", "10-B"])
            limit: Döndürülecek maksimum kayıt sayısı (None = sınırsız)
            offset: Atlanacak kayıt sayısı (pagination için)
        """
        query = "SELECT * FROM ogrenciler WHERE aktif_mi = 1"
        params = []
        
        if sinif is not None:
            query += " AND sinif = ?"
            params.append(sinif)
        
        if siniflar is not None and len(siniflar) > 0:
            # sinif-sube formatını kontrol et (örn: "5-A", "10-B")
            sinif_sube_pairs = []
            plain_siniflar = []
            
            for s in siniflar:
                s_str = str(s)
                if '-' in s_str:
                    # sinif-sube formatı
                    parts = s_str.rsplit('-', 1)
                    if len(parts) == 2:
                        sinif_sube_pairs.append((parts[0], parts[1]))
                else:
                    plain_siniflar.append(s_str)
            
            conditions = []
            
            # Sadece sınıf olanlar
            if plain_siniflar:
                placeholders = ','.join('?' * len(plain_siniflar))
                conditions.append(f"sinif IN ({placeholders})")
                params.extend(plain_siniflar)
            
            # sinif-sube çiftleri için
            for sinif_val, sube_val in sinif_sube_pairs:
                conditions.append("(sinif = ? AND sube = ?)")
                params.append(sinif_val)
                params.append(sube_val)
            
            if conditions:
                query += " AND (" + " OR ".join(conditions) + ")"
        
        if sube is not None:
            query += " AND sube = ?"
            params.append(sube.strip())
        
        if sabit_mi is not None:
            query += " AND sabit_mi = ?"
            params.append(sabit_mi)
        
        query += " ORDER BY sinif, sube, soyad, ad"
        
        # Pagination
        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params.append(limit)
            params.append(offset)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def ogrenci_sayisi(self, sinif: Optional[int] = None, sube: Optional[str] = None,
                       sabit_mi: Optional[bool] = None, siniflar: Optional[List[int]] = None) -> int:
        """Filtrelenmiş öğrenci sayısını döndür (pagination için toplam sayı)"""
        query = "SELECT COUNT(*) as count FROM ogrenciler WHERE aktif_mi = 1"
        params = []
        
        if sinif is not None:
            query += " AND sinif = ?"
            params.append(sinif)
        
        if siniflar is not None and len(siniflar) > 0:
            sinif_sube_pairs = []
            plain_siniflar = []
            
            for s in siniflar:
                s_str = str(s)
                if '-' in s_str:
                    parts = s_str.rsplit('-', 1)
                    if len(parts) == 2:
                        sinif_sube_pairs.append((parts[0], parts[1]))
                else:
                    plain_siniflar.append(s_str)
            
            conditions = []
            
            if plain_siniflar:
                placeholders = ','.join('?' * len(plain_siniflar))
                conditions.append(f"sinif IN ({placeholders})")
                params.extend(plain_siniflar)
            
            for sinif_val, sube_val in sinif_sube_pairs:
                conditions.append("(sinif = ? AND sube = ?)")
                params.append(sinif_val)
                params.append(sube_val)
            
            if conditions:
                query += " AND (" + " OR ".join(conditions) + ")"
        
        if sube is not None:
            query += " AND sube = ?"
            params.append(sube.strip())
        
        if sabit_mi is not None:
            query += " AND sabit_mi = ?"
            params.append(sabit_mi)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return row['count'] if row else 0

    def sinif_hiyerarsisi(self) -> List[SinifSeviye]:
        """Tüm öğrencileri sınıf/şube hiyerarşisine dönüştür."""
        ogrenciler = self.ogrencileri_listele()
        seviyeler: Dict[int, SinifSeviye] = {}
        for ogr in ogrenciler:
            sinif = str(ogr['sinif'])  # String olarak işle
            seviye = seviyeler.setdefault(sinif, SinifSeviye(sinif))
            seviye.add_ogrenci(ogr)
        return [seviyeler[key] for key in sorted(seviyeler.keys())]
    
    def benzersiz_siniflar(self) -> List[str]:
        """
        Veritabanındaki öğrencilerden benzersiz sınıf listesini döndür.
        Sıralı olarak döner (önce sayılar, sonra string'ler).
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT sinif FROM ogrenciler 
                WHERE aktif_mi = 1 
                ORDER BY sinif
            """)
            rows = cursor.fetchall()
            
            siniflar = [str(row['sinif']) for row in rows]
            
            # Sayısal ve metin sınıfları ayır ve sırala
            sayisal = []
            metin = []
            for s in siniflar:
                if s.isdigit():
                    sayisal.append((int(s), s))
                else:
                    metin.append(s)
            
            # Önce sayısal (küçükten büyüğe), sonra metin (alfabetik)
            sayisal.sort(key=lambda x: x[0])
            metin.sort()
            
            return [s[1] for s in sayisal] + metin
    
    def benzersiz_sinif_sube(self) -> List[str]:
        """
        Veritabanındaki öğrencilerden benzersiz sınıf-şube kombinasyonlarını döndür.
        Format: "5-A", "11sayısal-B" gibi
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT sinif, sube FROM ogrenciler 
                WHERE aktif_mi = 1 
                ORDER BY sinif, sube
            """)
            rows = cursor.fetchall()
            
            kombinasyonlar = []
            for row in rows:
                sinif = str(row['sinif'])
                sube = str(row['sube'])
                kombinasyonlar.append(f"{sinif}-{sube}")
            
            # Sıralama: önce sayısal sınıflar, sonra metin sınıflar
            def sort_key(item):
                parts = item.split('-', 1)
                sinif = parts[0]
                sube = parts[1] if len(parts) > 1 else ''
                if sinif.isdigit():
                    return (0, int(sinif), sube)
                else:
                    return (1, sinif, sube)
            
            kombinasyonlar.sort(key=sort_key)
            return kombinasyonlar
    
    # ==================== DERS İŞLEMLERİ ====================
    
    def ders_ekle(self, ders_adi: str, sinif_seviyeleri: List[int]) -> int:
        """
        Ders ekle. Aynı isimde silinmiş ders varsa reaktif et.
        """
        sinif_json = json.dumps(sinif_seviyeleri)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Aynı isimde silinmiş ders var mı kontrol et
            cursor.execute("""
                SELECT id FROM dersler WHERE ders_adi = ? AND aktif_mi = 0
            """, (ders_adi.strip(),))
            existing = cursor.fetchone()
            
            if existing:
                # Silinmiş dersi reaktif et ve bilgilerini güncelle
                cursor.execute("""
                    UPDATE dersler SET aktif_mi = 1, sinif_seviyeleri = ?
                    WHERE id = ?
                """, (sinif_json, existing['id']))
                return existing['id']
            else:
                # Yeni ders ekle
                cursor.execute("""
                    INSERT INTO dersler (ders_adi, sinif_seviyeleri)
                    VALUES (?, ?)
                """, (ders_adi.strip(), sinif_json))
                return cursor.lastrowid
    
    def ders_guncelle(self, ders_id: int, ders_adi: Optional[str] = None, 
                      sinif_seviyeleri: Optional[List[int]] = None) -> bool:
        updates = []
        params = []
        
        if ders_adi:
            updates.append("ders_adi = ?")
            params.append(ders_adi.strip())
        if sinif_seviyeleri:
            updates.append("sinif_seviyeleri = ?")
            params.append(json.dumps(sinif_seviyeleri))
        
        if not updates:
            return False
        
        params.append(ders_id)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE dersler SET {', '.join(updates)} WHERE id = ?", params)
            return cursor.rowcount > 0
    
    def ders_sil(self, ders_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE dersler SET aktif_mi = 0 WHERE id = ?", (ders_id,))
            return cursor.rowcount > 0
    
    def dersleri_listele(self) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM dersler WHERE aktif_mi = 1 ORDER BY ders_adi")
            rows = cursor.fetchall()
            return [{**dict(row), 'sinif_seviyeleri': json.loads(row['sinif_seviyeleri'])} 
                    for row in rows]
    
    def ders_getir(self, ders_id: int) -> Optional[Dict]:
        """YENİ: Tek ders getir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM dersler WHERE id = ? AND aktif_mi = 1", (ders_id,))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                result['sinif_seviyeleri'] = json.loads(result['sinif_seviyeleri'])
                return result
            return None
    
    # ==================== SINAV İŞLEMLERİ ====================
    
    def sinav_ekle(self, sinav_adi: str, ders_id: int,
                   secili_siniflar: List[int],
                   secili_salonlar: Optional[List[int]] = None,
                   soru_dosyasi_id: Optional[int] = None) -> int:
        """Sınav ekleme - tarih/saat/ders_no kaldırıldı"""
        siniflar_json = json.dumps(secili_siniflar or [])
        salonlar_json = json.dumps(secili_salonlar or [])
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sinavlar (sinav_adi, ders_id, sinav_tarihi, sinav_saati, 
                                     kacinci_ders, secili_siniflar, secili_salonlar, soru_dosyasi_id)
                VALUES (?, ?, NULL, NULL, NULL, ?, ?, ?)
            """, (sinav_adi, ders_id, siniflar_json, salonlar_json, soru_dosyasi_id))
            return cursor.lastrowid
    
    def sinav_getir(self, sinav_id: int) -> Optional[Dict]:
        """YENİ: Detaylı sınav bilgisi getir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, d.ders_adi,
                       sb.dosya_adi AS soru_dosyasi_adi,
                       sb.dosya_yolu AS soru_dosyasi_yolu,
                       sb.orjinal_dosya AS soru_dosyasi_orjinal
                FROM sinavlar s
                JOIN dersler d ON s.ders_id = d.id
                LEFT JOIN soru_bankasi sb ON s.soru_dosyasi_id = sb.id
                WHERE s.id = ? AND s.aktif_mi = 1
            """, (sinav_id,))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                result['secili_siniflar'] = json.loads(result['secili_siniflar'])
                result['secili_salonlar'] = json.loads(result['secili_salonlar'])
                if row['soru_dosyasi_adi']:
                    result['soru_dosyasi'] = {
                        'id': row['soru_dosyasi_id'],
                        'dosya_adi': row['soru_dosyasi_adi'],
                        'dosya_yolu': row['soru_dosyasi_yolu'],
                        'orjinal_dosya': row['soru_dosyasi_orjinal']
                    }
                else:
                    result['soru_dosyasi'] = None
                return result
            return None

    def sinav_sil(self, sinav_id: int) -> bool:
        """Sınavı pasifleştir ve ilişkili kayıtları temizle"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Önce sınavı pasifleştir ve sonucu kaydet
            cursor.execute("UPDATE sinavlar SET aktif_mi = 0 WHERE id = ?", (sinav_id,))
            guncellendi = cursor.rowcount > 0
            # İlişkili kayıtları temizle (başarı durumuna bağlı değil)
            cursor.execute("DELETE FROM sinav_yerlesim WHERE sinav_id = ?", (sinav_id,))
            cursor.execute("DELETE FROM gozetmen_atama WHERE sinav_id = ?", (sinav_id,))
            return guncellendi

    def sinav_soru_dosyasi_guncelle(self, sinav_id: int,
                                    soru_dosyasi_id: Optional[int]) -> bool:
        """Seçili sınavın soru dosyasını güncelle"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE sinavlar SET soru_dosyasi_id = ? WHERE id = ? AND aktif_mi = 1",
                (soru_dosyasi_id, sinav_id)
            )
            return cursor.rowcount > 0
    
    def sinavlari_listele(self, tarih_baslangic: Optional[str] = None,
                         tarih_bitis: Optional[str] = None) -> List[Dict]:
        """Sınavları listele"""
        query = """
            SELECT s.*, d.ders_adi,
                   sb.dosya_adi AS soru_dosyasi_adi,
                   sb.dosya_yolu AS soru_dosyasi_yolu,
                   sb.orjinal_dosya AS soru_dosyasi_orjinal
            FROM sinavlar s
            JOIN dersler d ON s.ders_id = d.id
            LEFT JOIN soru_bankasi sb ON s.soru_dosyasi_id = sb.id
            WHERE s.aktif_mi = 1
        """
        params = []
        
        if tarih_baslangic:
            query += " AND s.sinav_tarihi >= ?"
            params.append(tarih_baslangic)
        if tarih_bitis:
            query += " AND s.sinav_tarihi <= ?"
            params.append(tarih_bitis)
        
        query += " ORDER BY s.sinav_tarihi, s.sinav_saati"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                result['secili_siniflar'] = json.loads(result['secili_siniflar'])
                result['secili_salonlar'] = json.loads(result['secili_salonlar'])
                if row['soru_dosyasi_adi']:
                    result['soru_dosyasi'] = {
                        'id': row['soru_dosyasi_id'],
                        'dosya_adi': row['soru_dosyasi_adi'],
                        'dosya_yolu': row['soru_dosyasi_yolu'],
                        'orjinal_dosya': row['soru_dosyasi_orjinal']
                    }
                else:
                    result['soru_dosyasi'] = None
                results.append(result)
            return results
    
    def harmanlanmis_sinavlar(self) -> List[Dict]:
        """Yerleşimi kaydedilmiş sınavları listele"""
        query = """
            SELECT s.*, d.ders_adi,
                   sb.dosya_adi AS soru_dosyasi_adi,
                   sb.dosya_yolu AS soru_dosyasi_yolu,
                   sb.orjinal_dosya AS soru_dosyasi_orjinal
            FROM sinavlar s
            JOIN dersler d ON s.ders_id = d.id
            LEFT JOIN soru_bankasi sb ON s.soru_dosyasi_id = sb.id
            WHERE s.aktif_mi = 1
              AND EXISTS (SELECT 1 FROM sinav_yerlesim sy WHERE sy.sinav_id = s.id)
            ORDER BY s.sinav_tarihi, s.sinav_saati
        """
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                result['secili_siniflar'] = json.loads(result['secili_siniflar'])
                result['secili_salonlar'] = json.loads(result['secili_salonlar'])
                if row['soru_dosyasi_adi']:
                    result['soru_dosyasi'] = {
                        'id': row['soru_dosyasi_id'],
                        'dosya_adi': row['soru_dosyasi_adi'],
                        'dosya_yolu': row['soru_dosyasi_yolu'],
                        'orjinal_dosya': row['soru_dosyasi_orjinal']
                    }
                else:
                    result['soru_dosyasi'] = None
                results.append(result)
            return results
    
    def sinav_salonlari_getir(self, sinav_id: int) -> List[Dict]:
        """YENİ: Sınava ait salonları getir"""
        sinav = self.sinav_getir(sinav_id)
        if not sinav:
            return []
        
        salon_ids = sinav['secili_salonlar']
        if not salon_ids:
            return []
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ','.join('?' * len(salon_ids))
            cursor.execute(f"""
                SELECT * FROM salonlar 
                WHERE id IN ({placeholders}) AND aktif_mi = 1
                ORDER BY salon_adi
            """, salon_ids)
            return [dict(row) for row in cursor.fetchall()]

    # ==================== SORU BANKASI ====================
    
    def soru_bankasi_ekle(self, ders_id: int, dosya_adi: str, orjinal_dosya: str,
                           dosya_yolu: str, mime_tipi: Optional[str] = None,
                           aciklama: Optional[str] = None) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO soru_bankasi (ders_id, dosya_adi, orjinal_dosya, mime_tipi, dosya_yolu, aciklama)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (ders_id, dosya_adi.strip(), orjinal_dosya.strip(),
                  mime_tipi, dosya_yolu, aciklama))
            return cursor.lastrowid
    
    def soru_bankasi_listele(self, ders_id: Optional[int] = None) -> List[Dict]:
        query = """
            SELECT sb.*, d.ders_adi
            FROM soru_bankasi sb
            JOIN dersler d ON sb.ders_id = d.id
            ORDER BY sb.olusturma_tarihi DESC
        """
        params: List[Any] = []
        
        if ders_id:
            query = """
                SELECT sb.*, d.ders_adi
                FROM soru_bankasi sb
                JOIN dersler d ON sb.ders_id = d.id
                WHERE sb.ders_id = ?
                ORDER BY sb.olusturma_tarihi DESC
            """
            params.append(ders_id)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def soru_bankasi_getir(self, dosya_id: int) -> Optional[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sb.*, d.ders_adi
                FROM soru_bankasi sb
                JOIN dersler d ON sb.ders_id = d.id
                WHERE sb.id = ?
            """, (dosya_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def soru_bankasi_sil(self, dosya_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM soru_bankasi WHERE id = ?", (dosya_id,))
            return cursor.rowcount > 0
    
    # ==================== SALON İŞLEMLERİ ====================
    
    def salon_ekle(self, salon_adi: str, kapasite: int) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO salonlar (salon_adi, kapasite)
                VALUES (?, ?)
            """, (salon_adi.strip(), kapasite))
            salon_id = cursor.lastrowid
            self._sync_salon_sira_for(cursor, salon_id, kapasite)
            return salon_id
    
    def salon_guncelle(self, salon_id: int, salon_adi: Optional[str] = None,
                       kapasite: Optional[int] = None, aktif_mi: Optional[bool] = None) -> bool:
        updates = []
        params = []
        
        if salon_adi:
            updates.append("salon_adi = ?")
            params.append(salon_adi.strip())
        if kapasite:
            updates.append("kapasite = ?")
            params.append(kapasite)
        if aktif_mi is not None:
            updates.append("aktif_mi = ?")
            params.append(aktif_mi)
        
        if not updates:
            return False
        
        params.append(salon_id)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE salonlar SET {', '.join(updates)} WHERE id = ?", params)
            if kapasite is not None:
                self._sync_salon_sira_for(cursor, salon_id, kapasite)
            return cursor.rowcount > 0
    
    def salonlari_listele(self) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM salonlar WHERE aktif_mi = 1 ORDER BY salon_adi")
            return [dict(row) for row in cursor.fetchall()]

    def salon_sira_durumlari(self, salon_id: int) -> List[Dict]:
        """Belirli salonun sıra listesini ve doluluk durumunu döndür"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    ss.*,
                    o.id AS ogrenci_id,
                    o.ad AS ogrenci_ad,
                    o.soyad AS ogrenci_soyad,
                    o.sabit_mi AS ogrenci_sabit
                FROM salon_sira ss
                LEFT JOIN ogrenciler o ON o.sabit_salon_sira_id = ss.id AND o.aktif_mi = 1
                WHERE ss.salon_id = ?
                ORDER BY ss.sira_no
            """, (salon_id,))
            return [dict(row) for row in cursor.fetchall()]

    def salon_sira_guncelle(self, sira_id: int, **kwargs) -> bool:
        """Sıra kaydı güncelle"""
        allowed = ['sira_no', 'etiket', 'aktif_mi']
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return False
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        params = list(updates.values())
        params.append(sira_id)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE salon_sira SET {set_clause} WHERE id = ?", params)
            return cursor.rowcount > 0

    def salon_sira_haritasi(self, salon_ids: List[int]) -> Dict[int, List[Dict]]:
        """Seçili salonlar için sıra objelerini harita olarak döndür"""
        if not salon_ids:
            return {}
        placeholders = ','.join('?' * len(salon_ids))
        query = f"""
            SELECT ss.*, s.salon_adi
            FROM salon_sira ss
            JOIN salonlar s ON ss.salon_id = s.id
            WHERE ss.salon_id IN ({placeholders})
              AND ss.aktif_mi = 1
            ORDER BY ss.salon_id, ss.sira_no
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, salon_ids)
            sonuc: Dict[int, List[Dict]] = {}
            for row in cursor.fetchall():
                data = dict(row)
                sonuc.setdefault(data['salon_id'], []).append(data)
            return sonuc

    def salon_sira_sahibi(self, sira_id: int, exclude_ogrenci_id: Optional[int] = None) -> Optional[Dict]:
        """Bir sıranın mevcut sahibini döndür"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            params: List[Any] = [sira_id]
            query = """
                SELECT id, ad, soyad
                FROM ogrenciler
                WHERE sabit_salon_sira_id = ? AND aktif_mi = 1
            """
            if exclude_ogrenci_id:
                query += " AND id != ?"
                params.append(exclude_ogrenci_id)
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # ==================== GÖZETMEN İŞLEMLERİ ====================
    
    def gozetmen_ekle(self, ad: str, soyad: str, email: Optional[str] = None,
                      telefon: Optional[str] = None) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO gozetmenler (ad, soyad, email, telefon)
                VALUES (?, ?, ?, ?)
            """, (ad.strip().title(), soyad.strip().upper(), email, telefon))
            return cursor.lastrowid
    
    def gozetmen_toplu_ekle(self, gozetmen_listesi: List[Dict]) -> int:
        eklenen = 0
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for goz in gozetmen_listesi:
                try:
                    cursor.execute("""
                        INSERT INTO gozetmenler (ad, soyad, email, telefon)
                        VALUES (?, ?, ?, ?)
                    """, (
                        goz['ad'].strip().title(),
                        goz['soyad'].strip().upper(),
                        goz.get('email'),
                        goz.get('telefon')
                    ))
                    eklenen += 1
                except:
                    continue
        return eklenen
    
    def gozetmen_guncelle(self, gozetmen_id: int, **kwargs) -> bool:
        """YENİ: Gözetmen güncelleme"""
        allowed_fields = ['ad', 'soyad', 'email', 'telefon', 'aktif_mi']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return False
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [gozetmen_id]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE gozetmenler SET {set_clause} WHERE id = ?", values)
            return cursor.rowcount > 0
    
    def gozetmenleri_listele(self) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM gozetmenler WHERE aktif_mi = 1 ORDER BY soyad, ad")
            return [dict(row) for row in cursor.fetchall()]
    
    def musait_gozetmenler(self, sinav_id: int) -> List[Dict]:
        """YENİ: Bu sınavda henüz atanmamış gözetmenleri listele"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT g.* FROM gozetmenler g
                WHERE g.aktif_mi = 1
                AND g.id NOT IN (
                    SELECT gozetmen_id FROM gozetmen_atama 
                    WHERE sinav_id = ?
                )
                ORDER BY g.soyad, g.ad
            """, (sinav_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== GÖZETMEN ATAMA İŞLEMLERİ ====================
    
    def gozetmen_ata(self, sinav_id: int, gozetmen_id: int, 
                     salon_id: int, gorev_turu: str = 'asil') -> int:
        """YENİ: Gözetmen atama"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO gozetmen_atama (sinav_id, gozetmen_id, salon_id, gorev_turu)
                VALUES (?, ?, ?, ?)
            """, (sinav_id, gozetmen_id, salon_id, gorev_turu))
            return cursor.lastrowid
    
    def gozetmen_atamalari_listele(self, sinav_id: int) -> List[Dict]:
        """YENİ: Sınava ait gözetmen atamalarını listele"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    ga.*,
                    g.ad, g.soyad, g.email, g.telefon,
                    s.salon_adi
                FROM gozetmen_atama ga
                JOIN gozetmenler g ON ga.gozetmen_id = g.id
                JOIN salonlar s ON ga.salon_id = s.id
                WHERE ga.sinav_id = ?
                ORDER BY s.salon_adi, ga.gorev_turu
            """, (sinav_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def gozetmen_atama_sil(self, atama_id: int) -> bool:
        """YENİ: Gözetmen atamasını sil"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM gozetmen_atama WHERE id = ?", (atama_id,))
            return cursor.rowcount > 0
    
    def gozetmen_atamalarini_temizle(self, sinav_id: int) -> bool:
        """YENİ: Sınava ait tüm gözetmen atamalarını temizle"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM gozetmen_atama WHERE sinav_id = ?", (sinav_id,))
            return True
    
    # ==================== SINAV YERLEŞİM İŞLEMLERİ ====================
    
    def yerlesim_kaydet(self, sinav_id: int, yerlesim_data: List[Dict]) -> bool:
        """Harmanlama sonucu yerleşimi kaydet"""
        if sinav_id is None:
            raise ValueError("sinav_id boş olamaz")
        
        temiz_liste: List[Dict] = []
        seat_seen: Set[Tuple[int, int]] = set()
        ogrenci_seen: Set[int] = set()
        for yer in yerlesim_data:
            if yer.get('ogrenci_id') is None or yer.get('salon_id') is None or yer.get('sira_no') is None:
                continue
            if yer.get('sinav_id') not in (None, sinav_id):
                continue
            seat_key = (yer['salon_id'], yer['sira_no'])
            ogr_key = yer['ogrenci_id']
            if seat_key in seat_seen or ogr_key in ogrenci_seen:
                continue
            seat_seen.add(seat_key)
            ogrenci_seen.add(ogr_key)
            temiz_liste.append(yer)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Önce mevcut yerleşimi temizle
            cursor.execute("DELETE FROM sinav_yerlesim WHERE sinav_id = ?", (sinav_id,))
            
            # Yeni yerleşimi ekle
            for yer in temiz_liste:
                cursor.execute("""
                    INSERT OR REPLACE INTO sinav_yerlesim (sinav_id, ogrenci_id, salon_id, sira_no)
                    VALUES (?, ?, ?, ?)
                """, (sinav_id, yer['ogrenci_id'], yer['salon_id'], yer['sira_no']))
            
            return True

    def yerlesim_toplu_kaydet(self, yerlesim_data: List[Dict]) -> bool:
        """Birden fazla sınava ait yerleşimleri aynı anda kaydet"""
        if not yerlesim_data:
            return False
        grouped: Dict[int, List[Dict]] = {}
        for yer in yerlesim_data:
            sinav_id = yer.get('sinav_id')
            if sinav_id is None:
                continue
            grouped.setdefault(sinav_id, []).append(yer)
        if not grouped:
            return False
        for sinav_id, kayitlar in grouped.items():
            self.yerlesim_kaydet(sinav_id, kayitlar)
        return True
    
    def yerlesim_getir(self, sinav_id: int) -> List[Dict]:
        """Sınav yerleşimini getir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    sy.*,
                    o.ad, o.soyad, o.sinif, o.sube,
                    s.salon_adi
                FROM sinav_yerlesim sy
                JOIN ogrenciler o ON sy.ogrenci_id = o.id
                JOIN salonlar s ON sy.salon_id = s.id
                WHERE sy.sinav_id = ?
                ORDER BY s.salon_adi, sy.sira_no
            """, (sinav_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    # Alias for backwards compatibility
    def yerlesim_listele(self, sinav_id: int) -> List[Dict]:
        """yerlesim_getir için alias"""
        return self.yerlesim_getir(sinav_id)
    
    def tum_yerlesimleri_listele(self) -> List[Dict]:
        """Tüm sınavlar için tüm yerleşimleri getir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    sy.*,
                    o.ad, o.soyad, o.sinif, o.sube,
                    s.salon_adi,
                    sinav.sinav_adi,
                    sinav.sinav_tarihi,
                    sinav.sinav_saati
                FROM sinav_yerlesim sy
                JOIN ogrenciler o ON sy.ogrenci_id = o.id
                JOIN salonlar s ON sy.salon_id = s.id
                JOIN sinavlar sinav ON sy.sinav_id = sinav.id
                ORDER BY sinav.sinav_tarihi, sinav.sinav_saati, s.salon_adi, sy.sira_no
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== YARDIMCI FONKSİYONLAR ====================
    
    def istatistikler(self) -> Dict[str, int]:
        """Genel sistem istatistikleri"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM ogrenciler WHERE aktif_mi = 1")
            toplam_ogrenci = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM ogrenciler WHERE aktif_mi = 1 AND sabit_mi = 1")
            sabit_ogrenci = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM dersler WHERE aktif_mi = 1")
            toplam_ders = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM salonlar WHERE aktif_mi = 1")
            toplam_salon = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(kapasite) FROM salonlar WHERE aktif_mi = 1")
            toplam_kapasite = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT COUNT(*) FROM gozetmenler WHERE aktif_mi = 1")
            toplam_gozetmen = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM soru_bankasi")
            toplam_soru_dosyasi = cursor.fetchone()[0]
            
            return {
                'toplam_ogrenci': toplam_ogrenci,
                'sabit_ogrenci': sabit_ogrenci,
                'mobil_ogrenci': toplam_ogrenci - sabit_ogrenci,
                'toplam_ders': toplam_ders,
                'toplam_salon': toplam_salon,
                'toplam_kapasite': toplam_kapasite,
                'toplam_gozetmen': toplam_gozetmen,
                'toplam_soru_dosyasi': toplam_soru_dosyasi
            }


# Singleton pattern için global instance
_db_instance = None

def get_db() -> DatabaseManager:
    """Global database instance'ını getir (Singleton)"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance
