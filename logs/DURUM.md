# DURUM
Aktif faz: 4 — Baseline'lar, Bölme ve Modelleme
Aktif adım: 4.6 make test-degerlendir (seçim commit edildi: ridge alpha=0.1; test henüz kullanılmadı)
Döngü: 0/8 · Yeniden tasarım: 0/2 · Bu hata için deneme: 0/3
## Notlar
- Kapılar `./make <hedef>` ile çalıştırılır (K-002). Python: .venv/Scripts/python.exe (3.12).
- data/raw: 52 dosya tam (2000-2025 Base+Advanced). oyuncu_sezon.csv: 12.810 satır.
- Konsol cp1254: ad-hoc python çıktısında PYTHONIOENCODING=utf-8 kullan.
## Plan (Faz 4)
- [ ] 4.1 bolme.py + test_bolme.py (filtre: t'de GP>=20 & MIN>=10; t+1 GP>=20 + HEDEF_PTS dolu)
- [ ] 4.2 baseline.py (naif, yas_egrisi_hesapla yalnız eğitim, marcel) + test
- [ ] 4.3 degerlendir.py (metrikler, test_seti_degerlendir + bayrak) + test_koruma.py
- [ ] 4.4 model.py (Ridge/RF/LGBM ızgara, doğrulama MAE ile seçim, quantile_egit) + test_model.py
- [ ] 4.5 make egit → metrikler.json (doğrulama) ; K7 kontrol ; Marcel denemeleri (≤3)
- [ ] 4.6 make test-degerlendir (TEK SEFER) → model_karsilastirma.md, flag
## Son kapı sonuçları (2026-10-04)
Faz 0: K1 ✅ K2 ✅ K3 ✅ K9 ✅ · Faz 1: make veri ✅, make test 22 passed, make test-veri 13 passed, lint ✅
Faz 2: make eda ✅, tepe yaş 27, 3 grafik + eda_bulgular.md, make test 26 passed
Faz 3: make oznitelik ✅, sızıntı+öznitelik 9 passed, make test 35 passed, lint ✅
## KISMİ işaretli maddeler
(yok)
