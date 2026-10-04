# CLAUDE.md — NBA Oyuncu Sayı Tahmini Projesi

> Bu dosya Claude Code tarafından her oturumda otomatik okunur.
> Klasör yapısı, modül arayüzleri ve proje sınırları: **İskelet.md**
> Otonom çalışma döngüsü (tasarla → uygula → kontrol et → düzelt → yeniden tasarla): **.claude/agents/Agent.md**

@İskelet.md
@.claude/agents/Agent.md

---

## 1. Proje Özeti

**Amaç:** Bir NBA oyuncusunun t sezonundaki ve önceki sezonlardaki istatistiklerini kullanarak
t+1 sezonundaki **maç başı sayı ortalamasını (PTS)** tahmin eden bir regresyon sistemi kurmak.

- **Gözlem birimi:** oyuncu-sezon satırı (`PLAYER_ID`, `SEZON_YIL`)
- **Hedef değişken:** `HEDEF_PTS` = aynı oyuncunun bir sonraki ardışık sezondaki maç başı sayısı
- **Altın kural:** t+1 sezonuna ait hiçbir bilgi öznitelik olamaz. Şüphedeysen kullanma.
- **Veri aralığı:** 2000-01 sezonundan 2025-26 sezonuna kadar (`SEZON_YIL` = 2000 … 2025)
- **Nihai tahmin:** 2025-26 verisiyle **2026-27 sezonu** için tahmin + %80 tahmin aralığı

**Proje sahibi:** Bilgisayar mühendisliği son sınıf öğrencisi. Bu bir portföy projesi:
kod okunaklı olmalı, her önemli karar gerekçesiyle belgelenmeli, README bir işe alımcının
5 dakikada anlayacağı netlikte olmalı.

**Başarı tanımı (öncelik sırasıyla):**
1. Uçtan uca tekrar üretilebilir pipeline (`make hepsi` tek komutla çalışır)
2. Sızıntısız, zamana göre doğru bölünmüş değerlendirme
3. Naif baseline'ı doğrulama setinde yenen model
4. Dürüst hata analizi ve yorumlama
5. Marcel baseline'ını yenmek (hedef, zorunlu değil — yenemezse dürüstçe raporla)

---

## 2. Çalışma Modu: OTONOM

- **Kullanıcıya soru sorma, onay bekleme, ara rapor için durma.**
- Belirsizlikte önce İskelet.md'deki **Varsayılan Kararlar** tablosuna bak.
  Orada yoksa en basit ve savunulabilir seçeneği seç, `KARARLAR.md`'ye gerekçesiyle yaz, devam et.
- Her oturumun başında `logs/DURUM.md` dosyasını oku ve kaldığın yerden devam et.
- Çalışma döngüsü ve kalite kapıları Agent.md'de tanımlı. **Kontrol kapıları geçmeden bir
  fazı bitmiş sayma, bir sonraki faza geçme.**
- Tek meşru durma sebepleri Agent.md §7'de listeli (proje tamamlandı veya aşılamaz engel).

---

## 3. Alan Bilgisi (Modelin ve Kontrollerin Dayandığı Basketbol Gerçekleri)

Bu bilgiler hem öznitelik tasarımını hem de "sonuç mantıklı mı?" kontrollerini yönlendirir.

1. **Yaş eğrisi:** Oyuncular genelde ~26-28 yaşına kadar gelişir, 30'lu yaşlardan sonra düşer.
   Delta yöntemiyle hesapla: ardışık iki sezon oynayan oyuncular için `HEDEF_PTS - PTS`
   değişiminin yaşa göre ortalaması. **Öznitelik olarak kullanılacaksa sadece eğitim setinden
   hesapla** (aksi halde sızıntı).
2. **Hayatta kalma yanlılığı:** Performansı çok düşen yaşlı oyuncular ligden çıkar ve veride
   görünmez. Hesaplanan yaş eğrisi düşüşü olduğundan hafif gösterir. EDA raporunda belirt.
3. **Ortalamaya dönüş:** Olağanüstü bir sezonun ardından gerileme, çok kötü bir sezonun ardından
   toparlanma beklenir. Tek sezon yerine çok sezonlu ağırlıklı ortalama kullan.
4. **Sayının ayrıştırılması:** `PTS = MIN × (PTS / MIN)`. Dakika (rol, rotasyon, sakatlık)
   oynaktır; 36 dakika başına sayı (skor üretme hızı) daha istikrarlıdır. İkisinin sezondan
   sezona korelasyonunu EDA'da ayrı ayrı raporla.
