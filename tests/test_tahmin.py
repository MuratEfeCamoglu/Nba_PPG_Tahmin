"""2026-27 tahmin tablosu birim testleri (sentetik)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.tahmin import sezon_tahmini


class Sabit:
    def __init__(self, kaydirma: float) -> None:
        self.kaydirma = kaydirma

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        return df["PTS"].to_numpy() + self.kaydirma


def test_sezon_tahmini_sutunlar_ve_siralama() -> None:
    df = pd.DataFrame(
        {
            "PLAYER_ID": [1, 2, 3],
            "PLAYER_NAME": ["A", "B", "C"],
            "TEAM_ABBREVIATION": ["BOS", "LAL", "MIA"],
            "AGE": [22.0, 28.0, 33.0],
            "PTS": [10.0, 25.0, 15.0],
        }
    )
    sonuc = sezon_tahmini(Sabit(0.5), Sabit(-3.0), Sabit(3.0), df)
    assert {"OYUNCU", "TAHMIN", "ALT", "UST"} <= set(sonuc.columns)
    assert sonuc["OYUNCU"].tolist() == ["B", "C", "A"]
    assert (sonuc["ALT"] <= sonuc["TAHMIN"]).all() and (sonuc["TAHMIN"] <= sonuc["UST"]).all()
    assert len(sonuc) == 3


def test_streamlit_uygulamasi_import_yan_etkisiz() -> None:
    """Uygulama modülü içe aktarıldığında arayüz kodu çalışmaz."""
    import importlib

    modul = importlib.import_module("app.streamlit_app")
    assert callable(modul.main)
