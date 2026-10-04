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
