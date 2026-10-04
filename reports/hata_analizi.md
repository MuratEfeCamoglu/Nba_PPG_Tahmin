# Hata Analizi ve Yorumlama

Model: **Ridge** `{"alpha": 0.1}` (yalnız eğitim kümesinde eğitilmiş). Analiz kümesi: **doğrulama** (2020-2022, n = 1009). Doğrulama MAE 2.244, RMSE 2.866, R² 0.821. Test MAE (bir kez, `metrikler.json`): 2.402.

## Makullük kontrolleri (CLAUDE.md §3.8)

| Kontrol | Sonuç | Değer |
|---|---|---|
| Tahminler [0, 40] aralığında | ✅ | min 1.43, max 33.29 |
| Ortalama tahmin, gerçek ortalamadan ±1 içinde | ✅ | tahmin 11.74 / gerçek 11.25 |
| Yaş kısmi etkisi ≤23 yaşta pozitif | ✅ | [2.71, 2.27, 1.84, 1.44, 1.05] |
| Yaş kısmi etkisi 31+ yaşta negatif | ✅ | [-1.27, -1.46, -1.64, -1.79, -1.93, -2.04, -2.13, -2.2, -2.25, -2.28] |

Ortalama yanlılık (tahmin − gerçek): **+0.49** sayı. Model doğrulama yıllarında hafifçe fazla tahmin ediyor; yanlılık en çok çaylaklarda (t−1 sezonu yok) ve az maç oynamış oyuncularda büyük (aşağıdaki tablolar).

## Yaş kısmi bağımlılığı ve EDA karşılaştırması

Kısmi bağımlılık: doğrulama kümesindeki her oyuncunun yaşı (ve AGE_KARE) sabit bir değere ayarlanıp diğer öznitelikler korunarak ortalama tahmin alındı; *beklenen değişim* = ortalama tahmin − ortalama PTS(t). Grafik: `figures/yas_kismi_bagimlilik.png`.

| Yaş | Model beklenen değişim | EDA ortalama değişim |
|---|---|---|
| 19 | +2.71 | +2.21 |
| 20 | +2.27 | +2.70 |
| 21 | +1.84 | +1.85 |
| 22 | +1.44 | +1.27 |
| 23 | +1.05 | +0.95 |
| 24 | +0.69 | +0.62 |
| 25 | +0.35 | +0.12 |
| 26 | +0.03 | -0.03 |
| 27 | -0.27 | -0.24 |
| 28 | -0.55 | -0.74 |
| 29 | -0.81 | -0.61 |
| 30 | -1.05 | -0.99 |
| 31 | -1.27 | -1.07 |
| 32 | -1.46 | -1.21 |
| 33 | -1.64 | -1.39 |
| 34 | -1.79 | -1.62 |
| 35 | -1.93 | -1.47 |
| 36 | -2.04 | -1.61 |
| 37 | -2.13 | -2.64 |
| 38 | -2.20 | — |
| 39 | -2.25 | — |
| 40 | -2.28 | — |

