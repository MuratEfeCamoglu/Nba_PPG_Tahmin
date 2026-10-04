"""Öznitelik üretimi birim testleri (İskelet.md §4)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.oznitelik import OZNITELIKLER, oznitelik_uret


def _oyuncu(yillar, pts, dakika, takimlar=None, pid=1) -> pd.DataFrame:
    n = len(yillar)
    return pd.DataFrame(
        {
            "PLAYER_ID": [pid] * n,
            "PLAYER_NAME": ["A"] * n,
            "TEAM_ABBREVIATION": takimlar or ["BOS"] * n,
            "SEZON_YIL": yillar,
            "AGE": [25.0 + i for i in range(n)],
            "GP": [60] * n,
            "MIN": dakika,
            "PTS": pts,
            "FGA": [10.0] * n,
            "FG3A": [4.0] * n,
            "FTA": [3.0] * n,
            "AST": [2.0] * n,
            "REB": [5.0] * n,
            "TOV": [1.0] * n,
            "USG_PCT": [0.2] * n,
            "TS_PCT": [0.55] * n,
        }
    )


def test_tum_oznitelikler_uretiliyor(sentetik_veri) -> None:
    """OZNITELIKLER listesindeki her sütun çıktıda var; satır sayısı korunuyor."""
    sonuc = oznitelik_uret(sentetik_veri)
    assert set(OZNITELIKLER) <= set(sonuc.columns)
    assert len(sonuc) == len(sentetik_veri)
    assert "HEDEF_PTS" not in OZNITELIKLER


def test_pts_36_hesabi_ve_sifir_dakika() -> None:
    """PTS_36 = PTS / MIN × 36; MIN = 0 ise NaN."""
    sonuc = oznitelik_uret(_oyuncu([2010, 2011], [12.0, 3.0], [24.0, 0.0]))
    assert sonuc.loc[0, "PTS_36"] == pytest.approx(18.0)
    assert sonuc.loc[0, "FGA_36"] == pytest.approx(15.0)
    assert np.isnan(sonuc.loc[1, "PTS_36"])
    assert np.isnan(sonuc.loc[1, "FTA_36"])


def test_fg3a_orani_ve_sifir_sut() -> None:
    """FG3A_ORAN = FG3A / FGA; FGA = 0 ise NaN."""
    df = _oyuncu([2010, 2011], [10.0, 10.0], [20.0, 20.0])
    df.loc[1, "FGA"] = 0.0
    sonuc = oznitelik_uret(df)
    assert sonuc.loc[0, "FG3A_ORAN"] == pytest.approx(0.4)
    assert np.isnan(sonuc.loc[1, "FG3A_ORAN"])


def test_lag_ardisiklik_kontrolu() -> None:
    """t-1 satırı gerçekten SEZON_YIL-1 değilse lag NaN; L2 yalnızca t-2 sezonundan gelir."""
    sonuc = oznitelik_uret(_oyuncu([2010, 2011, 2013], [10.0, 12.0, 15.0], [20.0, 22.0, 30.0]))
    s = sonuc.set_index("SEZON_YIL")
    assert np.isnan(s.loc[2010, "PTS_L1"])
    assert s.loc[2011, "PTS_L1"] == 10.0
    assert s.loc[2011, "MIN_L1"] == 20.0
    assert s.loc[2011, "GP_L1"] == 60
    assert s.loc[2011, "PTS_36_L1"] == pytest.approx(18.0)
    assert np.isnan(s.loc[2013, "PTS_L1"])  # 2012 yok
    assert s.loc[2013, "PTS_L2"] == 12.0  # 2011 = t-2
    assert np.isnan(s.loc[2011, "PTS_L2"])
    assert np.isnan(s.loc[2013, "PTS_TREND"])
    assert s.loc[2011, "PTS_TREND"] == pytest.approx(2.0)
    assert s.loc[2011, "MIN_TREND"] == pytest.approx(2.0)


def test_agirlikli_ortalama_eksik_sezon_normalizasyonu() -> None:
    """Eksik sezonlar ağırlık toplamından düşülür."""
    sonuc = oznitelik_uret(_oyuncu([2010, 2011, 2012], [9.0, 18.0, 12.0], [20.0] * 3))
    s = sonuc.set_index("SEZON_YIL")["PTS_AGIRLIKLI"]
    assert s.loc[2010] == pytest.approx(9.0)
    assert s.loc[2011] == pytest.approx((5 * 18 + 4 * 9) / 9)
    assert s.loc[2012] == pytest.approx((5 * 12 + 4 * 18 + 3 * 9) / 12)


def test_yas_kariyer_ve_takim_degisimi() -> None:
    """AGE_KARE, GECMIS_SEZON ve TAKIM_DEGISTI doğru; girdi değişmez."""
    df = _oyuncu([2010, 2011, 2013], [10.0, 12.0, 15.0], [20.0] * 3, ["BOS", "LAL", "LAL"])
    kopya = df.copy()
    s = oznitelik_uret(df).set_index("SEZON_YIL")
    pd.testing.assert_frame_equal(df, kopya)
    assert s.loc[2011, "AGE_KARE"] == pytest.approx(26.0**2)
    assert s["GECMIS_SEZON"].tolist() == [0, 1, 2]
    assert np.isnan(s.loc[2010, "TAKIM_DEGISTI"])
    assert s.loc[2011, "TAKIM_DEGISTI"] == 1
    assert np.isnan(s.loc[2013, "TAKIM_DEGISTI"])  # t-1 sezonu yok


def test_takim_id_varsa_tasinma_degisim_sayilmaz() -> None:
    """TEAM_ID aynıysa (ör. SEA → OKC taşınması) kısaltma değişse de takım değişmemiş sayılır."""
    df = _oyuncu([2007, 2008], [10.0, 12.0], [20.0, 20.0], ["SEA", "OKC"])
    df["TEAM_ID"] = [1610612760, 1610612760]
    s = oznitelik_uret(df).set_index("SEZON_YIL")
    assert s.loc[2008, "TAKIM_DEGISTI"] == 0
