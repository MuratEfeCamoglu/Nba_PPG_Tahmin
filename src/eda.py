"""Faz 2 — Keşifsel analiz: yaş eğrisi (delta yöntemi), ortalamaya dönüş, ardışık korelasyonlar.

Bu modüldeki hesaplar yalnızca raporlama içindir; hiçbiri modele öznitelik olarak girmez
(öğrenilen yaş düzeltmesi `src.baseline` içinde yalnızca eğitim setinden hesaplanır).
"""

from __future__ import annotations

import logging

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402

from src.ayarlar import ayarlari_yukle, loglama_kur, yol_al  # noqa: E402
from src.hedef import oyuncu_sezon_yolu  # noqa: E402

LOG = logging.getLogger(__name__)
DPI = 150
MIN_GOZLEM = 30


def grafik_stili() -> None:
    """Proje grafik stilini uygular (İskelet.md §8: seaborn whitegrid, 150 dpi)."""
    sns.set_theme(style="whitegrid")
    plt.rcParams["figure.dpi"] = DPI


def ardisik_ciftler(df: pd.DataFrame, min_gp: int, min_dakika: float) -> pd.DataFrame:
    """Ardışık sezon çiftlerini (t, t+1) döndürür; iki sezonda da GP/MIN filtresi uygulanır.

    Dönen tabloda t sütunlarının yanında `PTS_SONRAKI, MIN_SONRAKI, PTS_36_SONRAKI,
    GP_SONRAKI` ve t-1 için `PTS_ONCEKI` (ardışık değilse NaN) bulunur.
    """
    d = df.sort_values(["PLAYER_ID", "SEZON_YIL"]).reset_index(drop=True)
    d["PTS_36"] = np.where(d["MIN"] > 0, d["PTS"] / d["MIN"].where(d["MIN"] > 0) * 36, np.nan)
    g = d.groupby("PLAYER_ID", sort=False)
    sonraki_ardisik = g["SEZON_YIL"].shift(-1) == d["SEZON_YIL"] + 1
    onceki_ardisik = g["SEZON_YIL"].shift(1) == d["SEZON_YIL"] - 1
    for sutun in ["PTS", "MIN", "PTS_36", "GP"]:
        d[f"{sutun}_SONRAKI"] = g[sutun].shift(-1).where(sonraki_ardisik)
    d["PTS_ONCEKI"] = g["PTS"].shift(1).where(onceki_ardisik)
    filtre_t = (d["GP"] >= min_gp) & (d["MIN"] >= min_dakika)
    filtre_t1 = (d["GP_SONRAKI"] >= min_gp) & (d["MIN_SONRAKI"] >= min_dakika)
    return d[sonraki_ardisik & filtre_t & filtre_t1].reset_index(drop=True)


def yas_egrisi_delta(ciftler: pd.DataFrame, min_gozlem: int = MIN_GOZLEM) -> pd.DataFrame:
    """Delta yöntemiyle yaş eğrisi: her yaş için ortalama (PTS_{t+1} − PTS_t) ve kümülatif seviye.

    `KUMULATIF`, en genç yaştaki seviyeyi 0 kabul edip ortalama değişimlerin birikimidir;
    yaş a satırındaki değer a+1 yaşındaki beklenen seviyeyi gösterir.
    """
    degisim = ciftler["PTS_SONRAKI"] - ciftler["PTS"]
    egri = (
        pd.DataFrame({"AGE": ciftler["AGE"].round().astype(int), "DEGISIM": degisim})
        .groupby("AGE")["DEGISIM"]
        .agg(ORT_DEGISIM="mean", N="count")
        .reset_index()
    )
    egri = egri[egri["N"] >= min_gozlem].reset_index(drop=True)
    egri["KUMULATIF"] = egri["ORT_DEGISIM"].cumsum()
    return egri


def tepe_yas(egri: pd.DataFrame) -> int:
    """Kümülatif yaş eğrisinin tepe yaptığı yaşı döndürür.

    Yaş a satırındaki kümülatif değer a+1 yaşındaki seviyedir; başlangıç seviyesi (en genç
    yaş) 0'dır. Tepe, seviyenin en yüksek olduğu yaştır (ortalama değişimin negatife döndüğü yaş).
    """
    yaslar = [int(egri["AGE"].iloc[0])] + [int(a) + 1 for a in egri["AGE"]]
    seviyeler = [0.0] + egri["ORT_DEGISIM"].cumsum().tolist()
    return yaslar[int(np.argmax(seviyeler))]


