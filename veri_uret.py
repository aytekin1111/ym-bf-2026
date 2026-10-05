"""Veri uretici: poz_index.tsv + poz_veri.h (exe'ye gomulu veri).
Kullanim:  python veri_uret.py
Kaynak:    poz_arama_gui.yukle() (projeBf metinleri: CSB + PTT + MSB)
Cikti:     poz_index.tsv (inceleme) + poz_veri.h (derleme icin)
"""
import csv
import os

from poz_arama_gui import yukle

BASE = os.path.dirname(os.path.abspath(__file__))


def main():
    rows = yukle()
    print(f"satir: {len(rows)}")
    tsv = os.path.join(BASE, "poz_index.tsv")
    with open(tsv, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["poz_no", "tanim", "birim", "fiyat_tl", "kitap"])
        for r in rows:
            w.writerow([r["poz_no"], r.get("tanim", ""), r.get("birim", ""),
                        r.get("fiyat_tl", ""), r.get("kitap", "")])
    with open(tsv, "rb") as f:
        data = f.read()
    hdr = os.path.join(BASE, "poz_veri.h")
    with open(hdr, "w", encoding="utf-8") as f:
        f.write("// OTOMATIK URETILDI (veri_uret.py) - elle degistirme\n")
        f.write("#pragma once\n#include <cstddef>\n")
        f.write("static const unsigned char POZ_VERI[] = {")
        f.write(",".join(str(b) for b in data))
        f.write("};\nstatic const size_t POZ_VERI_LEN = sizeof(POZ_VERI);\n")
    print(f"yazildi: poz_index.tsv ({len(data)} bayt), poz_veri.h")


if __name__ == "__main__":
    main()
