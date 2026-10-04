"""Faz 5 — Yorumlama ve hata analizi: SHAP, yaş kısmi bağımlılığı, hata dağılımı, en büyük hatalar.

Analiz DOĞRULAMA kümesinde yapılır; test kümesi bu modülde kullanılmaz (test metrikleri
yalnızca `reports/metrikler.json`'dan okunur). Kısa sezon analizi için seçilen model
yapılandırması 2005-2022 yıllarında ileriye dönük (yalnız geçmiş yıllarla eğitilerek)
yeniden çalıştırılır; test yılları (2023-2024) bu analize girmez.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import joblib  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.linear_model import Ridge  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402

from src.ayarlar import ayarlari_yukle, loglama_kur, yol_al  # noqa: E402
from src.bolme import zamansal_bol  # noqa: E402
from src.degerlendir import (  # noqa: E402
    MODEL_ETIKETLERI,
    metrikler,
    metrikleri_oku,
    metrikleri_yaz,
)
from src.eda import DPI, ardisik_ciftler, grafik_stili, yas_egrisi_delta  # noqa: E402
from src.hedef import oyuncu_sezon_yolu  # noqa: E402
from src.model import yeniden_egit  # noqa: E402
from src.oznitelik import oznitelikler_yolu  # noqa: E402

LOG = logging.getLogger(__name__)
SHAP_ORNEK = 2000
YAS_IZGARASI = list(range(19, 41))


def _gostergeleri_topla(katki: np.ndarray, imputer: Any, n: int) -> np.ndarray:
    """Eksiklik göstergesi sütunlarının katkısını ait oldukları özgün özniteliğe ekler."""
    degerler = katki[:, :n].copy()
    gosterge = getattr(imputer, "indicator_", None)
    if gosterge is not None:
        for k, j in enumerate(gosterge.features_):
            degerler[:, j] += katki[:, n + k]
    return degerler


def _shap_degerleri(model: Any, X_m: pd.DataFrame) -> np.ndarray:
    """Model türüne uygun SHAP değerleri (satır × öznitelik) döndürür.

    - Ridge pipeline: doğrusal modelde kesin SHAP = w·(z − E[z]) (bağımsız maskeleyici,
      arka plan = açıklanan küme); eksiklik göstergeleri özgün özniteliğe eklenir.
    - LightGBM / RandomForest: TreeExplainer.
    - Diğer: permütasyon açıklayıcısı (yavaş yedek yol).
    Kırpma ([0, 40]) etkisi yok sayılır (doğrulamada kırpılan tahmin yok denecek kadar az).
    """
    import shap

    tahminci = model.tahminci
    n = len(model.oznitelikler)
    if isinstance(tahminci, Pipeline) and isinstance(tahminci[-1], Ridge):
        Z = tahminci[:-1].transform(X_m)
        katki = (Z - Z.mean(axis=0)) * tahminci[-1].coef_
        return _gostergeleri_topla(katki, tahminci[0], n)
    if isinstance(tahminci, Pipeline):  # RandomForest pipeline
        Z = tahminci[:-1].transform(X_m)
        katki = shap.TreeExplainer(tahminci[-1])(Z).values
        return _gostergeleri_topla(katki, tahminci[0], n)
    if hasattr(tahminci, "booster_"):  # LightGBM
        return shap.TreeExplainer(tahminci)(X_m).values
    arka_plan = X_m.sample(min(100, len(X_m)), random_state=42)

    def tahmin_fn(dizi: np.ndarray) -> np.ndarray:
        return model.predict(pd.DataFrame(dizi, columns=model.oznitelikler))

    return shap.Explainer(tahmin_fn, arka_plan, seed=42)(X_m, silent=True).values


def shap_ozet(model: Any, X: pd.DataFrame, yol: Path | None = None) -> pd.Series:
    """SHAP değerlerini hesaplar, özet grafiğini (varsa `yol`) kaydeder.

    `X` öznitelik içeren tablodur; en fazla 2000 satır `random_state=42` ile örneklenir.
    Dönen seri: özniteliklere göre ortalama |SHAP| (büyükten küçüğe).
    """
    import shap

    X_m = model.X(X)
    if len(X_m) > SHAP_ORNEK:
        X_m = X_m.sample(SHAP_ORNEK, random_state=42)
    degerler = _shap_degerleri(model, X_m)
    onem = pd.Series(np.abs(degerler).mean(axis=0), index=model.oznitelikler)
    if yol is not None:
        plt.figure()
        shap.summary_plot(degerler, X_m, show=False, max_display=15,
                          rng=np.random.default_rng(42))
        plt.title("SHAP özet — doğrulama kümesi")
        plt.xlabel("SHAP değeri (tahmine katkı, sayı)")
        plt.tight_layout()
        plt.savefig(yol, dpi=DPI, bbox_inches="tight")
        plt.close("all")
    return onem.sort_values(ascending=False)


def kismi_bagimlilik(
    model: Any, X: pd.DataFrame, sutun: str = "AGE", izgara: list[int] | None = None
) -> pd.DataFrame:
    """Kısmi bağımlılık: her satırda `sutun` ızgara değerine sabitlenip ortalama tahmin alınır.

    `sutun == "AGE"` ise `AGE_KARE` de tutarlı biçimde (a²) değiştirilir. Dönen tablo:
    `DEGER, ORT_TAHMIN, BEKLENEN_DEGISIM` (= ortalama tahmin − ortalama PTS_t).
    """
    izgara = izgara or YAS_IZGARASI
    satirlar = []
    for deger in izgara:
        kopya = X.copy()
        kopya[sutun] = float(deger)
        if sutun == "AGE" and "AGE_KARE" in kopya.columns:
            kopya["AGE_KARE"] = float(deger) ** 2
        tahmin = model.predict(kopya)
        satirlar.append(
            {
                "DEGER": deger,
                "ORT_TAHMIN": float(np.mean(tahmin)),
                "BEKLENEN_DEGISIM": float(np.mean(tahmin - X["PTS"].to_numpy())),
            }
        )
    return pd.DataFrame(satirlar)


def _grup_mae(df: pd.DataFrame, grup: pd.Series, ad: str) -> list[str]:
    """Bir gruplama için MAE/ortalama hata/N markdown tablosu satırları."""
    hata = df["TAHMIN"] - df["HEDEF_PTS"]
    ozet = (
        pd.DataFrame({"g": grup, "mutlak": hata.abs(), "hata": hata})
        .groupby("g", observed=True)
        .agg(N=("mutlak", "size"), MAE=("mutlak", "mean"), YANLILIK=("hata", "mean"))
    )
    satirlar = [f"| {ad} | N | MAE | Ort. hata (tahmin − gerçek) |", "|---|---|---|---|"]
    for etiket, r in ozet.iterrows():
        satirlar.append(f"| {etiket} | {int(r.N)} | {r.MAE:.3f} | {r.YANLILIK:+.3f} |")
    return satirlar


def hata_tablosu(df: pd.DataFrame) -> str:
    """Hata dağılımını yaş grubu, önceki GP, takım değişikliği ve sezon bazında markdown döndürür.

    Gerekli sütunlar: HEDEF_PTS, TAHMIN, AGE, GP, TAKIM_DEGISTI, SEZON_YIL.
    """
    yas = pd.cut(df["AGE"], [17, 23, 27, 30, 33, 45],
                 labels=["≤23", "24-27", "28-30", "31-33", "34+"])
    gp = pd.cut(df["GP"], [0, 39, 59, 85], labels=["20-39", "40-59", "60+"])
    takim = df["TAKIM_DEGISTI"].map({0.0: "Aynı takım", 1.0: "Takım değişti"}).fillna(
        "t−1 sezonu yok"
    )
    sezon = df["SEZON_YIL"].map(lambda y: f"{y}-{str(y + 1)[-2:]}")
    bloklar = [
        ("Yaş grubu (t)", yas),
        ("Önceki sezon GP (t)", gp),
        ("Takım değişikliği (t−1 → t)", takim),
        ("Sezon (t)", sezon),
    ]
    metin: list[str] = []
    for ad, grup in bloklar:
        metin += [f"### {ad}", "", *_grup_mae(df, grup, ad), ""]
    return "\n".join(metin)


def ileriye_donuk_tahmin(
    degerlendirilebilir: pd.DataFrame, secim: dict[str, Any], ayar: dict[str, Any],
    bas: int = 2005, bit: int = 2022,
) -> pd.DataFrame:
    """Her y yılı için modeli yalnızca SEZON_YIL ≤ y−1 satırlarıyla eğitip y yılını tahmin eder."""
    parcalar = []
    for yil in range(bas, bit + 1):
        egitim = degerlendirilebilir[degerlendirilebilir["SEZON_YIL"] <= yil - 1]
        hedef = degerlendirilebilir[degerlendirilebilir["SEZON_YIL"] == yil].copy()
        model = yeniden_egit(secim["model"], secim["parametreler"], egitim, ayar)
        hedef["TAHMIN"] = model.predict(hedef)
        parcalar.append(hedef)
    return pd.concat(parcalar, ignore_index=True)


def kisa_sezon_tablosu(df: pd.DataFrame, kisa: list[int]) -> str:
    """t veya t+1 sezonu kısa olan satırların MAE'sini normal sezonlarla karşılaştırır."""
    def etiket(yil: int) -> str:
        if yil in kisa:
            return f"t kısa sezon ({yil}-{str(yil + 1)[-2:]})"
        if yil + 1 in kisa:
            return f"t+1 kısa sezon ({yil + 1}-{str(yil + 2)[-2:]})"
        return "Normal"

    return "\n".join(_grup_mae(df, df["SEZON_YIL"].map(etiket), "Sezon türü"))


