"""Metrikler, test seti koruması ve model karşılaştırma raporu.

Test seti yalnızca `make test-degerlendir` (bu modülün `main`'i) ile kullanılır. İlk
kullanımda `reports/test_kullanildi.flag` dosyasına seçilen modelin adı ve parametreleri
yazılır; bayrak varken farklı bir modelle test değerlendirmesi reddedilir (İskelet.md §7.5).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from src.ayarlar import ayarlari_yukle, loglama_kur, yol_al
from src.baseline import marcel_tahmin, naif_tahmin, yas_egrisi_hesapla
from src.bolme import zamansal_bol
from src.oznitelik import oznitelikler_yolu

LOG = logging.getLogger(__name__)

MODEL_ETIKETLERI = {
    "naif": "Naif (PTS_t)",
    "marcel": "Marcel (5-4-3 + yaş)",
    "ridge": "Ridge",
    "random_forest": "RandomForest",
    "lightgbm": "LightGBM",
}


def metrikler(y: pd.Series | np.ndarray, tahmin: pd.Series | np.ndarray) -> dict[str, float]:
    """MAE, RMSE ve R² değerlerini sözlük olarak döndürür."""
    y = np.asarray(y, dtype=float)
    tahmin = np.asarray(tahmin, dtype=float)
    return {
        "MAE": float(mean_absolute_error(y, tahmin)),
        "RMSE": float(np.sqrt(mean_squared_error(y, tahmin))),
        "R2": float(r2_score(y, tahmin)),
    }


def bayrak_yolu_varsayilan() -> Path:
    """Test seti koruma bayrağının varsayılan yolu."""
    return yol_al("raporlar") / "test_kullanildi.flag"


def _kimlik(model_adi: str, parametreler: dict[str, Any]) -> str:
    """Model adı + parametrelerden karşılaştırılabilir kanonik dizge üretir."""
    return json.dumps({"model": model_adi, "parametreler": parametreler}, sort_keys=True)


def test_seti_degerlendir(
    model: Any,
    test: pd.DataFrame,
    model_adi: str,
    parametreler: dict[str, Any],
    bayrak_yolu: Path | None = None,
) -> dict[str, float]:
    """Seçilen modeli test kümesinde değerlendirir; koruma bayrağını kontrol eder/yazar.

    Bayrak yoksa oluşturulur. Bayrak varsa ve içindeki model/parametreler farklıysa
    RuntimeError fırlatılır; aynı modelle yeniden üretim serbesttir (bayrak değişmez).
    """
    bayrak = Path(bayrak_yolu) if bayrak_yolu is not None else bayrak_yolu_varsayilan()
    parametreler = json.loads(json.dumps(parametreler))  # JSON'a gidiş-dönüşle normalize
    if bayrak.exists():
        kayit = json.loads(bayrak.read_text(encoding="utf-8"))
        if _kimlik(kayit["model"], kayit["parametreler"]) != _kimlik(model_adi, parametreler):
            raise RuntimeError(
                f"Test seti daha önce '{kayit['model']}' ({kayit['parametreler']}) ile "
                f"kullanıldı; farklı model '{model_adi}' ({parametreler}) ile değerlendirme "
                "reddedildi (İskelet.md §7.5)."
            )
        LOG.info("Bayrak mevcut ve model aynı: yeniden üretim.")
    else:
        bayrak.parent.mkdir(parents=True, exist_ok=True)
        icerik = {
            "model": model_adi,
            "parametreler": parametreler,
            "olusturma": datetime.now().isoformat(timespec="seconds"),
        }
        bayrak.write_text(json.dumps(icerik, ensure_ascii=False, indent=2), encoding="utf-8")
        LOG.info("Test seti ilk kez kullanılıyor; bayrak yazıldı: %s", bayrak)
    return metrikler(test["HEDEF_PTS"], model.predict(test))


test_seti_degerlendir.__test__ = False  # pytest bunu test fonksiyonu sanmasın


def baseline_metrikleri(
    egitim: pd.DataFrame, kume: pd.DataFrame, ayar: dict[str, Any]
) -> dict[str, dict[str, float]]:
    """Naif ve Marcel baseline'larının verilen kümedeki metrikleri (yaş eğrisi eğitimden)."""
    egri = yas_egrisi_hesapla(egitim)
    return {
        "naif": metrikler(kume["HEDEF_PTS"], naif_tahmin(kume)),
        "marcel": metrikler(
            kume["HEDEF_PTS"], marcel_tahmin(kume, egri, ayar["marcel"]["agirliklar"])
        ),
    }


