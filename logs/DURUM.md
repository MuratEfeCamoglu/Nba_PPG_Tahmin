# DURUM
Aktif faz: 1 — Veri Toplama ve Hedef
Aktif adım: 1.1 veri_topla.py (başlanacak)
Döngü: 0/8 · Yeniden tasarım: 0/2 · Bu hata için deneme: 0/3
## Notlar
- Kapılar `./make <hedef>` ile çalıştırılır (K-002). Python: .venv/Scripts/python.exe (3.12).
- NBA API erişimi çalışıyor (2025-26 Base: 582 satır, ~3 sn).
## Plan (Faz 1)
- [ ] 1.1 veri_topla.py: sezon_cek (önbellek + backoff), tum_sezonlari_topla (Base+Advanced birleşik)
- [ ] 1.2 hedef.py: hedef_olustur + test_hedef.py
- [ ] 1.3 test_veri.py (@veri) — sözleşme §3
- [ ] 1.4 make veri ile 52 dosyayı çek (parça parça), oyuncu_sezon.csv
- [ ] 1.5 Kapılar: make test, make test-veri, lint, satır sayısı 10k-15k, 26 yıl
## Son kapı sonuçları (2026-10-04)
Faz 0: K1 ✅ K2 ✅ (13 passed) K3 ✅ K9 ✅
## KISMİ işaretli maddeler
(yok)
