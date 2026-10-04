"""config.yaml okuyucu: projedeki tüm sabitlerin tek kaynağı."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import yaml

KOK_DIZIN = Path(__file__).resolve().parent.parent


def ayarlari_yukle(yol: str | Path = "config.yaml") -> dict[str, Any]:
    """YAML yapılandırma dosyasını okuyup sözlük olarak döndürür.

    Göreli yol verilirse proje kök dizinine göre çözülür.
    """
    yol = Path(yol)
    if not yol.is_absolute():
        yol = KOK_DIZIN / yol
    with open(yol, encoding="utf-8") as dosya:
        return yaml.safe_load(dosya)


def yol_al(anahtar: str, ayar: dict[str, Any] | None = None) -> Path:
    """config.yaml'daki `yollar` bölümünden mutlak bir yol döndürür ve klasörü oluşturur."""
    ayar = ayar if ayar is not None else ayarlari_yukle()
    yol = KOK_DIZIN / ayar["yollar"][anahtar]
    yol.mkdir(parents=True, exist_ok=True)
    return yol


def loglama_kur() -> None:
    """Modüllerin komut satırından çalıştırılmasında ortak loglama biçimini ayarlar."""
    for akis in (sys.stdout, sys.stderr):
        if hasattr(akis, "reconfigure"):
            akis.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )


if __name__ == "__main__":
    loglama_kur()
    logging.getLogger(__name__).info("Ayarlar: %s", ayarlari_yukle())
