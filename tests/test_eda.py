"""EDA yardımcı fonksiyonlarının birim testleri (sentetik veri)."""

from __future__ import annotations

import pandas as pd
import pytest

from src.eda import ardisik_ciftler, ardisik_korelasyon, tepe_yas, yas_egrisi_delta


def test_ardisik_ciftler_yalniz_ardisik_ve_filtreli() -> None:
    """Çiftler yalnızca ardışık sezonlardan ve iki sezonda da filtreyi geçenlerden oluşur."""
    df = pd.DataFrame(
        {
            "PLAYER_ID": [1, 1, 1, 2, 2],
            "SEZON_YIL": [2010, 2011, 2013, 2010, 2011],
            "AGE": [25.0, 26.0, 28.0, 30.0, 31.0],
            "GP": [50, 60, 70, 50, 5],
            "MIN": [20.0, 25.0, 30.0, 20.0, 20.0],
            "PTS": [10.0, 12.0, 15.0, 8.0, 6.0],
        }
    )
    ciftler = ardisik_ciftler(df, min_gp=20, min_dakika=10)
    assert len(ciftler) == 1
    satir = ciftler.iloc[0]
    assert (satir.PLAYER_ID, satir.SEZON_YIL, satir.PTS_SONRAKI) == (1, 2010, 12.0)
    assert satir.PTS_36_SONRAKI == pytest.approx(12.0 / 25 * 36)


def test_tepe_yas_kumulatif_egrinin_tepesi() -> None:
    """Ortalama değişim 27 yaşından itibaren negatife dönüyorsa tepe yaş 27'dir."""
    egri = pd.DataFrame(
        {"AGE": [24, 25, 26, 27, 28], "ORT_DEGISIM": [1.0, 0.6, 0.2, -0.3, -0.8], "N": [50] * 5}
    )
    assert tepe_yas(egri) == 27


def test_yas_egrisi_az_gozlemli_yaslari_atar(sentetik_veri) -> None:
    """Gözlem sayısı eşiğin altındaki yaşlar eğriye girmez; sütunlar beklendiği gibi."""
    ciftler = ardisik_ciftler(sentetik_veri, min_gp=1, min_dakika=0)
    egri = yas_egrisi_delta(ciftler, min_gozlem=10)
    assert {"AGE", "ORT_DEGISIM", "N", "KUMULATIF"} <= set(egri.columns)
    assert (egri["N"] >= 10).all()


def test_ardisik_korelasyon_uc_olcu(sentetik_veri) -> None:
    """PTS, MIN ve PTS_36 için [-1, 1] aralığında korelasyon döner."""
    ciftler = ardisik_ciftler(sentetik_veri, min_gp=1, min_dakika=1)
    kor = ardisik_korelasyon(ciftler)
    assert set(kor) == {"PTS", "MIN", "PTS_36"}
    assert all(-1 <= v <= 1 for v in kor.values())
