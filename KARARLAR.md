# KARARLAR

Ajanın verdiği her karar ve gerekçesi (yalnızca eklenir).

## K-001 · Faz 0 · 2026-10-04
Durum: İskelet §7.4 Python 3.11 istiyor; makinede 3.11 yok (3.13 varsayılan, 3.12 `py -3.12`). Global kurulum yasak.
Karar: Sanal ortam `py -3.12 -m venv .venv` ile Python 3.12.6 üzerinde kuruldu. Kod 3.11 uyumlu yazılır (ruff `target-version = "py311"`).
Gerekçe: 3.11'e en yakın mevcut sürüm; bilimsel paket (lightgbm, shap, numba) uyumluluğu 3.13'ten daha olgun. 3.11 kurmak global kurulum gerektirir (yasak).
Alternatifler: Python 3.13 (reddedildi: shap/numba gibi paketlerde daha geç destek riski).

## K-002 · Faz 0 · 2026-10-04
Durum: `make` sistemde yok; global kurulum yasak, ağ yalnız PyPI + NBA API.
Karar: Gerçek, TAB girintili `Makefile` tek doğruluk kaynağı olarak yazıldı. Yanına (1) yalnız standart kütüphane kullanan `mini_make.py` (Makefile'ın kullandığı alt kümeyi — `:=`/`=`/`?=`, `$(VAR)`, `ifeq/ifneq/else/endif`, bağımlılıklar, `@`/`-` önekleri — yorumlayıp her tarif satırını ayrı bir bash sürecinde çalıştırır, ilk hatada çıkış kodunu döndürür), (2) Git Bash/Linux için çalıştırılabilir `./make` sarmalayıcısı (sistemde GNU make varsa onu, yoksa mini_make.py'yi çağırır), (3) cmd/PowerShell için `make.bat` eklendi. Tüm kapılar `./make <hedef>` ile çalıştırılır.
Gerekçe: PyPI'de GNU make sağlayan yaygın ve güvenilir bir paket bilinmiyor; küçük ve test edilebilir bir yorumlayıcı belirsiz bir paket bağımlılığından daha güvenli. GNU make olan makinede (Linux/macOS) `make hepsi` doğrudan aynı Makefile ile çalışır.
Alternatifler: `py-make` gibi PyPI paketleri (reddedildi: bakım/uyumluluk belirsiz); Makefile'ı tamamen Python betiğiyle değiştirmek (reddedildi: İskelet §5 Makefile ister).

## K-003 · Faz 0 · 2026-10-04
Durum: Windows'ta sanal ortam yolu `.venv/Scripts`, POSIX'te `.venv/bin`.
Karar: Makefile `ifeq ($(OS),Windows_NT)` ile `PY` değişkenini seçer (`.venv/Scripts/python.exe` / `.venv/bin/python`) ve venv'i Windows'ta `py -3.12`, diğerlerinde `python3` ile kurar. pip, pytest ve ruff hep `$(PY) -m ...` ile çağrılır.
Gerekçe: Tek Makefile iki platformda çalışır; `-m` kullanımı PATH bağımsızdır.

## K-004 · Faz 0 · 2026-10-04
Durum: requirements.txt sürümleri belirtilmemiş; tekrar üretilebilirlik başarı ölçütü #1.
Karar: Kurulan sürümler `==` ile sabitlendi (pandas 3.0.6, scikit-learn 1.9.1, lightgbm 4.7.0, shap 0.52.0 vb.). Ek olarak lint ayarları için `ruff.toml` (satır 100, py311) eklendi.
Gerekçe: Aynı sürümlerle `make kur` aynı ortamı üretir. Paket listesi İskelet §5 ile aynı, yeni paket eklenmedi.

## K-005 · Faz 0 · 2026-10-04
Durum: Windows konsolu/borusu cp1252 kodlaması kullanıyor; Türkçe log mesajları bozuluyor.
Karar: `src.ayarlar.loglama_kur()` ve `mini_make.py` stdout/stderr'i UTF-8'e yeniden yapılandırır (`errors="replace"`).
Gerekçe: Log okunabilirliği; hata yutmadan kodlama hatasını önler.

## K-006 · Faz 0 · 2026-10-04
Durum: config.yaml'a koddaki sabitler için ek anahtarlar gerekiyor (istek zaman aşımı, dizin yolları).
Karar: `veri.timeout_sn: 60` (Agent.md §8) ve `yollar` bölümü eklendi; İskelet §5'teki filtre/bölme değerleri değiştirilmedi.
Gerekçe: CLAUDE.md §5 "sabitler koda gömülmez".

