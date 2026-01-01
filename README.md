# TSOMTAL - Pardus ETAP Uzaktan Yönetim Paneli

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-brightgreen.svg)
![Platform](https://img.shields.io/badge/platform-Pardus%20ETAP%2023-orange.svg)

**Geliştirici:** Nuri Tıraş  
**Kurum:** Ticaret ve Sanayi Odası Mesleki ve Teknik Anadolu Lisesi (TSOMTAL)

Bu uygulama, **Pardus ETAP 23** yüklü etkileşimli tahtaların yerel ağ üzerinden merkezi olarak yönetilmesi için geliştirilmiştir. Python ve PyQt6 kullanılarak hazırlanan bu araç; uyandırma (WoL), uzaktan kapatma (SSH), canlı durum takibi (Ping) ve zamanlanmış görev yönetimini tek bir panelde birleştirir.

---

## 🚀 Özellikler

* 🔍 **Otomatik Ağ Taraması:** `arp-scan` kullanarak ağdaki tüm aktif cihazları tespit eder ve IP-MAC eşleşmelerini listeler.
* ⚡ **Wake-on-LAN (WoL):** Kapalı durumdaki tahtalara "Magic Packet" göndererek uzaktan açılmalarını sağlar.
* 🛑 **Uzaktan Kapatma:** SSH protokolü üzerinden tek tıkla tüm ağa veya seçili tahtalara güvenli kapatma komutu gönderir.
* 📡 **Canlı Durum Takibi:** `ping` protokolü ile tahtaların o anki erişilebilirlik durumunu (Açık/Kapalı) anlık olarak raporlar.
* ⏰ **Akıllı Zamanlayıcı (Cron):** Hafta içi belirlenen saatlerde (Örn: 08:30) tahtaların otomatik olarak açılmasını sağlar.



---

## 🛠 Kurulum

Pardus ETAP üzerinde uygulamanın çalışması için gerekli sistem paketlerini aşağıdaki komutla yükleyebilirsiniz:

```bash
sudo apt update
sudo apt install python3-pyqt6 nmap arp-scan wakeonlan sshpass -y
