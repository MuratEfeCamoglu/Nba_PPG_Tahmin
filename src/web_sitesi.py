"""Tahminleri ve yöntemi anlatan tek sayfalık web sitesini üretir (`site/index.html`).

`site/sablon.html` içindeki yer tutucular `reports/` çıktıları, işlenmiş veri ve en yeni
kadro görüntüsüyle (src.kadro) doldurulur. Sayfadaki her sayı bir proje dosyasından gelir;
elle yazılmış metrik yoktur. Ağ erişimi gerekmez.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd

from src.ayarlar import KOK_DIZIN, ayarlari_yukle, loglama_kur, yol_al
from src.degerlendir import metrikleri_oku
from src.hedef import oyuncu_sezon_yolu
from src.kadro import guncel_takim_ekle, son_kadro

LOG = logging.getLogger(__name__)

SITE_DIZIN = KOK_DIZIN / "site"
MODEL_ADLARI = {
    "naif": "Naif",
    "marcel": "Marcel",
    "ridge": "Ridge",
    "random_forest": "RandomForest",
    "lightgbm": "LightGBM",
}
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül",
         "Ekim", "Kasım", "Aralık"]


def site_yolu() -> Path:
    """Üretilen sitenin yolunu döndürür."""
    return SITE_DIZIN / "index.html"


def _virgul(x: float, basamak: int) -> str:
    """Sayıyı Türkçe ondalık virgülle yazar."""
    return f"{x:.{basamak}f}".replace(".", ",")


def _binlik(n: int) -> str:
    """Tam sayıyı Türkçe binlik ayırıcıyla (nokta) yazar."""
    return f"{n:,}".replace(",", ".")


def md_tablo(md: str, baslik: str) -> list[list[str]]:
    """Markdown metninde `baslik`tan sonraki ilk tablonun veri satırlarını döndürür."""
    blok = md.split(baslik, 1)[1]
    satirlar: list[str] = []
    for satir in blok.splitlines():
        if satir.startswith("|"):
            satirlar.append(satir)
        elif satirlar:
            break
    return [[h.strip() for h in s.strip("|").split("|")] for s in satirlar[2:]]


def _sayi_ya_da_bos(x: str) -> float | None:
    """'—' veya boş hücreyi None, diğerlerini float yapar."""
    return None if x in ("—", "") else float(x.replace("+", ""))


def _aciklama_sadelestir(metin: str) -> str:
    """Açıklamalardaki t / t+1 gösterimini sadeleştirir, ondalık noktayı virgül yapar."""
    metin = re.sub(r"(\d)\.(\d)", r"\1,\2", metin)
    return (metin.replace("t+1'de beklenenden", "Ertesi sezon beklenenden")
            .replace(", t+1'de yalnızca", ", ertesi sezon yalnızca")
            .replace(": t sezonunda yalnızca", ": o sezon yalnızca")
            .replace("(rol kaybı/sakatlık)", "(rol kaybı veya sakatlık)"))


def site_verisi(tahmin: pd.DataFrame, metrik: dict[str, Any], hata_md: str) -> dict[str, Any]:
    """Sayfadaki betiğin kullandığı JSON verisini hazırlar.

    `tahmin` tablosunda `GUNCEL_TAKIM` ve `KADRO_DURUMU` sütunları bulunmalıdır.
    """
    tahmin = tahmin.sort_values("TAHMIN", ascending=False)
    satirlar = [
        [r.OYUNCU, r.TAKIM, int(r.YAS_2025_26), round(float(r.PTS_2025_26), 1),
         round(float(r.TAHMIN), 2), round(float(r.ALT), 2), round(float(r.UST), 2),
         r.GUNCEL_TAKIM, r.KADRO_DURUMU]
        for r in tahmin.itertuples()
    ]
    modeller = []
    for anahtar, ad in MODEL_ADLARI.items():
        dog = metrik["dogrulama"][anahtar]
        test = metrik["test"].get(anahtar)
        modeller.append({
            "ad": ad, "dog": dog["MAE"], "dogR2": dog["R2"],
            "test": test["MAE"] if test else None, "testR2": test["R2"] if test else None,
            "secili": anahtar == metrik["secilen_model"],
        })
    yas = [[int(r[0]), _sayi_ya_da_bos(r[2]), _sayi_ya_da_bos(r[1])]
           for r in md_tablo(hata_md, "## Yaş kısmi bağımlılığı")]
    shap = [[r[0], float(r[1])] for r in md_tablo(hata_md, "## SHAP")]
    hatalar = [[r[0], r[1], int(r[2]), float(r[3]), float(r[4]), float(r[5]),
                _aciklama_sadelestir(r[7])]
               for r in md_tablo(hata_md, "## En büyük 10 hata")]
    isabetler = [[r[0], r[1], int(r[2]), float(r[3]), float(r[4]), float(r[5]),
                  _aciklama_sadelestir(r[8])]
                 for r in md_tablo(hata_md, "## En isabetli 10 tahmin")]
    return {"tahmin": satirlar, "modeller": modeller, "yas": yas, "shap": shap,
            "hatalar": hatalar, "isabetler": isabetler}


def site_olustur() -> Path:
    """Şablonu doldurup `site/index.html` dosyasını yazar ve yolunu döndürür."""
    ayar = ayarlari_yukle()
    raporlar = yol_al("raporlar")
    metrik = metrikleri_oku()
    kadro_sezon = str(ayar["kadro"]["sezon"])
    kadro = son_kadro(kadro_sezon)
    tahmin = pd.read_csv(raporlar / "tahmin_2026_27.csv")
    tahmin = guncel_takim_ekle(tahmin, kadro[0] if kadro else None)
    if kadro:
        tarih = kadro[1]
        kadro_tarih = f"{tarih.day} {AYLAR[tarih.month - 1]} {tarih.year}"
    else:
        kadro_tarih = "kadro verisi yok (make kadro)"
        LOG.warning("Kadro görüntüsü bulunamadı; takımlar 2025-26 olarak gösterilecek.")
    veri = site_verisi(tahmin, metrik,
                       (raporlar / "hata_analizi.md").read_text(encoding="utf-8"))
    oyuncu_sezon = pd.read_csv(oyuncu_sezon_yolu())
    son_yil = int(ayar["bolme"]["tahmin_yil"])
    naif, ridge = metrik["test"]["naif"]["MAE"], metrik["test"][metrik["secilen_model"]]["MAE"]
    kb = metrik["kume_boyutlari"]
    isabet = metrik["isabet_dogrulama"]
    durum = tahmin["KADRO_DURUMU"].value_counts()
    degerler = {
        "__OYUNCU__": str(len(tahmin)),
        "__TEST_MAE__": _virgul(ridge, 2),
        "__KAZANC__": _virgul((naif - ridge) / naif * 100, 1),
        "__KAPSAMA__": _virgul(metrik["aralik_dogrulama"]["kapsama"] * 100, 1),
        "__SATIR__": _binlik(len(oyuncu_sezon)),
        "__MAKS_GP__": str(int(oyuncu_sezon.loc[oyuncu_sezon["SEZON_YIL"] == son_yil, "GP"].max())),
        "__N_EGITIM__": _binlik(kb["egitim"]),
        "__N_DOGRULAMA__": _binlik(kb["dogrulama"]),
        "__N_TEST__": _binlik(kb["test"]),
        "__KADRO_SEZON__": kadro_sezon,
        "__KADRO_TARIH__": kadro_tarih,
        "__N_DEGISTI__": str(int(durum.get("degisti", 0))),
        "__N_YOK__": str(int(durum.get("yok", 0))),
        "__N_DEGISEN__": str(int(isabet["n_degisen"])),
        "__N_BIR_ALTI__": str(int(isabet["n_bir_alti"])),
        "__NAIFI_YENEN__": _virgul(isabet["naifi_yenen_oran"] * 100, 1),
        "__GENEL_BIR_ALTI__": _virgul(isabet["genel_bir_alti_oran"] * 100, 1),
        "__DOG_MAE__": _virgul(metrik["dogrulama"][metrik["secilen_model"]]["MAE"], 2),
        "__VERI__": json.dumps(veri, ensure_ascii=False),
    }
    html = (SITE_DIZIN / "sablon.html").read_text(encoding="utf-8")
    for yer_tutucu, deger in degerler.items():
        if yer_tutucu not in html:
            raise ValueError(f"Şablonda yer tutucu yok: {yer_tutucu}")
        html = html.replace(yer_tutucu, deger)
    # Tarayıcıda doğrudan açılabilsin diye tam belge iskeleti (charset olmadan Türkçe bozulur).
    bas, govde = html.split("</style>", 1)
    html = (
        '<!doctype html>\n<html lang="tr">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        f"{bas}</style>\n</head>\n<body>{govde}\n</body>\n</html>\n"
    )
    yol = site_yolu()
    yol.write_text(html, encoding="utf-8", newline="\n")
    LOG.info("Site yazıldı: %s (%d oyuncu, kadro: %s)", yol, len(tahmin), kadro_tarih)
    return yol


def main() -> None:
    """`site/index.html` dosyasını üretir."""
    site_olustur()


if __name__ == "__main__":
    loglama_kur()
    main()
