"""Poz arama/karşılaştırma scripti.
Kullanım:
  python poz_arama.py <poz_no>            Tam eşleşme (15.225.1010)
  python poz_arama.py <prefix: 15.225>    O kategorideki tüm pozlar
  python poz_arama.py <kategori: 15>      O bölümdeki tüm pozlar
  python poz_arama.py "<anahtar kelime>"  Metin araması (örn "asma tavan")
"""
import csv
import sys
import re

KATALOG = "poz_katalog.csv"


def yukle():
    rows = []
    with open(KATALOG, encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    return rows


KAT = yukle()


def poz_ara(poz_no=None, anahtar=None, prefix=None, kategori=None):
    results = []
    for r in KAT:
        if poz_no and r["poz_no"] != poz_no:
            continue
        if prefix and not r["poz_no"].startswith(prefix):
            continue
        if kategori and not r["poz_no"].startswith(kategori + "."):
            continue
        if anahtar and anahtar.lower() not in r["tanim"].lower():
            continue
        results.append(r)
    return results


def goster(results, baslik=""):
    if not results:
        print("  Sonuc bulunamadi.")
        return
    print(f"\n{baslik} - {len(results)} sonuc:\n")
    print(f"  {'POZ NO':13s} {'BIRIM':8s} {'FIYAT (TL)':>12s}  ACIKLAMA")
    print(f"  {'-'*13} {'-'*8} {'-'*12}  {'-'*60}")
    for r in results:
        fiyat = r["fiyat_tl"] if r["fiyat_tl"] else "-"
        print(f"  {r['poz_no']:13s} {r['birim']:8s} {fiyat:>12s}  {r['tanim'][:60]}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanim:")
        print("  python poz_arama.py <poz_no>")
        print("  python poz_arama.py <prefix: orn 15.225>")
        print("  python poz_arama.py <kategori: orn 15>")
        print('  python poz_arama.py "<anahtar kelime>"')
        sys.exit(0)
    arg = sys.argv[1]
    if re.match(r"^\d{2}(\.\d{1,3}){0,2}$", arg):
        if arg.count(".") == 2:
            goster(poz_ara(poz_no=arg), f"Tam eslesme: {arg}")
        elif arg.count(".") == 1:
            goster(poz_ara(prefix=arg), f"Prefix: {arg}")
        else:
            goster(poz_ara(kategori=arg), f"Kategori: {arg}")
    else:
        goster(poz_ara(anahtar=arg), f"Anahtar: {arg}")
