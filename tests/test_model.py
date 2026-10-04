"""Model testleri: uzunluk, makullük aralığı, determinizm (küçük ızgara, sentetik veri)."""

from __future__ import annotations

import copy

import numpy as np
import pytest

from src.ayarlar import ayarlari_yukle
from src.bolme import zamansal_bol
from src.model import izgara_ara, modelleri_egit, quantile_egit
from src.oznitelik import oznitelik_uret
from tests.conftest import sentetik_oyuncu_sezon


@pytest.fixture(scope="module")
def kucuk_ayar() -> dict:
    """Testleri hızlandırmak için küçültülmüş ızgara (config.yaml değişmez)."""
    ayar = copy.deepcopy(ayarlari_yukle())
    ayar["model"]["ridge_alpha"] = [1, 10]
    ayar["model"]["rf"] = {"n_estimators": 30, "min_samples_leaf": [5]}
    ayar["model"]["lgbm"].update(
        {"num_leaves": [15], "learning_rate": [0.1], "n_estimators": 200, "early_stopping": 20}
    )
    return ayar


@pytest.fixture(scope="module")
def parcalar():
    return zamansal_bol(oznitelik_uret(sentetik_oyuncu_sezon(600)), ayarlari_yukle())


def test_tahmin_uzunlugu_ve_aralik(parcalar, kucuk_ayar) -> None:
    modeller = modelleri_egit(parcalar["egitim"], parcalar["dogrulama"], kucuk_ayar)
    assert set(modeller) == {"ridge", "random_forest", "lightgbm"}
    for ad, model in modeller.items():
        tahmin = model.predict(parcalar["dogrulama"])
        assert len(tahmin) == len(parcalar["dogrulama"]), ad
        assert np.all((tahmin >= 0) & (tahmin <= 40)), ad
        assert not np.isnan(tahmin).any(), ad


def test_ayni_seed_ile_deterministik(parcalar, kucuk_ayar) -> None:
    a, sonuc_a = izgara_ara(parcalar["egitim"], parcalar["dogrulama"], kucuk_ayar)
    b, sonuc_b = izgara_ara(parcalar["egitim"], parcalar["dogrulama"], kucuk_ayar)
    for ad in a:
        np.testing.assert_allclose(
            a[ad].predict(parcalar["test"]), b[ad].predict(parcalar["test"])
        )
    assert [s["dogrulama_mae"] for s in sonuc_a] == [s["dogrulama_mae"] for s in sonuc_b]


def test_quantile_alt_ust_sirasi(parcalar, kucuk_ayar) -> None:
    """Alt (0.1) quantile tahminleri ortalamada üst (0.9) quantile'dan küçüktür."""
    params = {"num_leaves": 15, "learning_rate": 0.1, "n_estimators": 100}
    alt = quantile_egit(parcalar["egitim"], 0.1, kucuk_ayar, params)
    ust = quantile_egit(parcalar["egitim"], 0.9, kucuk_ayar, params)
    assert alt.predict(parcalar["test"]).mean() < ust.predict(parcalar["test"]).mean()
