"""Test seti koruması: bayrak varken farklı modelle değerlendirme reddedilir."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from src.degerlendir import metrikler, test_seti_degerlendir


class SabitModel:
    """Her satır için sabit değer tahmin eden basit model."""

    def __init__(self, deger: float) -> None:
        self.deger = deger

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        return np.full(len(df), self.deger)


@pytest.fixture
def test_df() -> pd.DataFrame:
    return pd.DataFrame({"HEDEF_PTS": [10.0, 12.0, 14.0]})


def test_metrikler() -> None:
    m = metrikler(pd.Series([1.0, 2.0, 3.0]), np.array([1.0, 2.0, 5.0]))
    assert m["MAE"] == pytest.approx(2 / 3)
    assert m["RMSE"] == pytest.approx(np.sqrt(4 / 3))
    assert set(m) == {"MAE", "RMSE", "R2"}


def test_ilk_kullanim_bayragi_yazar(tmp_path, test_df) -> None:
    bayrak = tmp_path / "test_kullanildi.flag"
    sonuc = test_seti_degerlendir(
        SabitModel(12.0), test_df, "ridge", {"alpha": 10}, bayrak_yolu=bayrak
    )
    assert bayrak.exists()
    icerik = json.loads(bayrak.read_text(encoding="utf-8"))
    assert icerik["model"] == "ridge"
    assert icerik["parametreler"] == {"alpha": 10}
    assert sonuc["MAE"] == pytest.approx(4 / 3)


def test_ayni_modelle_yeniden_uretim_serbest(tmp_path, test_df) -> None:
    bayrak = tmp_path / "test_kullanildi.flag"
    test_seti_degerlendir(SabitModel(12.0), test_df, "ridge", {"alpha": 10}, bayrak_yolu=bayrak)
    ilk = bayrak.read_text(encoding="utf-8")
    test_seti_degerlendir(SabitModel(12.0), test_df, "ridge", {"alpha": 10}, bayrak_yolu=bayrak)
    assert bayrak.read_text(encoding="utf-8") == ilk


def test_farkli_modelle_reddedilir(tmp_path, test_df) -> None:
    bayrak = tmp_path / "test_kullanildi.flag"
    test_seti_degerlendir(SabitModel(12.0), test_df, "ridge", {"alpha": 10}, bayrak_yolu=bayrak)
    with pytest.raises(RuntimeError):
        test_seti_degerlendir(
            SabitModel(12.0), test_df, "lightgbm", {"num_leaves": 31}, bayrak_yolu=bayrak
        )
    with pytest.raises(RuntimeError):
        test_seti_degerlendir(
            SabitModel(12.0), test_df, "ridge", {"alpha": 1}, bayrak_yolu=bayrak
        )
