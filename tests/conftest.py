"""Sentetik veri fixture'ları: birim testleri ağ ve gerçek veri olmadan çalışır."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

TAKIMLAR = ["ATL", "BOS", "LAL", "GSW", "MIA", "NYK", "CHI", "SAS"]


def sentetik_oyuncu_sezon(oyuncu_sayisi: int = 300, tohum: int = 42) -> pd.DataFrame:
    """Veri sözleşmesine (İskelet.md §3) uyan sentetik oyuncu-sezon tablosu üretir.

    Kariyerler 2000-2025 arasına rastgele yayılır; bazı oyuncuların sezon boşlukları vardır.
    `HEDEF_PTS` ardışık sezon kuralıyla doldurulur.
    """
    rng = np.random.default_rng(tohum)
    satirlar = []
    for pid in range(1, oyuncu_sayisi + 1):
        bas = int(rng.integers(2000, 2024))
        uzunluk = int(rng.integers(1, 12))
        yas0 = int(rng.integers(19, 30))
        yetenek = float(rng.uniform(0.3, 0.9))
        yillar = [y for y in range(bas, min(bas + uzunluk, 2026))]
        if len(yillar) > 3 and rng.random() < 0.3:
            yillar.pop(int(rng.integers(1, len(yillar) - 1)))  # sezon boşluğu
        takim = TAKIMLAR[int(rng.integers(0, len(TAKIMLAR)))]
        for yil in yillar:
            yas = yas0 + (yil - bas)
            if rng.random() < 0.15:
                takim = TAKIMLAR[int(rng.integers(0, len(TAKIMLAR)))]
            dakika = float(np.clip(rng.normal(22, 8), 0, 42))
            pts_36 = yetenek * 30 * (1 - 0.004 * (yas - 27) ** 2) + rng.normal(0, 1.5)
            pts = max(0.0, pts_36 * dakika / 36)
            fga = pts / 1.1 + rng.uniform(0, 1)
            satirlar.append(
                {
                    "PLAYER_ID": pid,
                    "PLAYER_NAME": f"Oyuncu {pid}",
                    "TEAM_ABBREVIATION": takim,
                    "SEZON_YIL": yil,
                    "AGE": float(yas),
                    "GP": int(rng.integers(1, 83)),
                    "MIN": round(dakika, 1),
                    "PTS": round(pts, 1),
                    "FGA": round(fga, 1),
                    "FG3A": round(fga * rng.uniform(0, 0.5), 1),
                    "FTA": round(pts * rng.uniform(0.1, 0.35), 1),
                    "AST": round(rng.uniform(0, 8), 1),
                    "REB": round(rng.uniform(0, 12), 1),
                    "TOV": round(rng.uniform(0, 3), 1),
                    "USG_PCT": round(rng.uniform(0.1, 0.35), 3),
                    "TS_PCT": round(rng.uniform(0.45, 0.65), 3),
                }
            )
    df = pd.DataFrame(satirlar).sort_values(["PLAYER_ID", "SEZON_YIL"]).reset_index(drop=True)
    g = df.groupby("PLAYER_ID")
    sonraki_pts = g["PTS"].shift(-1)
    ardisik = g["SEZON_YIL"].shift(-1) == df["SEZON_YIL"] + 1
    df["HEDEF_PTS"] = sonraki_pts.where(ardisik)
    return df


@pytest.fixture
def sentetik_veri() -> pd.DataFrame:
    """Sentetik oyuncu-sezon tablosu (HEDEF_PTS dahil)."""
    return sentetik_oyuncu_sezon()