## K-007 · Faz 0 · 2026-10-04
Durum: `data/raw/` önbelleği git'e eklenmeli mi?
Karar: Evet, `data/raw/` ve `data/processed/` depoya dahil (gitignore'da değil).
Gerekçe: İskelet §1 .gitignore içeriğini `.venv/, __pycache__/, models/*.joblib` olarak tanımlıyor; ham önbelleğin depoda olması API erişimi olmadan tekrar üretimi mümkün kılar.

## K-008 · Faz 1 · 2026-10-04
Durum: Veri toplama ve hedef üretimi iki modülde; ara dosya ve önbellek adlandırma.
Karar: Önbellek `data/raw/{Base|Advanced}_{yil}.csv` (API'nin ham çıktısı, tüm sütunlar). `src.veri_topla` birleşik tabloyu `data/processed/birlesik_ham.csv` ara dosyasına yazar, `src.hedef` onu okuyup `oyuncu_sezon.csv` üretir (ara dosya yoksa önbellekten yeniden kurar). `make veri` ikisini sırayla çalıştırır. `veri_topla` uzun çekimler için `--bas/--bit` ile parça parça çalıştırılabilir.
Gerekçe: Her modül `python -m` ile bağımsız çalışır; önbellek API'yi yalnızca bir kez çağırır.

## K-009 · Faz 1 · 2026-10-04
Durum: LeagueDashPlayerStats takas edilen oyuncuları zaten sezon başına tek satırda (son takım) veriyor; Advanced'ten hangi sütunlar alınacak?
Karar: Yine de İskelet §8'e uygun GP ağırlıklı `takaslari_birlestir` güvenlik adımı uygulandı (gerçek veride tekrar bulunmadı). Advanced'ten `USG_PCT, TS_PCT, EFG_PCT, AST_PCT, REB_PCT, PIE, PACE, OFF_RATING, DEF_RATING` alındı; eşleşmeyen oyuncu Base satırıyla kalır.
Gerekçe: Sözleşme benzersiz anahtar şart koşuyor; ek advanced sütunlar ileride EDA/öznitelik için kullanılabilir, modelin öznitelik listesi yine İskelet §4'tür.
Sonuç: 12.810 satır, her yıl 428-605 satır, 9.850 satırda HEDEF_PTS dolu; advanced sütunlarında eksik yok.

## K-010 · Faz 2 · 2026-10-04
Durum: Delta yöntemi ve EDA tanımlarının ayrıntıları.
Karar: (1) Çiftler: ardışık iki sezonda da GP ≥ 20 ve MIN ≥ 10 (t+1 değerlendirme filtresiyle tutarlı). (2) Yaş eğrisi: t yaşına göre ortalama (PTS_{t+1} − PTS_t), ≥ 30 gözlemli yaşlar; tepe yaş = kümülatif seviyenin en yüksek olduğu yaş. (3) Ortalamaya dönüş: PTS(t)−PTS(t−1) ile PTS(t+1)−PTS(t) arasındaki eğim. (4) Hayatta kalma: ertesi sezon veride olmayan oyuncuların yaş grubuna göre oranı ve PTS'si. EDA tüm yılları kullanır ama yalnızca betimseldir; modele/baseline'a giren yaş eğrisi `baseline.yas_egrisi_hesapla` ile yalnız eğitimden hesaplanacak.
Gerekçe: CLAUDE.md §3.1-3.4. Sonuç: tepe yaş 27; r(PTS)=0.865, r(MIN)=0.758, r(PTS_36)=0.857; dönüş eğimi −0.086.

## K-011 · Faz 3 · 2026-10-04
Durum: Lag özniteliklerinde ardışıklık ve PTS_L2 tanımı; takım değişimi ölçütü.
Karar: (1) Lag'ler `groupby.shift` yerine (PLAYER_ID, SEZON_YIL−k) anahtarıyla birleştirilir: PTS_L1 yalnızca t−1 sezonundan, PTS_L2 yalnızca t−2 sezonundan gelir (t−1 eksik olsa bile t−2 varsa kullanılır; Marcel mantığıyla tutarlı). (2) TAKIM_DEGISTI, varsa `TEAM_ID` ile karşılaştırılır (SEA→OKC, NJN→BKN gibi taşınmalar değişim sayılmaz), t−1 sezonu yoksa NaN. (3) `oznitelikler.csv` filtrelenmemiş tüm satırları içerir; GP/MIN ve hedef filtreleri `bolme`'de uygulanır. (4) Sızıntı testine ek olarak birden fazla kesme yılında aynı kontrol eklendi; sızdıran bir sütunun (`shift(-1)`) testi kırdığı geçici mutasyonla doğrulandı.
Gerekçe: İskelet §4 ardışık sezon kontrolü; birleştirme tabanlı lag sezon boşluklarında yanlış değer üretemez.

## K-012 · Faz 4 · 2026-10-04
Durum: Bölme filtreleri ve değerlendirme kümesi tanımı.
Karar: Tüm kümelerde t sezonunda GP ≥ 20 ve MIN ≥ 10; eğitim/doğrulama/test'te ek olarak HEDEF_PTS dolu ve t+1 sezonunda GP ≥ 20 (`HEDEF_GP`, yalnız filtre — öznitelik değil). t+1'de dakika filtresi uygulanmadı. Tahmin kümesi: 2025 sezonu, GP ≥ 20 ve MIN ≥ 10 (406 oyuncu).
Gerekçe: CLAUDE.md §3.7 (t+1'de en az 20 maç) ve Faz 6 tanımı; config değerleri değiştirilmedi. Boyutlar: eğitim 6066, doğrulama 1009, test 665, tahmin 406.

## K-013 · Faz 4 · 2026-10-04
Durum: Model ayrıntıları (eksik değer, sınırlar, erken durdurma, seçim).
Karar: Ridge/RF: sklearn Pipeline (medyan doldurma + eksiklik göstergesi, Ridge'de StandardScaler; yalnız eğitimde fit). LightGBM: NaN doğal, `deterministic=True`, erken durdurma doğrulama kümesinde l1 metriği (100 tur); bulunan en iyi iterasyon parametre olarak kaydedilir. Tüm tahminler `SinirliModel` sarmalayıcısında [0, 40] aralığına kırpılır (`config.sinirlar`, CLAUDE.md §3.8). Seçim doğrulama MAE'siyle; fark < 0,02 ise sadelik sırası Ridge > RF > LightGBM.
Gerekçe: İskelet §8. Not: LightGBM'in erken durdurması doğrulama kümesini kullandığından doğrulama MAE'si LightGBM lehine hafif iyimserdir; buna rağmen Ridge eşitlik kuralıyla seçildi.
Sonuç: Doğrulama MAE — naif 2,381 · Marcel 2,471 · Ridge(α=0,1) 2,244 · RF 2,270 · LightGBM 2,233. Seçilen: Ridge (LightGBM'den farkı 0,011 < 0,02).

## K-014 · Faz 4 · 2026-10-04
Durum: `test_model::test_ayni_seed_ile_deterministik` aralıklı başarısız (MAE'ler ~4e-16 farklı).
Karar: Kök neden: RandomForest `n_jobs=-1` ile tahminde ağaç çıktıları iş parçacıklarında farklı sırayla toplanıyor. Eğitim paralel bırakıldı, eğitimden sonra tahminci `n_jobs=1`'e alındı (`_rf_tahmini_sabitle`). Test gevşetilmedi; 6 tekrarlı izole denemede fark kalmadı.
Gerekçe: Test seti bayrağı model kimliğine bağlı; bit düzeyinde determinizm yeniden üretimi güvenceye alır.

## K-015 · Faz 4 · 2026-10-04
Durum: Test değerlendirmesinde hangi model örneği kullanılacak; Marcel neden naiften kötü?
Karar: Test, doğrulamada seçilen ve yalnız eğitim kümesinde eğitilmiş modelle (yeniden eğitim yapmadan) bir kez yapıldı; model seçimi test öncesi commit edildi (2fd599b). Marcel spesifikasyona (ağırlıklı ort. + eğitimden yaş eğrisi) sadık uygulandı; ortalamaya dönüş için lig ortalamasına çekme bileşeni İskelet'te olmadığından eklenmedi.
Gerekçe: Doğrulanan model = test edilen model. Bulgu: 5-4-3 ağırlıklı ortalama, yükselen oyuncuların son sezonunu geride bırakıyor ve yaş düzeltmesi PTS deltasından hesaplandığı için ağırlıklı ortalamaya uygulandığında eksik kalıyor; bu yüzden Marcel doğrulamada naiften kötü (2,471 > 2,381). Testte ikisi neredeyse eşit (2,565 / 2,568).
Sonuç (test, tek sefer): Ridge 2,402 · naif 2,568 · Marcel 2,565.
