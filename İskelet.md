# İskelet.md — Proje İskeleti ve Sınırları

> Bu dosya projenin **yapısını** (ne nerede durur, hangi fonksiyon neyi döndürür) ve
> **sınırlarını** (ne yapılır, ne asla yapılmaz) tanımlar. CLAUDE.md "ne ve neden",
> Agent.md "nasıl çalışılır" sorusunu cevaplar; bu dosya "hangi çerçevede" sorusunu cevaplar.
> Bu dosyadaki bir kuralı değiştirmek **kapsam değişikliğidir**: ajan bunu yapmaz.

---

## 1. Klasör Yapısı

```
nba-sayi-tahmini/
├── CLAUDE.md                  # Proje rehberi (otomatik okunur)
├── İskelet.md                 # Bu dosya
├── .claude/
│   ├── agents/Agent.md        # Otonom ajan tanımı
│   └── settings.json          # İzin verilen komutlar
├── KARARLAR.md                # Ajanın verdiği her karar + gerekçe
├── README.md                  # Faz 6'da yazılır (şablon §6)
├── requirements.txt
├── Makefile
├── config.yaml                # Tüm sabitler (§5)
├── pytest.ini                 # Test işaretleri: veri, rapor (§9)
├── .gitignore                 # .venv/, __pycache__/, models/*.joblib
├── data/
│   ├── raw/                   # API önbelleği: {olcum}_{yil}.csv — ASLA silinmez
│   └── processed/             # oyuncu_sezon.csv, oznitelikler.csv
├── src/
│   ├── __init__.py
│   ├── ayarlar.py             # config.yaml okuyucu
│   ├── veri_topla.py          # nba_api + önbellek + birleştirme
│   ├── hedef.py               # HEDEF_PTS üretimi
│   ├── eda.py                 # Faz 2 grafikleri ve bulgular
│   ├── oznitelik.py           # Faz 3
│   ├── bolme.py               # Zamansal bölme
│   ├── baseline.py            # Naif + Marcel
│   ├── model.py               # Ridge, RF, LightGBM, quantile
│   ├── degerlendir.py         # Metrikler + test seti koruması
│   ├── yorumla.py             # SHAP, kısmi bağımlılık, hata analizi
│   └── tahmin.py              # 2026-27 tahmini
├── tests/
│   ├── conftest.py            # Sentetik veri fixture'ları (ağ gerektirmez)
│   └── test_*.py              # Katalog §9
├── models/                    # en_iyi_model.joblib, quantile modelleri
├── reports/
│   ├── figures/
│   ├── eda_bulgular.md
│   ├── metrikler.json
│   ├── model_karsilastirma.md
│   ├── hata_analizi.md
│   ├── tahmin_2026_27.csv
│   └── test_kullanildi.flag
├── app/streamlit_app.py
├── notebooks/                 # Yalnızca keşif, pipeline'a dahil değil
└── logs/
    ├── DURUM.md               # Anlık durum (ajan her iterasyonda günceller)
    └── ilerleme.md            # Kronolojik günlük
```

---

## 2. Modül Arayüzleri

Fonksiyon adları ve imzaları sabittir; modüller arası tutarlılık bunlara dayanır.

