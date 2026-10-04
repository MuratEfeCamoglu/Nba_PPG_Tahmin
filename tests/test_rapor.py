"""Final çıktı testleri (Faz 6): README başlıkları, rapor/grafik dosyaları, tahmin tablosu."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from src.ayarlar import KOK_DIZIN

pytestmark = pytest.mark.rapor

RAPOR = KOK_DIZIN / "reports"
BASLIKLAR = [
    "## Problem",
    "## Veri ve Filtreler",
    "## EDA Bulguları",
    "## Yöntem",
    "## Sonuçlar",
    "## Hata Analizi",
    "## 2026-27 Tahminleri",
    "## Sınırlamalar",
    "## Nasıl Çalıştırılır",
    "## Sonuç Takibi",
]
DOSYALAR = [
    "eda_bulgular.md",
    "metrikler.json",
    "model_karsilastirma.md",
    "hata_analizi.md",
    "tahmin_2026_27.csv",
    "test_kullanildi.flag",
    "figures/yas_egrisi.png",
    "figures/ortalamaya_donus.png",
    "figures/ardisik_korelasyon.png",
    "figures/shap_ozet.png",
    "figures/yas_kismi_bagimlilik.png",
]


@pytest.fixture(scope="module")
def readme() -> str:
    yol = KOK_DIZIN / "README.md"
    assert yol.exists(), "README.md yok"
    return yol.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def metrik() -> dict:
    return json.loads((RAPOR / "metrikler.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def tahmin() -> pd.DataFrame:
    return pd.read_csv(RAPOR / "tahmin_2026_27.csv")


def test_readme_basliklari_sirali(readme: str) -> None:
    """README §6 başlıklarını bu sırayla ve bu adlarla içerir."""
    satirlar = [s.strip() for s in readme.splitlines()]
    konumlar = []
    for baslik in BASLIKLAR:
        assert baslik in satirlar, baslik
        konumlar.append(satirlar.index(baslik))
    assert konumlar == sorted(konumlar)


@pytest.mark.parametrize("dosya", DOSYALAR)
def test_rapor_dosyalari_var_ve_bos_degil(dosya: str) -> None:
    yol = RAPOR / dosya
    assert yol.exists(), dosya
    assert yol.stat().st_size > 0, dosya


def test_tahmin_tablosu(tahmin: pd.DataFrame) -> None:
    """Oyuncu, tahmin, alt, üst sütunları; tahminler [0, 40]; ≥%95 satırda alt ≤ tahmin ≤ üst."""
    assert {"OYUNCU", "TAHMIN", "ALT", "UST"} <= set(tahmin.columns)
    assert len(tahmin) > 300
    assert tahmin["TAHMIN"].between(0, 40).all()
    tutarli = (tahmin["ALT"] <= tahmin["TAHMIN"]) & (tahmin["TAHMIN"] <= tahmin["UST"])
    assert tutarli.mean() >= 0.95


def test_metrikler_tam(metrik: dict) -> None:
    """Doğrulama ve test metrikleri mevcut; seçilen model doğrulamada naiften iyi."""
    secilen = metrik["secilen_model"]
    assert {"naif", "marcel", "ridge", "random_forest", "lightgbm"} <= set(metrik["dogrulama"])
    assert {secilen, "naif", "marcel"} <= set(metrik["test"])
    assert metrik["dogrulama"][secilen]["MAE"] < metrik["dogrulama"]["naif"]["MAE"]


def test_bayrak_secilen_modelle_ayni(metrik: dict) -> None:
    bayrak = json.loads((RAPOR / "test_kullanildi.flag").read_text(encoding="utf-8"))
    assert bayrak["model"] == metrik["secilen_model"]
    assert bayrak["parametreler"] == metrik["secilen_parametreler"]


def test_readme_sayilari_raporlarla_tutarli(
    readme: str, metrik: dict, tahmin: pd.DataFrame
) -> None:
    """README'deki temel sayılar reports/ dosyalarından gelir (Agent.md §10.7)."""
    secilen = metrik["secilen_model"]
    for ad in (secilen, "naif", "marcel"):
        assert f"{metrik['test'][ad]['MAE']:.3f}" in readme, ad
        assert f"{metrik['dogrulama'][ad]['MAE']:.3f}" in readme, ad
    for _, r in tahmin.head(20).iterrows():
        assert r["OYUNCU"] in readme, r["OYUNCU"]
        assert f"{r['TAHMIN']:.1f}" in readme, r["OYUNCU"]
