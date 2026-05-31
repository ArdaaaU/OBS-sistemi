# Öğrenci Bilgi Sistemi (OBS)

Bu proje, İleri Programlama dersi için geliştirilmiş, Python (Flask) ve SQLite kullanılarak hazırlanmış bir Öğrenci Bilgi Sistemi'dir.

## Özellikler

- **3 Farklı Rol:** Admin, Akademisyen ve Öğrenci
- **Admin Paneli:** Kullanıcı (Öğrenci/Akademisyen) ve Ders ekleme, silme, derslere akademisyen ve öğrenci atama işlemleri.
- **Akademisyen Paneli:** Atandığı dersleri görme, öğrencileri listeleme, vize/final/proje/sunum notları ile devamsızlık girişi yapma ve öğrenci detaylarına bakabilme.
- **Öğrenci Paneli:** Kayıtlı olduğu dersleri, bu derslerdeki notlarını ve devamsızlık durumunu görüntüleme.
- **Tasarım:** Modern, Tailwind CSS ile şekillendirilmiş duyarlı (responsive) kullanıcı arayüzü.

## Kurulum ve Çalıştırma

1. Python 3.x yüklü olduğundan emin olun.
2. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install -r requirements.txt
   ```
3. Uygulamayı başlatın:
   ```bash
   python app.py
   ```
   *Not: İlk çalıştırmada veritabanı otomatik olarak oluşturulacak ve varsayılan yönetici (admin) hesabı tanımlanacaktır.*

4. Tarayıcınızdan `http://127.0.0.1:5000/` adresine giderek giriş yapabilirsiniz.

## Varsayılan Yönetici Bilgileri
- **Kullanıcı Adı:** `admin`
- **Şifre:** `123456`

*(Sistemden eklenen tüm yeni kullanıcılar (öğrenci/akademisyen) için varsayılan şifre `123456` olarak tanımlanır.)*