def hata_aciklamasi(r: pd.Series) -> str:
    """Bir tahmin hatası için t ve t+1 verisine dayanan tek cümlelik açıklama üretir."""
    yon = "beklenenden çok daha fazla" if r["HEDEF_PTS"] > r["TAHMIN"] else "beklenenden az"
    nedenler = []
    if pd.notna(r.get("MIN_SONRAKI")):
        fark = r["MIN_SONRAKI"] - r["MIN"]
        if abs(fark) >= 5:
            nedenler.append(
                f"dakikası {r['MIN']:.1f} → {r['MIN_SONRAKI']:.1f} "
                + ("arttı (rol büyümesi)" if fark > 0 else "düştü (rol kaybı/sakatlık)")
            )
    if pd.notna(r.get("TAKIM_SONRAKI")) and r["TAKIM_SONRAKI"] != r["TEAM_ABBREVIATION"]:
        nedenler.append(f"takım değiştirdi ({r['TEAM_ABBREVIATION']} → {r['TAKIM_SONRAKI']})")
    if r["GP"] < 40 and r["HEDEF_PTS"] > r["TAHMIN"]:
        nedenler.append(f"t sezonunda yalnızca {int(r['GP'])} maç oynamıştı (sakatlık/kısa sezon)")
    if pd.notna(r.get("HEDEF_GP")) and r["HEDEF_GP"] < 40:
        nedenler.append(f"t+1'de yalnızca {int(r['HEDEF_GP'])} maç oynadı")
    if r["AGE"] <= 22 and r["HEDEF_PTS"] > r["TAHMIN"]:
        nedenler.append(f"{int(r['AGE'])} yaşında beklenmedik bir sıçrama yaptı")
    if r["AGE"] >= 32 and r["HEDEF_PTS"] < r["TAHMIN"]:
        nedenler.append(f"{int(r['AGE'])} yaşında sert düşüş yaşadı")
    if not nedenler:
        nedenler.append("skor üretme hızı (36 dk başına) belirgin biçimde değişti")
    return f"t+1'de {yon} sayı attı: " + ", ".join(nedenler) + "."


