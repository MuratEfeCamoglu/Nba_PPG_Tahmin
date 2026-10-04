"""2026-27 tahmin tablosunu PDF raporu olarak sunar.

`reports/tahmin_2026_27.csv` ve `reports/metrikler.json` okunur; `reports/tahmin_2026_27.pdf`
yazılır. Yalnızca mevcut bağımlılık matplotlib (PdfPages) kullanılır. İlk sayfa özet, model
karşılaştırması ve ilk 20 oyuncunun aralık grafiği; sonraki sayfalar tüm oyuncuların tablosu.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402

from src.ayarlar import ayarlari_yukle, loglama_kur, yol_al  # noqa: E402
from src.degerlendir import metrikleri_oku  # noqa: E402
from src.kadro import guncel_takim_ekle, son_kadro  # noqa: E402

LOG = logging.getLogger(__name__)

A4 = (8.27, 11.69)
MAKS_SATIR = 45  # sayfa başına en fazla oyuncu; satırlar sayfalara eşit dağıtılır
MODEL_ADLARI = {
    "naif": "Naif (PTS_t)",
    "marcel": "Marcel",
    "ridge": "Ridge",
    "random_forest": "RandomForest",
    "lightgbm": "LightGBM",
}
SUTUNLAR = [
    "#", "Oyuncu", "Takım (güncel)", "Yaş", "2025-26 PTS", "Tahmin", "Alt (%10)", "Üst (%90)",
]
SUTUN_GENISLIK = [0.06, 0.29, 0.14, 0.06, 0.12, 0.10, 0.115, 0.115]


def pdf_yolu() -> Path:
    """PDF raporunun yazılacağı yolu döndürür."""
    return yol_al("raporlar") / "tahmin_2026_27.pdf"


def _sayi(x: float) -> str:
    """Ondalık sayıyı Türkçe biçimde (virgüllü) iki basamakla yazar."""
    return f"{x:.2f}".replace(".", ",")


def takim_metni(r: Any) -> str:
    """Güncel takımı yazar; değiştiyse "eski→yeni", kadroda yoksa "eski (yok)"."""
    durum = r.get("KADRO_DURUMU", "bilinmiyor")
    if durum == "degisti":
        return f"{r['TAKIM']}→{r['GUNCEL_TAKIM']}"
    if durum == "yok":
        return f"{r['TAKIM']} (kadrosuz)"
    return str(r["TAKIM"])


def tablo_satirlari(tahmin: pd.DataFrame, bas: int, bit: int) -> list[list[str]]:
    """Tahmin tablosunun [bas, bit) aralığındaki satırlarını metin hücrelerine çevirir."""
    satirlar = []
    for i, r in tahmin.iloc[bas:bit].iterrows():
        satirlar.append([
            str(i + 1), str(r["OYUNCU"]), takim_metni(r), str(int(r["YAS_2025_26"])),
            f"{r['PTS_2025_26']:.1f}".replace(".", ","), _sayi(r["TAHMIN"]),
            _sayi(r["ALT"]), _sayi(r["UST"]),
        ])
    return satirlar


def _altbilgi(fig: plt.Figure, sayfa: int, toplam: int) -> None:
    """Sayfa numarası ve kaynak notunu sayfanın altına yazar."""
    fig.text(0.5, 0.02, f"NBA Oyuncu Sayı Tahmini · 2026-27 · Sayfa {sayfa}/{toplam}",
             ha="center", fontsize=8, color="#666666")


def ozet_sayfasi(
    tahmin: pd.DataFrame, metrik: dict[str, Any], toplam: int, kadro_notu: str = ""
) -> plt.Figure:
    """Başlık, özet metni, model karşılaştırma tablosu ve ilk 20 aralık grafiğini çizer."""
    fig = plt.figure(figsize=A4)
    fig.text(0.5, 0.955, "2026-27 NBA Sezonu — Maç Başı Sayı Tahminleri",
             ha="center", fontsize=16, weight="bold")
    secilen = MODEL_ADLARI.get(metrik["secilen_model"], metrik["secilen_model"])
    t = metrik["tahmin_2026_27"]
    kapsama = metrik["aralik_dogrulama"]["kapsama"]
    ozet = (
        f"2025-26 sezonunda en az 20 maç ve maç başı 10 dakika oynayan {t['oyuncu_sayisi']} "
        f"oyuncu için\n2026-27 maç başı sayı tahmini. Model: {secilen} "
        f"(doğrulama MAE'sine göre seçildi). Aralık: LightGBM\nquantile ile %80 tahmin "
        f"aralığı (doğrulamada gerçek kapsama %{f'{kapsama * 100:.1f}'.replace('.', ',')}).\n"
        "Tahmin, oyuncunun 2026-27'de anlamlı süre alması (≥ 20 maç) koşuluna dayanır."
        + (f"\n{kadro_notu}" if kadro_notu else "")
    )
    fig.text(0.07, 0.915, ozet, fontsize=9, va="top", linespacing=1.5)

    ax_t = fig.add_axes([0.07, 0.715, 0.86, 0.13])
    ax_t.axis("off")
    hucre = []
    for ad, etiket in MODEL_ADLARI.items():
        dog = metrik["dogrulama"].get(ad, {}).get("MAE")
        tst = metrik["test"].get(ad, {}).get("MAE")
        hucre.append([etiket + (" ★" if ad == metrik["secilen_model"] else ""),
                      _sayi(dog) if dog is not None else "—",
                      _sayi(tst) if tst is not None else "—"])
    tablo = ax_t.table(cellText=hucre, colLabels=["Model", "Doğrulama MAE", "Test MAE"],
                       loc="center", cellLoc="center")
    tablo.auto_set_font_size(False)
    tablo.set_fontsize(9)
    tablo.scale(1, 1.25)
    for (satir, _), c in tablo.get_celld().items():
        if satir == 0:
            c.set_facecolor("#1f3b6f")
            c.get_text().set_color("white")
            c.get_text().set_weight("bold")
    fig.text(0.07, 0.70, "★ seçilen model · Test seti yalnızca seçilen model ve baseline'lar "
             "için bir kez kullanıldı.", fontsize=7.5, color="#555555")

    ilk = tahmin.head(20).iloc[::-1]
    ax = fig.add_axes([0.30, 0.07, 0.63, 0.57])
    y = range(len(ilk))
    ax.hlines(y, ilk["ALT"], ilk["UST"], color="#9bb3d9", linewidth=5, label="%80 aralık")
    ax.scatter(ilk["TAHMIN"], y, color="#1f3b6f", zorder=3, s=22, label="Tahmin")
    ax.scatter(ilk["PTS_2025_26"], y, color="#d95f02", marker="x", zorder=3, s=22,
               label="2025-26 PTS")
    takim = ilk.get("GUNCEL_TAKIM", ilk["TAKIM"])
    takim = takim.where(takim != "", ilk["TAKIM"])
    ax.set_yticks(list(y), [f"{o} ({tk})" for o, tk in zip(ilk["OYUNCU"], takim)], fontsize=8)
    ax.set_xlabel("Maç başı sayı")
    ax.set_title("En yüksek tahmine sahip 20 oyuncu", fontsize=11, weight="bold")
    ax.grid(axis="x", alpha=0.3)
    ax.legend(loc="lower right", fontsize=8)
    _altbilgi(fig, 1, toplam)
    return fig


def tablo_sayfasi(
    tahmin: pd.DataFrame, bas: int, adet: int, sayfa: int, toplam: int
) -> plt.Figure:
    """Tahmin tablosunun [bas, bas + adet) dilimini bir sayfaya çizer."""
    fig = plt.figure(figsize=A4)
    fig.text(0.5, 0.96, "2026-27 Tahminleri — Tüm Oyuncular (tahmine göre sıralı)",
             ha="center", fontsize=12, weight="bold")
    satirlar = tablo_satirlari(tahmin, bas, bas + adet)
    yukseklik = 0.88 * (len(satirlar) + 1) / (MAKS_SATIR + 1)  # +1: başlık satırı
    ax = fig.add_axes([0.05, 0.93 - yukseklik, 0.90, yukseklik])
    ax.axis("off")
    tablo = ax.table(cellText=satirlar, colLabels=SUTUNLAR, colWidths=SUTUN_GENISLIK,
                     bbox=[0, 0, 1, 1], cellLoc="center")
    tablo.auto_set_font_size(False)
    tablo.set_fontsize(8)
    for (satir, sutun), c in tablo.get_celld().items():
        c.set_edgecolor("#dddddd")
        if satir == 0:
            c.set_facecolor("#1f3b6f")
            c.get_text().set_color("white")
            c.get_text().set_weight("bold")
        elif satir % 2 == 0:
            c.set_facecolor("#f2f5fa")
        if sutun == 1 and satir > 0:
            c.get_text().set_horizontalalignment("left")
            c.PAD = 0.03
    _altbilgi(fig, sayfa, toplam)
    return fig


def pdf_olustur(
    tahmin: pd.DataFrame, metrik: dict[str, Any], yol: Path, kadro_notu: str = ""
) -> int:
    """Tahmin PDF'ini yazar ve sayfa sayısını döndürür."""
    tablo_sayfa = -(-len(tahmin) // MAKS_SATIR)
    adet = -(-len(tahmin) // tablo_sayfa)
    toplam = 1 + tablo_sayfa
    # CreationDate yazılmaz: aynı girdiden bayt düzeyinde aynı PDF üretilir.
    with PdfPages(yol, metadata={"Title": "2026-27 NBA Sayı Tahminleri",
                                 "CreationDate": None}) as pdf:
        fig = ozet_sayfasi(tahmin, metrik, toplam, kadro_notu)
        pdf.savefig(fig)
        plt.close(fig)
        for k in range(tablo_sayfa):
            fig = tablo_sayfasi(tahmin, k * adet, adet, k + 2, toplam)
            pdf.savefig(fig)
            plt.close(fig)
    return toplam


def main() -> None:
    """CSV ve metriklerden `reports/tahmin_2026_27.pdf` raporunu üretir."""
    tahmin = pd.read_csv(yol_al("raporlar") / "tahmin_2026_27.csv")
    kadro = son_kadro(str(ayarlari_yukle()["kadro"]["sezon"]))
    tahmin = guncel_takim_ekle(tahmin, kadro[0] if kadro else None)
    kadro_notu = (f"Takımlar: NBA API {kadro[1].isoformat()} tarihli kadrolar; takım değişikliği "
                  "tahmine dahil değildir." if kadro else "")
    tahmin = tahmin.sort_values("TAHMIN", ascending=False).reset_index(drop=True)
    yol = pdf_yolu()
    sayfa = pdf_olustur(tahmin, metrikleri_oku(), yol, kadro_notu)
    LOG.info("PDF yazıldı: %s (%d sayfa, %d oyuncu)", yol, sayfa, len(tahmin))


if __name__ == "__main__":
    loglama_kur()
    main()
