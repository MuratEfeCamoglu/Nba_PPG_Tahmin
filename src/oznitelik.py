"""Faz 3 — Öznitelik mühendisliği (İskelet.md §4).

Tüm öznitelikler yalnızca t ve önceki sezonlara aittir. Gecikmeli (lag) değerler
(PLAYER_ID, SEZON_YIL − k) anahtarıyla birleştirilerek alınır; böylece sezon boşluğu
olan oyuncuda yanlış sezona ait değer gelmez (ardışık sezon kontrolü).
Satırlar filtrelenmez; GP/MIN ve hedef filtreleri `src.bolme` içinde uygulanır.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.ayarlar import ayarlari_yukle, loglama_kur, yol_al
from src.hedef import oyuncu_sezon_yolu

LOG = logging.getLogger(__name__)

HAM: list[str] = ["AGE", "GP", "MIN", "PTS", "FGA", "FTA", "AST", "REB", "TOV", "USG_PCT",
                  "TS_PCT"]
HIZ: list[str] = ["PTS_36", "FGA_36", "FTA_36", "FG3A_ORAN"]
GECMIS: list[str] = ["PTS_L1", "PTS_L2", "MIN_L1", "PTS_36_L1", "GP_L1"]
AGIRLIKLI: list[str] = ["PTS_AGIRLIKLI"]
TREND: list[str] = ["PTS_TREND", "MIN_TREND"]
YAS_KARIYER: list[str] = ["AGE_KARE", "GECMIS_SEZON"]
BAGLAM: list[str] = ["TAKIM_DEGISTI"]

OZNITELIKLER: list[str] = HAM + HIZ + GECMIS + AGIRLIKLI + TREND + YAS_KARIYER + BAGLAM


def _guvenli_bol(pay: pd.Series, payda: pd.Series) -> pd.Series:
    """Payda 0 veya eksikse NaN döndüren bölme."""
    return pay / payda.where(payda > 0)


def _gecikmeli(df: pd.DataFrame, sutunlar: list[str], k: int) -> pd.DataFrame:
    """Her satır için tam olarak (SEZON_YIL − k) sezonundaki değerleri döndürür (yoksa NaN).

    Dönen tablo `df` ile aynı indekse ve `<sutun>_G{k}` adlı sütunlara sahiptir.
    """
    gecmis = df[["PLAYER_ID", "SEZON_YIL", *sutunlar]].copy()
    gecmis["SEZON_YIL"] = gecmis["SEZON_YIL"] + k
    gecmis = gecmis.rename(columns={s: f"{s}_G{k}" for s in sutunlar})
    birlesik = df[["PLAYER_ID", "SEZON_YIL"]].merge(
        gecmis, on=["PLAYER_ID", "SEZON_YIL"], how="left", validate="one_to_one"
    )
    birlesik.index = df.index
    return birlesik.drop(columns=["PLAYER_ID", "SEZON_YIL"])


def oznitelik_uret(df: pd.DataFrame) -> pd.DataFrame:
    """İskelet.md §4 öznitelikleri eklenmiş, (PLAYER_ID, SEZON_YIL) sıralı kopya döndürür.

    Eksik geçmiş NaN bırakılır. Girdi tablo değiştirilmez.
    """
    agirliklar = ayarlari_yukle()["marcel"]["agirliklar"]
    d = df.sort_values(["PLAYER_ID", "SEZON_YIL"]).reset_index(drop=True)

    # Hız öznitelikleri (t)
    d["PTS_36"] = _guvenli_bol(d["PTS"], d["MIN"]) * 36
    d["FGA_36"] = _guvenli_bol(d["FGA"], d["MIN"]) * 36
    d["FTA_36"] = _guvenli_bol(d["FTA"], d["MIN"]) * 36
    d["FG3A_ORAN"] = _guvenli_bol(d["FG3A"], d["FGA"])

    # Geçmiş (ardışık sezon kontrollü)
    takim_sutunu = "TEAM_ID" if "TEAM_ID" in d.columns else "TEAM_ABBREVIATION"
    g1 = _gecikmeli(d, ["PTS", "MIN", "PTS_36", "GP", takim_sutunu], 1)
    g2 = _gecikmeli(d, ["PTS"], 2)
    d["PTS_L1"] = g1["PTS_G1"]
    d["PTS_L2"] = g2["PTS_G2"]
    d["MIN_L1"] = g1["MIN_G1"]
    d["PTS_36_L1"] = g1["PTS_36_G1"]
    d["GP_L1"] = g1["GP_G1"]

    # Ağırlıklı ortalama: mevcut sezonların ağırlık toplamına normalize
    degerler = np.column_stack([d["PTS"], d["PTS_L1"], d["PTS_L2"]])
    w = np.asarray(agirliklar, dtype=float)
    mevcut = ~np.isnan(degerler)
    pay = np.nansum(degerler * w, axis=1)
    payda = (mevcut * w).sum(axis=1)
    d["PTS_AGIRLIKLI"] = np.where(payda > 0, pay / np.where(payda > 0, payda, 1), np.nan)

    # Trend
    d["PTS_TREND"] = d["PTS"] - d["PTS_L1"]
    d["MIN_TREND"] = d["MIN"] - d["MIN_L1"]

    # Yaş / kariyer
    d["AGE_KARE"] = d["AGE"] ** 2
    d["GECMIS_SEZON"] = d.groupby("PLAYER_ID", sort=False).cumcount()

    # Bağlam: t-1 → t takım değişimi (t+1 takımı kullanılmaz)
    onceki_takim = g1[f"{takim_sutunu}_G1"]
    degisti = (d[takim_sutunu] != onceki_takim).astype(float)
    d["TAKIM_DEGISTI"] = degisti.where(onceki_takim.notna())
    return d


def oznitelikler_yolu() -> Path:
    """Öznitelik tablosunun yolunu döndürür."""
    return yol_al("islenmis") / "oznitelikler.csv"


def main() -> None:
    """`oyuncu_sezon.csv`'den öznitelikleri üretip `oznitelikler.csv`'ye yazar."""
    df = pd.read_csv(oyuncu_sezon_yolu())
    sonuc = oznitelik_uret(df)
    sonuc.to_csv(oznitelikler_yolu(), index=False)
    eksik = sonuc[OZNITELIKLER].isna().mean().sort_values(ascending=False).head(5)
    LOG.info("Yazıldı: %s (%d satır, %d öznitelik)", oznitelikler_yolu(), len(sonuc),
             len(OZNITELIKLER))
    LOG.info("En çok eksik olan öznitelikler: %s", eksik.round(3).to_dict())


if __name__ == "__main__":
    loglama_kur()
    main()