def en_buyuk_hatalar(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Mutlak hatası en büyük `n` satırı açıklamalarıyla döndürür."""
    d = df.assign(MUTLAK_HATA=(df["TAHMIN"] - df["HEDEF_PTS"]).abs())
    d = d.sort_values("MUTLAK_HATA", ascending=False).head(n).copy()
    d["ACIKLAMA"] = d.apply(hata_aciklamasi, axis=1)
    return d


def isabet_aciklamasi(r: pd.Series) -> str:
    """İsabetli bir tahmin için modelin değişimi t anındaki hangi bilgiden öngördüğünü yazar.

    Yalnızca t ve öncesine ait sütunlar (yaş, ağırlıklı ortalama, GP) kullanılır.
    """
    degisim = r["HEDEF_PTS"] - r["PTS"]
    nedenler = []
    if r["AGE"] <= 23 and degisim > 0:
        nedenler.append(f"{int(r['AGE'])} yaşında gelişim payı")
    if r["AGE"] >= 31 and degisim < 0:
        nedenler.append(f"{int(r['AGE'])} yaşında yaşa bağlı düşüş")
    ort = r.get("PTS_AGIRLIKLI")
    if pd.notna(ort) and degisim < 0 and r["PTS"] - ort >= 1.5:
        nedenler.append(f"son sezonu ({r['PTS']:.1f}) ağırlıklı ortalamasının ({ort:.1f}) "
                        "üstündeydi (ortalamaya dönüş)")
    if pd.notna(ort) and degisim > 0 and ort - r["PTS"] >= 1.5:
        nedenler.append(f"son sezonu ağırlıklı ortalamasının ({ort:.1f}) altındaydı (toparlanma)")
    if r["GP"] < 45 and degisim > 0:
        nedenler.append(f"yalnızca {int(r['GP'])} maçlık sezon sonrası toparlanma")
    if not nedenler:
        nedenler.append("dakika ve 36 dakika başına sayı geçmişi")
    yon = "artışı" if degisim > 0 else "düşüşü"
    return (f"Gerçek {abs(degisim):.1f} sayılık {yon} öngördü: "
            + ", ".join(nedenler) + ".")


def en_isabetli_tahminler(
    df: pd.DataFrame, n: int = 10, min_degisim: float = 3.0
) -> pd.DataFrame:
    """Naif tahminin en az `min_degisim` sayı yanıldığı satırlardan en isabetli `n` tanesi.

    Yalnızca PTS'si değişmeyen oyuncuları göstermemek için "gerçekten değişim olan" sezonlar
    seçilir; sıralama modelin mutlak hatasına göre artandır.
    """
    d = df.assign(MUTLAK_HATA=(df["TAHMIN"] - df["HEDEF_PTS"]).abs(),
                  NAIF_HATA=(df["PTS"] - df["HEDEF_PTS"]).abs())
    d = d[d["NAIF_HATA"] >= min_degisim]
    d = d.sort_values(["MUTLAK_HATA", "NAIF_HATA"], ascending=[True, False]).head(n).copy()
    d["ACIKLAMA"] = d.apply(isabet_aciklamasi, axis=1)
    return d


def _sonraki_bilgiler(df: pd.DataFrame, oyuncu_sezon: pd.DataFrame) -> pd.DataFrame:
    """Açıklama için (yalnız analiz) t+1 dakikası ve takımını ekler — öznitelik değildir."""
    sonraki = oyuncu_sezon[["PLAYER_ID", "SEZON_YIL", "MIN", "TEAM_ABBREVIATION"]].copy()
    sonraki["SEZON_YIL"] -= 1
    sonraki = sonraki.rename(columns={"MIN": "MIN_SONRAKI", "TEAM_ABBREVIATION": "TAKIM_SONRAKI"})
    return df.merge(sonraki, on=["PLAYER_ID", "SEZON_YIL"], how="left")


def grafik_yas_kismi(kismi: pd.DataFrame, eda_egri: pd.DataFrame, yol: Path) -> None:
    """Modelin yaş kısmi etkisi (beklenen değişim) ile EDA delta eğrisini karşılaştırır."""
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(kismi["DEGER"], kismi["BEKLENEN_DEGISIM"], marker="o", color="tab:blue",
            label="Model: yaşa göre beklenen değişim (kısmi bağımlılık)")
    ax.plot(eda_egri["AGE"], eda_egri["ORT_DEGISIM"], marker="s", color="tab:orange",
            linestyle="--", label="EDA: gözlenen ortalama değişim (delta)")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Yaş (t sezonu)")
    ax.set_ylabel("Beklenen maç başı sayı değişimi (t → t+1)")
    ax.set_title("Yaş kısmi bağımlılığı ve EDA yaş eğrisi")
    ax.legend()
    fig.tight_layout()
    fig.savefig(yol, dpi=DPI)
    plt.close(fig)


def makullik_kontrolleri(
    dogrulama: pd.DataFrame, kismi: pd.DataFrame, ayar: dict[str, Any]
) -> dict[str, Any]:
    """CLAUDE.md §3.8 makullük sınırlarını kontrol eder ve sonuçları döndürür."""
    alt, ust = ayar["sinirlar"]["tahmin_alt"], ayar["sinirlar"]["tahmin_ust"]
    tahmin = dogrulama["TAHMIN"]
    genc = kismi[kismi["DEGER"] <= 23]["BEKLENEN_DEGISIM"]
    yasli = kismi[kismi["DEGER"] >= 31]["BEKLENEN_DEGISIM"]
    return {
        "aralik_icinde": bool(tahmin.between(alt, ust).all()),
        "tahmin_min": float(tahmin.min()),
        "tahmin_max": float(tahmin.max()),
        "ort_tahmin": float(tahmin.mean()),
        "ort_gercek": float(dogrulama["HEDEF_PTS"].mean()),
        "ort_sapma_tamam": bool(abs(tahmin.mean() - dogrulama["HEDEF_PTS"].mean()) <= 1.0),
        "genc_pozitif": bool((genc > 0).all()),
        "yasli_negatif": bool((yasli < 0).all()),
    }


def rapor_yaz(
    yol: Path, secim: dict[str, Any], dog_metrik: dict[str, float], kontrol: dict[str, Any],
    kismi: pd.DataFrame, eda_egri: pd.DataFrame, onem: pd.Series, hata_md: str,
    kisa_md: str, ileri_mae: float, buyuk: pd.DataFrame, metrik_veri: dict[str, Any],
    isabetli: pd.DataFrame | None = None, isabet_ozet: dict[str, float] | None = None,
) -> None:
    """`reports/hata_analizi.md` dosyasını yazar."""
    def tik(b: bool) -> str:
        return "✅" if b else "❌"

    eda = eda_egri.set_index("AGE")["ORT_DEGISIM"]
    test = metrik_veri.get("test", {}).get(secim["model"])
    satirlar = [
        "# Hata Analizi ve Yorumlama",
        "",
        f"Model: **{MODEL_ETIKETLERI[secim['model']]}** `{json.dumps(secim['parametreler'])}` "
        f"(yalnız eğitim kümesinde eğitilmiş). Analiz kümesi: **doğrulama** (2020-2022, "
        f"n = {kontrol['n']}). Doğrulama MAE {dog_metrik['MAE']:.3f}, RMSE "
        f"{dog_metrik['RMSE']:.3f}, R² {dog_metrik['R2']:.3f}."
        + (f" Test MAE (bir kez, `metrikler.json`): {test['MAE']:.3f}." if test else ""),
        "",
        "## Makullük kontrolleri (CLAUDE.md §3.8)",
        "",
        "| Kontrol | Sonuç | Değer |",
        "|---|---|---|",
        f"| Tahminler [0, 40] aralığında | {tik(kontrol['aralik_icinde'])} | "
        f"min {kontrol['tahmin_min']:.2f}, max {kontrol['tahmin_max']:.2f} |",
        f"| Ortalama tahmin, gerçek ortalamadan ±1 içinde | {tik(kontrol['ort_sapma_tamam'])} | "
        f"tahmin {kontrol['ort_tahmin']:.2f} / gerçek {kontrol['ort_gercek']:.2f} |",
        f"| Yaş kısmi etkisi ≤23 yaşta pozitif | {tik(kontrol['genc_pozitif'])} | "
        f"{kismi[kismi.DEGER <= 23]['BEKLENEN_DEGISIM'].round(2).tolist()} |",
        f"| Yaş kısmi etkisi 31+ yaşta negatif | {tik(kontrol['yasli_negatif'])} | "
        f"{kismi[kismi.DEGER >= 31]['BEKLENEN_DEGISIM'].round(2).tolist()} |",
        "",
        "Ortalama yanlılık (tahmin − gerçek): "
        f"**{kontrol['ort_tahmin'] - kontrol['ort_gercek']:+.2f}**"
        " sayı. Model doğrulama yıllarında hafifçe fazla tahmin ediyor; yanlılık en çok "
        "çaylaklarda (t−1 sezonu yok) ve az maç oynamış oyuncularda büyük (aşağıdaki tablolar).",
        "",
        "## Yaş kısmi bağımlılığı ve EDA karşılaştırması",
        "",
        "Kısmi bağımlılık: doğrulama kümesindeki her oyuncunun yaşı (ve AGE_KARE) sabit bir "
        "değere ayarlanıp diğer öznitelikler korunarak ortalama tahmin alındı; *beklenen "
        "değişim* = ortalama tahmin − ortalama PTS(t). Grafik: `figures/yas_kismi_bagimlilik.png`.",
        "",
        "| Yaş | Model beklenen değişim | EDA ortalama değişim |",
        "|---|---|---|",
    ]
    for _, r in kismi.iterrows():
        e = eda.get(int(r.DEGER))
        satirlar.append(
            f"| {int(r.DEGER)} | {r.BEKLENEN_DEGISIM:+.2f} | "
            + (f"{e:+.2f}" if e is not None and pd.notna(e) else "—")
            + " |"
        )
    satirlar += [
        "",
        "Model, Ridge'de AGE ve AGE_KARE ile ikinci dereceden bir yaş etkisi öğrenir; eğri "
        "EDA'daki delta eğrisiyle aynı yönde (gençlerde artış, 30'lardan sonra düşüş). "
        "Modelin eğrisi EDA'dan daha düzgündür ve diğer öznitelikler (ağırlıklı ortalama, "
        "trend, dakika) ortalamaya dönüşün bir kısmını üstlendiği için genlikleri farklıdır.",
        "",
        "## SHAP — en etkili öznitelikler",
        "",
        "Ortalama |SHAP| (sayı cinsinden tahmine katkı), doğrulama kümesi. Grafik: "
        "`figures/shap_ozet.png`.",
        "",
        "| Öznitelik | Ortalama \\|SHAP\\| |",
        "|---|---|",
        *[f"| {ad} | {deger:.3f} |" for ad, deger in onem.head(10).items()],
        "",
        "## Hata dağılımı (doğrulama)",
        "",
        hata_md,
        "## Kısa sezonlar (ileriye dönük geriye test, 2005-2022)",
        "",
        "Doğrulama kümesi yalnızca 2020-21'i (72 maç) içerdiği için kısa sezonlar, seçilen "
        "model yapılandırması her yıl yalnızca geçmiş yıllarla yeniden eğitilerek 2005-2022 "
        f"yıllarında incelendi (genel MAE {ileri_mae:.3f}; test yılları dahil değil). Kısa "
        "sezonlar: 2011-12 (lokavt, 66 maç), 2019-20 (pandemi kesintisi), 2020-21 (72 maç).",
        "",
        kisa_md,
        "",
        "## En büyük 10 hata (doğrulama)",
        "",
        "| Oyuncu | Sezon (t) | Yaş | PTS(t) | Tahmin | Gerçek (t+1) | Hata | Açıklama |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for _, r in buyuk.iterrows():
        satirlar.append(
            f"| {r.PLAYER_NAME} | {r.SEZON_YIL}-{str(r.SEZON_YIL + 1)[-2:]} | {int(r.AGE)} | "
            f"{r.PTS:.1f} | {r.TAHMIN:.1f} | {r.HEDEF_PTS:.1f} | "
            f"{r.TAHMIN - r.HEDEF_PTS:+.1f} | {r.ACIKLAMA} |"
        )
    satirlar += [
        "",
        "**Genel yorum:** En büyük hatalar, modelin t anında göremediği rol değişikliklerinden "
        "(dakika artışı/azalışı, takım değişikliği) ve sakatlıklardan kaynaklanıyor. Bunlar "
        "t+1 bilgisi olduğundan öznitelik yapılamaz; modelin sınırıdır.",
        "",
    ]
    if isabetli is not None and isabet_ozet is not None:
        satirlar += [
            "## En isabetli 10 tahmin (doğrulama)",
            "",
            f"Seçim: naif tahminin (PTS(t)) en az 3 sayı yanıldığı, yani sayısı gerçekten "
            f"değişen {int(isabet_ozet['n_degisen'])} oyuncu-sezon arasından modelin mutlak "
            f"hatası en küçük 10 tanesi. Bu grupta model {int(isabet_ozet['n_bir_alti'])} "
            f"oyuncuyu 1 sayıdan az hatayla bildi ve {isabet_ozet['naifi_yenen_oran']:.1%}'inde "
            f"naiften daha az yanıldı. Tüm doğrulama kümesinde hatası 1 sayının altında kalan "
            f"tahminlerin oranı {isabet_ozet['genel_bir_alti_oran']:.1%}. Bunlar seçilmiş en iyi "
            "örneklerdir; genel başarı için MAE'ye bakın.",
            "",
            "| Oyuncu | Sezon (t) | Yaş | PTS(t) | Tahmin | Gerçek (t+1) | Hata | Naif hata "
            "| Açıklama |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        for _, r in isabetli.iterrows():
            satirlar.append(
                f"| {r.PLAYER_NAME} | {r.SEZON_YIL}-{str(r.SEZON_YIL + 1)[-2:]} | {int(r.AGE)} | "
                f"{r.PTS:.1f} | {r.TAHMIN:.1f} | {r.HEDEF_PTS:.1f} | "
                f"{r.TAHMIN - r.HEDEF_PTS:+.1f} | {r.PTS - r.HEDEF_PTS:+.1f} | {r.ACIKLAMA} |"
            )
        satirlar.append("")
    yol.write_text("\n".join(satirlar), encoding="utf-8")


def main() -> None:
    """SHAP, yaş kısmi bağımlılığı, hata analizi grafik ve raporunu üretir."""
    ayar = ayarlari_yukle()
    grafik_stili()
    secim = json.loads((yol_al("modeller") / "secim.json").read_text(encoding="utf-8"))
    model = joblib.load(yol_al("modeller") / "en_iyi_model.joblib")
    parcalar = zamansal_bol(pd.read_csv(oznitelikler_yolu()), ayar)
    oyuncu_sezon = pd.read_csv(oyuncu_sezon_yolu())
    dogrulama = parcalar["dogrulama"].copy()
    dogrulama["TAHMIN"] = model.predict(dogrulama)
    dog_metrik = metrikler(dogrulama["HEDEF_PTS"], dogrulama["TAHMIN"])

    sekiller = yol_al("sekiller")
    onem = shap_ozet(model, dogrulama, sekiller / "shap_ozet.png")
    kismi = kismi_bagimlilik(model, dogrulama, "AGE")
    egitim_ciftleri = ardisik_ciftler(
        oyuncu_sezon[oyuncu_sezon["SEZON_YIL"] <= ayar["bolme"]["egitim_son_yil"]],
        ayar["filtre"]["min_gp"], ayar["filtre"]["min_dakika"],
    )
    eda_egri = yas_egrisi_delta(egitim_ciftleri)
    grafik_yas_kismi(kismi, eda_egri, sekiller / "yas_kismi_bagimlilik.png")

    kontrol = makullik_kontrolleri(dogrulama, kismi, ayar)
    kontrol["n"] = len(dogrulama)
    hata_md = hata_tablosu(dogrulama)
    degerlendirilebilir = pd.concat([parcalar["egitim"], parcalar["dogrulama"]],
                                    ignore_index=True)
    ileri = ileriye_donuk_tahmin(degerlendirilebilir, secim, ayar)
    ileri_mae = metrikler(ileri["HEDEF_PTS"], ileri["TAHMIN"])["MAE"]
    kisa_md = kisa_sezon_tablosu(ileri, ayar["kisa_sezonlar"])
    buyuk = en_buyuk_hatalar(_sonraki_bilgiler(dogrulama, oyuncu_sezon))
    isabetli = en_isabetli_tahminler(dogrulama)
    hata = (dogrulama["TAHMIN"] - dogrulama["HEDEF_PTS"]).abs()
    naif = (dogrulama["PTS"] - dogrulama["HEDEF_PTS"]).abs()
    degisen = naif >= 3.0
    isabet_ozet = {
        "n_degisen": float(degisen.sum()),
        "n_bir_alti": float((hata[degisen] < 1.0).sum()),
        "naifi_yenen_oran": float((hata[degisen] < naif[degisen]).mean()),
        "genel_bir_alti_oran": float((hata < 1.0).mean()),
    }
    metrik_veri = metrikleri_oku()
    metrik_veri["isabet_dogrulama"] = isabet_ozet
    metrikleri_yaz(metrik_veri)
    rapor_yaz(yol_al("raporlar") / "hata_analizi.md", secim, dog_metrik, kontrol, kismi,
              eda_egri, onem, hata_md, kisa_md, ileri_mae, buyuk, metrik_veri,
              isabetli, isabet_ozet)
    LOG.info("Makullük: %s", kontrol)
    if not (kontrol["aralik_icinde"] and kontrol["ort_sapma_tamam"]):
        raise RuntimeError(f"Makullük sınırı ihlali: {kontrol}")


if __name__ == "__main__":
    loglama_kur()
    main()
