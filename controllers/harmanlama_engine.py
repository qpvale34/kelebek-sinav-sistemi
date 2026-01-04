"""
Kelebek Sınav Sistemi - Harmanlama Engine
Öğrencileri salonlara yerleştiren algoritma motoru
"""

import math
import random
import sys
import os
from typing import List, Dict, Optional, Tuple, Any, Set
from collections import defaultdict, deque
from dataclasses import dataclass

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import SINIF_SEVIYELERI, CP_SAT_FORBID_SAME_GRADE_ADJACENT
from models import SalonSira, SabitOgrenciKonum


@dataclass
class HarmanlamaConfig:
    """Harmanlama ayarları"""
    min_aralik: int = 2  # Aynı sınıftan en az kaç kişi aralık (ekstra önlem)
    max_deneme: int = 100  # Maksimum deneme sayısı
    seed: Optional[int] = None  # Random seed (test için)
    satir_genisligi: int = 2  # Bir sıradaki varsayılan koltuk sayısı (yan/arka kontrolü)
    
    def __post_init__(self):
        if self.seed is not None:
            random.seed(self.seed)


class HarmanlamaEngine:
    """Öğrenci harmanlama algoritması motoru"""
    
    def __init__(self, config: Optional[HarmanlamaConfig] = None):
        self.config = config or HarmanlamaConfig()
        self.hata_loglari = []
        self.uyumsuzluk_loglari: List[str] = []
    
    def harmanla(self, ogrenciler: List[Dict], salonlar: List[Dict],
                 sabit_ogrenciler: Optional[List[Dict]] = None,
                 salon_sira_haritasi: Optional[Dict[int, List[Dict]]] = None) -> Dict[str, any]:
        """
        Ana harmanlama fonksiyonu
        """
        self.hata_loglari = []
        self.uyumsuzluk_loglari = []
        
        try:
            if not self._validate_input(ogrenciler, salonlar):
                return self._hata_response()
            
            sabit_liste = sabit_ogrenciler or []
            sabit_ids = {o['id'] for o in sabit_liste}
            mobil_ogr = [o for o in ogrenciler if o['id'] not in sabit_ids]
            tum_ogrenciler = mobil_ogr + sabit_liste

            salon_sira_map = self._hazirla_salon_sira_map(salonlar, salon_sira_haritasi)
            try:
                sabit_yerlesim, occupied_map, occupied_classes = self._sabit_ogrenci_yerlestir(
                    sabit_liste,
                    salonlar,
                    salon_sira_map
                )
            except RuntimeError as exc:
                self.hata_loglari.append(str(exc))
                return self._hata_response()

            dagitim_modu = "ozel-kural"
            yerlesim: List[Dict] = list(sabit_yerlesim)
            koltuk_listesi: List[str] = []

            if mobil_ogr:
                random.shuffle(mobil_ogr)
                koltuk_sirasi = [dict(o) for o in mobil_ogr]
                try:
                    yerlesim_mobil, teacher_logs, teacher_ids = self._cp_sat_assign(
                        koltuk_sirasi,
                        salonlar,
                        salon_sira_map,
                        occupied_map
                    )
                except RuntimeError as exc:
                    self.hata_loglari.append(str(exc))
                    return self._hata_response()
                if teacher_logs:
                    self.uyumsuzluk_loglari.extend(teacher_logs)
                yerlesim.extend(yerlesim_mobil)
                koltuk_listesi = self._format_koltuk_listesi(koltuk_sirasi, teacher_ids)

            yerlesim.sort(key=lambda x: (x['salon_adi'], x['sira_no']))
            
            istatistikler = self._istatistik_hesapla(
                yerlesim,
                ogrenciler,
                salonlar,
                dagitim_modu=dagitim_modu
            )
        
            return {
                'basarili': True,
                'yerlesim': yerlesim,
                'istatistikler': istatistikler,
                'hatalar': [],
                'uyumsuzluklar': self.uyumsuzluk_loglari,
                'uyumsuzluk_var': bool(self.uyumsuzluk_loglari),
                'koltuk_listesi': koltuk_listesi
            }
        
        except Exception as e:
            self.hata_loglari.append(f"❌ Kritik hata: {str(e)}")
            return self._hata_response()
    
    def _validate_input(self, ogrenciler: List[Dict], salonlar: List[Dict]) -> bool:
        """Giriş verilerini doğrula"""
        if not ogrenciler:
            self.hata_loglari.append("❌ Öğrenci listesi boş!")
            return False
        
        if not salonlar:
            self.hata_loglari.append("❌ Salon listesi boş!")
            return False
        
        toplam_kapasite = sum(s['kapasite'] for s in salonlar)
        if len(ogrenciler) > toplam_kapasite:
            self.hata_loglari.append(
                f"❌ Yetersiz kapasite! Öğrenci: {len(ogrenciler)}, Kapasite: {toplam_kapasite}"
            )
            return False
        
        return True
    
    def _sinif_gruplarina_ayir(self, ogrenciler: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Öğrencileri sınıf-şube gruplarına ayır
        Returns: {'9-A': [...], '10-B': [...], ...}
        """
        gruplar = defaultdict(list)
        for ogr in ogrenciler:
            anahtar = f"{ogr['sinif']}-{ogr['sube']}"
            gruplar[anahtar].append(ogr)
        
        # Her grubu karıştır
        for grup in gruplar.values():
            random.shuffle(grup)
        
        return dict(gruplar)
    
    def _sirali_salon_dagitim(self, ogrenci_listesi: List[Dict], salonlar: List[Dict],
                              salon_sira_map: Dict[int, Dict[str, Any]],
                              occupied_map: Dict[int, set]) -> List[Dict]:
        """(Eski yöntem) öğrenci sırasını boş koltuklara aktarır"""
        if not ogrenci_listesi:
            return []
        tum_slotlar: List[Tuple[Dict, SalonSira]] = []
        for salon in salonlar:
            bos_siralar = self._bos_siralar_for_salon(
                salon['id'],
                salon_sira_map,
                occupied_map
            )
            for slot in bos_siralar:
                tum_slotlar.append((salon, slot))
        if len(ogrenci_listesi) > len(tum_slotlar):
            raise RuntimeError("Yeterli boş sıra bulunamadı.")
        yerlesim: List[Dict] = []
        for ogrenci, (salon, slot) in zip(ogrenci_listesi, tum_slotlar):
            yerlesim.append({
                'ogrenci_id': ogrenci['id'],
                'salon_id': salon['id'],
                'sira_no': slot.sira_no,
                'ogrenci_sinif': ogrenci['sinif'],
                'ogrenci_sube': ogrenci['sube'],
                'salon_adi': salon['salon_adi'],
                'sabit_mi': False,
                'sinav_id': ogrenci.get('sinav_id'),
                'sinav_adi': ogrenci.get('sinav_adi')
            })
            occupied_map.setdefault(salon['id'], set()).add(slot.sira_no)
        return yerlesim

    def _format_koltuk_listesi(self, ogrenciler: List[Dict],
                               teacher_ids: Optional[Set[int]] = None) -> List[str]:
        """Koltuk sırasını insan okunabilir metne dönüştür"""
        sonuc = []
        teacher_ids = teacher_ids or set()
        for idx, ogr in enumerate(ogrenciler, start=1):
            isim = ogr.get('isim')
            if not isim:
                ad = ogr.get('ad', '')
                soyad = ogr.get('soyad', '')
                isim = f"{ad} {soyad}".strip() or f"ID:{ogr.get('id')}"
            satir = f"{idx}. sıra: {isim} ({ogr.get('sinif')}/{ogr.get('sube')})"
            if ogr.get('id') in teacher_ids:
                satir += " [Öğretmen Masası]"
            sonuc.append(satir)
        return sonuc

    def _cp_sat_assign(self, ogrenciler: List[Dict], salonlar: List[Dict],
                       salon_sira_map: Dict[int, Dict[str, Any]],
                       occupied_map: Dict[int, set]) -> Tuple[List[Dict], List[str], Set[int]]:
        """CP-SAT modeli ile öğrencileri koltuklara yerleştir"""
        seat_data, adjacency_pairs = self._prepare_seat_data(
            salonlar,
            salon_sira_map,
            occupied_map,
            include_teacher_desks=False
        )
        assignment = self._solve_cp_sat(ogrenciler, seat_data, adjacency_pairs)
        teacher_mode = False
        if assignment is None:
            seat_data, adjacency_pairs = self._prepare_seat_data(
                salonlar,
                salon_sira_map,
                occupied_map,
                include_teacher_desks=True
            )
            assignment = self._solve_cp_sat(ogrenciler, seat_data, adjacency_pairs)
            teacher_mode = True
        if assignment is None:
            raise RuntimeError(
                "CP-SAT çözüm üretemedi. Salon kapasitesini artırın veya kısıtları gevşetin."
            )
        yerlesim: List[Dict] = []
        teacher_ids: Set[int] = set()
        usage_counter = defaultdict(int)
        for s_idx, seat_idx in assignment.items():
            student = ogrenciler[s_idx]
            seat = seat_data[seat_idx]
            entry = {
                'ogrenci_id': student['id'],
                'salon_id': seat['salon_id'],
                'sira_no': seat['sira_no'],
                'ogrenci_sinif': student['sinif'],
                'ogrenci_sube': student['sube'],
                'salon_adi': seat['salon_adi'],
                'sabit_mi': False,
                'sinav_id': student.get('sinav_id'),
                'sinav_adi': student.get('sinav_adi')
            }
            if seat.get('teacher'):
                entry['ogretmen_masasi'] = True
                entry['sira_label'] = "Öğretmen Masası"
                teacher_ids.add(student['id'])
                usage_counter[seat['salon_id']] += 1
            yerlesim.append(entry)
        teacher_logs: List[str] = []
        if teacher_mode and usage_counter:
            for salon_id, count in usage_counter.items():
                salon_adi = next(
                    (s['salon_adi'] for s in seat_data if s['salon_id'] == salon_id),
                    str(salon_id)
                )
                teacher_logs.append(
                    f"{salon_adi} salonunda {count} öğrenci Öğretmen Masasına alındı."
                )
        return yerlesim, teacher_logs, teacher_ids

    def _prepare_seat_data(self, salonlar: List[Dict],
                           salon_sira_map: Dict[int, Dict[str, Any]],
                           occupied_map: Dict[int, set],
                           include_teacher_desks: bool = False) -> Tuple[List[Dict], Set[Tuple[int, int]]]:
        seat_data: List[Dict[str, Any]] = []
        seat_index_map: Dict[Tuple[int, int], int] = {}
        for salon in salonlar:
            salon_id = salon['id']
            bos_siralar = self._bos_siralar_for_salon(
                salon_id,
                salon_sira_map,
                occupied_map
            )
            sira_data = salon_sira_map.get(salon_id, {})
            tum_sira_seti = {slot.sira_no for slot in sira_data.get('siralar', [])}
            if not tum_sira_seti:
                tum_sira_seti = {slot.sira_no for slot in bos_siralar}
            satir_gen = sira_data.get('satir_genisligi', self.config.satir_genisligi)
            for slot in bos_siralar:
                idx = len(seat_data)
                seat_data.append({
                    'salon_id': salon_id,
                    'salon_adi': salon['salon_adi'],
                    'sira_no': slot.sira_no,
                    'teacher': False,
                    'neighbor_numbers': self._seat_neighbors(slot.sira_no, satir_gen, tum_sira_seti)
                })
                seat_index_map[(salon_id, slot.sira_no)] = idx
            if include_teacher_desks:
                idx = len(seat_data)
                seat_data.append({
                    'salon_id': salon_id,
                    'salon_adi': salon['salon_adi'],
                    'sira_no': self._teacher_desk_no(salon_id, 0),
                    'teacher': True,
                    'neighbor_numbers': set()
                })
                seat_index_map[(salon_id, seat_data[idx]['sira_no'])] = idx
        adjacency_pairs: Set[Tuple[int, int]] = set()
        for idx, seat in enumerate(seat_data):
            if seat['teacher']:
                continue
            for neighbor_no in seat['neighbor_numbers']:
                nb_idx = seat_index_map.get((seat['salon_id'], neighbor_no))
                if nb_idx is None or nb_idx == idx:
                    continue
                pair = tuple(sorted((idx, nb_idx)))
                adjacency_pairs.add(pair)
        return seat_data, adjacency_pairs

    def _solve_cp_sat(self, ogrenciler: List[Dict], seat_data: List[Dict],
                      adjacency_pairs: Set[Tuple[int, int]]) -> Optional[Dict[int, int]]:
        try:
            from ortools.sat.python import cp_model
        except ImportError as exc:
            raise RuntimeError(
                "CP-SAT için OR-Tools gerekiyor. Lütfen 'pip install ortools' çalıştırın."
            ) from exc
        num_students = len(ogrenciler)
        num_seats = len(seat_data)
        if num_students > num_seats:
            return None
        model = cp_model.CpModel()
        x = {}
        for s_idx in range(num_students):
            for seat_idx in range(num_seats):
                x[(s_idx, seat_idx)] = model.NewBoolVar(f"x_{s_idx}_{seat_idx}")
        for s_idx in range(num_students):
            model.Add(sum(x[(s_idx, seat_idx)] for seat_idx in range(num_seats)) == 1)
        for seat_idx in range(num_seats):
            model.Add(sum(x[(s_idx, seat_idx)] for s_idx in range(num_students)) <= 1)
        if CP_SAT_FORBID_SAME_GRADE_ADJACENT:
            students_by_grade: Dict[int, List[int]] = defaultdict(list)
            for idx, ogr in enumerate(ogrenciler):
                students_by_grade[int(ogr['sinif'])].append(idx)
            for seat_a, seat_b in adjacency_pairs:
                for grade, stu_list in students_by_grade.items():
                    if not stu_list:
                        continue
                    model.Add(
                        sum(x[(s_idx, seat_a)] for s_idx in stu_list) +
                        sum(x[(s_idx, seat_b)] for s_idx in stu_list)
                    <= 1)
        teacher_seats = [idx for idx, seat in enumerate(seat_data) if seat['teacher']]
        if teacher_seats:
            teacher_usage = [
                sum(x[(s_idx, seat_idx)] for s_idx in range(num_students))
                for seat_idx in teacher_seats
            ]
            model.Minimize(sum(teacher_usage))
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 15
        solver.parameters.num_search_workers = 8
        status = solver.Solve(model)
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return None
        assignment: Dict[int, int] = {}
        for s_idx in range(num_students):
            for seat_idx in range(num_seats):
                if solver.Value(x[(s_idx, seat_idx)]):
                    assignment[s_idx] = seat_idx
                    break
        return assignment

    def _teacher_desk_no(self, salon_id: int, index: int) -> int:
        return 900000 + salon_id * 100 + index
    
    def _round_robin_harmanlama(self, sinif_gruplari: Dict[str, List[Dict]]) -> List[Dict]:
        """
        Interleaved weighted round-robin ile öğrencileri harmanla.
        Büyük gruplar daha fazla slot alır, aynı sınıf tekrarını minimumda tutar.
        """
        karma_liste: List[Dict] = []
        if not sinif_gruplari:
            return karma_liste
        
        weights = self._grup_agirliklari_hesapla(sinif_gruplari)
        max_weight = max(weights.values()) if weights else 1
        toplam_ogrenci = sum(len(grup) for grup in sinif_gruplari.values())
        fallback_used = False
        
        while toplam_ogrenci > 0:
            turde_ilerleme = False
            for round_index in range(1, max_weight + 1):
                round_keys = [
                    key for key, grup in sinif_gruplari.items()
                    if grup and round_index <= weights.get(key, 1)
                ]
                if not round_keys:
                    continue
                
                ogrenci_atandi = False
                for key in round_keys:
                    ogrenci = sinif_gruplari[key][0]
                    if not self._son_n_ayni_siniftan(karma_liste, ogrenci, self.config.min_aralik):
                        karma_liste.append(sinif_gruplari[key].pop(0))
                        toplam_ogrenci -= 1
                        turde_ilerleme = True
                        ogrenci_atandi = True
                        break
                
                if not ogrenci_atandi and round_keys:
                    # Bu turda hiç kimse kuralı sağlayamadı, ağırlıklı fallback uyguluyoruz.
                    fallback_used = True
                    hedef_key = max(round_keys, key=lambda k: len(sinif_gruplari[k]))
                    karma_liste.append(sinif_gruplari[hedef_key].pop(0))
                    toplam_ogrenci -= 1
                    turde_ilerleme = True
                
                if toplam_ogrenci == 0:
                    break
            
            if not turde_ilerleme:
                raise RuntimeError("Round-robin ilerleyemedi; sınıf dağılımını kontrol edin.")
        
        if fallback_used:
            self.hata_loglari.append(
                "⚠️ Bazı turlarda minimum aralık sağlanamadı; weighted fallback devreye girdi."
            )
        return karma_liste
    
    def _grup_agirliklari_hesapla(self, sinif_gruplari: Dict[str, List[Dict]]) -> Dict[str, int]:
        """Sınıf büyüklüklerine göre ağırlık hesapla (IWRR için)."""
        if not sinif_gruplari:
            return {}
        
        taban = max(1, self.config.min_aralik - 1)
        weights = {}
        for key, grup in sinif_gruplari.items():
            weights[key] = max(1, math.ceil(len(grup) / taban))
        return weights

    def _hazirla_salon_sira_map(self, salonlar: List[Dict],
                                salon_sira_haritasi: Optional[Dict[int, List[Dict]]]) -> Dict[int, Dict[str, Any]]:
        """Salon -> sıra nesnesi haritası hazırla"""
        sonuc: Dict[int, Dict[str, any]] = {}
        for salon in salonlar:
            raw_list = []
            if salon_sira_haritasi and salon['id'] in salon_sira_haritasi:
                raw_list = salon_sira_haritasi[salon['id']]
            if raw_list:
                siralar = [
                    item if isinstance(item, SalonSira) else SalonSira.from_dict(item)
                    for item in raw_list
                ]
            else:
                siralar = [
                    SalonSira(
                        id=None,
                        salon_id=salon['id'],
                        salon_adi=salon['salon_adi'],
                        sira_no=index + 1
                    )
                    for index in range(salon['kapasite'])
                ]
            siralar.sort(key=lambda x: x.sira_no)
            sonuc[salon['id']] = {
                'siralar': siralar,
                'by_id': {slot.id: slot for slot in siralar if slot.id is not None},
                'by_no': {slot.sira_no: slot for slot in siralar},
                'satir_genisligi': self._infer_satir_genisligi(salon, raw_list)
            }
        return sonuc

    def _infer_satir_genisligi(self, salon: Dict, raw_list: Optional[List[Dict]]) -> int:
        """
        Sınıf düzeni bilgisi yoksa varsayılan satır genişliğini kullan.
        İleride etiket / meta bilgilerle dinamik olarak güncellenebilir.
        """
        custom = salon.get('satir_genisligi') if isinstance(salon, dict) else None
        if isinstance(custom, int) and custom > 0:
            return custom
        return max(1, self.config.satir_genisligi)

    def _bos_siralar_for_salon(self, salon_id: int, salon_sira_map: Dict[int, Dict[str, Any]],
                               occupied_map: Optional[Dict[int, set]]) -> List[SalonSira]:
        salon_data = salon_sira_map.get(salon_id)
        if not salon_data:
            return []
        occupied = occupied_map.get(salon_id, set()) if occupied_map else set()
        return [slot for slot in salon_data['siralar'] if slot.sira_no not in occupied]

    def _pop_sira(self, salon_state_entry: Dict, class_key: Optional[str] = None) -> Optional[SalonSira]:
        bos = salon_state_entry.get('bos_siralar')
        if not bos:
            return None
        if not class_key or 'satir_genisligi' not in salon_state_entry:
            return bos.popleft() if bos else None
        skipped = deque()
        slot = None
        while bos:
            aday = bos.popleft()
            if not self._violates_neighbor_rule(aday.sira_no, class_key, salon_state_entry):
                slot = aday
                break
            skipped.append(aday)
        if slot is None:
            if skipped:
                slot = skipped.popleft()
                self.hata_loglari.append(
                    f"⚠️ {salon_state_entry['salon']['salon_adi']} salonunda {class_key} için yan/arka kuralı geçici olarak gevşetildi.")
            else:
                return None
        if skipped:
            bos.extend(skipped)
        salon_state_entry.setdefault('dolu_siralar', {})[slot.sira_no] = class_key
        return slot

    def _find_salon_sira_by_id(self, salon_id: int, sira_id: int,
                               salon_sira_map: Dict[int, Dict[str, Any]]) -> Optional[SalonSira]:
        salon_data = salon_sira_map.get(salon_id)
        if not salon_data:
            return None
        return salon_data['by_id'].get(sira_id)

    def _violates_neighbor_rule(self, sira_no: int, class_key: str, salon_state_entry: Dict) -> bool:
        tum_sira_seti = salon_state_entry.get('tum_sira_seti') or set()
        satir_gen = salon_state_entry.get('satir_genisligi', self.config.satir_genisligi)
        neighbors = self._seat_neighbors(sira_no, satir_gen, tum_sira_seti)
        dolu = salon_state_entry.get('dolu_siralar', {})
        for komsu in neighbors:
            if dolu.get(komsu) == class_key:
                return True
        return False

    def _seat_neighbors(self, sira_no: int, satir_genisligi: int, tum_siralar: Optional[Set[int]]) -> List[int]:
        if satir_genisligi <= 0:
            satir_genisligi = 1
        tum_siralar = tum_siralar or set()
        neighbors: List[int] = []
        row = (sira_no - 1) // satir_genisligi
        col = (sira_no - 1) % satir_genisligi
        # Yan komşular
        left = sira_no - 1
        if left >= 1 and ((left - 1) // satir_genisligi) == row and left in tum_siralar:
            neighbors.append(left)
        right = sira_no + 1
        if ((right - 1) // satir_genisligi) == row and right in tum_siralar:
            neighbors.append(right)
        # Ön / arka
        up = sira_no - satir_genisligi
        if up >= 1 and up in tum_siralar:
            neighbors.append(up)
        down = sira_no + satir_genisligi
        if down in tum_siralar:
            neighbors.append(down)
        return neighbors

    def _son_n_ayni_siniftan(self, liste: List[Dict], ogrenci: Dict, n: int) -> bool:
        """
        Son N öğrenciden herhangi biri bu öğrenci ile aynı sınıf/şubeden mi?
        """
        if len(liste) < n:
            return False
        
        son_n = liste[-n:]
        ogrenci_sinif_sube = f"{ogrenci['sinif']}-{ogrenci['sube']}"
        
        for ogr in son_n:
            if f"{ogr['sinif']}-{ogr['sube']}" == ogrenci_sinif_sube:
                return True
        
        return False
    
    def _salonlara_yerlestir(self, ogrenci_listesi: List[Dict], 
                            salonlar: List[Dict],
                            salon_sira_map: Dict[int, Dict],
                            occupied_map: Optional[Dict[int, set]] = None,
                            occupied_classes: Optional[Dict[int, Dict[int, str]]] = None) -> List[Dict]:
        """Salonları, mümkün oldukça aynı sınıf tekrarını engelleyecek şekilde doldur"""
        yerlesim: List[Dict] = []
        occupied_map = occupied_map or defaultdict(set)
        occupied_classes = occupied_classes or defaultdict(dict)
        salon_state = {}
        for salon in sorted(salonlar, key=lambda x: x['kapasite'], reverse=True):
            bos_siralar = deque(self._bos_siralar_for_salon(
                salon['id'],
                salon_sira_map,
                occupied_map
            ))
            sira_data = salon_sira_map.get(salon['id'], {})
            tum_sira_seti = {slot.sira_no for slot in sira_data.get('siralar', [])}
            if not tum_sira_seti:
                tum_sira_seti = {slot.sira_no for slot in bos_siralar}
            satir_gen = sira_data.get('satir_genisligi', self.config.satir_genisligi)
            initial_classes = dict(occupied_classes.get(salon['id'], {}))
            sinif_counter = defaultdict(int)
            for class_key in initial_classes.values():
                sinif_counter[class_key] += 1
            salon_state[salon['id']] = {
                'salon': salon,
                'kalan': len(bos_siralar),
                'bos_siralar': bos_siralar,
                'sinif_sayaci': sinif_counter,
                'satir_genisligi': satir_gen,
                'tum_sira_seti': tum_sira_seti,
                'dolu_siralar': initial_classes
            }
        
        for ogrenci in ogrenci_listesi:
            salon_id = self._find_salon_for_ogrenci(ogrenci, salon_state)
            if salon_id is None:
                raise RuntimeError("Yeterli boş sıra bulunamadı (mobil öğrenciler için)")
            state = salon_state[salon_id]
            class_key = f"{ogrenci['sinif']}-{ogrenci['sube']}"
            slot = self._pop_sira(state, class_key)
            if slot is None:
                raise RuntimeError(f"Salon {state['salon']['salon_adi']} için boş sıra kalmadı")
            yerlesim.append({
                'ogrenci_id': ogrenci['id'],
                'salon_id': salon_id,
                'sira_no': slot.sira_no,
                'ogrenci_sinif': ogrenci['sinif'],
                'ogrenci_sube': ogrenci['sube'],
                'salon_adi': state['salon']['salon_adi'],
                'sabit_mi': False,
                'sinav_id': ogrenci.get('sinav_id'),
                'sinav_adi': ogrenci.get('sinav_adi')
            })
            state['kalan'] = max(0, state['kalan'] - 1)
            state['sinif_sayaci'][class_key] += 1
        
        return yerlesim
    
    def _find_salon_for_ogrenci(self, ogrenci: Dict, salon_state: Dict) -> Optional[int]:
        """Öğrenci için uygun salon seç (boş salon varsa önce onları kullan)"""
        class_key = f"{ogrenci['sinif']}-{ogrenci['sube']}"
        adaylar = [
            (salon_id, state) for salon_id, state in salon_state.items()
            if state['kalan'] > 0
        ]
        if not adaylar:
            return None
        
        # Önce bu sınıf/şubeden kimse olmayan salonları dene (boş salonlar dahil)
        temiz = [
            (salon_id, state)
            for salon_id, state in adaylar
            if state['sinif_sayaci'].get(class_key, 0) == 0
        ]
        hedefler = temiz if temiz else adaylar
        
        # En fazla boş yeri olan salonu seç
        hedefler.sort(key=lambda item: item[1]['kalan'], reverse=True)
        return hedefler[0][0]
    
    def _group_key(self, ogrenci: Dict, mode: str) -> str:
        if mode == "sinif_sube":
            return f"{ogrenci['sinif']}-{ogrenci['sube']}"
        return str(ogrenci['sinif'])
    
    def _can_distribute_groups(self, ogrenciler: List[Dict], salonlar: List[Dict],
                               mode: str,
                               reserved_counts: Optional[Dict[int, int]] = None) -> bool:
        """Belirtilen grup modunu salonlara tek tek yerleştirmek mümkün mü?"""
        if not salonlar:
            return False
        
        group_counts = defaultdict(int)
        for ogr in ogrenciler:
            group_counts[self._group_key(ogr, mode)] += 1
        
        if not group_counts:
            return False
        
        if len(group_counts) > len(salonlar):
            return False
        
        group_sizes = sorted(group_counts.values(), reverse=True)
        reserved_counts = reserved_counts or {}
        salon_caps = sorted([
            max(0, s['kapasite'] - reserved_counts.get(s['id'], 0))
            for s in salonlar
        ], reverse=True)
        
        for size, kapasite in zip(group_sizes, salon_caps):
            if size > kapasite:
                return False
        return True
    
    def _assign_groups_to_salons(self, ogrenciler: List[Dict], salonlar: List[Dict],
                                 mode: str,
                                 salon_sira_map: Dict[int, Dict],
                                 occupied_map: Optional[Dict[int, set]] = None,
                                 occupied_classes: Optional[Dict[int, Dict[int, str]]] = None) -> List[Dict]:
        """Grupları salonlara dağıt (boş salon varken aynı grup farklı salonlara yayılır)"""
        occupied_map = occupied_map or defaultdict(set)
        occupied_classes = occupied_classes or defaultdict(dict)
        groups = defaultdict(list)
        for ogr in ogrenciler:
            groups[self._group_key(ogr, mode)].append(ogr)
        
        sorted_groups = sorted(groups.items(), key=lambda item: len(item[1]), reverse=True)
        state = {}
        for salon in sorted(salonlar, key=lambda x: x['kapasite'], reverse=True):
            bos_list = self._bos_siralar_for_salon(salon['id'], salon_sira_map, occupied_map)
            sira_data = salon_sira_map.get(salon['id'], {})
            tum_sira_seti = {slot.sira_no for slot in sira_data.get('siralar', [])}
            if not tum_sira_seti:
                tum_sira_seti = {slot.sira_no for slot in bos_list}
            satir_gen = sira_data.get('satir_genisligi', self.config.satir_genisligi)
            initial_groups = set()
            if occupied_classes.get(salon['id']):
                for class_key in occupied_classes[salon['id']].values():
                    if mode == "sinif":
                        initial_groups.add(class_key.split('-')[0])
                    else:
                        initial_groups.add(class_key)
            state[salon['id']] = {
                'salon': salon,
                'kalan': len(bos_list),
                'bos_siralar': deque(bos_list),
                'gruplar': initial_groups,
                'satir_genisligi': satir_gen,
                'tum_sira_seti': tum_sira_seti,
                'dolu_siralar': dict(occupied_classes.get(salon['id'], {}))
            }
        
        yerlesim = []
        for key, students in sorted_groups:
            random.shuffle(students)
            for ogr in students:
                hedef = self._choose_salon_for_group(key, state)
                if hedef is None:
                    raise RuntimeError("Gruplar için yeterli boş sıra bulunamadı")
                salon_state = state[hedef]
                class_key = self._group_key(ogr, "sinif_sube")
                slot = self._pop_sira(salon_state, class_key)
                if slot is None:
                    raise RuntimeError(f"Salon {salon_state['salon']['salon_adi']} için boş sıra kalmadı")
                yerlesim.append({
                    'ogrenci_id': ogr['id'],
                    'salon_id': hedef,
                    'sira_no': slot.sira_no,
                    'ogrenci_sinif': ogr['sinif'],
                    'ogrenci_sube': ogr['sube'],
                    'salon_adi': salon_state['salon']['salon_adi'],
                    'grup': key,
                    'sabit_mi': False
                })
                salon_state['kalan'] = max(0, salon_state['kalan'] - 1)
                salon_state['gruplar'].add(key)
        
        yerlesim.sort(key=lambda x: (x['salon_adi'], x['sira_no']))
        return yerlesim

    def _reserved_kapasite(self, occupied_map: Optional[Dict[int, set]]) -> Dict[int, int]:
        if not occupied_map:
            return {}
        return {salon_id: len(siralar) for salon_id, siralar in occupied_map.items()}
    
    def _choose_salon_for_group(self, group_key: str, state: Dict[int, Dict]) -> Optional[int]:
        uygun = [
            (salon_id, data) for salon_id, data in state.items()
            if data['kalan'] > 0
        ]
        if not uygun:
            return None
        
        temiz = [
            (salon_id, data) for salon_id, data in uygun
            if group_key not in data['gruplar']
        ]
        hedefler = temiz if temiz else uygun
        hedefler.sort(key=lambda item: item[1]['kalan'], reverse=True)
        return hedefler[0][0]
    
    def _sabit_ogrenci_yerlestir(self, sabit_ogrenciler: List[Dict],
                                 salonlar: List[Dict],
                                 salon_sira_map: Dict[int, Dict[str, Any]]) -> Tuple[List[Dict], Dict[int, set], Dict[int, Dict[int, str]]]:
        """Sabit öğrencileri kayıtlı salon ve sıralarına yerleştir"""
        yerlesim: List[Dict] = []
        occupied = defaultdict(set)
        occupied_classes: Dict[int, Dict[int, str]] = defaultdict(dict)
        sorun_var = False
        if not sabit_ogrenciler:
            return yerlesim, occupied, occupied_classes
        salon_map = {salon['id']: salon for salon in salonlar}
        for sabit in sabit_ogrenciler:
            salon_id = sabit.get('sabit_salon_id')
            sira_id = sabit.get('sabit_salon_sira_id')
            if not salon_id or not sira_id:
                self.hata_loglari.append(
                    f"⚠️ Sabit öğrenci {sabit['ad']} {sabit['soyad']} için salon/sıra seçilmemiş")
                sorun_var = True
                continue
            salon = salon_map.get(salon_id)
            if not salon:
                self.hata_loglari.append(
                    f"⚠️ Sabit öğrenci {sabit['ad']} {sabit['soyad']} aktif olmayan bir salonu kullanıyor")
                sorun_var = True
                continue
            slot = self._find_salon_sira_by_id(salon_id, sira_id, salon_sira_map)
            if not slot:
                self.hata_loglari.append(
                    f"⚠️ Salon {salon['salon_adi']} için tanımlı olmayan sıra seçildi")
                sorun_var = True
                continue
            if slot.sira_no in occupied[salon_id]:
                self.hata_loglari.append(
                    f"⚠️ {salon['salon_adi']} salonunda {slot.sira_no}. sıra zaten başka sabit öğrenciye ayrılmış")
                sorun_var = True
                continue
            occupied[salon_id].add(slot.sira_no)
            class_key = f"{sabit['sinif']}-{sabit['sube']}"
            occupied_classes[salon_id][slot.sira_no] = class_key
            konum = SabitOgrenciKonum(
                ogrenci_id=sabit['id'],
                salon_id=salon_id,
                salon_adi=salon['salon_adi'],
                sira_id=slot.id,
                sira_no=slot.sira_no,
                sira_etiket=slot.etiket
            )
            yerlesim.append({
                'ogrenci_id': sabit['id'],
                'salon_id': salon_id,
                'sira_no': slot.sira_no,
                'ogrenci_sinif': sabit['sinif'],
                'ogrenci_sube': sabit['sube'],
                'salon_adi': salon['salon_adi'],
                'sabit_mi': True,
                'sabit_konum': konum.display,
                'sinav_id': sabit.get('sinav_id'),
                'sinav_adi': sabit.get('sinav_adi')
            })
        if sorun_var:
            raise RuntimeError("Sabit öğrencilerin sabit konum bilgileri eksik veya hatalı.")
        return yerlesim, occupied, occupied_classes
    
    def _validate_yerlesim(self, yerlesim: List[Dict], min_aralik: int,
                           salon_sira_map: Optional[Dict[int, Dict[str, Any]]] = None,
                           uyumsuzluklar: Optional[List[str]] = None,
                           strict: bool = True) -> bool:
        """
        Yerleşimin kuralları karşılayıp karşılamadığını kontrol et.
        - Yanında veya arkasında aynı sınıftan öğrenci olmamalı.
        - Kullanıcı isterse ek olarak lineer min_aralik kuralı uygulanabilir.
        """
        if not yerlesim:
            return True
        ihlal = False
        salonlar_dict = defaultdict(list)
        for yer in yerlesim:
            salonlar_dict[yer['salon_id']].append(yer)
        
        for salon_id, salon_yerlesim in salonlar_dict.items():
            salon_yerlesim.sort(key=lambda x: x['sira_no'])
            class_map = {yer['sira_no']: f"{yer['ogrenci_sinif']}-{yer['ogrenci_sube']}" for yer in salon_yerlesim}
            salon_map_entry = salon_sira_map.get(salon_id) if salon_sira_map else {}
            tum_sira_seti = {slot.sira_no for slot in salon_map_entry.get('siralar', [])}
            if not tum_sira_seti:
                tum_sira_seti = set(class_map.keys())
            satir_gen = salon_map_entry.get('satir_genisligi', self.config.satir_genisligi)
            
            # Yan/arka kontrolü
            for yer in salon_yerlesim:
                sinif_sube = f"{yer['ogrenci_sinif']}-{yer['ogrenci_sube']}"
                neighbors = self._seat_neighbors(yer['sira_no'], satir_gen, tum_sira_seti)
                for komsu in neighbors:
                    if class_map.get(komsu) == sinif_sube:
                        msg = (
                            f"⚠️ {yer['salon_adi']} salonunda {yer['sira_no']}. sıranın "
                            f"yanında/arkasında aynı sınıftan öğrenci bulundu ({sinif_sube})."
                        )
                        if uyumsuzluklar is not None:
                            uyumsuzluklar.append(msg)
                        if strict:
                            self.hata_loglari.append(msg)
                            return False
                        ihlal = True
            
            # Ekstra lineer aralık kontrolü (isteğe bağlı)
            if min_aralik and min_aralik > 1:
                for i, ogrenci in enumerate(salon_yerlesim):
                    sinif_sube = f"{ogrenci['ogrenci_sinif']}-{ogrenci['ogrenci_sube']}"
                    kontrol_baslangic = max(0, i - min_aralik)
                    kontrol_ogrenciler = salon_yerlesim[kontrol_baslangic:i]
                    ayni_sinif_var = any(
                        f"{o['ogrenci_sinif']}-{o['ogrenci_sube']}" == sinif_sube
                        for o in kontrol_ogrenciler
                    )
                    if ayni_sinif_var:
                        msg = (
                            f"⚠️ {ogrenci['salon_adi']} salonunda {ogrenci['sira_no']}. sıraya "
                            f"çok yakın başka bir {sinif_sube} öğrencisi yerleşmiş."
                        )
                        if uyumsuzluklar is not None:
                            uyumsuzluklar.append(msg)
                        if strict:
                            self.hata_loglari.append(msg)
                            return False
                        ihlal = True
        
        return not ihlal
    
    def _istatistik_hesapla(self, yerlesim: List[Dict], ogrenciler: List[Dict],
                           salonlar: List[Dict], dagitim_modu: str = "karma") -> Dict:
        """Harmanlama istatistiklerini hesapla"""
        salon_doluluk = defaultdict(int)
        for yer in yerlesim:
            salon_doluluk[yer['salon_id']] += 1
        
        salon_istatistikleri = []
        for salon in salonlar:
            doluluk = salon_doluluk.get(salon['id'], 0)
            oran = (doluluk / salon['kapasite'] * 100) if salon['kapasite'] else 0
            salon_istatistikleri.append({
                'salon_adi': salon['salon_adi'],
                'kapasite': salon['kapasite'],
                'doluluk': doluluk,
                'oran': round(oran, 2)
            })
        
        sinif_dagilim = defaultdict(int)
        for ogr in ogrenciler:
            sinif_dagilim[f"{ogr['sinif']}/{ogr['sube']}"] += 1
        
        return {
            'toplam_ogrenci': len(ogrenciler),
            'yerlestirilen': len(yerlesim),
            'kullanilan_salon': len([d for d in salon_doluluk.values() if d > 0]),
            'toplam_salon': len(salonlar),
            'salon_istatistikleri': salon_istatistikleri,
            'sinif_dagilim': dict(sinif_dagilim),
            'dagitim_modu': dagitim_modu
        }
    
    def _hata_response(self) -> Dict:
        """Hata durumunda response"""
        return {
            'basarili': False,
            'yerlesim': [],
            'istatistikler': {},
            'hatalar': self.hata_loglari,
            'uyumsuzluklar': self.uyumsuzluk_loglari,
            'uyumsuzluk_var': bool(self.uyumsuzluk_loglari)
        }
    
    def yerlesim_gorsellesitir(self, yerlesim: List[Dict]) -> str:
        """
        Yerleşimi görsel ASCII formatında göster (debug için)
        """
        if not yerlesim:
            return "⚠️ Yerleşim boş!"
        
        # Salonlara göre grupla
        salonlar = defaultdict(list)
        for yer in sorted(yerlesim, key=lambda x: (x['salon_id'], x['sira_no'])):
            salonlar[yer['salon_adi']].append(yer)
        
        output = []
        output.append("=" * 60)
        output.append("YERLEŞİM GÖRSELLEŞTİRME")
        output.append("=" * 60)
        
        for salon_adi, ogrenciler in salonlar.items():
            output.append(f"\n📍 {salon_adi} ({len(ogrenciler)} öğrenci)")
            output.append("-" * 60)
            
            for yer in ogrenciler[:10]:  # İlk 10 öğrenci
                output.append(
                    f"  Sıra {yer['sira_no']:3d}: "
                    f"{yer['ogrenci_sinif']}/{yer['ogrenci_sube']} "
                    f"[ID: {yer['ogrenci_id']}]"
                )
            
            if len(ogrenciler) > 10:
                output.append(f"  ... ve {len(ogrenciler) - 10} öğrenci daha")
        
        return "\n".join(output)


class GozetmenAtamaEngine:
    """Gözetmen atama motoru"""
    
    def __init__(self):
        self.hata_loglari = []
    
    def otomatik_ata(self, salonlar, gozetmenler, salon_basina_gozetmen=1):
        """
        Gözetmenleri salonlara otomatik ata
        
        Args:
            salonlar: Salon listesi
            gozetmenler: Gözetmen listesi
            salon_basina_gozetmen: Salon başına gözetmen sayısı
            
        Returns:
            Atama listesi: [{gozetmen_id, salon_id, gorev_turu}, ...]
        """
        self.hata_loglari = []
        
        try:
            if not salonlar:
                self.hata_loglari.append("❌ Salon listesi boş!")
                return []
            
            if not gozetmenler:
                self.hata_loglari.append("❌ Gözetmen listesi boş!")
                return []
            
            # Toplam ihtiyaç
            toplam_ihtiyac = len(salonlar) * salon_basina_gozetmen
            
            if len(gozetmenler) < toplam_ihtiyac:
                self.hata_loglari.append(
                    f"❌ Yetersiz gözetmen! İhtiyaç: {toplam_ihtiyac}, Mevcut: {len(gozetmenler)}"
                )
                # En azından bazı atamaları yap
                atanabilir_sayisi = len(gozetmenler) // salon_basina_gozetmen
                if atanabilir_sayisi == 0:
                    atanabilir_sayisi = 1
            else:
                atanabilir_sayisi = len(salonlar)
            
            # Basit atama algoritması: round-robin
            atamalar = []
            gozetmen_index = 0
            
            for i, salon in enumerate(salonlar[:atanabilir_sayisi]):
                for j in range(salon_basina_gozetmen):
                    if gozetmen_index < len(gozetmenler):
                        gozetmen = gozetmenler[gozetmen_index]
                        gorev_turu = "asil" if j == 0 else "yedek"
                        
                        atamalar.append({
                            'gozetmen_id': gozetmen['id'],
                            'salon_id': salon['id'],
                            'gorev_turu': gorev_turu
                        })
                        
                        gozetmen_index += 1
            
            return atamalar
            
        except Exception as e:
            self.hata_loglari.append(f"❌ Gözetmen atama hatası: {str(e)}")
            return []


if __name__ == "__main__":
    # Test
    print("🧪 Harmanlama Engine Test\n")
    
    # Test verileri
    test_ogrenciler = []
    sinif_listesi = SINIF_SEVIYELERI
    for i in range(1, 51):
        test_ogrenciler.append({
            'id': i,
            'ad': f'Öğrenci{i}',
            'soyad': 'TEST',
            'sinif': sinif_listesi[i % len(sinif_listesi)],
            'sube': ['A', 'B', 'C'][i % 3]
        })
    
    test_salonlar = [
        {'id': 1, 'salon_adi': 'A-101', 'kapasite': 20},
        {'id': 2, 'salon_adi': 'B-102', 'kapasite': 20},
        {'id': 3, 'salon_adi': 'C-103', 'kapasite': 15}
    ]
    
    # Harmanlama
    engine = HarmanlamaEngine(HarmanlamaConfig(seed=42))
    sonuc = engine.harmanla(test_ogrenciler, test_salonlar)
    
    if sonuc['basarili']:
        print("✅ Harmanlama başarılı!\n")
        print("📊 İstatistikler:")
        for key, value in sonuc['istatistikler'].items():
            if key != 'salon_istatistikleri':
                print(f"  {key}: {value}")
        
        print("\n" + engine.yerlesim_gorsellesitir(sonuc['yerlesim']))
    else:
        print("❌ Harmanlama başarısız!")
        for hata in sonuc['hatalar']:
            print(f"  {hata}")
