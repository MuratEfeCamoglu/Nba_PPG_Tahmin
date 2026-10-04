"""Naif ve Marcel baseline testleri."""

from __future__ import annotations

import pandas as pd
import pytest

from src.baseline import marcel_tahmin, naif_tahmin, yas_egrisi_hesapla


def test_naif_tahmin_pts() -> None:
    df = pd.DataFrame({"PTS": [10.0, 20.0]})
    assert naif_tahmin(df).tolist() == [10.0, 20.0]


def test_yas_egrisi_yalniz_verilen_kumeden_ve_tam_aralik() -> None:
    """Eğri verilen kümenin (HEDEF_PTS - PTS) ortalamasıdır; 18-45 tüm yaşları kapsar."""
    df = pd.DataFrame(
        {
            "AGE": [24.0] * 40 + [30.0] * 40,
            "PTS": [10.0] * 80,
            "HEDEF_PTS": [11.0] * 40 + [9.0] * 40,
        }
    )
    egri = yas_egrisi_hesapla(df)
    assert egri.loc[24] == pytest.approx(1.0)
    assert egri.loc[30] == pytest.approx(-1.0)
    assert egri.loc[27] == pytest.approx(0.0)  # doğrusal ara değer
    assert egri.loc[18] == pytest.approx(1.0)
    assert egri.loc[45] == pytest.approx(-1.0)


def test_marcel_agirlikli_ve_yas_duzeltmesi() -> None:
    df = pd.DataFrame(
        {
            "PTS": [12.0, 10.0],
            "PTS_L1": [9.0, None],
            "PTS_L2": [6.0, None],
            "AGE": [24.0, 30.0],
        }
    )
    egri = pd.Series({a: (1.0 if a < 27 else -1.0) for a in range(18, 46)})
    tahmin = marcel_tahmin(df, egri, [5, 4, 3])
    assert tahmin.iloc[0] == pytest.approx((60 + 36 + 18) / 12 + 1.0)
    assert tahmin.iloc[1] == pytest.approx(10.0 - 1.0)
