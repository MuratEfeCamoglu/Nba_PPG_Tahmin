#!/bin/sh
# make sarmalayicisi: sistemde GNU make varsa onu, yoksa mini_make.py'yi kullanir.
# Kullanim: ./make <hedef>   (orn. ./make kur, ./make test)
cd "$(dirname "$0")" || exit 1
if command -v gmake >/dev/null 2>&1; then exec gmake "$@"; fi
m=$(command -v make 2>/dev/null)
case "$m" in
  ""|./make|make|"$PWD/make") ;;
  *) exec "$m" "$@" ;;
esac
for aday in .venv/Scripts/python.exe .venv/bin/python; do
  if [ -x "$aday" ]; then exec "$aday" mini_make.py "$@"; fi
done
for aday in python3 python py; do
  if command -v "$aday" >/dev/null 2>&1; then exec "$aday" mini_make.py "$@"; fi
done
echo "make: Python bulunamadi" >&2
exit 127
