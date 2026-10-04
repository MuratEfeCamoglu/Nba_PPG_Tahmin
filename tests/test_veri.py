"""Gerçek veri sözleşmesi testleri (İskelet.md §3). Dosya yoksa başarısız olur."""

from __future__ import annotations

import pandas as pd
import pytest

from src.ayarlar import KOK_DIZIN

pytestmark = pytest.mark.veri

YOL = KOK_DIZIN / "data" / "processed" / "oyuncu_sezon.csv"
ZORUNLU = [
    "PLAYER_ID", "PLAYER_NAME", "TEAM_ABBREVIATION", "SEZON_YIL", "AGE", "GP", "MIN",
    "PTS", "FGA", "FG3A", "FTA", "AST", "REB", "TOV", "USG_PCT", "TS_PCT", "HEDEF_PTS",
]


@pytest.fixture(scope="module")
def veri() -> pd.DataFrame:
    """Gerçek oyuncu-sezon tablosu."""
    assert YOL.exists(), f"{YOL} yok — önce `make veri` çalıştırın"
    return pd.read_csv(YOL)


def test_benzersiz_anahtar(veri: pd.DataFrame) -> None:
    """(PLAYER_ID, SEZON_YIL) tekrar etmez."""
    assert not veri.duplicated(["PLAYER_ID", "SEZON_YIL"]).any()


def test_zorunlu_sutunlar(veri: pd.DataFrame) -> None:
    """Tüm zorunlu sütunlar mevcut."""
    eksik = [c for c in ZORUNLU if c not in veri.columns]
    assert not eksik, eksik


@pytest.mark.parametrize(
    ("sutun", "alt", "ust"),
    [("AGE", 18, 45), ("GP", 1, 85), ("MIN", 0, 48), ("USG_PCT", 0, 1), ("TS_PCT", 0, 1.5)],
)
def test_deger_araliklari(veri: pd.DataFrame, sutun: str, alt: float, ust: float) -> None:
    """Değerler sözleşmedeki aralıkta (NaN'lar hariç)."""
    degerler = veri[sutun].dropna()
    assert degerler.between(alt, ust).all(), degerler[~degerler.between(alt, ust)].head()


def test_pts_negatif_degil(veri: pd.DataFrame) -> None:
    """PTS ≥ 0 ve eksik değil."""
    assert veri["PTS"].notna().all()
    assert (veri["PTS"] >= 0).all()


def test_kimlik_ve_temel_sutunlar_eksiksiz(veri: pd.DataFrame) -> None:
    """Anahtar ve temel sütunlarda eksik değer yok."""
    for sutun in ["PLAYER_ID", "PLAYER_NAME", "SEZON_YIL", "AGE", "GP", "MIN"]:
        assert veri[sutun].notna().all(), sutun


def test_yil_kapsami(veri: pd.DataFrame) -> None:
    """2000-2025 aralığındaki 26 yılın her biri en az 350 satır içerir."""
    sayim = veri["SEZON_YIL"].value_counts()
    for yil in range(2000, 2026):
        assert sayim.get(yil, 0) >= 350, (yil, sayim.get(yil, 0))
    assert set(sayim.index) == set(range(2000, 2026))


def test_satir_sayisi(veri: pd.DataFrame) -> None:
    """Toplam satır sayısı 10.000-15.000 aralığında (CLAUDE.md Faz 1 DoD)."""
    assert 10_000 <= len(veri) <= 15_000


def test_hedef_kurali(veri: pd.DataFrame) -> None:
    """HEDEF_PTS yalnızca ardışık sezonda dolu ve o sezonun PTS'sine eşit; 2025'te NaN."""
    assert veri.loc[veri.SEZON_YIL == 2025, "HEDEF_PTS"].isna().all()
    sirali = veri.sort_values(["PLAYER_ID", "SEZON_YIL"])
    g = sirali.groupby("PLAYER_ID")
    ardisik = g["SEZON_YIL"].shift(-1) == sirali["SEZON_YIL"] + 1
    assert sirali.loc[~ardisik, "HEDEF_PTS"].isna().all()
    pd.testing.assert_series_equal(
        sirali.loc[ardisik, "HEDEF_PTS"], g["PTS"].shift(-1)[ardisik], check_names=False
    )


def test_pts_mac_basi_olcekte(veri: pd.DataFrame) -> None:
    """PerGame ölçeği: hiçbir oyuncu maç başı 40'tan fazla sayı ortalaması tutmaz."""
    assert veri["PTS"].max() < 40
