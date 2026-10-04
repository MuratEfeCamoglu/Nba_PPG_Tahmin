# NBA oyuncu sayi tahmini — tek dogruluk kaynagi olan komut tanimlari.
# Girintiler TAB karakteridir. GNU make yoksa ./make (veya make.bat) bu dosyayi
# mini_make.py ile ayni anlamda calistirir (bkz. KARARLAR.md K-002).

ifeq ($(OS),Windows_NT)
VENV_BIN := .venv/Scripts
PY := .venv/Scripts/python.exe
SISTEM_PY := py -3.12
else
VENV_BIN := .venv/bin
PY := .venv/bin/python
SISTEM_PY := python3
endif

.PHONY: kur veri eda oznitelik egit test-degerlendir yorumla tahmin pdf test test-veri test-tam lint hepsi

kur:
	test -e $(PY) || $(SISTEM_PY) -m venv .venv
	$(PY) -m pip install -r requirements.txt

veri:
	$(PY) -m src.veri_topla
	$(PY) -m src.hedef

eda:
	$(PY) -m src.eda

oznitelik:
	$(PY) -m src.oznitelik

egit:
	$(PY) -m src.model

test-degerlendir:
	$(PY) -m src.degerlendir

yorumla:
	$(PY) -m src.yorumla

tahmin:
	$(PY) -m src.tahmin

pdf:
	$(PY) -m src.pdf_rapor

test:
	$(PY) -m pytest -m "not veri and not rapor"

test-veri:
	$(PY) -m pytest -m veri

test-tam:
	$(PY) -m pytest

lint:
	$(PY) -m ruff check src tests app mini_make.py

hepsi: veri eda oznitelik egit test-degerlendir yorumla tahmin pdf
