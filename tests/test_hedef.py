"""HEDEF_PTS üretimi: ardışık sezon kuralı."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.hedef import hedef_olustur


def _ornek() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "PLAYER_ID": [1, 1, 1, 2, 2, 3],
            "SEZON_YIL": [2010, 2011, 2013, 2024, 2025, 2015],
            "PTS": [10.0, 12.0, 15.0, 20.0, 22.0, 5.0],
        }
    )


def test_ardisik_sezonda_dogru_deger() -> None:
    """Sonraki satır SEZON_YIL+1 ise HEDEF_PTS onun PTS değeridir."""
    sonuc = hedef_olustur(_ornek()).set_index(["PLAYER_ID", "SEZON_YIL"])
    assert sonuc.loc[(1, 2010), "HEDEF_PTS"] == 12.0
    assert sonuc.loc[(2, 2024), "HEDEF_PTS"] == 22.0


def test_ardisik_olmayan_sezonda_nan() -> None:
    """Sezon boşluğu (2011 → 2013) varsa HEDEF_PTS NaN olur."""
    sonuc = hedef_olustur(_ornek()).set_index(["PLAYER_ID", "SEZON_YIL"])
    assert np.isnan(sonuc.loc[(1, 2011), "HEDEF_PTS"])
    assert np.isnan(sonuc.loc[(1, 2013), "HEDEF_PTS"])
    assert np.isnan(sonuc.loc[(3, 2015), "HEDEF_PTS"])


def test_son_sezonda_nan_ve_girdi_degismez() -> None:
    """2025 satırında hedef her zaman NaN; girdi tablo değiştirilmez; sıra bağımsız."""
    girdi = _ornek().sample(frac=1, random_state=42)
    kopya = girdi.copy()
    sonuc = hedef_olustur(girdi)
    assert sonuc.loc[sonuc.SEZON_YIL == 2025, "HEDEF_PTS"].isna().all()
    pd.testing.assert_frame_equal(girdi, kopya)
    assert "HEDEF_PTS" not in girdi.columns


def test_sentetik_veride_sozlesmeye_uygun(sentetik_veri) -> None:
    """Sentetik veride hedef, fixture'daki bağımsız hesapla aynıdır."""
    beklenen = sentetik_veri["HEDEF_PTS"]
    sonuc = hedef_olustur(sentetik_veri.drop(columns="HEDEF_PTS"))
    pd.testing.assert_series_equal(sonuc["HEDEF_PTS"], beklenen, check_names=False)
