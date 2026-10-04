# DURUM
Aktif faz: 3 — Öznitelik Mühendisliği
Aktif adım: 3.1 oznitelik.py (başlanacak)
Döngü: 0/8 · Yeniden tasarım: 0/2 · Bu hata için deneme: 0/3
## Notlar
- Kapılar `./make <hedef>` ile çalıştırılır (K-002). Python: .venv/Scripts/python.exe (3.12).
- data/raw: 52 dosya tam (2000-2025 Base+Advanced). oyuncu_sezon.csv: 12.810 satır.
- Konsol cp1254: ad-hoc python çıktısında PYTHONIOENCODING=utf-8 kullan.
## Plan (Faz 3)
- [ ] 3.1 test_oznitelik.py + test_sizinti.py (kırmızı)
- [ ] 3.2 oznitelik.py: hız, lag (ardışık kontrol), ağırlıklı, trend, yaş/kariyer, takım değişimi
- [ ] 3.3 make oznitelik → oznitelikler.csv; kapılar K5 + regresyon
## Son kapı sonuçları (2026-10-04)
Faz 0: K1 ✅ K2 ✅ K3 ✅ K9 ✅ · Faz 1: make veri ✅, make test 22 passed, make test-veri 13 passed, lint ✅
Faz 2: make eda ✅, tepe yaş 27, 3 grafik + eda_bulgular.md, make test 26 passed
## KISMİ işaretli maddeler
(yok)