def metrikler_yolu() -> Path:
    """`reports/metrikler.json` yolu."""
    return yol_al("raporlar") / "metrikler.json"


def metrikleri_oku() -> dict[str, Any]:
    """Var olan metrikler dosyasını okur (yoksa boş sözlük)."""
    yol = metrikler_yolu()
    return json.loads(yol.read_text(encoding="utf-8")) if yol.exists() else {}


def metrikleri_yaz(veri: dict[str, Any]) -> None:
    """Metrikler sözlüğünü JSON olarak yazar."""
    metrikler_yolu().write_text(
        json.dumps(veri, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def karsilastirma_yaz(veri: dict[str, Any]) -> None:
    """`reports/model_karsilastirma.md` dosyasını metrikler sözlüğünden üretir."""
    dog = veri["dogrulama"]
    test = veri.get("test", {})
    secilen = veri["secilen_model"]
    boy = veri.get("kume_boyutlari", {})
    satirlar = [
        "# Model Karşılaştırma",
        "",
        f"Küme boyutları: eğitim {boy.get('egitim')} · doğrulama {boy.get('dogrulama')} · "
        f"test {boy.get('test')} · tahmin {boy.get('tahmin')} satır.",
        "",
        f"**Seçilen model:** {MODEL_ETIKETLERI[secilen]} — doğrulama MAE'sine göre "
        "(fark < 0,02 ise daha basit model tercih edilir).",
        "",
        "| Model | Doğrulama MAE | Doğrulama RMSE | Doğrulama R² "
        "| Test MAE | Test RMSE | Test R² |",
        "|---|---|---|---|---|---|---|",
    ]
    for ad in ["naif", "marcel", "ridge", "random_forest", "lightgbm"]:
        d = dog[ad]
        t = test.get(ad)
        test_hucre = (
            f"{t['MAE']:.3f} | {t['RMSE']:.3f} | {t['R2']:.3f}" if t else "— | — | —"
        )
        isaret = " ✅" if ad == secilen else ""
        satirlar.append(
            f"| {MODEL_ETIKETLERI[ad]}{isaret} | {d['MAE']:.3f} | {d['RMSE']:.3f} | "
            f"{d['R2']:.3f} | {test_hucre} |"
        )
    satirlar += [
        "",
        "Test sütunları yalnızca seçilen model ve iki baseline için doldurulur; test seti "
        "bir kez, model seçimi bittikten sonra kullanılmıştır (`test_kullanildi.flag`)."
        if test
        else "Test seti henüz kullanılmadı (`make test-degerlendir`).",
        "",
        "## Hiperparametre ızgarası (doğrulama MAE)",
        "",
        "| Model | Parametreler | Doğrulama MAE |",
        "|---|---|---|",
    ]
    for s in veri.get("izgara", []):
        satirlar.append(
            f"| {MODEL_ETIKETLERI[s['model']]} | `{json.dumps(s['parametreler'])}` | "
            f"{s['dogrulama_mae']:.4f} |"
        )
    satirlar.append("")
    (yol_al("raporlar") / "model_karsilastirma.md").write_text(
        "\n".join(satirlar), encoding="utf-8"
    )


def main() -> None:
    """Seçilen modeli ve iki baseline'ı test kümesinde BİR KEZ değerlendirir."""
    ayar = ayarlari_yukle()
    secim_yolu = yol_al("modeller") / "secim.json"
    secim = json.loads(secim_yolu.read_text(encoding="utf-8"))
    model = joblib.load(yol_al("modeller") / "en_iyi_model.joblib")
    parcalar = zamansal_bol(pd.read_csv(oznitelikler_yolu()), ayar)
    test = parcalar["test"]
    sonuc = {secim["model"]: test_seti_degerlendir(model, test, secim["model"],
                                                    secim["parametreler"])}
    sonuc.update(baseline_metrikleri(parcalar["egitim"], test, ayar))
    veri = metrikleri_oku()
    veri["test"] = sonuc
    metrikleri_yaz(veri)
    karsilastirma_yaz(veri)
    LOG.info("Test metrikleri: %s", {k: round(v["MAE"], 3) for k, v in sonuc.items()})


if __name__ == "__main__":
    loglama_kur()
    main()