def ardisik_korelasyon(ciftler: pd.DataFrame) -> dict[str, float]:
    """PTS, MIN ve PTS_36 için sezondan sezona Pearson korelasyonunu döndürür."""
    return {
        sutun: float(ciftler[sutun].corr(ciftler[f"{sutun}_SONRAKI"]))
        for sutun in ["PTS", "MIN", "PTS_36"]
    }


def ortalamaya_donus(ciftler: pd.DataFrame) -> dict[str, float]:
    """Önceki yıl değişimi (PTS_t − PTS_{t-1}) ile sonraki değişim (PTS_{t+1} − PTS_t) ilişkisi.

    Negatif eğim, büyük sıçramaların ardından gerileme olduğunu (ortalamaya dönüş) gösterir.
    """
    d = ciftler.dropna(subset=["PTS_ONCEKI"])
    x = d["PTS"] - d["PTS_ONCEKI"]
    y = d["PTS_SONRAKI"] - d["PTS"]
    egim, kesisim = np.polyfit(x, y, 1)
    return {
        "egim": float(egim),
        "kesisim": float(kesisim),
        "korelasyon": float(x.corr(y)),
        "n": int(len(d)),
    }


def hayatta_kalma_ozeti(df: pd.DataFrame, min_gp: int, min_dakika: float) -> pd.DataFrame:
    """Yaş grubuna göre ligden çıkış oranı ve çıkanların/kalanların ortalama PTS'si.

    Çıkış: oyuncunun t+1'de veri setinde satırı yok (2025 sezonu hariç tutulur).
    """
    d = df[(df["SEZON_YIL"] < df["SEZON_YIL"].max()) & (df["GP"] >= min_gp)]
    d = d[d["MIN"] >= min_dakika].copy()
    sirali = df.sort_values(["PLAYER_ID", "SEZON_YIL"])
    sonraki = sirali.groupby("PLAYER_ID")["SEZON_YIL"].shift(-1)
    devam = (sonraki == sirali["SEZON_YIL"] + 1).reindex(d.index)
    d["CIKTI"] = ~devam.astype(bool)
    d["YAS_GRUBU"] = pd.cut(d["AGE"], [17, 23, 27, 30, 33, 45], labels=[
        "≤23", "24-27", "28-30", "31-33", "34+"
    ])
    return (
        d.groupby("YAS_GRUBU", observed=True)
        .apply(
            lambda g: pd.Series(
                {
                    "N": len(g),
                    "CIKIS_ORANI": g["CIKTI"].mean(),
                    "CIKAN_PTS": g.loc[g["CIKTI"], "PTS"].mean(),
                    "KALAN_PTS": g.loc[~g["CIKTI"], "PTS"].mean(),
                }
            ),
            include_groups=False,
        )
        .reset_index()
    )


def grafik_yas_egrisi(egri: pd.DataFrame, tepe: int, yol) -> None:
    """Yaş eğrisi grafiği: ortalama değişim çubukları + kümülatif seviye çizgisi."""
    fig, ax1 = plt.subplots(figsize=(9, 5))
    renkler = ["tab:green" if v >= 0 else "tab:red" for v in egri["ORT_DEGISIM"]]
    ax1.bar(egri["AGE"], egri["ORT_DEGISIM"], color=renkler, alpha=0.6, label="Ortalama değişim")
    ax1.axhline(0, color="black", linewidth=0.8)
    ax1.set_xlabel("Yaş (t sezonu)")
    ax1.set_ylabel("Ortalama maç başı sayı değişimi (t → t+1)")
    ax2 = ax1.twinx()
    x_seviye = [int(egri["AGE"].iloc[0])] + (egri["AGE"] + 1).tolist()
    y_seviye = [0.0] + egri["KUMULATIF"].tolist()
    ax2.plot(x_seviye, y_seviye, color="tab:blue", marker="o",
             label="Kümülatif seviye")
    ax2.axvline(tepe, color="tab:blue", linestyle="--", linewidth=1)
    ax2.set_ylabel("Kümülatif seviye (sayı)")
    ax2.grid(False)
    ax1.set_title(f"Yaş eğrisi (delta yöntemi) — tepe yaş ≈ {tepe}")
    fig.legend(loc="upper right", bbox_to_anchor=(0.9, 0.88))
    fig.tight_layout()
    fig.savefig(yol, dpi=DPI)
    plt.close(fig)


