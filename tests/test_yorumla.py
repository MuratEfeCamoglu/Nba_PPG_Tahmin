"""Yorumlama/hata analizi yardımcılarının birim testleri (sentetik veri)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.yorumla import en_buyuk_hatalar, hata_tablosu, kisa_sezon_tablosu, kismi_bagimlilik


class YasModeli:
    """Tahmin = PTS + (27 − AGE) × 0.5; AGE_KARE tutarlılığını da kontrol eder."""

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        assert np.allclose(df["AGE"] ** 2, df["AGE_KARE"])
        return (df["PTS"] + (27 - df["AGE"]) * 0.5).to_numpy()


def _df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "PLAYER_NAME": ["A", "B", "C", "D"],
            "TEAM_ABBREVIATION": ["BOS", "LAL", "MIA", "NYK"],
            "SEZON_YIL": [2011, 2015, 2019, 2020],
            "AGE": [21.0, 26.0, 31.0, 35.0],
            "AGE_KARE": [441.0, 676.0, 961.0, 1225.0],
            "GP": [25, 45, 70, 80],
            "MIN": [15.0, 25.0, 30.0, 20.0],
            "PTS": [5.0, 12.0, 20.0, 8.0],
            "HEDEF_PTS": [9.0, 12.5, 15.0, 7.0],
            "TAHMIN": [6.0, 12.0, 19.0, 7.5],
            "TAKIM_DEGISTI": [np.nan, 0.0, 1.0, 0.0],
            "HEDEF_GP": [60, 70, 30, 75],
        }
    )


def test_kismi_bagimlilik_yasi_ve_kareyi_birlikte_degistirir() -> None:
    kismi = kismi_bagimlilik(YasModeli(), _df(), "AGE", [21, 27, 33])
    assert kismi["DEGER"].tolist() == [21, 27, 33]
    np.testing.assert_allclose(kismi["BEKLENEN_DEGISIM"], [3.0, 0.0, -3.0])


def test_hata_tablosu_gruplari_icerir() -> None:
    metin = hata_tablosu(_df())
    for baslik in ("Yaş grubu", "Önceki sezon GP", "Takım değişikliği", "Sezon (t)"):
        assert baslik in metin
    assert "t−1 sezonu yok" in metin


def test_kisa_sezon_etiketleri() -> None:
    metin = kisa_sezon_tablosu(_df(), [2011, 2019, 2020])
    assert "t kısa sezon (2011-12)" in metin
    assert "Normal" in metin


def test_en_buyuk_hatalar_sirali_ve_aciklamali() -> None:
    buyuk = en_buyuk_hatalar(_df(), n=2)
    assert buyuk["PLAYER_NAME"].tolist() == ["C", "A"]
    assert all(isinstance(a, str) and a.endswith(".") for a in buyuk["ACIKLAMA"])
    assert "30 maç" in buyuk.iloc[0]["ACIKLAMA"]
