"""Duman testi: tüm src modülleri import edilebiliyor."""

from __future__ import annotations

import importlib

import pytest

MODULLER = [
    "ayarlar",
    "veri_topla",
    "hedef",
    "eda",
    "oznitelik",
    "bolme",
    "baseline",
    "model",
    "degerlendir",
    "yorumla",
    "tahmin",
]


@pytest.mark.parametrize("ad", MODULLER)
def test_modul_import_ediliyor(ad: str) -> None:
    """Her modül hatasız import edilir."""
    importlib.import_module(f"src.{ad}")


def test_ayarlar_okunuyor() -> None:
    """config.yaml okunur ve zorunlu bölümleri içerir."""
    from src.ayarlar import ayarlari_yukle

    ayar = ayarlari_yukle()
    for bolum in ("veri", "filtre", "bolme", "marcel", "model", "aralik"):
        assert bolum in ayar
    assert ayar["model"]["random_state"] == 42


def test_sentetik_veri_sozlesmesi(sentetik_veri) -> None:
    """Sentetik fixture benzersiz anahtar kuralına uyar."""
    assert not sentetik_veri.duplicated(["PLAYER_ID", "SEZON_YIL"]).any()