def grafik_ortalamaya_donus(ciftler: pd.DataFrame, ozet: dict[str, float], yol) -> None:
    """Önceki değişim ile sonraki değişim saçılım grafiği ve regresyon doğrusu."""
    d = ciftler.dropna(subset=["PTS_ONCEKI"])
    x = d["PTS"] - d["PTS_ONCEKI"]
    y = d["PTS_SONRAKI"] - d["PTS"]
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(x, y, s=6, alpha=0.25, color="tab:gray")
    xs = np.linspace(x.quantile(0.005), x.quantile(0.995), 50)
    ax.plot(xs, ozet["kesisim"] + ozet["egim"] * xs, color="tab:red",
            label=f"Eğim = {ozet['egim']:.2f}, r = {ozet['korelasyon']:.2f}")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Önceki yıla göre değişim: PTS(t) − PTS(t−1)")
    ax.set_ylabel("Sonraki değişim: PTS(t+1) − PTS(t)")
    ax.set_title("Ortalamaya dönüş: büyük sıçramaları gerileme izler")
    ax.legend()
    fig.tight_layout()
    fig.savefig(yol, dpi=DPI)
    plt.close(fig)


def grafik_ardisik_korelasyon(kor: dict[str, float], yol) -> None:
    """PTS, MIN, PTS_36 için sezondan sezona korelasyon çubuk grafiği."""
    etiketler = {"PTS": "Maç başı sayı", "MIN": "Dakika", "PTS_36": "36 dk başına sayı"}
    fig, ax = plt.subplots(figsize=(7, 5))
    cubuklar = ax.bar([etiketler[k] for k in kor], list(kor.values()),
                      color=["tab:blue", "tab:orange", "tab:green"])
    for cubuk, deger in zip(cubuklar, kor.values(), strict=True):
        ax.text(cubuk.get_x() + cubuk.get_width() / 2, deger + 0.01, f"{deger:.3f}",
                ha="center")
    ax.set_ylim(0, 1)
    ax.set_ylabel("Pearson korelasyonu (t, t+1)")
    ax.set_title("Sezondan sezona istikrar")
    fig.tight_layout()
    fig.savefig(yol, dpi=DPI)
    plt.close(fig)


