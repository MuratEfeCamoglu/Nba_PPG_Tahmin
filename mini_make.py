"""GNU make olmayan ortamlar için yalnızca standart kütüphane kullanan küçük Makefile çalıştırıcı.

Desteklenen alt küme (bu projenin Makefile'ı için yeterli):
- ``VAR := deger``, ``VAR = deger``, ``VAR ?= deger`` atamaları ve ``$(VAR)`` açılımı
- ``ifeq (a,b)`` / ``ifneq (a,b)`` / ``else`` / ``endif``
- ``hedef: bagimliliklar`` kuralları, TAB ile girintili tarif satırları
- Tarif öneklerinden ``@`` (yankısız) ve ``-`` (hatayı yok say)

Tüm hedefler .PHONY gibi ele alınır (dosya zaman damgası karşılaştırması yapılmaz).
Her tarif satırı, GNU make'teki gibi ayrı bir POSIX kabuğunda (bash) çalıştırılır.
Kullanım: ``python mini_make.py [hedef ...] [VAR=deger ...]``
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
LOG = logging.getLogger("mini_make")

DEGISKEN_DESENI = re.compile(r"\$\(([A-Za-z_][A-Za-z0-9_]*)\)")
ATAMA_DESENI = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*(:=|\?=|=)\s*(.*)$")
KOSUL_DESENI = re.compile(r"^(ifeq|ifneq)\s*\((.*),(.*)\)\s*$")


def ac(metin: str, degiskenler: dict[str, str], derinlik: int = 0) -> str:
    """Metindeki $(VAR) ifadelerini özyinelemeli açar; $$ dizisini $ yapar."""
    if derinlik > 20:
        raise RuntimeError("Değişken açılımında döngü: " + metin)
    yer_tutucu = "\x00DOLAR\x00"
    metin = metin.replace("$$", yer_tutucu)

    def degistir(eslesme: re.Match[str]) -> str:
        return ac(degiskenler.get(eslesme.group(1), ""), degiskenler, derinlik + 1)

    return DEGISKEN_DESENI.sub(degistir, metin).replace(yer_tutucu, "$")


def makefile_oku(
    yol: Path, degiskenler: dict[str, str]
) -> tuple[dict[str, tuple[list[str], list[str]]], list[str]]:
    """Makefile'ı ayrıştırır; (hedef -> (bağımlılıklar, tarifler)) ve hedef sırasını döndürür."""
    kurallar: dict[str, tuple[list[str], list[str]]] = {}
    sira: list[str] = []
    aktif: list[str] = []
    kosul_yigini: list[bool] = []
    for ham in yol.read_text(encoding="utf-8").splitlines():
        etkin = all(kosul_yigini)
        if ham.startswith("\t"):
            if etkin and aktif:
                for hedef in aktif:
                    kurallar[hedef][1].append(ham[1:])
            continue
        satir = ham.split("#", 1)[0].rstrip()
        if not satir.strip():
            continue
        kosul = KOSUL_DESENI.match(satir.strip())
        if kosul:
            sol = ac(kosul.group(2).strip(), degiskenler)
            sag = ac(kosul.group(3).strip(), degiskenler)
            sonuc = (sol == sag) if kosul.group(1) == "ifeq" else (sol != sag)
            kosul_yigini.append(sonuc)
            continue
        if satir.strip() == "else":
            kosul_yigini[-1] = not kosul_yigini[-1]
            continue
        if satir.strip() == "endif":
            kosul_yigini.pop()
            continue
        if not etkin:
            continue
        atama = ATAMA_DESENI.match(satir)
        if atama:
            ad, islec, deger = atama.groups()
            if islec == "?=" and ad in degiskenler:
                continue
            degiskenler[ad] = ac(deger, degiskenler) if islec == ":=" else deger
            aktif = []
            continue
        if ":" in satir:
            sol, sag = satir.split(":", 1)
            hedefler = ac(sol, degiskenler).split()
            bagimliliklar = ac(sag, degiskenler).split()
            aktif = [h for h in hedefler if not h.startswith(".")]
            for hedef in aktif:
                if hedef not in kurallar:
                    kurallar[hedef] = ([], [])
                    sira.append(hedef)
                kurallar[hedef][0].extend(bagimliliklar)
            continue
        raise SyntaxError(f"Makefile satırı anlaşılamadı: {ham!r}")
    if kosul_yigini:
        raise SyntaxError("Kapatılmamış ifeq/ifneq bloğu")
    return kurallar, sira


def bash_bul() -> str:
    """POSIX kabuğunu bulur; Windows'ta WSL yerine Git Bash'i tercih eder."""
    if os.name == "nt":
        git = shutil.which("git")
        if git:
            kok = Path(git).resolve().parent.parent
            for aday in (kok / "bin" / "bash.exe", kok / "usr" / "bin" / "bash.exe"):
                if aday.exists():
                    return str(aday)
    bulunan = shutil.which("bash") or shutil.which("sh")
    if not bulunan:
        raise FileNotFoundError("POSIX kabuğu (bash/sh) bulunamadı")
    return bulunan


def hedef_calistir(
    hedef: str,
    kurallar: dict[str, tuple[list[str], list[str]]],
    degiskenler: dict[str, str],
    kabuk: str,
    yapilan: set[str],
) -> int:
    """Hedefi (önce bağımlılıklarını) bir kez çalıştırır; ilk hatalı çıkış kodunu döndürür."""
    if hedef in yapilan:
        return 0
    if hedef not in kurallar:
        LOG.error("mini_make: *** '%s' hedefini oluşturacak kural yok.", hedef)
        return 2
    yapilan.add(hedef)
    bagimliliklar, tarifler = kurallar[hedef]
    for bagimlilik in bagimliliklar:
        kod = hedef_calistir(bagimlilik, kurallar, degiskenler, kabuk, yapilan)
        if kod != 0:
            return kod
    for tarif in tarifler:
        komut = ac(tarif, degiskenler).strip()
        sessiz = yoksay = False
        while komut[:1] in ("@", "-", "+"):
            sessiz = sessiz or komut[0] == "@"
            yoksay = yoksay or komut[0] == "-"
            komut = komut[1:].lstrip()
        if not komut:
            continue
        if not sessiz:
            LOG.info(komut)
        sys.stdout.flush()
        kod = subprocess.call([kabuk, "-c", komut])
        if kod != 0 and not yoksay:
            LOG.error("mini_make: *** [%s] Hata %d", hedef, kod)
            return kod
    return 0


def main(argumanlar: list[str]) -> int:
    """Komut satırı girişi: hedefleri ve VAR=deger geçersiz kılmalarını işler."""
    for akis in (sys.stdout, sys.stderr):
        if hasattr(akis, "reconfigure"):
            akis.reconfigure(encoding="utf-8", errors="replace")
    kok = Path(__file__).resolve().parent
    os.chdir(kok)
    degiskenler = dict(os.environ)
    gecersiz_kilma = {}
    hedefler = []
    for arguman in argumanlar:
        if "=" in arguman and not arguman.startswith("-"):
            ad, deger = arguman.split("=", 1)
            gecersiz_kilma[ad] = deger
        else:
            hedefler.append(arguman)
    degiskenler.update(gecersiz_kilma)
    kurallar, sira = makefile_oku(kok / "Makefile", degiskenler)
    degiskenler.update(gecersiz_kilma)
    if not hedefler:
        hedefler = sira[:1]
    kabuk = bash_bul()
    yapilan: set[str] = set()
    for hedef in hedefler:
        kod = hedef_calistir(hedef, kurallar, degiskenler, kabuk, yapilan)
        if kod != 0:
            return kod
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
