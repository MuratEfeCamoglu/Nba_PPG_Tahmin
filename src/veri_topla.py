"""nba_api üzerinden sezon bazlı oyuncu istatistiklerini toplar, önbelleğe alır ve birleştirir.

Kaynak: `LeagueDashPlayerStats` (Normal Sezon, PerGame), `Base` ve `Advanced` ölçümleri.
Önbellek: `data/raw/{olcum}_{yil}.csv`. Önbellekte dosya varsa API'ye gidilmez;
önbellek hiçbir koşulda silinmez (İskelet.md §7.3).
"""

from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path

import pandas as pd

from src.ayarlar import ayarlari_yukle, loglama_kur, yol_al

LOG = logging.getLogger(__name__)

OLCUMLER: tuple[str, ...] = ("Base", "Advanced")

# API sütun adları beklenenden farklı gelirse tek yerden eşlenir (Agent.md §8).
SUTUN_ESLEME: dict[str, str] = {}

BASE_SUTUNLAR: list[str] = [
    "PLAYER_ID", "PLAYER_NAME", "TEAM_ID", "TEAM_ABBREVIATION", "AGE", "GP", "MIN",
    "FGM", "FGA", "FG3M", "FG3A", "FTM", "FTA", "OREB", "DREB", "REB", "AST", "TOV",
    "STL", "BLK", "PF", "PTS", "PLUS_MINUS",
]
ADVANCED_SUTUNLAR: list[str] = [
    "PLAYER_ID", "USG_PCT", "TS_PCT", "EFG_PCT", "AST_PCT", "REB_PCT", "PIE", "PACE",
    "OFF_RATING", "DEF_RATING",
]
TOPLANAN_SUTUNLAR: set[str] = {"GP"}


def sezon_dizgesi(yil: int) -> str:
    """Başlangıç yılını nba_api sezon biçimine çevirir (2000 → "2000-01")."""
    return f"{yil}-{str(yil + 1)[-2:]}"


def onbellek_yolu(yil: int, olcum: str) -> Path:
    """Bir sezon/ölçüm çiftinin önbellek dosya yolunu döndürür."""
    return yol_al("ham") / f"{olcum}_{yil}.csv"


def _api_istegi(yil: int, olcum: str, timeout: float) -> pd.DataFrame:
    """Tek bir API isteği yapar (geri çekilme mantığı çağırandadır)."""
    from nba_api.stats.endpoints import leaguedashplayerstats

    yanit = leaguedashplayerstats.LeagueDashPlayerStats(
        season=sezon_dizgesi(yil),
        season_type_all_star="Regular Season",
        per_mode_detailed="PerGame",
        measure_type_detailed_defense=olcum,
        timeout=timeout,
    )
    df = yanit.get_data_frames()[0]
    if df.empty:
        raise ValueError(f"{sezon_dizgesi(yil)} {olcum}: API boş tablo döndürdü")
    return df


def sezon_cek(yil: int, olcum: str) -> pd.DataFrame:
    """Bir sezonun ölçüm tablosunu döndürür: önbellek varsa oradan, yoksa API'den (backoff'lu).

    API'den başarıyla gelen veri önbelleğe yazılır. `max_deneme` deneme sonunda hâlâ
    başarısızsa son hata yeniden fırlatılır.
    """
    yol = onbellek_yolu(yil, olcum)
    if yol.exists():
        return pd.read_csv(yol)
    ayar = ayarlari_yukle()["veri"]
    son_hata: Exception | None = None
    for deneme in range(1, int(ayar["max_deneme"]) + 1):
        try:
            df = _api_istegi(yil, olcum, float(ayar["timeout_sn"]))
            df.to_csv(yol, index=False)
            LOG.info("%s %s: %d satır API'den çekildi", sezon_dizgesi(yil), olcum, len(df))
            time.sleep(float(ayar["bekleme_sn"]))
            return df
        except Exception as hata:  # noqa: BLE001 — her hata loglanır ve yeniden denenir
            son_hata = hata
            bekleme = 2**deneme
            LOG.warning(
                "%s %s deneme %d başarısız (%s: %s); %d sn bekleniyor",
                sezon_dizgesi(yil), olcum, deneme, type(hata).__name__, hata, bekleme,
            )
            time.sleep(bekleme)
    assert son_hata is not None
    raise son_hata


