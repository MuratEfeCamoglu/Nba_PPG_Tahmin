"""Yerel Streamlit uygulaması: 2026-27 maç başı sayı tahminleri ve model özeti.

Çalıştırma (yalnızca yerelde): `.venv/Scripts/python.exe -m streamlit run app/streamlit_app.py`
(Linux/macOS: `.venv/bin/python -m streamlit run app/streamlit_app.py`).
İçe aktarıldığında hiçbir kod çalışmaz; uygulama gövdesi `main()` içindedir.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

KOK = Path(__file__).resolve().parent.parent
RAPORLAR = KOK / "reports"


def verileri_yukle() -> tuple[pd.DataFrame, dict]:
    """Tahmin tablosunu ve metrikleri okur."""
    tahminler = pd.read_csv(RAPORLAR / "tahmin_2026_27.csv")
    metrik = json.loads((RAPORLAR / "metrikler.json").read_text(encoding="utf-8"))
    return tahminler, metrik


def main() -> None:
    """Streamlit arayüzünü çizer."""
    import streamlit as st

    st.set_page_config(page_title="NBA 2026-27 Sayı Tahmini", layout="wide")
    st.title("NBA 2026-27 maç başı sayı tahmini")
    st.caption(
        "2025-26 sezonunda en az 20 maç ve maç başı 10 dakika oynayan oyuncular için; "
        "%80 tahmin aralığıyla. Model oyuncunun anlamlı süre aldığını varsayar."
    )
    tahminler, metrik = verileri_yukle()

    secilen = metrik["secilen_model"]
    sutunlar = st.columns(4)
    sutunlar[0].metric("Seçilen model", secilen)
    sutunlar[1].metric("Test MAE (model)", f"{metrik['test'][secilen]['MAE']:.2f}")
    sutunlar[2].metric("Test MAE (naif)", f"{metrik['test']['naif']['MAE']:.2f}")
    sutunlar[3].metric("Doğrulamada %80 aralık kapsaması",
                       f"{metrik['aralik_dogrulama']['kapsama']:.1%}")

    takimlar = ["Tümü", *sorted(tahminler["TAKIM"].unique())]
    takim = st.selectbox("Takım", takimlar)
    arama = st.text_input("Oyuncu ara")
    goster = tahminler
    if takim != "Tümü":
        goster = goster[goster["TAKIM"] == takim]
    if arama:
        goster = goster[goster["OYUNCU"].str.contains(arama, case=False, na=False)]
    st.dataframe(goster, width="stretch", hide_index=True)

    st.subheader("İlk 20 oyuncu (tahmin ve aralık)")
    ilk = tahminler.head(20).set_index("OYUNCU")[["ALT", "TAHMIN", "UST"]]
    st.bar_chart(ilk["TAHMIN"])
    st.dataframe(ilk, width="stretch")

    st.subheader("Model yorumlama")
    for dosya, baslik in [("shap_ozet.png", "SHAP özet"),
                          ("yas_kismi_bagimlilik.png", "Yaş kısmi bağımlılığı"),
                          ("yas_egrisi.png", "EDA yaş eğrisi")]:
        yol = RAPORLAR / "figures" / dosya
        if yol.exists():
            st.image(str(yol), caption=baslik)


if __name__ == "__main__":
    main()
