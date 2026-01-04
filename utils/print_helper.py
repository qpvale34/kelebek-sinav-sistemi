"""
Kelebek Sınav Sistemi - Yazdırma Yardımcıları
Sınav oturma planı çıktıları için PDF üretim araçları
"""

from dataclasses import dataclass
from typing import List, Dict
from pathlib import Path
import textwrap

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas


@dataclass
class ExamPrintItem:
    """Sınav yazdırma kuyruğundaki tek satır"""
    order: int
    salon: str
    seat_no: int
    student: str
    class_label: str
    file_name: str
    file_path: str


def create_exam_manifest_pdf(output_path: str, exam_info: Dict[str, str],
                             items: List[ExamPrintItem]) -> bool:
    """Oturma düzeni için yazdırma manifestosu oluştur"""
    try:
        c = canvas.Canvas(output_path, pagesize=A4)
        width, height = A4
        margin = 40
        row_height = 18
        page_no = 1
        
        def draw_header():
            c.setFont("Helvetica-Bold", 14)
            c.drawString(margin, height - margin, f"Sınav: {exam_info.get('sinav_adi', '')}")
            c.setFont("Helvetica", 11)
            c.drawString(margin, height - margin - 20,
                         f"Ders: {exam_info.get('ders_adi', '')} | Tarih: {exam_info.get('tarih', '')} | Saat: {exam_info.get('saat', '')}")
            c.drawString(margin, height - margin - 38,
                         f"Soru Dosyası: {exam_info.get('dosya_adi', '—')} ({exam_info.get('dosya_yolu', '—')})")
            c.drawRightString(width - margin, height - margin, f"Sayfa {page_no}")
            
            c.setFillColor(colors.HexColor("#1F4788"))
            c.rect(margin, height - margin - 60, width - 2 * margin, 20, fill=1, stroke=0)
            c.setFillColor(colors.white)
            headers = ["#", "Salon", "Sıra", "Öğrenci", "Sınıf", "Dosya"]
            offsets = [0, 40, 120, 170, 360, 420]
            for header, offset in zip(headers, offsets):
                c.drawString(margin + offset, height - margin - 55, header)
            c.setFillColor(colors.black)
        
        draw_header()
        y = height - margin - 80
        
        for item in items:
            if y <= margin + 40:
                c.showPage()
                page_no += 1
                draw_header()
                y = height - margin - 80
            
            c.setFont("Helvetica", 9)
            c.drawString(margin, y, str(item.order))
            c.drawString(margin + 40, y, item.salon)
            c.drawString(margin + 120, y, str(item.seat_no))
            c.drawString(margin + 170, y, item.student)
            c.drawString(margin + 360, y, item.class_label)
            
            file_text = f"{item.file_name} ({Path(item.file_path).name})"
            wrapped = textwrap.wrap(file_text, width=45)
            for idx, line in enumerate(wrapped[:2]):
                c.drawString(margin + 420, y - idx * 10, line)
            y -= row_height
        
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(margin, margin, "Not: Liste oturma düzeni sıranıza göre sıralanmıştır.")
        c.save()
        return True
    except Exception as exc:  # pragma: no cover - yalnızca runtime hataları için
        print(f"❌ Manifest PDF oluşturulamadı: {exc}")
        return False
