"""Zamansal bölme: yıl bazlı eğitim / doğrulama / test / tahmin kümeleri (İskelet.md §5, §7.5).

Rastgele bölme kullanılmaz. Filtreler:
- Tüm kümeler: t sezonunda GP >= `filtre.min_gp` ve MIN >= `filtre.min_dakika`.
- Eğitim/doğrulama/test: HEDEF_PTS dolu ve t+1 sezonunda GP >= `filtre.min_gp`
  (seçim etkisi: model "anlamlı süre alırsa kaç sayı atar?" sorusunu cevaplar).
`HEDEF_GP` (t+1 maç sayısı) yalnızca filtre içindir; asla öznitelik değildir.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from src.ayarlar import ayarlari_yukle, loglama_kur
from src.oznitelik import oznitelikler_yolu

LOG = logging.getLogger(__name__)


def hedef_gp_ekle(df: pd.DataFrame) -> pd.DataFrame:
    """Ardışık sonraki sezonun GP değerini `HEDEF_GP` olarak ekler (yoksa NaN)."""
    sonraki = df[["PLAYER_ID", "SEZON_YIL", "GP"]].copy()
    sonraki["SEZON_YIL"] = sonraki["SEZON_YIL"] - 1
    sonraki = sonraki.rename(columns={"GP": "HEDEF_GP"})
    sonuc = df.drop(columns=["HEDEF_GP"], errors="ignore").merge(
        sonraki, on=["PLAYER_ID", "SEZON_YIL"], how="left", validate="one_to_one"
    )
    sonuc.index = df.index
    return sonuc


def zamansal_bol(df: pd.DataFrame, ayar: dict[str, Any]) -> dict[str, pd.DataFrame]:
    """Öznitelik tablosunu `{"egitim","dogrulama","test","tahmin"}` kümelerine böler.

    `ayar` tam config sözlüğüdür (`bolme` ve `filtre` bölümleri kullanılır). Girdi değişmez.
    """
    b, f = ayar["bolme"], ayar["filtre"]
    d = hedef_gp_ekle(df)
    temel = (d["GP"] >= f["min_gp"]) & (d["MIN"] >= f["min_dakika"])
    hedefli = d["HEDEF_PTS"].notna() & (d["HEDEF_GP"] >= f["min_gp"])
    yil = d["SEZON_YIL"]
    maskeler = {
        "egitim": temel & hedefli & (yil <= b["egitim_son_yil"]),
        "dogrulama": temel & hedefli & yil.between(*b["dogrulama_yillari"]),
        "test": temel & hedefli & yil.between(*b["test_yillari"]),
        "tahmin": temel & (yil == b["tahmin_yil"]),
    }
    parcalar = {ad: d[m].reset_index(drop=True) for ad, m in maskeler.items()}
    if parcalar["tahmin"]["HEDEF_PTS"].notna().any():
        raise ValueError("Tahmin kümesinde hedef değeri olmamalı")
    return parcalar


def main() -> None:
    """Bölme özetini loglar (kontrol amaçlı)."""
    df = pd.read_csv(oznitelikler_yolu())
    for ad, parca in zamansal_bol(df, ayarlari_yukle()).items():
        LOG.info("%-10s %5d satır, yıllar %s-%s", ad, len(parca),
                 parca["SEZON_YIL"].min(), parca["SEZON_YIL"].max())


if __name__ == "__main__":
    loglama_kur()
    main()
