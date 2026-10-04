# DURUM
Aktif faz: 5 — Hata Analizi ve Yorumlama
Aktif adım: 5.1 yorumla.py (başlanacak)
Döngü: 0/8 · Yeniden tasarım: 0/2 · Bu hata için deneme: 0/3
## Notlar
- Kapılar `./make <hedef>` ile çalıştırılır (K-002). Python: .venv/Scripts/python.exe (3.12).
- data/raw: 52 dosya tam (2000-2025 Base+Advanced). oyuncu_sezon.csv: 12.810 satır.
- Konsol cp1254: ad-hoc python çıktısında PYTHONIOENCODING=utf-8 kullan.
## Plan (Faz 5)
- [ ] 5.1 yorumla.py: shap_ozet (Ridge → LinearExplainer / genel Explainer, doğrulamadan 2000 örnek), kismi_bagimlilik (AGE, AGE_KARE birlikte değişir!), hata_tablosu
- [ ] 5.2 hata analizi DOĞRULAMA kümesinde (test tekrar kullanılmaz); test özetini metrikler.json'dan al
- [ ] 5.3 makullük §3.8: [0,40], ort sapma ±1, yaş etkisi işaretleri
- [ ] 5.4 test_yorumla.py ; kapılar
## ÖNEMLİ
- Test seti KULLANILDI (bayrak: ridge alpha=0.1). Tekrar `make test-degerlendir` yalnız aynı modelle. Modele/özniteliklere geri dönülmez.
## Son kapı sonuçları (2026-10-04)
Faz 0: K1 ✅ K2 ✅ K3 ✅ K9 ✅ · Faz 1: make veri ✅, make test 22 passed, make test-veri 13 passed, lint ✅
Faz 2: make eda ✅, tepe yaş 27, 3 grafik + eda_bulgular.md, make test 26 passed
Faz 3: make oznitelik ✅, sızıntı+öznitelik 9 passed, make test 35 passed, lint ✅
Faz 4: egit ✅, test 51 passed, K6/K7/K8 ✅, test MAE ridge 2.402 / naif 2.568 / marcel 2.565
## KISMİ işaretli maddeler
(yok)
