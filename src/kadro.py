"""Güncel takım bilgisi: nba_api `PlayerIndex` ile 2026-27 kadrolarının anlık görüntüsü.

Yalnızca **gösterim** içindir (PDF ve web sitesi); modele girmez. t+1 takımını öznitelik
yapmak sızıntı olurdu (İskelet.md §4, `TAKIM_DEGISTI` yalnızca t−1 → t). Anlık görüntü
`data/raw/kadro_{sezon}_{YYYY-AA-GG}.csv` olarak tarihli saklanır: aynı gün tekrar
çalıştırmak API'ye gitmez, eski görüntüler silinmez (İskelet.md §7.3).
"""

from __future__ import annotations

import datetime as dt
import logging
import re
import time
from pathlib import Path

import pandas as pd

from src.ayarlar import ayarlari_yukle, loglama_kur, yol_al

LOG = logging.getLogger(__name__)

KADRO_SUTUNLAR: list[str] = ["PERSON_ID", "TEAM_ABBREVIATION", "ROSTER_STATUS"]


def kadro_yolu(sezon: str, tarih: dt.date) -> Path:
    """Bir sezonun belirli gündeki kadro anlık görüntüsünün yolunu döndürür."""
    return yol_al("ham") / f"kadro_{sezon}_{tarih.isoformat()}.csv"


def _api_istegi(sezon: str, timeout: float) -> pd.DataFrame:
    """Tek bir PlayerIndex isteği yapar (geri çekilme mantığı çağırandadır)."""
    from nba_api.stats.endpoints import playerindex

    df = playerindex.PlayerIndex(season=sezon, league_id="00", timeout=timeout).get_data_frames()[0]
    if df.empty:
        raise ValueError(f"{sezon}: PlayerIndex boş tablo döndürdü")
    return df


def guncel_kadro_cek(sezon: str, tarih: dt.date | None = None) -> pd.DataFrame:
    """Günün kadro görüntüsünü döndürür: o gün için dosya varsa oradan, yoksa API'den."""
    yol = kadro_yolu(sezon, tarih or dt.date.today())
    if yol.exists():
        return pd.read_csv(yol)
    ayar = ayarlari_yukle()["veri"]
    son_hata: Exception | None = None
    for deneme in range(1, int(ayar["max_deneme"]) + 1):
        try:
            df = _api_istegi(sezon, float(ayar["timeout_sn"]))[KADRO_SUTUNLAR]
            df.to_csv(yol, index=False)
            LOG.info("%s kadrosu: %d oyuncu API'den çekildi → %s", sezon, len(df), yol.name)
            return df
        except Exception as hata:  # noqa: BLE001 — her hata loglanır ve yeniden denenir
            son_hata = hata
            bekleme = 2**deneme
            LOG.warning("%s kadro deneme %d başarısız (%s); %d sn bekleniyor",
                        sezon, deneme, hata, bekleme)
            time.sleep(bekleme)
    assert son_hata is not None
    raise son_hata


def son_kadro(sezon: str) -> tuple[pd.DataFrame, dt.date] | None:
    """En yeni tarihli kadro görüntüsünü ve tarihini döndürür; hiç yoksa None."""
    desen = re.compile(rf"kadro_{re.escape(sezon)}_(\d{{4}}-\d{{2}}-\d{{2}})\.csv$")
    adaylar = sorted(
        (dt.date.fromisoformat(m.group(1)), p)
        for p in yol_al("ham").glob(f"kadro_{sezon}_*.csv")
        if (m := desen.search(p.name))
    )
    if not adaylar:
        return None
    tarih, yol = adaylar[-1]
    return pd.read_csv(yol), tarih


def guncel_takim_ekle(tahmin: pd.DataFrame, kadro: pd.DataFrame | None) -> pd.DataFrame:
    """Tahmin tablosuna `GUNCEL_TAKIM` ve `KADRO_DURUMU` sütunlarını ekler (kopya döndürür).

    KADRO_DURUMU: "ayni" (2025-26 takımında), "degisti" (başka takımda), "yok" (hiçbir
    güncel kadroda değil) veya "bilinmiyor" (kadro görüntüsü yok).
    """
    sonuc = tahmin.copy()
    if kadro is None:
        sonuc["GUNCEL_TAKIM"] = sonuc["TAKIM"]
        sonuc["KADRO_DURUMU"] = "bilinmiyor"
        return sonuc
    aktif = kadro[kadro["ROSTER_STATUS"].fillna(0) > 0]
    esle = aktif.drop_duplicates("PERSON_ID").set_index("PERSON_ID")["TEAM_ABBREVIATION"]
    guncel = sonuc["PLAYER_ID"].map(esle)
    sonuc["GUNCEL_TAKIM"] = guncel.fillna("")
    sonuc["KADRO_DURUMU"] = "degisti"
    sonuc.loc[guncel == sonuc["TAKIM"], "KADRO_DURUMU"] = "ayni"
    sonuc.loc[guncel.isna() | (guncel == ""), "KADRO_DURUMU"] = "yok"
    return sonuc


def main() -> None:
    """Güncel kadro görüntüsünü çeker ve tahmin listesindeki takım değişikliklerini loglar."""
    sezon = str(ayarlari_yukle()["kadro"]["sezon"])
    kadro = guncel_kadro_cek(sezon)
    tahmin = pd.read_csv(yol_al("raporlar") / "tahmin_2026_27.csv")
    durum = guncel_takim_ekle(tahmin, kadro)["KADRO_DURUMU"].value_counts().to_dict()
    LOG.info("Tahmin listesinde kadro durumu: %s", durum)


if __name__ == "__main__":
    loglama_kur()
    main()
