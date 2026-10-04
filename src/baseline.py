"""Baseline'lar: naif (geçen sezonun PTS'si) ve Marcel (ağırlıklı ortalama + yaş düzeltmesi).

Yaş eğrisi yalnızca kendisine verilen (eğitim) kümeden hesaplanır (İskelet.md §7.5).
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

import numpy as np
import pandas as pd

from src.ayarlar import loglama_kur

LOG = logging.getLogger(__name__)
YAS_ARALIGI = range(18, 46)
MIN_GOZLEM = 30


def naif_tahmin(df: pd.DataFrame) -> pd.Series:
    """Naif tahmin: t+1 sayısı = t sezonundaki maç başı sayı (PTS)."""
    return df["PTS"].astype(float).copy()


def yas_egrisi_hesapla(egitim_df: pd.DataFrame, min_gozlem: int = MIN_GOZLEM) -> pd.Series:
    """Yaş → beklenen (HEDEF_PTS − PTS) değişimi; yalnızca verilen eğitim kümesinden.

    En az `min_gozlem` gözlemli yaşlar kullanılır; aradaki yaşlar doğrusal ara değerle,
    uçtakiler en yakın geçerli yaşın değeriyle doldurulur. İndeks 18-45 tüm tam sayı yaşlardır.
    """
    yas = egitim_df["AGE"].round().astype(int)
    degisim = egitim_df["HEDEF_PTS"] - egitim_df["PTS"]
    ozet = degisim.groupby(yas).agg(["mean", "count"])
    gecerli = ozet.loc[ozet["count"] >= min_gozlem, "mean"]
    if gecerli.empty:
        raise ValueError("Yaş eğrisi için yeterli gözlem yok")
    egri = gecerli.reindex(YAS_ARALIGI).interpolate(method="index").ffill().bfill()
    egri.index.name = "AGE"
    return egri.rename("BEKLENEN_DEGISIM")


def agirlikli_ortalama(df: pd.DataFrame, agirliklar: Sequence[float]) -> pd.Series:
    """PTS, PTS_L1, PTS_L2 ağırlıklı ortalaması (mevcut sezonların ağırlık toplamına bölünür)."""
    degerler = df[["PTS", "PTS_L1", "PTS_L2"]].to_numpy(dtype=float)
    w = np.asarray(agirliklar, dtype=float)
    mevcut = ~np.isnan(degerler)
    pay = np.nansum(degerler * w, axis=1)
    payda = (mevcut * w).sum(axis=1)
    return pd.Series(pay / np.where(payda > 0, payda, np.nan), index=df.index)


def marcel_tahmin(
    df: pd.DataFrame, yas_egrisi: pd.Series, agirliklar: Sequence[float]
) -> pd.Series:
    """Marcel tahmini: 5-4-3 ağırlıklı sayı ortalaması + yaşa göre beklenen değişim."""
    yas = df["AGE"].round().astype(int).clip(min(yas_egrisi.index), max(yas_egrisi.index))
    duzeltme = yas.map(yas_egrisi).to_numpy(dtype=float)
    return (agirlikli_ortalama(df, agirliklar) + duzeltme).clip(lower=0)


if __name__ == "__main__":
    loglama_kur()
    LOG.info("Baseline'lar `make egit` ve `make test-degerlendir` içinde hesaplanır.")
