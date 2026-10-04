# Model Karşılaştırma

Küme boyutları: eğitim 6066 · doğrulama 1009 · test 665 · tahmin 406 satır.

**Seçilen model:** Ridge — doğrulama MAE'sine göre (fark < 0,02 ise daha basit model tercih edilir).

| Model | Doğrulama MAE | Doğrulama RMSE | Doğrulama R² | Test MAE | Test RMSE | Test R² |
|---|---|---|---|---|---|---|
| Naif (PTS_t) | 2.381 | 3.059 | 0.796 | 2.568 | 3.251 | 0.755 |
| Marcel (5-4-3 + yaş) | 2.471 | 3.144 | 0.785 | 2.565 | 3.268 | 0.752 |
| Ridge ✅ | 2.244 | 2.866 | 0.821 | 2.402 | 3.059 | 0.783 |
| RandomForest | 2.270 | 2.893 | 0.818 | — | — | — |
| LightGBM | 2.233 | 2.860 | 0.822 | — | — | — |

Test sütunları yalnızca seçilen model ve iki baseline için doldurulur; test seti bir kez, model seçimi bittikten sonra kullanılmıştır (`test_kullanildi.flag`).

## Hiperparametre ızgarası (doğrulama MAE)

| Model | Parametreler | Doğrulama MAE |
|---|---|---|
| Ridge | `{"alpha": 0.1}` | 2.2441 |
| Ridge | `{"alpha": 1}` | 2.2446 |
| Ridge | `{"alpha": 10}` | 2.2526 |
| Ridge | `{"alpha": 100}` | 2.2924 |
| RandomForest | `{"n_estimators": 500, "min_samples_leaf": 5}` | 2.2815 |
| RandomForest | `{"n_estimators": 500, "min_samples_leaf": 20}` | 2.2704 |
| LightGBM | `{"num_leaves": 15, "learning_rate": 0.03, "n_estimators": 232}` | 2.2333 |
| LightGBM | `{"num_leaves": 15, "learning_rate": 0.1, "n_estimators": 82}` | 2.2339 |
| LightGBM | `{"num_leaves": 31, "learning_rate": 0.03, "n_estimators": 189}` | 2.2574 |
| LightGBM | `{"num_leaves": 31, "learning_rate": 0.1, "n_estimators": 60}` | 2.2579 |
| LightGBM | `{"num_leaves": 63, "learning_rate": 0.03, "n_estimators": 165}` | 2.2832 |
| LightGBM | `{"num_leaves": 63, "learning_rate": 0.1, "n_estimators": 55}` | 2.2934 |