def takaslari_birlestir(df: pd.DataFrame) -> pd.DataFrame:
    """Aynı (PLAYER_ID, SEZON_YIL) için birden fazla satırı GP ağırlıklı ortalama ile birleştirir.

    GP toplanır, `TEAM_ABBREVIATION`/`TEAM_ID` son satırdan alınır (İskelet.md §8).
    Tekrar yoksa tablo değişmeden (kopya olarak) döner.
    """
    anahtar = ["PLAYER_ID", "SEZON_YIL"]
    if not df.duplicated(anahtar).any():
        return df.copy()
    sayisal = [
        c for c in df.select_dtypes("number").columns
        if c not in anahtar + ["TEAM_ID"] and c not in TOPLANAN_SUTUNLAR
    ]
    satirlar = []
    for _, grup in df.groupby(anahtar, sort=False):
        if len(grup) == 1:
            satirlar.append(grup.iloc[0])
            continue
        agirlik = grup["GP"].clip(lower=1)
        satir = grup.iloc[-1].copy()
        for sutun in sayisal:
            gecerli = grup[sutun].notna()
            if gecerli.any():
                satir[sutun] = (grup.loc[gecerli, sutun] * agirlik[gecerli]).sum() / agirlik[
                    gecerli
                ].sum()
        satir["GP"] = grup["GP"].sum()
        satirlar.append(satir)
    return pd.DataFrame(satirlar).reset_index(drop=True)


def sezonu_birlestir(base: pd.DataFrame, advanced: pd.DataFrame, yil: int) -> pd.DataFrame:
    """Bir sezonun Base ve Advanced tablolarını PLAYER_ID ile soldan birleştirir.

    Advanced'te eşleşmeyen oyuncuların Base satırı korunur, advanced sütunları NaN olur.
    """
    base = base.rename(columns=SUTUN_ESLEME)[BASE_SUTUNLAR]
    advanced = advanced.rename(columns=SUTUN_ESLEME)[ADVANCED_SUTUNLAR]
    advanced = advanced.drop_duplicates("PLAYER_ID", keep="last")
    birlesik = base.merge(advanced, on="PLAYER_ID", how="left", validate="many_to_one")
    birlesik.insert(3, "SEZON_YIL", yil)
    return birlesik


def tum_sezonlari_topla(bas: int, bit: int) -> pd.DataFrame:
    """`bas`..`bit` (dahil) sezonlarının Base + Advanced birleşik tablosunu döndürür.

    Başarısız sezonlar sonda bir tur daha denenir; yine başarısızsa RuntimeError fırlatılır.
    """
    basarisiz: list[tuple[int, str]] = []
    for yil in range(bas, bit + 1):
        for olcum in OLCUMLER:
            try:
                sezon_cek(yil, olcum)
            except Exception as hata:  # noqa: BLE001 — sonda tekrar denenir
                LOG.error("%s %s alınamadı: %s", sezon_dizgesi(yil), olcum, hata)
                basarisiz.append((yil, olcum))
    kalan = []
    for yil, olcum in basarisiz:
        try:
            sezon_cek(yil, olcum)
        except Exception as hata:  # noqa: BLE001 — listede raporlanır
            LOG.error("İkinci tur da başarısız: %s %s (%s)", sezon_dizgesi(yil), olcum, hata)
            kalan.append((yil, olcum))
    if kalan:
        raise RuntimeError(f"Çekilemeyen sezon/ölçümler: {kalan}")
    parcalar = [
        sezonu_birlestir(sezon_cek(yil, "Base"), sezon_cek(yil, "Advanced"), yil)
        for yil in range(bas, bit + 1)
    ]
    df = pd.concat(parcalar, ignore_index=True)
    df = takaslari_birlestir(df)
    return df.sort_values(["PLAYER_ID", "SEZON_YIL"]).reset_index(drop=True)


def ham_birlesik_yolu() -> Path:
    """Birleşik (hedefsiz) tablonun ara dosya yolunu döndürür."""
    return yol_al("islenmis") / "birlesik_ham.csv"


def main(argumanlar: list[str] | None = None) -> None:
    """Komut satırı: sezonları çeker; `--bas/--bit` yoksa config aralığının tamamı.

    Tam aralık çekildiğinde birleşik tablo `data/processed/birlesik_ham.csv` dosyasına yazılır.
    """
    ayar = ayarlari_yukle()["veri"]
    ayristirici = argparse.ArgumentParser(description=__doc__)
    ayristirici.add_argument("--bas", type=int, default=ayar["baslangic_yil"])
    ayristirici.add_argument("--bit", type=int, default=ayar["bitis_yil"])
    secenek = ayristirici.parse_args(argumanlar)
    df = tum_sezonlari_topla(secenek.bas, secenek.bit)
    LOG.info("%d-%d: %d satır birleştirildi", secenek.bas, secenek.bit, len(df))
    if secenek.bas == ayar["baslangic_yil"] and secenek.bit == ayar["bitis_yil"]:
        df.to_csv(ham_birlesik_yolu(), index=False)
        LOG.info("Yazıldı: %s", ham_birlesik_yolu())


if __name__ == "__main__":
    loglama_kur()
    main()
