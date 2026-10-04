# EDA Bulguları

Kaynak: `data/processed/oyuncu_sezon.csv` · Çiftler: ardışık iki sezonda da GP ≥ 20 ve MIN ≥ 10 olan 7398 oyuncu-sezon çifti (2000-01 → 2025-26, tüm yıllar; yalnızca betimsel — modele girmez).

## Yaş eğrisi (delta yöntemi)

**Tepe yaş: 27.** Ortalama maç başı sayı değişimi bu yaşa kadar pozitif, sonrasında negatif. 

| Yaş (t) | Ortalama değişim (t→t+1) | N | Kümülatif seviye (t+1) |
|---|---|---|---|
| 19 | +1.92 | 49 | +1.92 |
| 20 | +2.25 | 217 | +4.17 |
| 21 | +1.69 | 365 | +5.86 |
| 22 | +1.27 | 505 | +7.13 |
| 23 | +0.75 | 637 | +7.88 |
| 24 | +0.48 | 712 | +8.36 |
| 25 | +0.21 | 691 | +8.57 |
| 26 | +0.02 | 676 | +8.59 |
| 27 | -0.37 | 623 | +8.22 |
| 28 | -0.72 | 576 | +7.50 |
| 29 | -0.62 | 496 | +6.88 |
| 30 | -1.03 | 446 | +5.85 |
| 31 | -1.04 | 372 | +4.81 |
| 32 | -1.19 | 300 | +3.62 |
| 33 | -1.57 | 233 | +2.06 |
| 34 | -1.58 | 175 | +0.48 |
| 35 | -1.45 | 130 | -0.97 |
| 36 | -1.46 | 85 | -2.43 |
| 37 | -2.41 | 47 | -4.84 |
| 38 | -1.64 | 34 | -6.48 |

(Yalnızca en az 30 gözlemi olan yaşlar gösterilir.) Grafik: `figures/yas_egrisi.png`.

## Sezondan sezona korelasyonlar

| Ölçü | Pearson r (t, t+1) |
|---|---|
| PTS (maç başı sayı) | 0.865 |
| MIN (dakika) | 0.758 |
| PTS_36 (36 dakika başına sayı) | 0.857 |

PTS = MIN × (PTS/MIN) ayrıştırmasında skor üretme hızı (PTS_36) dakikadan daha istikrarlı. Grafik: `figures/ardisik_korelasyon.png`.

## Ortalamaya dönüş

Önceki yıl değişimi PTS(t)−PTS(t−1) ile sonraki değişim PTS(t+1)−PTS(t) arasında eğim **-0.086**, korelasyon **-0.091** (n = 6276). Negatif eğim: bir sezonda sayısını çok artıran oyuncu ertesi sezon kısmen geri düşer; tek sezon yerine çok sezonlu ağırlıklı ortalama kullanmanın gerekçesi budur. Grafik: `figures/ortalamaya_donus.png`.

## Hayatta kalma yanlılığı

Delta yöntemi yalnızca ertesi sezon da oynayan oyuncuları görür. Performansı çok düşen (özellikle yaşlı) oyuncular ligden çıkar ve hesaba girmez; bu yüzden yaş eğrisindeki düşüş gerçekte olduğundan **daha hafif** görünür.

| Yaş grubu | N | Ertesi sezon veride yok (çıkış oranı) | Çıkanların ort. PTS | Kalanların ort. PTS |
|---|---|---|---|---|
| ≤23 | 2075 | 5.0% | 6.22 | 9.87 |
| 24-27 | 3241 | 7.4% | 5.97 | 10.85 |
| 28-30 | 1853 | 9.4% | 6.65 | 11.16 |
| 31-33 | 1226 | 14.3% | 5.93 | 10.31 |
| 34+ | 804 | 26.0% | 5.51 | 9.39 |

Çıkış oranı yaşla belirgin biçimde artıyor ve çıkan oyuncuların sayı ortalaması kalanlardan düşük; yani yaşlı gruptaki gözlenen düşüş, ligden çıkanlar hesaba katılsaydı daha sert olurdu. (Not: ertesi sezon veride olmamanın bir kısmı sakatlık veya yurt dışına gitmekten kaynaklanır.)
