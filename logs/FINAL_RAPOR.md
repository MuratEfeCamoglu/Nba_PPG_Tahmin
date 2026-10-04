# FINAL RAPOR — NBA Oyuncu Sayı Tahmini

Tarih: 2026-10-04

## 1. Özet

nba_api'den 2000-01 → 2025-26 arası 12.810 oyuncu-sezon satırı toplandı, sızıntısız 26
öznitelik üretildi ve yıl bazlı bölmeyle naif, Marcel, Ridge, RandomForest ve LightGBM
karşılaştırıldı. Doğrulama MAE'sine göre (eşitlik kuralıyla) **Ridge (α = 0,1)** seçildi:
doğrulama MAE **2.244** (naif 2.381, Marcel 2.471), tek seferlik test MAE **2.402** (naif
2.568, Marcel 2.565) — naiften 0.166, Marcel'den 0.163 sayı daha iyi. Model tüm etiketli
veriyle yeniden eğitilip 406 oyuncu için 2026-27 tahmini ve LightGBM quantile ile %80 aralık
üretildi (doğrulamada gerçek kapsama %78,7).

## 2. Kapı kanıtları (son iterasyon, 2026-10-04)

- **Temiz durumdan `make hepsi`** (`data/raw` ve test bayrağı hariç tüm üretilen dosyalar
  silindikten sonra, `./make hepsi` → mini_make): exit 0, 60 sn. `veri → eda → oznitelik →
  egit → test-degerlendir ("Bayrak mevcut ve model aynı: yeniden üretim") → yorumla → tahmin`.
  Ardından `git status` boş: tüm çıktılar commit edilmiş sürümlerle bayt düzeyinde aynı.
- **`make test-tam`**: 86 passed / 86 (0 başarısız, 0 hata).
- `make test` 57 passed · `make test-veri` 13 passed · `pytest -m rapor` 16 passed.
- `make lint` (ruff): All checks passed.
- `python -c "import app.streamlit_app"`: exit 0; Streamlit AppTest ile uygulama istisnasız çizildi.
- README §6 başlıkları sıralı ve tam (`test_rapor.py`); README sayıları `reports/` ile birebir.
- Tahmin tablosu: alt ≤ tahmin ≤ üst oranı 0,998 (≥ 0,95); tahminler [0, 40] içinde.
- Önceki fazlar: K4 veri sözleşmesi ✅, tepe yaş 27 ✅, K5 sızıntı ✅ (mutasyonla doğrulandı),
  K6 bölme ✅, K7 ✅ (doğrulama MAE < naif ve < Marcel), K8 bayrak tek modelle ✅, makullük 4/4 ✅,
  K9 ✅ (git push yok, kapsam dışı iş yok).

## 3. KISMİ maddeler

Yok. Not: gerçek bir "temiz klon" testi proje klasörü dışında dosya oluşturmayı gerektirdiğinden
yapılmadı; yerine Agent.md §6'daki "üretilen her dosya silinmiş" temiz durum tanımı uygulandı
(K-018).

## 4. Önemli kararlar (KARARLAR.md)

1. **K-002 — make yok:** gerçek TAB girintili `Makefile` tek doğruluk kaynağı; GNU make
   olmayan makinede `./make` / `make.bat` sarmalayıcıları aynı Makefile'ı stdlib tabanlı
   `mini_make.py` ile çalıştırır (GNU make varsa doğrudan onu kullanır).
2. **K-001 — Python 3.12:** 3.11 yüklü değildi ve global kurulum yasaktı; venv 3.12 ile kuruldu,
   kod 3.11 uyumlu (ruff target py311), bağımlılıklar sürüm sabitli (K-004).
3. **K-011 — lag'ler birleştirmeyle:** (PLAYER_ID, SEZON_YIL−k) birleştirmesi sezon
   boşluklarında yanlış değeri imkânsız kılar; sızıntı kesme testi birden çok yılda uygulanır.
4. **K-013/K-015 — seçim ve test:** fark < 0,02 kuralıyla Ridge seçildi; seçim test öncesi
   commit edildi (2fd599b), test bir kez ve doğrulanan modelin aynısıyla kullanıldı.
5. **K-014 — determinizm:** RandomForest paralel tahmindeki 1e-16 düzeyindeki toplama sırası
   farkı giderildi; böylece bayrak kimliği ve tüm çıktılar bayt düzeyinde tekrar üretilebilir.

## 5. Kullanıcının yapacakları

- README ve `reports/` altındaki raporları (özellikle `hata_analizi.md`) gözden geçirmek.
- (İsteğe bağlı) Streamlit uygulamasını Hugging Face Spaces'e yüklemek
  (`.venv/Scripts/python.exe -m streamlit run app/streamlit_app.py` ile yerelde deneyin).
- Uzak depo oluşturup `git push` yapmak (ajan push yapmadı).
- Nisan 2027'de gerçek 2026-27 sonuçlarıyla README'deki "Sonuç Takibi" bölümünü güncellemek.
