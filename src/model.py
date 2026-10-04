"""Modeller: Ridge, RandomForest, LightGBM (nokta tahmini) ve LightGBM quantile (aralık).

Hiperparametre araması yalnızca config.yaml'daki ızgarayla, eğitim kümesinde eğitip doğrulama
MAE'siyle yapılır. LightGBM erken durdurması doğrulama kümesini kullanır (ayar = doğrulama).
Test kümesi bu modülde hiç kullanılmaz.
"""

from __future__ import annotations

import itertools
import json
import logging
from typing import Any

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import StandardScaler

from src.ayarlar import ayarlari_yukle, loglama_kur, yol_al
from src.bolme import zamansal_bol
from src.degerlendir import (
    baseline_metrikleri,
    karsilastirma_yaz,
    metrikler,
    metrikleri_oku,
    metrikleri_yaz,
)
from src.oznitelik import OZNITELIKLER, oznitelikler_yolu

LOG = logging.getLogger(__name__)

SADELIK_SIRASI: list[str] = ["ridge", "random_forest", "lightgbm"]
ESITLIK_ESIGI = 0.02


class SinirliModel:
    """Öznitelik sütunlarını seçen ve tahminleri makullük sınırlarına kırpan sarmalayıcı."""

    def __init__(self, tahminci: Any, oznitelikler: list[str], alt: float, ust: float) -> None:
        self.tahminci = tahminci
        self.oznitelikler = list(oznitelikler)
        self.alt = alt
        self.ust = ust

    def X(self, df: pd.DataFrame) -> pd.DataFrame:
        """Modelin kullandığı öznitelik matrisini döndürür."""
        return df[self.oznitelikler].astype(float)

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """Kırpılmış tahminleri döndürür."""
        return np.clip(self.tahminci.predict(self.X(df)), self.alt, self.ust)


def _sinirlar(ayar: dict[str, Any]) -> tuple[float, float]:
    s = ayar["sinirlar"]
    return float(s["tahmin_alt"]), float(s["tahmin_ust"])


def _ridge(alpha: float) -> Pipeline:
    return make_pipeline(
        SimpleImputer(strategy="median", add_indicator=True), StandardScaler(), Ridge(alpha=alpha)
    )


def _rf(n_estimators: int, min_samples_leaf: int, random_state: int) -> Pipeline:
    return make_pipeline(
        SimpleImputer(strategy="median", add_indicator=True),
        RandomForestRegressor(
            n_estimators=n_estimators,
            min_samples_leaf=min_samples_leaf,
            random_state=random_state,
            n_jobs=-1,
        ),
    )


def _rf_tahmini_sabitle(pipeline: Pipeline) -> Pipeline:
    """Eğitilmiş RF'nin tahmininde n_jobs=1 kullanır.

    Paralel tahminde ağaç çıktıları iş parçacıklarında farklı sırayla toplandığından sonuç
    son basamakta (~1e-16) değişebilir; tek iş parçacığı bit düzeyinde determinizm sağlar.
    """
    pipeline[-1].set_params(n_jobs=1)
    return pipeline


def _lgbm(parametreler: dict[str, Any], random_state: int, **ek: Any) -> lgb.LGBMRegressor:
    return lgb.LGBMRegressor(
        num_leaves=parametreler["num_leaves"],
        learning_rate=parametreler["learning_rate"],
        n_estimators=parametreler["n_estimators"],
        random_state=random_state,
        deterministic=True,
        force_col_wise=True,
        verbose=-1,
        **ek,
    )