def bulgular_yaz(
    egri: pd.DataFrame,
    tepe: int,
    kor: dict[str, float],
    donus: dict[str, float],
    hayatta: pd.DataFrame,
    n_cift: int,
    ayar: dict,
    yol,
) -> None:
    """Sayısal EDA bulgularını markdown olarak yazar."""
    f = ayar["filtre"]
    satirlar = [
        "# EDA Bulguları",
        "",
        f"Kaynak: `data/processed/oyuncu_sezon.csv` · Çiftler: ardışık iki sezonda da "
        f"GP ≥ {f['min_gp']} ve MIN ≥ {f['min_dakika']} olan {n_cift} oyuncu-sezon çifti "
        "(2000-01 → 2025-26, tüm yıllar; yalnızca betimsel — modele girmez).",
        "",
        "## Yaş eğrisi (delta yöntemi)",
        "",
        f"**Tepe yaş: {tepe}.** Ortalama maç başı sayı değişimi bu yaşa kadar pozitif, "
        "sonrasında negatif. ",
        "",
        "| Yaş (t) | Ortalama değişim (t→t+1) | N | Kümülatif seviye (t+1) |",
        "|---|---|---|---|",
    ]
    for _, r in egri.iterrows():
        satirlar.append(
            f"| {int(r.AGE)} | {r.ORT_DEGISIM:+.2f} | {int(r.N)} | {r.KUMULATIF:+.2f} |"
        )
    satirlar += [
        "",
        f"(Yalnızca en az {MIN_GOZLEM} gözlemi olan yaşlar gösterilir.) "
        "Grafik: `figures/yas_egrisi.png`.",
        "",
        "## Sezondan sezona korelasyonlar",
        "",
        "| Ölçü | Pearson r (t, t+1) |",
        "|---|---|",
        f"| PTS (maç başı sayı) | {kor['PTS']:.3f} |",
        f"| MIN (dakika) | {kor['MIN']:.3f} |",
        f"| PTS_36 (36 dakika başına sayı) | {kor['PTS_36']:.3f} |",
        "",
        "PTS = MIN × (PTS/MIN) ayrıştırmasında "
        + (
            "skor üretme hızı (PTS_36) dakikadan daha istikrarlı."
            if kor["PTS_36"] > kor["MIN"]
            else "dakika, skor üretme hızından (PTS_36) daha istikrarlı çıktı."
        )
        + " Grafik: `figures/ardisik_korelasyon.png`.",
        "",
        "## Ortalamaya dönüş",
        "",
        f"Önceki yıl değişimi PTS(t)−PTS(t−1) ile sonraki değişim PTS(t+1)−PTS(t) arasında "
        f"eğim **{donus['egim']:.3f}**, korelasyon **{donus['korelasyon']:.3f}** "
        f"(n = {donus['n']}). Negatif eğim: bir sezonda sayısını çok artıran oyuncu ertesi "
        "sezon kısmen geri düşer; tek sezon yerine çok sezonlu ağırlıklı ortalama kullanmanın "
        "gerekçesi budur. Grafik: `figures/ortalamaya_donus.png`.",
        "",
        "## Hayatta kalma yanlılığı",
        "",
        "Delta yöntemi yalnızca ertesi sezon da oynayan oyuncuları görür. Performansı çok düşen "
        "(özellikle yaşlı) oyuncular ligden çıkar ve hesaba girmez; bu yüzden yaş eğrisindeki "
        "düşüş gerçekte olduğundan **daha hafif** görünür.",
        "",
        "| Yaş grubu | N | Ertesi sezon veride yok (çıkış oranı) | Çıkanların ort. PTS | "
        "Kalanların ort. PTS |",
        "|---|---|---|---|---|",
    ]
    for _, r in hayatta.iterrows():
        satirlar.append(
            f"| {r.YAS_GRUBU} | {int(r.N)} | {r.CIKIS_ORANI:.1%} | {r.CIKAN_PTS:.2f} | "
            f"{r.KALAN_PTS:.2f} |"
        )
    satirlar += [
        "",
        "Çıkış oranı yaşla belirgin biçimde artıyor ve çıkan oyuncuların sayı ortalaması "
        "kalanlardan düşük; yani yaşlı gruptaki gözlenen düşüş, ligden çıkanlar hesaba "
        "katılsaydı daha sert olurdu. (Not: ertesi sezon veride olmamanın bir kısmı sakatlık "
        "veya yurt dışına gitmekten kaynaklanır.)",
        "",
    ]
    yol.write_text("\n".join(satirlar), encoding="utf-8")


def main() -> None:
    """EDA grafiklerini ve `reports/eda_bulgular.md` dosyasını üretir."""
    ayar = ayarlari_yukle()
    grafik_stili()
    df = pd.read_csv(oyuncu_sezon_yolu())
    f = ayar["filtre"]
    ciftler = ardisik_ciftler(df, f["min_gp"], f["min_dakika"])
    egri = yas_egrisi_delta(ciftler)
    tepe = tepe_yas(egri)
    kor = ardisik_korelasyon(ciftler)
    donus = ortalamaya_donus(ciftler)
    hayatta = hayatta_kalma_ozeti(df, f["min_gp"], f["min_dakika"])
    sekiller = yol_al("sekiller")
    grafik_yas_egrisi(egri, tepe, sekiller / "yas_egrisi.png")
    grafik_ortalamaya_donus(ciftler, donus, sekiller / "ortalamaya_donus.png")
    grafik_ardisik_korelasyon(kor, sekiller / "ardisik_korelasyon.png")
    bulgular_yaz(egri, tepe, kor, donus, hayatta, len(ciftler), ayar,
                 yol_al("raporlar") / "eda_bulgular.md")
    LOG.info("Tepe yaş: %d · korelasyonlar: %s · dönüş eğimi: %.3f", tepe, kor, donus["egim"])


if __name__ == "__main__":
    loglama_kur()
    main()
