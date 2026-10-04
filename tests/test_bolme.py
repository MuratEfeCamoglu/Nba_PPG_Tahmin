"""Zamansal bölme testleri."""

from __future__ import annotations

import pytest

from src.ayarlar import ayarlari_yukle
from src.bolme import zamansal_bol
from src.oznitelik import oznitelik_uret


@pytest.fixture
def parcalar(sentetik_veri):
    return zamansal_bol(oznitelik_uret(sentetik_veri), ayarlari_yukle())


def test_anahtarlar(parcalar) -> None:
    assert set(parcalar) == {"egitim", "dogrulama", "test", "tahmin"}
    assert all(len(p) > 0 for p in parcalar.values())


def test_yil_kumeleri_ayrik_ve_sirali(parcalar) -> None:
    """Yıl kümeleri kesişmez ve eğitim < doğrulama < test < tahmin sırasındadır."""
    yillar = {ad: set(p["SEZON_YIL"]) for ad, p in parcalar.items()}
    adlar = ["egitim", "dogrulama", "test", "tahmin"]
    for i, a in enumerate(adlar):
        for b in adlar[i + 1:]:
            assert not yillar[a] & yillar[b]
            assert max(yillar[a]) < min(yillar[b])


def test_yil_araliklari_configle_uyumlu(parcalar) -> None:
    """Eğitim ⊂ ≤2019, doğrulama ⊂ [2020, 2022], test ⊂ [2023, 2024], tahmin = {2025}."""
    assert parcalar["egitim"]["SEZON_YIL"].max() <= 2019
    assert parcalar["dogrulama"]["SEZON_YIL"].between(2020, 2022).all()
    assert parcalar["test"]["SEZON_YIL"].between(2023, 2024).all()
    assert set(parcalar["tahmin"]["SEZON_YIL"]) == {2025}


def test_tahmin_kumesinde_hedef_yok(parcalar) -> None:
    assert parcalar["tahmin"]["HEDEF_PTS"].isna().all()


def test_filtreler_uygulanmis(parcalar) -> None:
    """t sezonunda GP >= 20 ve MIN >= 10; değerlendirme kümelerinde hedef dolu, t+1 GP >= 20."""
    for ad, p in parcalar.items():
        assert (p["GP"] >= 20).all() and (p["MIN"] >= 10).all(), ad
    for ad in ("egitim", "dogrulama", "test"):
        assert parcalar[ad]["HEDEF_PTS"].notna().all()
        assert (parcalar[ad]["HEDEF_GP"] >= 20).all()


def test_girdi_degismez(sentetik_veri) -> None:
    df = oznitelik_uret(sentetik_veri)
    kopya = df.copy()
    zamansal_bol(df, ayarlari_yukle())
    assert df.equals(kopya)
