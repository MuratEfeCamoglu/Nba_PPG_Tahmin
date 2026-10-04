"""Güncel takım eşleştirmesi (src.kadro) — sentetik veriyle, ağ gerektirmez."""

from __future__ import annotations

import pandas as pd

from src.kadro import guncel_takim_ekle


def _tahmin() -> pd.DataFrame:
    return pd.DataFrame({"PLAYER_ID": [1, 2, 3], "TAKIM": ["LAL", "BOS", "MIA"],
                         "TAHMIN": [20.0, 15.0, 10.0]})


def test_kadro_durumlari() -> None:
    kadro = pd.DataFrame({"PERSON_ID": [1, 2, 9], "TEAM_ABBREVIATION": ["PHI", "BOS", "NYK"],
                          "ROSTER_STATUS": [1.0, 1.0, 1.0]})
    sonuc = guncel_takim_ekle(_tahmin(), kadro)
    assert sonuc["GUNCEL_TAKIM"].tolist() == ["PHI", "BOS", ""]
    assert sonuc["KADRO_DURUMU"].tolist() == ["degisti", "ayni", "yok"]


def test_kadro_yoksa_eski_takim_ve_girdi_degismez() -> None:
    girdi = _tahmin()
    sonuc = guncel_takim_ekle(girdi, None)
    assert sonuc["GUNCEL_TAKIM"].tolist() == ["LAL", "BOS", "MIA"]
    assert (sonuc["KADRO_DURUMU"] == "bilinmiyor").all()
    assert "GUNCEL_TAKIM" not in girdi.columns


def test_aktif_olmayan_kadro_satiri_sayilmaz() -> None:
    kadro = pd.DataFrame({"PERSON_ID": [1], "TEAM_ABBREVIATION": ["PHI"], "ROSTER_STATUS": [0.0]})
    sonuc = guncel_takim_ekle(_tahmin(), kadro)
    assert sonuc.loc[0, "KADRO_DURUMU"] == "yok"
