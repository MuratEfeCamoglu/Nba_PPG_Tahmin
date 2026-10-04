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

## K-016 · Faz 5 · 2026-10-04
Durum: Hata analizi hangi kümede; kısa sezonlar doğrulamada yok; SHAP yöntemi.
Karar: (1) Hata analizi ve SHAP doğrulama kümesinde; test kümesi Faz 4 sonrası hiç kullanılmadı (yalnız `metrikler.json`'daki test MAE'si raporda anılır). (2) Kısa sezonlar (2011, 2019, 2020 → `config.kisa_sezonlar`) için seçilen yapılandırma 2005-2022'de ileriye dönük yeniden eğitildi (y yılı için yalnız ≤ y−1 satırları; test yılları dışarıda). (3) Ridge için SHAP analitik ve kesin hesaplanır: w·(z − E[z]) (bağımsız maskeleyici, eksiklik göstergeleri özgün özniteliğe eklenir; toplamsallık hatası 1e-14). Permütasyon açıklayıcısı 5,5 dk sürüyordu; ağaç modeller için TreeExplainer, diğerleri için permütasyon yedek yol olarak kaldı. (4) Yaş kısmi bağımlılığında AGE_KARE = AGE² tutarlı değiştirilir; "kısmi etki" = ortalama tahmin − ortalama PTS(t) (yaşa göre beklenen değişim), EDA delta eğrisiyle (yalnız eğitim yılları) karşılaştırılır. (5) En büyük hataların açıklamaları t+1 dakika/takım/GP bilgisini yalnızca açıklama için kullanır (öznitelik değil).
Sonuç: Makullük ✅ (tahmin 1,43-33,29; ort. tahmin 11,74 / gerçek 11,25; ≤23 yaş pozitif, 31+ negatif). Sistematik yanlılık +0,49 raporlandı.

