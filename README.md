# 🦋 Kelebek Sınav Sistemi

**Kelebek Sınav Sistemi**, okullar ve eğitim kurumları için tasarlanmış, öğrencilerin sınav salonlarına optimize edilmiş bir şekilde yerleştirilmesini sağlayan modern bir masaüstü uygulamasıdır. "Kelebek sistemi" mantığına dayanarak farklı sınıflardan öğrencileri aynı salonda karma bir şekilde oturtarak kopya riskini minimize eder ve sınav organizasyonunu kolaylaştırır.

---

## ✨ Özellikler

- **Öğrenci Yönetimi:** Öğrencileri tek tek veya toplu (Excel) olarak sisteme ekleme, düzenleme ve silme.
- **Ders ve Sınıf Tanımlama:** Farklı dersleri ve sınıf seviyelerini (ortaokul, lise, hazırlık vb.) yönetme.
- **Salon Yönetimi:** Sınav salonlarını ve kapasitelerini tanımlama.
- **Gelişmiş Harmanlama (Kelebek Sistemi):**
  - Farklı sınıflardaki öğrencileri otomatik olarak karıştırarak yerleştirme.
  - Sınav türüne ve salon kapasitesine göre dinamik yerleşim.
- **Görsel Oturma Düzeni:** Sınav salonlarının oturma düzenini görsel olarak görüntüleme ve düzenleme.
- **Zengin Çıktı ve Raporlama:**
  - Sınıf listeleri (Excel).
  - Salon oturma planları (Excel/Görsel).
  - Sınav imza listeleri.
  - Gözetmen listeleri.
- **Soru Bankası:** Sınavlar için soru bankası oluşturma ve yönetme.

---

## 🚀 Kurulum

### Ön Gereksinimler

- Python 3.8 veya üzeri
- Pip (Python paket yöneticisi)

### Adımlar

1. **Projeyi Klonlayın:**

    ```bash
    git clone https://github.com/qpvale34/kelebek-sinav-sistemi.git
    cd kelebek-sinav-sistemi
    ```

2. **Sanal Ortam Oluşturun (Önerilir):**

    ```bash
    python -m venv venv
    # Windows için:
    venv\Scripts\activate
    # Linux/Mac için:
    source venv/bin/activate
    ```

3. **Bağımlılıkları Yükleyin:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Uygulamayı Çalıştırın:**

    ```bash
    python main.py
    ```

---

## 🛠 Kullanılan Teknolojiler

- **Dil:** Python
- **Arayüz (GUI):** Tkinter (Özel temalı ve modern tasarım)
- **Veritabanı:** SQLite
- **Veri İşleme:** Pandas, Openpyxl
- **Raporlama:** ReportLab

---

## 👨‍💻 Geliştirici

- **İbrahim ERTUĞRUL** - *Geliştirici* - [qpvale34](https://github.com/qpvale34)

---

## 📄 Lisans

Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır. Daha fazla bilgi için LICENSE dosyasına bakınız.