Model, Ridge'de AGE ve AGE_KARE ile ikinci dereceden bir yaş etkisi öğrenir; eğri EDA'daki delta eğrisiyle aynı yönde (gençlerde artış, 30'lardan sonra düşüş). Modelin eğrisi EDA'dan daha düzgündür ve diğer öznitelikler (ağırlıklı ortalama, trend, dakika) ortalamaya dönüşün bir kısmını üstlendiği için genlikleri farklıdır.

## SHAP — en etkili öznitelikler

Ortalama |SHAP| (sayı cinsinden tahmine katkı), doğrulama kümesi. Grafik: `figures/shap_ozet.png`.

| Öznitelik | Ortalama \|SHAP\| |
|---|---|
| PTS | 4.607 |
| AGE | 2.957 |
| PTS_AGIRLIKLI | 2.689 |
| AGE_KARE | 1.953 |
| FGA | 1.510 |
| MIN | 0.699 |
| USG_PCT | 0.545 |
| PTS_36 | 0.544 |
| AST | 0.365 |
| FTA | 0.361 |

## Hata dağılımı (doğrulama)

### Yaş grubu (t)

| Yaş grubu (t) | N | MAE | Ort. hata (tahmin − gerçek) |
|---|---|---|---|
| ≤23 | 303 | 2.607 | +0.707 |
| 24-27 | 342 | 2.210 | +0.460 |
| 28-30 | 187 | 1.936 | +0.384 |
| 31-33 | 114 | 2.344 | +0.441 |
| 34+ | 63 | 1.417 | +0.046 |

### Önceki sezon GP (t)

| Önceki sezon GP (t) | N | MAE | Ort. hata (tahmin − gerçek) |
|---|---|---|---|
| 20-39 | 118 | 2.431 | +1.059 |
| 40-59 | 336 | 2.154 | +0.590 |
| 60+ | 555 | 2.259 | +0.312 |

### Takım değişikliği (t−1 → t)

| Takım değişikliği (t−1 → t) | N | MAE | Ort. hata (tahmin − gerçek) |
|---|---|---|---|
| Aynı takım | 606 | 2.233 | +0.276 |
| Takım değişti | 281 | 2.071 | +0.731 |
| t−1 sezonu yok | 122 | 2.698 | +1.015 |

### Sezon (t)

| Sezon (t) | N | MAE | Ort. hata (tahmin − gerçek) |
|---|---|---|---|
| 2020-21 | 338 | 2.204 | +0.287 |
| 2021-22 | 336 | 2.283 | +0.415 |
| 2022-23 | 335 | 2.246 | +0.777 |

## Kısa sezonlar (ileriye dönük geriye test, 2005-2022)

Doğrulama kümesi yalnızca 2020-21'i (72 maç) içerdiği için kısa sezonlar, seçilen model yapılandırması her yıl yalnızca geçmiş yıllarla yeniden eğitilerek 2005-2022 yıllarında incelendi (genel MAE 2.227; test yılları dahil değil). Kısa sezonlar: 2011-12 (lokavt, 66 maç), 2019-20 (pandemi kesintisi), 2020-21 (72 maç).

| Sezon türü | N | MAE | Ort. hata (tahmin − gerçek) |
|---|---|---|---|
| Normal | 4062 | 2.220 | +0.074 |
| t kısa sezon (2011-12) | 306 | 2.188 | -0.306 |
| t kısa sezon (2019-20) | 318 | 2.397 | -0.018 |
| t kısa sezon (2020-21) | 338 | 2.204 | +0.287 |
| t+1 kısa sezon (2011-12) | 306 | 2.024 | +0.234 |
| t+1 kısa sezon (2019-20) | 312 | 2.405 | -0.093 |

## En büyük 10 hata (doğrulama)

| Oyuncu | Sezon (t) | Yaş | PTS(t) | Tahmin | Gerçek (t+1) | Hata | Açıklama |
|---|---|---|---|---|---|---|---|
| Lauri Markkanen | 2021-22 | 25 | 14.8 | 14.8 | 25.6 | -10.8 | t+1'de beklenenden çok daha fazla sayı attı: takım değiştirdi (CLE → UTA). |
| Christian Wood | 2022-23 | 27 | 16.6 | 17.1 | 6.9 | +10.2 | t+1'de beklenenden az sayı attı: dakikası 25.9 → 17.4 düştü (rol kaybı/sakatlık), takım değiştirdi (DAL → LAL). |
| Cam Thomas | 2022-23 | 21 | 10.6 | 12.3 | 22.5 | -10.2 | t+1'de beklenenden çok daha fazla sayı attı: dakikası 16.6 → 31.4 arttı (rol büyümesi), 21 yaşında beklenmedik bir sıçrama yaptı. |
| KJ Martin | 2022-23 | 22 | 12.7 | 13.6 | 3.7 | +9.9 | t+1'de beklenenden az sayı attı: dakikası 28.0 → 12.4 düştü (rol kaybı/sakatlık), takım değiştirdi (HOU → PHI). |
| AJ Griffin | 2022-23 | 19 | 8.9 | 11.7 | 2.4 | +9.3 | t+1'de beklenenden az sayı attı: dakikası 19.5 → 8.5 düştü (rol kaybı/sakatlık), t+1'de yalnızca 20 maç oynadı. |
| Damian Lillard | 2021-22 | 31 | 24.0 | 23.0 | 32.2 | -9.2 | t+1'de beklenenden çok daha fazla sayı attı: t sezonunda yalnızca 29 maç oynamıştı (sakatlık/kısa sezon). |
| Jalen Brunson | 2021-22 | 25 | 16.3 | 15.7 | 24.0 | -8.3 | t+1'de beklenenden çok daha fazla sayı attı: takım değiştirdi (DAL → NYK). |
| Jalen Johnson | 2022-23 | 21 | 5.6 | 7.7 | 16.0 | -8.3 | t+1'de beklenenden çok daha fazla sayı attı: dakikası 14.9 → 33.7 arttı (rol büyümesi), 21 yaşında beklenmedik bir sıçrama yaptı. |
| Terry Taylor | 2021-22 | 22 | 9.6 | 10.8 | 2.9 | +7.9 | t+1'de beklenenden az sayı attı: dakikası 21.6 → 8.5 düştü (rol kaybı/sakatlık), takım değiştirdi (IND → CHI), t+1'de yalnızca 31 maç oynadı. |
| Montrezl Harrell | 2021-22 | 28 | 13.1 | 13.5 | 5.6 | +7.9 | t+1'de beklenenden az sayı attı: dakikası 23.1 → 11.9 düştü (rol kaybı/sakatlık), takım değiştirdi (CHA → PHI). |

**Genel yorum:** En büyük hatalar, modelin t anında göremediği rol değişikliklerinden (dakika artışı/azalışı, takım değişikliği) ve sakatlıklardan kaynaklanıyor. Bunlar t+1 bilgisi olduğundan öznitelik yapılamaz; modelin sınırıdır.