def izgara_ara(
    egitim: pd.DataFrame, dogrulama: pd.DataFrame, ayar: dict[str, Any]
) -> tuple[dict[str, SinirliModel], list[dict[str, Any]]]:
    """Her model ailesi için ızgarayı dener; aile başına en iyi modeli ve tüm sonuçları döndürür.

    Sonuç listesi elemanları: `{"model", "parametreler", "dogrulama_mae"}`.
    LightGBM'de `n_estimators` erken durdurmanın bulduğu en iyi iterasyondur.
    """
    m = ayar["model"]
    rs = int(m["random_state"])
    alt, ust = _sinirlar(ayar)
    X_e, y_e = egitim[OZNITELIKLER].astype(float), egitim["HEDEF_PTS"]
    X_d, y_d = dogrulama[OZNITELIKLER].astype(float), dogrulama["HEDEF_PTS"]
    sonuclar: list[dict[str, Any]] = []
    en_iyi: dict[str, tuple[float, SinirliModel]] = {}

    def kaydet(ad: str, parametreler: dict[str, Any], tahminci: Any) -> None:
        model = SinirliModel(tahminci, OZNITELIKLER, alt, ust)
        mae = metrikler(y_d, model.predict(dogrulama))["MAE"]
        sonuclar.append({"model": ad, "parametreler": parametreler, "dogrulama_mae": mae})
        LOG.info("%s %s → doğrulama MAE %.4f", ad, parametreler, mae)
        if ad not in en_iyi or mae < en_iyi[ad][0]:
            en_iyi[ad] = (mae, model)

    for alpha in m["ridge_alpha"]:
        kaydet("ridge", {"alpha": alpha}, _ridge(alpha).fit(X_e, y_e))
    for yaprak in m["rf"]["min_samples_leaf"]:
        tahminci = _rf_tahmini_sabitle(_rf(m["rf"]["n_estimators"], yaprak, rs).fit(X_e, y_e))
        kaydet("random_forest", {"n_estimators": m["rf"]["n_estimators"],
                                 "min_samples_leaf": yaprak}, tahminci)
    lg = m["lgbm"]
    for yaprak, oran in itertools.product(lg["num_leaves"], lg["learning_rate"]):
        p = {"num_leaves": yaprak, "learning_rate": oran, "n_estimators": lg["n_estimators"]}
        tahminci = _lgbm(p, rs).fit(
            X_e, y_e, eval_X=(X_d,), eval_y=(y_d,), eval_metric="l1",
            callbacks=[lgb.early_stopping(lg["early_stopping"], first_metric_only=True,
                                          verbose=False)],
        )
        p["n_estimators"] = int(tahminci.best_iteration_ or lg["n_estimators"])
        kaydet("lightgbm", p, tahminci)
    return {ad: model for ad, (_, model) in en_iyi.items()}, sonuclar


def modelleri_egit(
    egitim: pd.DataFrame, dogrulama: pd.DataFrame, ayar: dict[str, Any]
) -> dict[str, SinirliModel]:
    """Ad → eğitilmiş (aile içinde doğrulama MAE'si en iyi) model sözlüğü döndürür."""
    modeller, _ = izgara_ara(egitim, dogrulama, ayar)
    return modeller


def model_sec(sonuclar: list[dict[str, Any]]) -> dict[str, Any]:
    """Doğrulama MAE'si en düşük sonucu seçer; fark < 0,02 olanlar arasında en basiti tercih edilir.

    Sadelik sırası: Ridge > RandomForest > LightGBM (İskelet.md §8).
    """
    aile_en_iyi: dict[str, dict[str, Any]] = {}
    for s in sonuclar:
        if s["model"] not in aile_en_iyi or s["dogrulama_mae"] < aile_en_iyi[s["model"]][
            "dogrulama_mae"
        ]:
            aile_en_iyi[s["model"]] = s
    en_dusuk = min(s["dogrulama_mae"] for s in aile_en_iyi.values())
    adaylar = [s for s in aile_en_iyi.values() if s["dogrulama_mae"] - en_dusuk < ESITLIK_ESIGI]
    return min(adaylar, key=lambda s: SADELIK_SIRASI.index(s["model"]))