## K-017 · Faz 6 · 2026-10-04
Durum: Final model, aralık ve tahmin tablosu ayrıntıları.
Karar: Seçilen tür ve parametreler (Ridge α=0,1) eğitim + doğrulama + test (7.740 satır) ile yeniden eğitildi (`models/final_model.joblib`; test değerlendirmesinde kullanılan yalnız-eğitim modeli `en_iyi_model.joblib` ayrı tutuldu). %80 aralık: LightGBM quantile α=0,1/0,9, parametreler doğrulamadaki en iyi LightGBM'den (num_leaves 15, lr 0,03, 232 iterasyon). Aralık zorla tahmini kapsayacak şekilde kırpılmadı; alt ≤ tahmin ≤ üst oranı 0,998 (DoD ≥ 0,95). Kalibrasyon: yalnız eğitimde eğitilen quantile modelleri doğrulamada %78,7 kapsama (hedef %80). Tahmin tablosu sütunları: PLAYER_ID, OYUNCU, TAKIM, YAS_2025_26, PTS_2025_26, TAHMIN, ALT, UST.
Gerekçe: CLAUDE.md Faz 6; test verisini eğitime katmak değerlendirme değildir (test metrikleri Faz 4'te bir kez alınmıştı).

## K-018 · Faz 6 · 2026-10-04
Durum: "Temiz durumdan make hepsi" tanımı ve test seti bayrağı; README sayılarının tutarlılığı.
Karar: Temiz durum = `data/raw/` ve `reports/test_kullanildi.flag` hariç tüm üretilen dosyalar (data/processed, models, reports/*.md/json/csv, figures) silinmiş hal. Bayrak bir koruma kaydıdır, çıktı değil; silinmesi korumayı anlamsızlaştırırdı. Temiz çalıştırmada `test-degerlendir` aynı modeli bulup "yeniden üretim" yaptı ve tüm çıktılar commit edilmiş sürümlerle bayt düzeyinde aynı çıktı (`git status` boş). README elle yazıldı; `tests/test_rapor.py` README'deki doğrulama/test MAE'lerinin ve ilk 20 tahminin `reports/` dosyalarıyla birebir eşleştiğini doğrular. Gerçek "temiz klon" testi proje klasörü dışında dosya oluşturmayı gerektirdiğinden (İskelet §7.6) yapılmadı; `make kur` Faz 0'da doğrulandı.
Gerekçe: Agent.md §6 Faz 6 kapısı, §10.7 ve İskelet §7.5-7.6.

## K-019 · Faz 6 · 2026-10-04
Durum: Geçici deneme betikleri nereye yazıldı?
Karar: Kök neden izolasyonu için küçük betikler (RF determinizmi, SHAP toplamsallığı) ve log çıktıları yalnızca oturuma özel geçici scratchpad dizinine yazıldı; proje verisi veya proje dosyası proje klasörü dışında oluşturulmadı/değiştirilmedi.
Gerekçe: Proje klasörünü geçici dosyalarla kirletmemek; şeffaflık için kayda geçirildi.

## K-020 · Faz 6 (ek) · 2026-10-04
Durum: Kullanıcı 2026-27 tahminlerinin PDF olarak sunulmasını istedi.
Karar: `src/pdf_rapor.py` + `make pdf` hedefi (`hepsi` zincirinin sonuna eklendi) → `reports/tahmin_2026_27.pdf`. Sayfa 1: özet, model karşılaştırması (doğrulama/test MAE), ilk 20 oyuncunun %80 aralık grafiği; sonraki 10 sayfa: 406 oyuncunun tamamı tahmine göre sıralı tablo. PDF yalnızca mevcut `reports/` çıktılarını okur; model veya test setiyle yeni bir işlem yapılmaz. `test_rapor.py` dosya listesine eklendi.
Gerekçe: Yeni paket gerekmesin diye matplotlib `PdfPages` kullanıldı (requirements.txt değişmedi). `CreationDate` yazılmıyor; aynı girdiden bayt düzeyinde aynı PDF üretiliyor (iki çalıştırmada md5 aynı), böylece temiz `make hepsi` tekrar üretilebilirliği korunuyor.
Alternatifler: reportlab (reddedildi: yeni bağımlılık gerektirirdi).

## K-021 · Faz 6 (ek) · 2026-10-04
Durum: Kullanıcı tahminleri ve yöntemi anlatan bir web sitesi istedi; takımların güncel olmasını istedi (örnek: LeBron James 2025-26'da LAL, 2026-27 kadrosunda PHI).
Karar: (1) `src/kadro.py` + `make kadro`: nba_api `PlayerIndex` (sezon `config.kadro.sezon` = 2026-27) ile günlük tarihli kadro görüntüsü `data/raw/kadro_2026-27_YYYY-AA-GG.csv`; aynı gün API'ye tekrar gidilmez, eski görüntüler silinmez. 4 Ekim 2026 görüntüsünde tahmin listesindeki 406 oyuncudan 273'ü aynı takımda, 103'ü takım değiştirmiş, 30'u hiçbir kadroda değil. (2) Güncel takım **yalnızca gösterimde** kullanılır (site ve PDF); model, öznitelikler ve tahmin CSV'si değişmedi. t+1 takımını öznitelik yapmak sızıntı olurdu (İskelet §4, CLAUDE.md §1 altın kural); bu yüzden takım değiştiren oyuncuların tahmini yeni takımdaki rolü yansıtmaz ve sitede bu açıkça yazılır. (3) `src/web_sitesi.py` + `site/sablon.html` + `make site` → `site/index.html` (çevrimdışı, `hepsi` zincirinde). Sayfadaki sayılar `reports/`, işlenmiş veri ve kadro görüntüsünden otomatik doldurulur. (4) Sitede "verilerin güncelliği" bölümü: istatistik sezonu, kadro tarihi, değişen/kadrosuz oyuncu sayısı.
Gerekçe: Tek veri kaynağı kuralı (İskelet §7.3) korunur: kadro da nba_api'den. `kadro` hedefi ağ gerektirdiği için `hepsi`'ye eklenmedi; `site` mevcut en yeni görüntüyü kullanır, görüntü yoksa 2025-26 takımlarıyla ve uyarıyla üretilir.
Alternatifler: Takım değişikliğini modele katmak (reddedildi: kapsam dışı ve sızıntı riski; README "Gelecek Çalışmalar"a uygun).

## K-022 · Faz 6 (ek) · 2026-10-04
Durum: Kullanıcı, sitede en büyük hataların yanında verilerle uyuşan (isabetli) tahmin örneklerinin de "Doğru tahminler" bölümünde gösterilmesini istedi.
Karar: `src/yorumla.py` → `en_isabetli_tahminler`: doğrulama kümesinde (2020-22) naif tahminin en az 3 sayı yanıldığı, yani sayısı gerçekten değişen 315 oyuncu-sezon arasından model hatası en küçük 10 satır; `isabet_aciklamasi` yalnızca t ve öncesi bilgiden (yaş, PTS_AGIRLIKLI, GP) neden yazar. Tablo `hata_analizi.md`'ye, özet (`isabet_dogrulama`: değişen 315, 1 sayı altı 12, naifi yenme %72,1, genel 1 sayı altı %28,7) `metrikler.json`'a yazılır; site bunları okur.
Gerekçe: En küçük hatayı tüm oyunculardan seçmek PTS'si hiç değişmeyen yedek oyuncuları getirir ve naif tahminin de isabet ettiği durumları "başarı" gibi gösterirdi. Seçilmiş örneklerin yanıltmaması için sitede genel MAE ve oranlar birlikte verilir. Test kümesi kullanılmadı (İskelet §7.5).

## K-023 · Faz 6 (ek) · 2026-10-04
Durum: Kullanıcı "Doğru tahminler" bölümünün PDF'e de eklenmesini istedi.
Karar: `src/pdf_rapor.py` → `isabet_sayfasi`: özet sayfasından sonra (sayfa 2) en isabetli 10 doğrulama tahmini tablosu + dört genel oran (naifi yenme %72,1, 1 sayı altı 12/315, genel %28,7, MAE 2,24) ve "seçilmiş örnekler" uyarısı. Veri K-022'deki kaynaklardan (`hata_analizi.md`, `metrikler.json`) okunur; tablo ayrıştırma `src/web_sitesi.py`'deki `md_tablo`/`aciklama_sadelestir` ile ortak. PDF 11 → 12 sayfa; bayt düzeyinde deterministik kaldı.

## K-024 · Faz 6 (ek) · 2026-10-04
Durum: Kullanıcı siteyi GitHub + Vercel ile yayına almak istedi; Vercel `requirements.txt` yüzünden projeyi Python uygulaması sanıp "No python entrypoint found" hatası verdi.
Karar: Kök dizine `vercel.json` eklendi: framework yok, kurulum ve derleme komutu boş, çıktı dizini `site`. Vercel yalnızca önceden üretilmiş `site/index.html`'i statik olarak sunar; Python pipeline'ı Vercel'de çalışmaz (veri ve model yerelde `make site` ile üretilip commit'lenir).
Gerekçe: Yayınlama kullanıcının kararı ve eylemi (İskelet §7.2'de ajan için kapsam dışı); ajan yalnızca yapılandırma dosyasını hazırladı, push ve Vercel bağlantısı kullanıcıda.