5. **Kısa sezonlar:** 2011-12 (lokavt, 66 maç), 2019-20 (pandemi kesintisi), 2020-21 (72 maç).
   Maç başı istatistik kullandığımız için ölçek sorunu yok; hata analizinde bu sezonlara ayrıca bak.
6. **Takas edilen oyuncular:** Aynı sezonda birden fazla takımda oynayanlar. Veri sözleşmesi
   (`PLAYER_ID`, `SEZON_YIL`) benzersizliğini şart koşar; ihlal varsa GP ağırlıklı birleştir.
7. **Seçim etkisi:** Değerlendirme kümesi t+1'de de en az 20 maç oynayanlarla sınırlı. Model
   aslında "oyuncu anlamlı süre alırsa kaç sayı atar?" sorusunu cevaplar. README'de açıkça yaz.
8. **Makullük sınırları:** Maç başı sayı tahminleri [0, 40] aralığında olmalı. Tahmin
   ortalaması, gerçek hedef ortalamasından ±1 sayıdan fazla sapmamalı. Yaşın kısmi etkisi
   genç oyuncularda pozitif, 31+ yaşta negatif olmalı.

---

## 4. Fazlar

Her faz için: **Görevler → Çıktılar → Bitti Tanımı (DoD)**. DoD'deki her madde bir komutla
doğrulanır. Komut çalıştırılıp çıktı okunmadan madde "tamam" işaretlenmez.

### Faz 0 — Kurulum
- **Görevler:** İskelet.md'deki klasör yapısını oluştur; `requirements.txt`, `Makefile`,
  `config.yaml`, `.gitignore` yaz; sanal ortam kur; `git init`; `logs/DURUM.md`,
  `logs/ilerleme.md`, `KARARLAR.md` dosyalarını başlat.
- **Çıktılar:** Çalışan iskelet, boş ama import edilebilir `src/` modülleri.
- **DoD:** `make kur` exit 0 · `make test` exit 0 (en az bir duman testi) · `make lint` 0 hata.

