"""veri_topla birim testleri: önbellek, birleştirme ve takas birleştirme (ağ yok)."""

from __future__ import annotations

import pandas as pd
import pytest

from src import veri_topla


def test_sezon_dizgesi() -> None:
    """Sezon dizgesi nba_api biçimindedir."""
    assert veri_topla.sezon_dizgesi(2000) == "2000-01"
    assert veri_topla.sezon_dizgesi(2009) == "2009-10"
    assert veri_topla.sezon_dizgesi(2025) == "2025-26"


def test_onbellek_varsa_api_cagrilmaz(tmp_path, monkeypatch) -> None:
    """Önbellek dosyası varsa API isteği yapılmaz."""
    dosya = tmp_path / "Base_2010.csv"
    pd.DataFrame({"PLAYER_ID": [1], "PTS": [10.0]}).to_csv(dosya, index=False)
    monkeypatch.setattr(veri_topla, "onbellek_yolu", lambda yil, olcum: dosya)

    def api_yasak(*args, **kwargs):
        raise AssertionError("API çağrılmamalıydı")

    monkeypatch.setattr(veri_topla, "_api_istegi", api_yasak)
    df = veri_topla.sezon_cek(2010, "Base")
    assert df["PTS"].tolist() == [10.0]


def test_api_basarisizsa_geri_cekilip_hata_firlatir(tmp_path, monkeypatch) -> None:
    """Tüm denemeler başarısızsa hata fırlatılır ve önbellek yazılmaz."""
    dosya = tmp_path / "Base_2010.csv"
    monkeypatch.setattr(veri_topla, "onbellek_yolu", lambda yil, olcum: dosya)
    monkeypatch.setattr(veri_topla.time, "sleep", lambda sn: None)
    sayac = {"n": 0}

    def hatali(*args, **kwargs):
        sayac["n"] += 1
        raise TimeoutError("zaman aşımı")

    monkeypatch.setattr(veri_topla, "_api_istegi", hatali)
    with pytest.raises(TimeoutError):
        veri_topla.sezon_cek(2010, "Base")
    assert sayac["n"] == 5
    assert not dosya.exists()


def test_takaslar_gp_agirlikli_birlesir() -> None:
    """Aynı oyuncu-sezonun iki satırı GP ağırlıklı ortalamayla tek satıra iner."""
    df = pd.DataFrame(
        {
            "PLAYER_ID": [7, 7, 8],
            "SEZON_YIL": [2015, 2015, 2015],
            "TEAM_ABBREVIATION": ["BOS", "LAL", "MIA"],
            "GP": [30, 10, 50],
            "PTS": [10.0, 20.0, 5.0],
        }
    )
    sonuc = veri_topla.takaslari_birlestir(df).set_index("PLAYER_ID")
    assert len(sonuc) == 2
    assert sonuc.loc[7, "GP"] == 40
    assert sonuc.loc[7, "PTS"] == pytest.approx(12.5)
    assert sonuc.loc[7, "TEAM_ABBREVIATION"] == "LAL"


def test_advanced_eslesmeyen_base_satiri_korunur() -> None:
    """Advanced'te olmayan oyuncu Base satırıyla kalır, advanced sütunları NaN."""
    base = pd.DataFrame({c: [1, 2] for c in veri_topla.BASE_SUTUNLAR})
    base["PLAYER_ID"] = [1, 2]
    adv = pd.DataFrame({c: [0.2] for c in veri_topla.ADVANCED_SUTUNLAR})
    adv["PLAYER_ID"] = [1]
    sonuc = veri_topla.sezonu_birlestir(base, adv, 2010)
    assert len(sonuc) == 2
    assert sonuc.loc[sonuc.PLAYER_ID == 2, "USG_PCT"].isna().all()
    assert (sonuc["SEZON_YIL"] == 2010).all()
