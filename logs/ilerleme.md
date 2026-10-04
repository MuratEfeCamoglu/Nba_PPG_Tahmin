# İlerleme Günlüğü

## 2026-10-04 — Faz 0, döngü 1
Yapılan: klasör yapısı, git init, Python 3.12 venv, requirements (sabit sürümler), config.yaml, Makefile + mini_make.py/./make/make.bat, src iskeleti, conftest + test_duman · Kapılar: K1 ✅ (make kur exit 0) K2 ✅ (13 passed) K3 ✅ (ruff temiz) K9 ✅ · Sonraki: Faz 1 veri toplama.

## 2026-10-04 — Faz 1, döngü 1
Yapılan: veri_topla.py (önbellek + 5 deneme üstel geri çekilme, timeout 60), hedef.py, test_hedef/test_veri_topla/test_veri; 52 önbellek dosyası çekildi (API hatası yok) · Kapılar: K1 ✅ make veri exit 0 · K2 ✅ make test 22 passed, make test-veri 13 passed · K3 ✅ · K4 ✅ · K10 ✅ (oyuncu_sezon.csv 12.810 satır, 26 yıl) · Sonraki: Faz 2 EDA.

## 2026-10-04 — Faz 2, döngü 1
Yapılan: eda.py (delta yaş eğrisi, ortalamaya dönüş, ardışık korelasyon, hayatta kalma tablosu), test_eda.py; tepe_yas KeyError düzeltildi (kümülatif fonksiyon içinde hesaplanıyor) · Kapılar: make eda ✅ · make test 26 passed · make test-veri 13 passed · lint ✅ · K10 ✅ · tepe yaş 27 ✅ · Sonraki: Faz 3 öznitelik.

## 2026-10-04 — Faz 3, döngü 1
Yapılan: oznitelik.py (26 öznitelik), test_oznitelik.py (7), test_sizinti.py (2) · Kapılar: make oznitelik ✅ · test_sizinti+test_oznitelik 9 passed · make test 35 passed · make test-veri 13 passed · lint ✅ (1 uzun satır düzeltildi) · K5 ✅ · Sonraki: Faz 4.

## 2026-10-04 — Faz 4, döngü 1-2
Yapılan: bolme.py, baseline.py, degerlendir.py (koruma bayrağı), model.py (ızgara, seçim, quantile, yeniden_egit); testler test_bolme/test_baseline/test_koruma/test_model. Döngü 2: RF paralel tahmin determinizmi düzeltildi (K-014). Seçim test öncesi commit edildi; test seti bir kez kullanıldı · Kapılar: make egit ✅ · make test 51 passed (2 kez) · make test-veri 13 passed · lint ✅ · K6 ✅ · K7 ✅ (Ridge 2,244 < naif 2,381 < Marcel 2,471) · K8 ✅ (bayrak: ridge α=0,1) · alarm yok · Sonraki: Faz 5.
