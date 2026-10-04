# DURUM
Aktif faz: 6 — 2026-27 Tahmini ve Sunum
Aktif adım: 6.1 tahmin.py (başlanacak)
Döngü: 0/8 · Yeniden tasarım: 0/2 · Bu hata için deneme: 0/3
## Notlar
- Kapılar `./make <hedef>` ile çalıştırılır (K-002). Python: .venv/Scripts/python.exe (3.12).
- data/raw: 52 dosya tam (2000-2025 Base+Advanced). oyuncu_sezon.csv: 12.810 satır.
- Konsol cp1254: ad-hoc python çıktısında PYTHONIOENCODING=utf-8 kullan.
## Plan (Faz 6)
- [ ] 6.1 tahmin.py: secilen model eğitim+doğrulama+test ile yeniden eğit (yeniden_egit), quantile 0.1/0.9 (lgbm_parametreler), 2025 satırları → reports/tahmin_2026_27.csv (oyuncu, tahmin, alt, üst) ; models/ altına kaydet
- [ ] 6.2 test_tahmin.py (sentetik) + test_rapor.py (@rapor: README başlıkları, dosyalar, aralık ≥%95)
- [ ] 6.3 app/streamlit_app.py (main() içinde, import yan etkisiz)
- [ ] 6.4 README.md (§6 şablonu, sayılar reports/'tan)
- [ ] 6.5 Temiz durum: üretilen dosyaları sil (data/raw + test_kullanildi.flag hariç) → make hepsi → make test-tam → python -c "import app.streamlit_app"
- [ ] 6.6 FINAL_RAPOR.md + son commit
## ÖNEMLİ
- Test seti KULLANILDI (bayrak: ridge alpha=0.1). Tekrar `make test-degerlendir` yalnız aynı modelle. Modele/özniteliklere geri dönülmez.
## Son kapı sonuçları (2026-10-04)
Faz 0: K1 ✅ K2 ✅ K3 ✅ K9 ✅ · Faz 1: make veri ✅, make test 22 passed, make test-veri 13 passed, lint ✅
Faz 2: make eda ✅, tepe yaş 27, 3 grafik + eda_bulgular.md, make test 26 passed
Faz 3: make oznitelik ✅, sızıntı+öznitelik 9 passed, make test 35 passed, lint ✅
Faz 5: yorumla ✅ (12 sn), makullük 4/4 ✅, make test 55 passed
Faz 4: egit ✅, test 51 passed, K6/K7/K8 ✅, test MAE ridge 2.402 / naif 2.568 / marcel 2.565
## KISMİ işaretli maddeler
(yok)
