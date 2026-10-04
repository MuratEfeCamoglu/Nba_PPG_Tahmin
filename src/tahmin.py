"""Faz 6 — 2026-27 sezon tahmini ve %80 tahmin aralığı.

Seçilen model (doğrulamada seçilen tür ve parametreler) eğitim + doğrulama + test kümelerinin
tamamıyla yeniden eğitilir; aralık LightGBM quantile (alpha 0,1 / 0,9) ile üretilir.
2025-26 sezonunda GP ≥ 20 ve MIN ≥ 10 olan oyuncular için `reports/tahmin_2026_27.csv` yazılır.
Ayrıca aralık kalibrasyonu, quantile modelleri yalnız eğitimde eğitilip DOĞRULAMA kümesinde
kapsama oranı ölçülerek raporlanır (test kümesi değerlendirme için kullanılmaz).
"""

from __future__ import annotations

import json
import logging
from typing import Any

import joblib
import numpy as np
import pandas as pd

from src.ayarlar import ayarlari_yukle, loglama_kur, yol_al
from src.bolme import zamansal_bol
from src.degerlendir import metrikleri_oku, metrikleri_yaz
from src.model import quantile_egit, yeniden_egit
from src.oznitelik import oznitelikler_yolu

LOG = logging.getLogger(__name__)


def sezon_tahmini(
    model: Any, alt_model: Any, ust_model: Any, df_2025: pd.DataFrame
) -> pd.DataFrame:
    """Oyuncu, tahmin, alt, üst sütunlu tahmin tablosunu (tahmine göre azalan) döndürür."""
    sonuc = pd.DataFrame(
        {
            "PLAYER_ID": df_2025["PLAYER_ID"].to_numpy(),
            "OYUNCU": df_2025["PLAYER_NAME"].to_numpy(),
            "TAKIM": df_2025["TEAM_ABBREVIATION"].to_numpy(),
            "YAS_2025_26": df_2025["AGE"].to_numpy(),
            "PTS_2025_26": df_2025["PTS"].to_numpy(),
            "TAHMIN": np.round(model.predict(df_2025), 2),
            "ALT": np.round(alt_model.predict(df_2025), 2),
            "UST": np.round(ust_model.predict(df_2025), 2),
        }
    )
    return sonuc.sort_values("TAHMIN", ascending=False).reset_index(drop=True)


def aralik_kalibrasyonu(
    egitim: pd.DataFrame, dogrulama: pd.DataFrame, ayar: dict[str, Any],
    parametreler: dict[str, Any],
) -> dict[str, float]:
    """Yalnız eğitimde eğitilen quantile modellerin doğrulamadaki kapsama ve genişliği."""
    a = ayar["aralik"]
    alt = quantile_egit(egitim, a["alt"], ayar, parametreler).predict(dogrulama)
    ust = quantile_egit(egitim, a["ust"], ayar, parametreler).predict(dogrulama)
    y = dogrulama["HEDEF_PTS"].to_numpy()
    return {
        "hedef_kapsama": float(a["ust"] - a["alt"]),
        "kapsama": float(np.mean((y >= alt) & (y <= ust))),
        "ort_genislik": float(np.mean(ust - alt)),
        "alt_alti_oran": float(np.mean(y < alt)),
        "ust_ustu_oran": float(np.mean(y > ust)),
    }


def main() -> None:
    """Final modelleri eğitir, 2026-27 tahminlerini ve aralık kalibrasyonunu kaydeder."""
    ayar = ayarlari_yukle()
    secim = json.loads((yol_al("modeller") / "secim.json").read_text(encoding="utf-8"))
    parcalar = zamansal_bol(pd.read_csv(oznitelikler_yolu()), ayar)
    tum = pd.concat([parcalar["egitim"], parcalar["dogrulama"], parcalar["test"]],
                    ignore_index=True)
    q_param = secim["lgbm_parametreler"]
    model = yeniden_egit(secim["model"], secim["parametreler"], tum, ayar)
    alt_model = quantile_egit(tum, ayar["aralik"]["alt"], ayar, q_param)
    ust_model = quantile_egit(tum, ayar["aralik"]["ust"], ayar, q_param)
    modeller = yol_al("modeller")
    joblib.dump(model, modeller / "final_model.joblib")
    joblib.dump(alt_model, modeller / "quantile_alt.joblib")
    joblib.dump(ust_model, modeller / "quantile_ust.joblib")

    tahminler = sezon_tahmini(model, alt_model, ust_model, parcalar["tahmin"])
    tahminler.to_csv(yol_al("raporlar") / "tahmin_2026_27.csv", index=False)
    tutarli = float(((tahminler["ALT"] <= tahminler["TAHMIN"])
                     & (tahminler["TAHMIN"] <= tahminler["UST"])).mean())
    kalibrasyon = aralik_kalibrasyonu(parcalar["egitim"], parcalar["dogrulama"], ayar, q_param)
    veri = metrikleri_oku()
    veri["tahmin_2026_27"] = {
        "oyuncu_sayisi": len(tahminler),
        "egitim_satiri": len(tum),
        "alt_tahmin_ust_tutarli_oran": tutarli,
        "ort_tahmin": float(tahminler["TAHMIN"].mean()),
        "ort_aralik_genisligi": float((tahminler["UST"] - tahminler["ALT"]).mean()),
    }
    veri["aralik_dogrulama"] = kalibrasyon
    metrikleri_yaz(veri)
    LOG.info("2026-27: %d oyuncu, alt≤tahmin≤üst oranı %.3f, doğrulama kapsama %.3f",
             len(tahminler), tutarli, kalibrasyon["kapsama"])
    LOG.info("İlk 5:\n%s", tahminler.head().to_string())


if __name__ == "__main__":
    loglama_kur()
    main()
