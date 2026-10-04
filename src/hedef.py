"""HEDEF_PTS üretimi: aynı oyuncunun bir sonraki ardışık sezondaki maç başı sayısı."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from src.ayarlar import ayarlari_yukle, loglama_kur, yol_al
from src.veri_topla import ham_birlesik_yolu, tum_sezonlari_topla

LOG = logging.getLogger(__name__)


def hedef_olustur(df: pd.DataFrame) -> pd.DataFrame:
    """`HEDEF_PTS` sütunu eklenmiş, (PLAYER_ID, SEZON_YIL) sıralı bir kopya döndürür.

    Oyuncunun sonraki satırı `SEZON_YIL + 1` değilse (boşluk ya da son sezon) hedef NaN olur.
    Girdi tablo değiştirilmez.
    """
    sonuc = df.sort_values(["PLAYER_ID", "SEZON_YIL"]).reset_index(drop=True)
    grup = sonuc.groupby("PLAYER_ID", sort=False)
    sonraki_pts = grup["PTS"].shift(-1)
    ardisik = grup["SEZON_YIL"].shift(-1) == sonuc["SEZON_YIL"] + 1
    sonuc["HEDEF_PTS"] = sonraki_pts.where(ardisik)
    return sonuc


def oyuncu_sezon_yolu() -> Path:
    """Veri sözleşmesindeki ana tablonun yolunu döndürür."""
    return yol_al("islenmis") / "oyuncu_sezon.csv"


def main() -> None:
    """Birleşik ham tabloyu okur (yoksa önbellekten üretir), hedefi ekler ve kaydeder."""
    ayar = ayarlari_yukle()["veri"]
    if ham_birlesik_yolu().exists():
        df = pd.read_csv(ham_birlesik_yolu())
    else:
        df = tum_sezonlari_topla(ayar["baslangic_yil"], ayar["bitis_yil"])
    sonuc = hedef_olustur(df)
    sonuc.to_csv(oyuncu_sezon_yolu(), index=False)
    LOG.info(
        "Yazıldı: %s (%d satır, %d hedefli)",
        oyuncu_sezon_yolu(), len(sonuc), int(sonuc["HEDEF_PTS"].notna().sum()),
    )


if __name__ == "__main__":
    loglama_kur()
    main()
