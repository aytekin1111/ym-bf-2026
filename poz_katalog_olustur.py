"""Poz kataloğu olusturucu.
projeBf/ klasorundeki 4 PDF'ten poz katalogu olusturur.

Cikti: poz_katalog.csv
  poz_no | tanim | birim | fiyat_tl | kitap
"""
import re
import csv

# Layout modunda: poz_no en solda, fiyat en sagda. Arada tanim ve birim.
# Iki format yakala:
# 1) "15.460.1010  MOZAYIK DENIZLIK ...                          526,64"
# 2) "10.100.1001  Tasci ustasl                          Sa    310,00"
RE = re.compile(
    r"^\s*(\d{2}\.\d{3}\.\d{4})\s+"
    r"(.{4,90}?)\s+"
    r"(?:(Sa|TL|Ad|m\u00b2|m2|m3|m\u00b3|Kg|kg|100 m\u00b2|100 m3|100 m\u00b3|1000 Ad|100 Ad|Ton|ton)\s+)?"
    r"([\d.,]+)\s*$"
)


def parse(path, kitap):
    rows = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = RE.match(line)
            if not m:
                continue
            poz_no, tanim, birim, fiyat = m.groups()
            fiyat_tl = fiyat.replace(".", "").replace(",", ".") if fiyat else ""
            try:
                float(fiyat_tl)
            except ValueError:
                continue
            if len(tanim) > 100:
                continue
            if poz_no in rows:
                if not rows[poz_no]["fiyat_tl"] and fiyat_tl:
                    rows[poz_no]["fiyat_tl"] = fiyat_tl
                    rows[poz_no]["birim"] = birim or rows[poz_no]["birim"]
            else:
                rows[poz_no] = {
                    "poz_no": poz_no,
                    "tanim": tanim.strip(),
                    "birim": birim or "",
                    "fiyat_tl": fiyat_tl,
                    "kitap": kitap,
                }
    return rows


FILES = [
    ("rawtxt/01_Ana_BF.txt", "Ana_BF_2026"),
    ("rawtxt/02_Insaat_Analiz_TUM.txt", "Insaat_Analiz_TUM_2026"),
    ("rawtxt/03_Insaat_Analiz_1.txt", "Insaat_Analiz_1_2026"),
    ("rawtxt/04_Insaat_Analiz_2.txt", "Insaat_Analiz_2_2026"),
]


def main():
    all_rows = {}
    for path, kitap in FILES:
        r = parse(path, kitap)
        print(f"{kitap:30s}: {len(r)} poz")
        for k, v in r.items():
            if k not in all_rows:
                all_rows[k] = v
            else:
                if not all_rows[k]["fiyat_tl"] and v["fiyat_tl"]:
                    all_rows[k]["fiyat_tl"] = v["fiyat_tl"]
                    all_rows[k]["birim"] = v["birim"] or all_rows[k]["birim"]
                if len(v["tanim"]) > len(all_rows[k]["tanim"]) and len(v["tanim"]) < 100:
                    all_rows[k]["tanim"] = v["tanim"]

    cats = {}
    for r in all_rows.values():
        cat = r["poz_no"].split(".")[0]
        cats[cat] = cats.get(cat, 0) + 1
    print("\nPoz kategori dagilimi:")
    for c in sorted(cats.keys()):
        print(f"  {c}.xxx: {cats[c]} poz")

    with open("poz_katalog.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["poz_no", "tanim", "birim", "fiyat_tl", "kitap"])
        w.writeheader()
        for k in sorted(all_rows.keys()):
            w.writerow(all_rows[k])
    print(f"\nYazildi: poz_katalog.csv ({len(all_rows)} poz)")


if __name__ == "__main__":
    main()
