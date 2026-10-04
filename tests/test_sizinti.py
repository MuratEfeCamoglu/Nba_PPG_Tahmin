"""Sızıntı kesme testi (İskelet.md §9 — aynen uygulanır)."""

from __future__ import annotations

import pandas as pd

from src.oznitelik import oznitelik_uret


def test_oznitelikler_gelecekten_bagimsiz(sentetik_veri):
    t = 2015
    tam = oznitelik_uret(sentetik_veri)
    kesik = oznitelik_uret(sentetik_veri[sentetik_veri.SEZON_YIL <= t])
    sec = lambda d: (d[d.SEZON_YIL == t].drop(columns=["HEDEF_PTS"], errors="ignore")  # noqa: E731
                     .sort_values("PLAYER_ID").reset_index(drop=True))
    pd.testing.assert_frame_equal(sec(tam), sec(kesik))


def test_her_kesme_yilinda_gelecekten_bagimsiz(sentetik_veri):
    """Ek güvence: birden fazla kesme yılında da t öznitelikleri değişmez."""
    tam = oznitelik_uret(sentetik_veri)
    for t in (2003, 2010, 2020, 2024):
        kesik = oznitelik_uret(sentetik_veri[sentetik_veri.SEZON_YIL <= t])
        a = tam[tam.SEZON_YIL == t].drop(columns=["HEDEF_PTS"]).sort_values("PLAYER_ID")
        b = kesik[kesik.SEZON_YIL == t].drop(columns=["HEDEF_PTS"]).sort_values("PLAYER_ID")
        pd.testing.assert_frame_equal(a.reset_index(drop=True), b.reset_index(drop=True))