| Modül | Fonksiyon | Girdi → Çıktı |
|---|---|---|
| `ayarlar` | `ayarlari_yukle(yol="config.yaml") -> dict` | YAML → sözlük |
| `veri_topla` | `sezon_cek(yil: int, olcum: str) -> pd.DataFrame` | Önbellek varsa oradan, yoksa API (backoff'lu) |
| `veri_topla` | `tum_sezonlari_topla(bas: int, bit: int) -> pd.DataFrame` | Base + Advanced birleşik tablo |
| `hedef` | `hedef_olustur(df) -> pd.DataFrame` | `HEDEF_PTS` sütunu eklenmiş kopya |
| `oznitelik` | `oznitelik_uret(df) -> pd.DataFrame` | §4'teki sütunlar eklenmiş kopya |
| `oznitelik` | `OZNITELIKLER: list[str]` | Modelin kullanacağı sütun listesi |
| `bolme` | `zamansal_bol(df, ayar) -> dict[str, pd.DataFrame]` | `{"egitim","dogrulama","test","tahmin"}` |
| `baseline` | `naif_tahmin(df) -> pd.Series` | `PTS` |
| `baseline` | `yas_egrisi_hesapla(egitim_df) -> pd.Series` | Yaş → beklenen değişim (yalnız eğitimden) |
| `baseline` | `marcel_tahmin(df, yas_egrisi, agirliklar) -> pd.Series` | Ağırlıklı ort. + yaş düzeltmesi |
| `model` | `modelleri_egit(egitim, dogrulama, ayar) -> dict` | Ad → eğitilmiş model |
| `model` | `quantile_egit(df, alpha: float, ayar)` | LightGBM quantile modeli |
| `degerlendir` | `metrikler(y, tahmin) -> dict` | `{"MAE","RMSE","R2"}` |
| `degerlendir` | `test_seti_degerlendir(model, test, ...) -> dict` | Koruma bayrağını kontrol eder (§7.5) |
| `yorumla` | `shap_ozet(model, X) / kismi_bagimlilik(model, X, "AGE") / hata_tablosu(df)` | Grafik + markdown |
| `tahmin` | `sezon_tahmini(model, alt_model, ust_model, df_2025) -> pd.DataFrame` | Oyuncu, tahmin, alt, üst |

Her modül `python -m src.<modul>` ile çalıştırılabilir olmalı (`if __name__ == "__main__":`).

---

## 3. Veri Sözleşmesi (`data/processed/oyuncu_sezon.csv`)

- **Benzersiz anahtar:** (`PLAYER_ID`, `SEZON_YIL`) — tekrar eden satır yok.
- **Zorunlu sütunlar:** `PLAYER_ID, PLAYER_NAME, TEAM_ABBREVIATION, SEZON_YIL, AGE, GP, MIN,
  PTS, FGA, FG3A, FTA, AST, REB, TOV, USG_PCT, TS_PCT, HEDEF_PTS`
- **Değer aralıkları:** `AGE` 18-45 · `GP` 1-85 · `MIN` 0-48 · `PTS` ≥ 0 · `USG_PCT` 0-1 · `TS_PCT` 0-1.5 (az şutlu oyuncularda uç değer olabilir)
- **`HEDEF_PTS`:** Sonraki satır `SEZON_YIL + 1` değilse NaN. Son sezonda (2025) her zaman NaN.
- **Kapsam:** `SEZON_YIL` 2000-2025 aralığındaki 26 yılın her biri en az 350 satır içerir.

---

## 4. Öznitelik Listesi

Tümü yalnızca t ve öncesine aittir. Gecikmeli sütunlarda ardışık sezon kontrolü zorunlu
(t-1 satırı gerçekten `SEZON_YIL - 1` değilse NaN).

| Grup | Sütunlar |
|---|---|
| Ham (t) | `AGE, GP, MIN, PTS, FGA, FTA, AST, REB, TOV, USG_PCT, TS_PCT` |
| Hız (t) | `PTS_36, FGA_36, FTA_36` (= değer / MIN × 36; MIN = 0 ise NaN), `FG3A_ORAN` (= FG3A / FGA; FGA = 0 ise NaN) |
| Geçmiş | `PTS_L1, PTS_L2, MIN_L1, PTS_36_L1, GP_L1` |
| Ağırlıklı | `PTS_AGIRLIKLI` = 5·PTS + 4·PTS_L1 + 3·PTS_L2, mevcut sezonların ağırlık toplamına bölünür |
| Trend | `PTS_TREND = PTS - PTS_L1`, `MIN_TREND = MIN - MIN_L1` |
| Yaş / kariyer | `AGE_KARE`, `GECMIS_SEZON` (veri setindeki önceki sezon sayısı) |
| Bağlam | `TAKIM_DEGISTI` (t-1 → t arasında takım değişti mi; t+1 takımı KULLANILMAZ) |

**Bilinen sınırlama:** 2000 öncesi sezonlar veride olmadığı için 2000-2002 satırlarında
`GECMIS_SEZON` eksik sayar. README'de belirt.

---

## 5. Yapılandırma

**config.yaml**
```yaml
veri:
  baslangic_yil: 2000
  bitis_yil: 2025
  bekleme_sn: 1.0
  max_deneme: 5          # üstel geri çekilme: 2, 4, 8, 16, 32 sn
filtre:
  min_gp: 20
  min_dakika: 10
bolme:
  egitim_son_yil: 2019
  dogrulama_yillari: [2020, 2022]   # kapalı aralık
  test_yillari: [2023, 2024]        # hedefleri 2024-25 ve 2025-26
  tahmin_yil: 2025                  # → 2026-27 tahmini
marcel:
  agirliklar: [5, 4, 3]
model:
  random_state: 42
  ridge_alpha: [0.1, 1, 10, 100]
  rf: {n_estimators: 500, min_samples_leaf: [5, 20]}
  lgbm:
    num_leaves: [15, 31, 63]
    learning_rate: [0.03, 0.1]
    n_estimators: 3000
    early_stopping: 100
aralik: {alt: 0.1, ust: 0.9}
```

**requirements.txt:** `pandas, numpy, scikit-learn, lightgbm, shap, matplotlib, seaborn,
nba_api, pyyaml, joblib, streamlit, pytest, ruff`

**Makefile hedefleri:** `kur, veri, eda, oznitelik, egit, test-degerlendir, yorumla, tahmin,
test, test-veri, test-tam, lint, hepsi`. `hepsi` = `veri eda oznitelik egit test-degerlendir yorumla tahmin`.
(Makefile girintileri TAB karakteri olmalı.)

**.claude/settings.json** — otonom çalışma için izin verilen komutlar:
```json
{
  "permissions": {
    "allow": [
      "Bash(make:*)", "Bash(python:*)", "Bash(python3:*)", "Bash(.venv/bin/python:*)",
      "Bash(.venv/bin/pip:*)", "Bash(pytest:*)", "Bash(ruff:*)",
      "Bash(git init)", "Bash(git add:*)", "Bash(git commit:*)", "Bash(git status)",
      "Bash(git diff:*)", "Bash(git log:*)", "Bash(ls:*)", "Bash(mkdir:*)", "Bash(cat:*)",
      "Edit", "Write"
    ],
    "deny": ["Bash(git push:*)", "Bash(sudo:*)", "Bash(rm -rf:*)"]
  }
}
```

---

## 6. README Şablonu (Faz 6)

Başlıklar bu sırayla ve bu adlarla bulunmalı (`tests/test_rapor.py` kontrol eder):

1. `## Problem` — tek paragraf, gözlem birimi ve hedef
2. `## Veri ve Filtreler` — kaynak, sezon aralığı, filtreler ve seçim etkisi notu
3. `## EDA Bulguları` — yaş eğrisi grafiği, korelasyonlar, hayatta kalma yanlılığı
4. `## Yöntem` — öznitelikler, zamansal bölme şeması, neden rastgele bölme kullanılmadığı
5. `## Sonuçlar` — naif / Marcel / Ridge / RF / LightGBM tablosu (doğrulama ve test MAE)
6. `## Hata Analizi` — en büyük hatalar ve nedenleri
7. `## 2026-27 Tahminleri` — ilk 20 oyuncu, aralıklarıyla
8. `## Sınırlamalar`
9. `## Nasıl Çalıştırılır` — `make kur && make hepsi`
10. `## Sonuç Takibi` — "Nisan 2027'de gerçek sonuçlarla güncellenecek" notu

---

## 7. Proje Sınırları

### 7.1 Kapsam İçi
Normal sezon, maç başı istatistikler, 2000-01 → 2025-26 verisi, tek hedef (`HEDEF_PTS`),
klasik ML modelleri (Ridge, RandomForest, LightGBM), SHAP ile yorumlama, quantile aralıklar,
yerel Streamlit uygulaması.

### 7.2 Kapsam Dışı (yapılmaz, önerilmez bile — yalnızca README "Gelecek Çalışmalar"da anılabilir)
Playoff verisi · play-by-play · şut haritaları · oyuncu takip verisi · sakatlık verisi ·
maaş/kontrat · draft bilgisi · derin öğrenme · canlı veri · bahis · başka ligler ·
iki aşamalı (dakika × hız) model · uygulamayı internete yayınlamak.

### 7.3 Veri Kaynağı Sınırları
- Tek kaynak: `nba_api`. Başka site kazınmaz (Basketball-Reference dahil).
- İstekler arası en az `bekleme_sn`, en fazla `max_deneme` deneme, üstel geri çekilme.
- Önbellekte dosya varsa API'ye gidilmez. `data/raw/` hiçbir koşulda silinmez.

### 7.4 Teknik Sınırlar
- Python 3.11, yalnızca CPU.
- `requirements.txt` dışına paket eklemek ancak zorunluysa ve `KARARLAR.md`'ye gerekçeyle.
- `make hepsi` veri toplama hariç 30 dakikadan kısa sürmeli.

### 7.5 Metodolojik Sınırlar (ihlali = proje geçersiz)
- Rastgele train/test bölmesi yasak; yalnızca §5'teki yıl bazlı bölme.
- Test seti yalnızca `make test-degerlendir` ile kullanılır. İlk çalıştırmada
  `reports/test_kullanildi.flag` dosyasına seçilen modelin adı ve parametre özeti yazılır.
  Bayrak varken **farklı** bir modelle test değerlendirmesi reddedilir; aynı modelle
  yeniden üretim serbesttir.
- Test sonuçlarına bakıp modele, özniteliklere veya hiperparametrelere geri dönülmez.
- `config.yaml`'daki filtre ve bölme değerleri değiştirilmez.
- Yaş eğrisi ve her türlü "öğrenilen" düzeltme yalnızca eğitim setinden hesaplanır.

### 7.6 Dosya Sistemi ve Güvenlik Sınırları
- Yalnızca proje klasörü içinde çalışılır; dışarıda dosya oluşturulmaz/değiştirilmez.
- `sudo`, `rm -rf`, `git push`, global paket kurulumu yasak.
- Ağ erişimi yalnızca PyPI (paket kurulumu) ve NBA istatistik API'si için.
- Hiçbir gizli anahtar, token veya kişisel bilgi dosyaya yazılmaz.

### 7.7 Otonomi Sınırları
İterasyon ve deneme limitleri Agent.md §5'te. Limitler aşıldığında ajan durur ya da
belgelenmiş kısmi sonuçla ilerler; sonsuz döngüye girmez.

---

## 8. Varsayılan Kararlar (Soru Sormak Yerine)

| Durum | Varsayılan karar |
|---|---|
| Aynı oyuncu-sezon için birden fazla satır | GP ağırlıklı ortalama ile birleştir, `TEAM_ABBREVIATION` = son takım |
| Advanced tabloda eşleşmeyen oyuncu | Base satırını tut, advanced sütunlar NaN |
| Eksik geçmiş (çaylak vb.) | LightGBM: NaN bırak · Ridge/RF: medyan doldurma + eksiklik göstergesi (sklearn Pipeline, yalnız eğitimde fit) |
| Hiperparametre arama | Yalnızca §5'teki ızgara; doğrulama MAE'si ile seç |
| Modeller eşit (MAE farkı < 0,02) | Daha basit olanı seç (Ridge > RF > LightGBM) |
| LightGBM Marcel'i yenemiyor | En fazla 3 iyileştirme denemesi (Agent.md §5), sonra dürüstçe raporla |
| Grafik stili | seaborn `whitegrid`, 150 dpi, Türkçe eksen etiketleri |
| Belirsiz isimlendirme | Bu dosyadaki tabloya uy; yoksa Türkçe, küçük harf, alt çizgi |

---

## 9. Test Kataloğu

Birim testleri `conftest.py`'deki **sentetik** verilerle çalışır (ağ yok, hızlı). Gerçek veri
üzerindeki testler `@pytest.mark.veri`, final çıktı testleri `@pytest.mark.rapor` ile işaretlenir.
Bu işaretli testler ilgili dosya yoksa **atlanmaz, başarısız olur**; bu yüzden fazlara göre
çalıştırılır:

- `make test` → `pytest -m "not veri and not rapor"` (her fazda)
- `make test-veri` → `pytest -m veri` (Faz 1 ve sonrası)
- `make test-tam` → `pytest` (Faz 6 ve son kontrol)

İşaretler `pytest.ini` (veya `pyproject.toml`) içinde tanımlanır.

| Dosya | Doğruladığı şey |
|---|---|
| `test_duman.py` | Tüm `src` modülleri import ediliyor |
| `test_veri.py` | Benzersiz anahtar, zorunlu sütunlar, değer aralıkları, 26 yıl kapsamı (§3) |
| `test_hedef.py` | Ardışık olmayan sezonda `HEDEF_PTS` NaN; ardışıkta doğru değer |
| `test_oznitelik.py` | `PTS_36` hesabı, MIN = 0 → NaN, ağırlıklı ortalamada eksik sezon normalizasyonu, lag ardışıklık kontrolü |
| `test_sizinti.py` | Kesme testi (aşağıda) |
| `test_bolme.py` | Yıl kümeleri ayrık ve sıralı; eğitim ⊂ ≤2019; tahmin kümesinde hedef yok |
| `test_model.py` | Tahmin uzunluğu doğru, [0, 40] aralığında, aynı seed ile deterministik |
| `test_koruma.py` | Bayrak varken farklı modelle test değerlendirmesi hata fırlatıyor |
| `test_rapor.py` | README başlıkları (§6), rapor ve grafik dosyalarının varlığı (Faz 6) |

**Sızıntı kesme testi (zorunlu, aynen uygulanır):**
```python
def test_oznitelikler_gelecekten_bagimsiz(sentetik_veri):
    t = 2015
    tam = oznitelik_uret(sentetik_veri)
    kesik = oznitelik_uret(sentetik_veri[sentetik_veri.SEZON_YIL <= t])
    sec = lambda d: (d[d.SEZON_YIL == t].drop(columns=["HEDEF_PTS"], errors="ignore")
                     .sort_values("PLAYER_ID").reset_index(drop=True))
    pd.testing.assert_frame_equal(sec(tam), sec(kesik))
```
Mantık: t sezonunun öznitelikleri, t sonrası veri silindiğinde değişiyorsa gelecekten bilgi sızıyor demektir.