### Faz 1 — Veri Toplama ve Hedef
- **Görevler:** `src/veri_topla.py` ile nba_api `LeagueDashPlayerStats` üzerinden her sezon için
  `Base` ve `Advanced` ölçümleri (PerGame) çek, `data/raw/` altına sezon sezon önbelleğe al
  (önbellek varsa API'ye gitme). İkisini birleştir. `src/hedef.py` ile ardışık sezon kontrolüyle
  `HEDEF_PTS` oluştur.
- **Çıktılar:** `data/processed/oyuncu_sezon.csv`
- **DoD:** `make test` ve `make test-veri` 0 hata · satır sayısı 10.000-15.000
  aralığında · `SEZON_YIL` 2000-2025 aralığının tamamını kapsıyor.

### Faz 2 — Keşifsel Analiz (EDA)
- **Görevler:** `src/eda.py` ile yaş eğrisi (delta yöntemi), ortalamaya dönüş grafiği,
  PTS / MIN / PTS_36 için sezondan sezona korelasyonları üret.
- **Çıktılar:** `reports/figures/yas_egrisi.png`, `ortalamaya_donus.png`,
  `ardisik_korelasyon.png`; `reports/eda_bulgular.md` (tepe yaş, korelasyon değerleri,
  hayatta kalma yanlılığı notu — sayılarla).
- **DoD:** Üç grafik dosyası mevcut · `eda_bulgular.md` sayısal tepe yaşı ve üç korelasyonu
  içeriyor · tepe yaş 24-30 aralığında (değilse kodu hatalı kabul et ve incele).

### Faz 3 — Öznitelik Mühendisliği
- **Görevler:** `src/oznitelik.py` ile İskelet.md §4'teki öznitelik listesini üret. Gecikmeli
  (lag) özniteliklerde ardışık sezon kontrolü uygula. Eksik geçmişi NaN bırak + `GECMIS_SEZON`.
- **Çıktılar:** `data/processed/oznitelikler.csv`
- **DoD:** `pytest tests/test_sizinti.py tests/test_oznitelik.py` 0 hata.

### Faz 4 — Baseline'lar, Bölme ve Modelleme
- **Görevler:** `src/bolme.py` (zamansal bölme), `src/baseline.py` (naif + Marcel),
  `src/model.py` (Ridge, RandomForest, LightGBM), `src/degerlendir.py` (MAE, RMSE, R²).
  Hiperparametre ayarı yalnızca eğitim + doğrulama setiyle. En iyi modeli doğrulama MAE'sine
  göre seç. **Test seti bu fazın sonunda yalnızca bir kez**, seçilen model ve iki baseline için
  kullanılır.
- **Çıktılar:** `models/en_iyi_model.joblib`, `reports/metrikler.json`,
  `reports/model_karsilastirma.md`
- **DoD:** `pytest tests/test_bolme.py tests/test_model.py` 0 hata · doğrulama MAE'si naif
  baseline'dan düşük · `reports/test_kullanildi.flag` tam bir kez oluşturulmuş.

### Faz 5 — Hata Analizi ve Yorumlama
- **Görevler:** `src/yorumla.py` ile SHAP özet grafiği, yaş için kısmi bağımlılık grafiği
  (EDA'daki yaş eğrisiyle karşılaştır), hata dağılımı (yaş grubu, önceki GP, takım değişikliği,
  kısa sezonlar), en büyük 10 hata (isimleriyle, birer cümlelik açıklama).
- **Çıktılar:** `reports/figures/shap_ozet.png`, `yas_kismi_bagimlilik.png`,
  `reports/hata_analizi.md`
- **DoD:** Dosyalar mevcut · Makullük sınırları (§3.8) sağlanıyor · yaş kısmi etkisinin
  işaretleri beklentiyle uyumlu (uyumsuzsa nedenini `hata_analizi.md`'de açıkla).

### Faz 6 — 2026-27 Tahmini ve Sunum
- **Görevler:** En iyi modeli eğitim + doğrulama + test verisiyle yeniden eğit. LightGBM
  quantile (alpha 0.1 ve 0.9) ile %80 tahmin aralığı üret. 2025-26 satırlarından
  (GP ≥ 20, MIN ≥ 10) 2026-27 tahminlerini yaz. `app/streamlit_app.py` hazırla (yalnızca
  yerelde; yayınlama kullanıcıya ait). README'yi İskelet.md §6'daki şablonla yaz.
- **Çıktılar:** `reports/tahmin_2026_27.csv` (oyuncu, tahmin, alt, üst), `README.md`,
  `app/streamlit_app.py`
- **DoD:** `make hepsi` temiz klonda baştan sona exit 0 · `make test-tam` 0 hata ·
  `python -c "import app.streamlit_app"` exit 0 · README tüm başlıkları içeriyor ·
  aralıkların ≥%95'inde alt ≤ tahmin ≤ üst.

---

## 5. Kod Standartları

- Python 3.11, tip ipuçları zorunlu, her public fonksiyonda Türkçe docstring.
- Değişken ve sütun adları Türkçe karakter içermez (`SEZON_YIL`, `HEDEF_PTS`, `yas_egrisi`).
- Sabit değerler koda gömülmez; `config.yaml`'dan okunur (`src/ayarlar.py`).
- Rastgelelik: her yerde `random_state = 42`.
- `print` yerine `logging`. Hata yutma (`except: pass`) yasak.
- Fonksiyonlar mümkün olduğunca saf: DataFrame alır, yeni DataFrame döndürür, girdiyi değiştirmez.
- Notebook'lar yalnızca keşif içindir (`notebooks/`); doğruluğun kaynağı `src/` ve `make`'tir.
- Her fazın sonunda yerel git commit'i: `git commit -m "faz-N: <özet>"`.

## 6. Komutlar

```
make kur         # sanal ortam + bağımlılıklar
make veri        # Faz 1
make eda         # Faz 2
make oznitelik   # Faz 3
make egit        # Faz 4 (doğrulama)
make test-degerlendir  # Faz 4 sonu, test setini bir kez kullanır
make yorumla     # Faz 5
make tahmin      # Faz 6
make test        # birim testleri (sentetik veri)
make test-veri   # gerçek veri testleri (Faz 1+)
make test-tam    # tüm testler (Faz 6 ve son kontrol)
make lint        # ruff
make hepsi       # veri → tahmin, tüm zincir
```

## 7. Kesin Yasaklar (özet — tam liste İskelet.md §7)

- Testi geçirmek için testi zayıflatmak veya silmek.
- Test setini hiperparametre ayarı, model seçimi veya öznitelik seçimi için kullanmak.
- t+1 bilgisini öznitelik yapmak; yaş eğrisini tüm veriden hesaplayıp öznitelik yapmak.
- `data/raw/` önbelleğini silmek; proje klasörü dışında dosya değiştirmek; `git push`.
- Kullanıcıya soru sormak veya onay beklemek.