def yeniden_egit(
    model_adi: str, parametreler: dict[str, Any], df: pd.DataFrame, ayar: dict[str, Any]
) -> SinirliModel:
    """Sabit parametrelerle (erken durdurma olmadan) verilen kümede modeli yeniden eğitir."""
    rs = int(ayar["model"]["random_state"])
    X, y = df[OZNITELIKLER].astype(float), df["HEDEF_PTS"]
    if model_adi == "ridge":
        tahminci = _ridge(parametreler["alpha"])
    elif model_adi == "random_forest":
        tahminci = _rf(parametreler["n_estimators"], parametreler["min_samples_leaf"], rs)
    elif model_adi == "lightgbm":
        tahminci = _lgbm(parametreler, rs)
    else:
        raise ValueError(f"Bilinmeyen model: {model_adi}")
    tahminci.fit(X, y)
    if model_adi == "random_forest":
        _rf_tahmini_sabitle(tahminci)
    alt, ust = _sinirlar(ayar)
    return SinirliModel(tahminci, OZNITELIKLER, alt, ust)


def quantile_egit(
    df: pd.DataFrame,
    alpha: float,
    ayar: dict[str, Any],
    parametreler: dict[str, Any] | None = None,
) -> SinirliModel:
    """LightGBM quantile modeli (objective="quantile", verilen alpha) eğitir.

    `parametreler` (num_leaves, learning_rate, n_estimators) verilmezse ızgaranın ilk
    değerleri ve 500 iterasyon kullanılır.
    """
    lg = ayar["model"]["lgbm"]
    p = parametreler or {"num_leaves": lg["num_leaves"][0],
                         "learning_rate": lg["learning_rate"][0], "n_estimators": 500}
    tahminci = _lgbm(p, int(ayar["model"]["random_state"]), objective="quantile", alpha=alpha)
    tahminci.fit(df[OZNITELIKLER].astype(float), df["HEDEF_PTS"])
    alt, ust = _sinirlar(ayar)
    return SinirliModel(tahminci, OZNITELIKLER, alt, ust)


def main() -> None:
    """Izgara araması, baseline karşılaştırması, model seçimi ve kayıt (test kullanılmaz)."""
    ayar = ayarlari_yukle()
    parcalar = zamansal_bol(pd.read_csv(oznitelikler_yolu()), ayar)
    egitim, dogrulama = parcalar["egitim"], parcalar["dogrulama"]
    modeller, sonuclar = izgara_ara(egitim, dogrulama, ayar)
    dog = baseline_metrikleri(egitim, dogrulama, ayar)
    for ad, model in modeller.items():
        dog[ad] = metrikler(dogrulama["HEDEF_PTS"], model.predict(dogrulama))
    secim = model_sec(sonuclar)
    lgbm_en_iyi = min((s for s in sonuclar if s["model"] == "lightgbm"),
                      key=lambda s: s["dogrulama_mae"])
    joblib.dump(modeller[secim["model"]], yol_al("modeller") / "en_iyi_model.joblib")
    (yol_al("modeller") / "secim.json").write_text(
        json.dumps({**secim, "lgbm_parametreler": lgbm_en_iyi["parametreler"]}, indent=2),
        encoding="utf-8",
    )
    veri = metrikleri_oku()
    veri.update({
        "dogrulama": dog,
        "secilen_model": secim["model"],
        "secilen_parametreler": secim["parametreler"],
        "izgara": sonuclar,
        "kume_boyutlari": {ad: len(p) for ad, p in parcalar.items()},
    })
    metrikleri_yaz(veri)
    karsilastirma_yaz(veri)
    secilen = dog[secim["model"]]
    LOG.info("Seçilen: %s %s · doğrulama MAE %.3f (naif %.3f, Marcel %.3f)", secim["model"],
             secim["parametreler"], secilen["MAE"], dog["naif"]["MAE"], dog["marcel"]["MAE"])
    if secilen["R2"] > 0.90 or secilen["MAE"] < 1.0:
        LOG.warning("ÇOK İYİ ALARMI: R²=%.3f MAE=%.3f — sızıntı şüphesi, inceleyin!",
                    secilen["R2"], secilen["MAE"])


if __name__ == "__main__":
    # SinirliModel'in `__main__` yerine `src.model` adıyla pickle'lanması için modül
    # paket adıyla içe aktarılıp çalıştırılır (joblib yüklemesi diğer modüllerde çalışsın).
    from src.model import main as paket_main

    loglama_kur()
    paket_main()
