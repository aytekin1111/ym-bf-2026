"""Poz Arama - Masaustu uygulamasi (tkinter, tarayici yok).
Kullanim:
    python poz_arama_gui.py
Veri:
    Ayni klasordeki poz_katalog.csv (poz_no,tanim,birim,fiyat_tl,kitap)
Ozellikler:
    - Arama kutusuna poz no (orn. 15.445 / 15.445.1002) veya 1+ kelime yazilir.
    - Cok kelimede varsayilan AND (tum kelimeler gececek), secimle OR.
    - Turkce karakter duyarsiz eslesme (mermer/MERMER, seramik/SERAMIK).
    - Sonuclar tam tanimiyla (2-3 satira sarmali) kaydirilabilir listede.
    - Dikey scrollbar (slider) ile uzun liste gezilir.
    - Sonuca cift tiklayinca poz_no panoya kopyalanir.
"""
import csv
import os
import re
import tkinter as tk
from tkinter import ttk

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KATALOG = os.path.join(BASE_DIR, "poz_katalog.csv")
MAX_GOSTER = 1000

# Turkce duyarsiz normalize
_TR_MAP = str.maketrans({
    "I": "ı", "İ": "i", "I".lower(): "ı",
    "Ş": "ş", "Ğ": "ğ", "Ü": "ü", "Ö": "ö", "Ç": "ç",
})


def norm(s: str) -> str:
    if s is None:
        return ""
    t = s.translate(_TR_MAP).casefold()
    # ASCII katlama: klavyede Turkce harf yoksa da bulunsun
    for a, b in (("ş", "s"), ("ğ", "g"), ("ü", "u"), ("ö", "o"), ("ç", "c"), ("ı", "i")):
        t = t.replace(a, b)
    return t


RAW_DIR = os.path.join(BASE_DIR, "rawtxt")
# Analiz metinleri (projeBf kaynakli): poz basligi = poz_no + tanim + birim
ANALIZ_DOSYALARI = [
    ("02_Insaat_Analiz_TUM.txt", "Insaat_Analiz_TUM_2026"),
    ("03_Insaat_Analiz_1.txt", "Insaat_Analiz_1_2026"),
    ("04_Insaat_Analiz_2.txt", "Insaat_Analiz_2_2026"),
]
_BIRIM = (r"Sa|TL|Ad|m²|m2|m3|m³|Kg|kg|100 m²|100 m3|100 m³|"
           r"1000 Ad|100 Ad|Ton|ton|m\b")
_BASLIK_RE = re.compile(
    r"^\s*(\d{2}\.\d{3}\.\d{4})\s+(.+?)\s+(" + _BIRIM + r")\s*$"
)
_ATLA = ("poz no", "tanimi", "olcu", "tutari",
         "malzeme", "iscilik", "genel fiyat", "1.01.2026", "01.01.2026")


_FIYAT_RE = re.compile(
    r"1\s+(m\u00b2|m2|m3|m\u00b3|Ad|Kg|Ton|ton|m)\s+Fiyat\u0131\s+([\d.,]+)"
)


_PTT_POZ = re.compile(r"^\s*(77\.\d{3}\.\d{4})\s*(.*?)\s*$")
_PTT_BIRIM = re.compile(r"\b(M2|MT|M3|AD|KG|TON|SA|SET|TK|PK)\b")
_PTT_FIYAT = re.compile(r"Toplam Tutar\s+([\d.,]+)")


_MSB_POZ = re.compile(r"^\s*(48\.\d{3}\.\d{4})\s*(.*?)\s*$")
_MSB_BIRIM = re.compile(r"\b(m³|m²|M2|M3|MT|AD|KG|TON|SA|sa|m\b)\b")
_MSB_FIYAT = re.compile(r"1\s+(\S+)\s+Fiyatı\s*:\s*([\d.,]+)")
_MSB_ATLA = ("poz no", "tanimi", "olcu", "birimi", "fiyati", "tutari",
             "malzeme", "iscilik", "ekipman", "girdiler")


def _msb_baslik_mi(lines, i):
    if not _MSB_POZ.match(lines[i]):
        return False
    return "FİYAT ANALİZİ" in "".join(lines[max(0, i - 10):i])


def _msb_parse(path):
    """MSB 2026 insaat analizleri (10_MSB_2026.txt). Donus {poz_no: {...}}."""
    rows = {}
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return rows
    basliklar = [i for i in range(len(lines)) if _msb_baslik_mi(lines, i)]
    for n, i in enumerate(basliklar):
        m = _MSB_POZ.match(lines[i])
        poz, rest = m.group(1), m.group(2).strip()
        bm = _MSB_BIRIM.search(rest)
        birim = bm.group(1).upper().replace("M2", "m²").replace("M3", "m³") if bm else ""
        tanim = _MSB_BIRIM.sub("", rest).strip() if bm else rest
        for l in lines[i + 1:i + 3]:
            s = l.strip()
            if not s or _MSB_POZ.match(l):
                break
            nl = norm(s)
            if any(a in nl for a in _MSB_ATLA) or len(s) < 6:
                break
            if len(tanim) + len(s) < 300:
                tanim = (tanim + " " + s).strip()
            break
        end = basliklar[n + 1] if n + 1 < len(basliklar) else len(lines)
        fiyat, fb = "", ""
        for l in lines[i + 1:end]:
            fm = _MSB_FIYAT.search(l)
            if fm:
                try:
                    fiyat = f"{float(fm.group(2).replace('.', '').replace(',', '.')):.2f}"
                    fb = fm.group(1)
                except ValueError:
                    pass
                break
        if not birim and fb:
            birim = fb.upper().replace("M2", "m²").replace("M3", "m³")
        if poz not in rows:
            rows[poz] = {"poz_no": poz, "tanim": tanim, "birim": birim,
                         "fiyat_tl": fiyat, "kitap": "MSB_2026"}
    return rows


def _ptt_baslik_mi(lines, i):
    if not _PTT_POZ.match(lines[i]):
        return False
    ctx = "".join(lines[max(0, i - 12):i])
    return ("Grubu No" in ctx) or ("Analiz Format No" in ctx)


def _ptt_parse(path):
    """PTT Ozel Birim Fiyat analiz paftalari (07_PTT_1.txt).
    Donus: {poz_no: {...}} ; fiyati paftada hesaplanmamis (taslak) olanlar
    fiyatsiz gelir, uydurma fiyat yazilmaz."""
    rows = {}
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return rows
    basliklar = [i for i in range(len(lines))
                 if _PTT_POZ.match(lines[i]) and _ptt_baslik_mi(lines, i)]
    for n, i in enumerate(basliklar):
        m = _PTT_POZ.match(lines[i])
        poz, rest = m.group(1), m.group(2).strip()
        end = basliklar[n + 1] if n + 1 < len(basliklar) else len(lines)
        govde = lines[i:end]
        if rest:  # V1: tanim ayni satirda
            tanim = rest
            birim = ""
            for k in range(max(0, i - 6), i):
                for b in _PTT_BIRIM.findall(lines[k]):
                    birim = b
            for l in govde[1:]:
                s = l.strip()
                if not s or s.startswith("Poz No") or "GİRDİLER" in s:
                    break
                if _PTT_POZ.match(l):
                    break
                if len(tanim) + len(s) < 300:
                    tanim = (tanim + " " + s).strip()
                break
        else:  # V2: tanim "Grubu No :" satirinda
            tanim, birim = "", ""
            for k in range(max(0, i - 6), i):
                if "Grubu No" in lines[k]:
                    t = lines[k].replace("Grubu No", "").replace(":", "").strip()
                    bm = _PTT_BIRIM.search(t)
                    if bm:
                        birim = bm.group(1)
                        t = (t[:bm.start()] + t[bm.end():]).strip()
                    tanim = t
        fiyat = ""
        for l in govde[1:]:
            fm = _PTT_FIYAT.search(l)
            if fm:
                try:
                    fiyat = f"{float(fm.group(1).replace('.', '').replace(',', '.')):.2f}"
                except ValueError:
                    fiyat = ""
                break
        if poz not in rows:
            rows[poz] = {"poz_no": poz, "tanim": tanim, "birim": birim,
                         "fiyat_tl": fiyat, "kitap": "PTT_Ozel_07-2026"}
    return rows


def _analiz_parse(path, kitap):
    """Analiz txt'den poz basliklarini cikar; devam satirini tanima ekle,
    '1 m2 Fiyati' satirindan birim fiyati da alir."""
    rows = {}
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return rows
    for i, line in enumerate(lines):
        m = _BASLIK_RE.match(line)
        if not m:
            continue
        poz_no, tanim, birim = m.group(1), m.group(2).strip(), m.group(3)
        if len(tanim) < 4 or len(tanim) > 120:
            continue
        nt = norm(tanim)
        if "olcu birimi" in nt or "birim fiyati" in nt:
            continue  # tablo basligi satiri, temiz ciftini baska dosyadan al
        if tanim.startswith("("):
            continue  # analiz ici rayic satiri artigi
        # devam satiri: bir sonraki anlamli satir baslik degilse tanima ekle
        for j in range(i + 1, min(i + 3, len(lines))):
            nxt = lines[j].replace("Tutar\u0131 (TL)", "").strip()
            if not nxt or _BASLIK_RE.match(lines[j]):
                break
            nl = norm(nxt)
            if any(a in nl for a in _ATLA) or len(nxt) < 8:
                break
            if len(tanim) + len(nxt) < 300:
                tanim = (tanim + " " + nxt).strip()
            break
        fiyat = ""
        for j in range(i + 1, min(i + 45, len(lines))):
            if _BASLIK_RE.match(lines[j]) and j > i + 1:
                break
            fm = _FIYAT_RE.search(lines[j])
            if fm:
                fiyat = fm.group(2).replace(".", "").replace(",", ".")
                try:
                    float(fiyat)
                except ValueError:
                    fiyat = ""
                break
        if poz_no not in rows:
            rows[poz_no] = {"poz_no": poz_no, "tanim": tanim, "birim": birim,
                            "fiyat_tl": fiyat, "kitap": kitap}
        elif fiyat and not rows[poz_no]["fiyat_tl"]:
            rows[poz_no]["fiyat_tl"] = fiyat
    return rows


def yukle():
    # 1) fiyatlar icin katalog (Ana_BF fiyatlari)
    fiyat = {}
    try:
        with open(KATALOG, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                p, fl = r.get("poz_no", ""), (r.get("fiyat_tl") or "").strip()
                if p and fl and p not in fiyat:
                    fiyat[p] = fl
    except FileNotFoundError:
        pass
    # 2) analiz metinlerinden tam basliklar (15.xxx icin dogru tanim)
    rows = {}
    for ad, kitap in ANALIZ_DOSYALARI:
        for k, v in _analiz_parse(os.path.join(RAW_DIR, ad), kitap).items():
            if k not in rows:
                rows[k] = v
    # 2b) PTT ozel pozlar (77.xxx) - analiz paftalarindan
    for k, v in _ptt_parse(os.path.join(RAW_DIR, "07_PTT_1.txt")).items():
        if k not in rows:
            rows[k] = v
    # 2c) MSB 2026 insaat pozlari (48.xxx)
    for k, v in _msb_parse(os.path.join(RAW_DIR, "10_MSB_2026.txt")).items():
        if k not in rows:
            rows[k] = v
    # 3) katalogtaki analiz-disi pozlari ekle (10.xxx rayic, 25.xxx, 35.xxx)
    try:
        with open(KATALOG, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                p = r.get("poz_no", "")
                t = r.get("tanim", "")
                if not p or p in rows or len(t) >= 100:
                    continue
                nt = norm(t)
                if "olcu birimi" in nt or "birim fiyati" in nt:
                    continue  # tablo basligi artigi
                if t.startswith("("):
                    continue  # analiz ici rayic satiri artigi
                rows[p] = {"poz_no": p, "tanim": t,
                           "birim": r.get("birim", ""), "fiyat_tl": r.get("fiyat_tl", ""),
                           "kitap": r.get("kitap", "")}
    except FileNotFoundError:
        pass
    # 4) fiyatlari birlestir
    out = []
    for k in sorted(rows.keys()):
        r = rows[k]
        if not r.get("fiyat_tl") and k in fiyat:
            r["fiyat_tl"] = fiyat[k]
        r["_n_tanim"] = norm(r.get("tanim", ""))
        r["_n_poz"] = norm(r.get("poz_no", ""))
        out.append(r)
    return out


def ara(rows, sorgu: str, mod: str = "AND"):
    """sorgu: ham metin. Donus: eslesen satir listesi."""
    q = sorgu.strip()
    if not q:
        return []
    # Poz no benzeri mi? (rakam ve nokta agirlikli)
    if re.fullmatch(r"[\d.\s]+", q):
        prefix = q.strip()
        return [r for r in rows if r["poz_no"].startswith(prefix)]
    kelimeler = [norm(k) for k in q.split() if k.strip()]
    if not kelimeler:
        return []
    out = []
    for r in rows:
        blob = r["_n_tanim"] + " " + r["_n_poz"]
        if mod == "OR":
            if any(k in blob for k in kelimeler):
                out.append(r)
        else:
            if all(k in blob for k in kelimeler):
                out.append(r)
    return out


def fiyat_goster(r) -> str:
    f = (r.get("fiyat_tl") or "").strip()
    if not f:
        return "-"
    try:
        return f"{float(f):,.2f} TL".replace(",", "X").replace(".", ",").replace("X", ".")
    except ValueError:
        return f


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Poz Arama - CSB 2026 (projeBf)")
        self.geometry("1020x700")
        try:
            self.rows = yukle()
        except FileNotFoundError:
            self.rows = []
        self._after_id = None
        self._sonuclar = []
        self._kur_gui()
        self._durum(f"{len(self.rows)} poz yuklendi. Arama yazin.")

    def _kur_gui(self):
        ust = ttk.Frame(self, padding=8)
        ust.pack(fill="x")
        ttk.Label(ust, text="Arama:").pack(side="left")
        self.entry = ttk.Entry(ust, width=60)
        self.entry.pack(side="left", padx=(6, 6), fill="x", expand=True)
        self.entry.bind("<Return>", lambda e: self._calistir())
        self.entry.bind("<KeyRelease>", self._canli)
        ttk.Button(ust, text="Ara", command=self._calistir).pack(side="left")
        ttk.Button(ust, text="Temizle", command=self._temizle).pack(side="left", padx=(6, 0))

        sec = ttk.Frame(self, padding=(8, 0))
        sec.pack(fill="x")
        self.mod = tk.StringVar(value="AND")
        ttk.Radiobutton(sec, text="Tumu (AND)", variable=self.mod, value="AND",
                        command=self._calistir).pack(side="left")
        ttk.Radiobutton(sec, text="Herhangi biri (OR)", variable=self.mod, value="OR",
                        command=self._calistir).pack(side="left", padx=(12, 0))
        self.bilgi = ttk.Label(sec, text="")
        self.bilgi.pack(side="right")

        govde = ttk.Frame(self, padding=(8, 4))
        govde.pack(fill="both", expand=True)
        self.scroll = ttk.Scrollbar(govde, orient="vertical")
        self.scroll.pack(side="right", fill="y")
        self.text = tk.Text(govde, wrap="word", state="disabled",
                            yscrollcommand=self.scroll.set, font=("Segoe UI", 10))
        self.text.pack(side="left", fill="both", expand=True)
        self.scroll.config(command=self.text.yview)
        self.text.tag_configure("baslik", font=("Segoe UI", 10, "bold"))
        self.text.tag_configure("tanim", foreground="#111111")
        self.text.tag_configure("ayrac", foreground="#999999")
        self.text.bind("<Double-Button-1>", self._kopyala)

        alt = ttk.Frame(self, padding=8)
        alt.pack(fill="x")
        self.durum_lbl = ttk.Label(alt, text="")
        self.durum_lbl.pack(side="left")
        ttk.Label(alt, text="Cift tik: poz_no'yu kopyalar").pack(side="right")

    def _durum(self, msg):
        self.durum_lbl.config(text=msg)

    def _canli(self, _e=None):
        if self._after_id:
            self.after_cancel(self._after_id)
        self._after_id = self.after(300, self._calistir)

    def _temizle(self):
        self.entry.delete(0, "end")
        self._calistir()

    def _calistir(self):
        q = self.entry.get()
        if not q.strip():
            self._yaz([], q)
            self._durum(f"{len(self.rows)} poz yuklu. Arama yazin.")
            return
        res = ara(self.rows, q, self.mod.get())
        # AND bos ise OR ile tekrar dene (kullanici dostu)
        if not res and self.mod.get() == "AND" and len(q.split()) > 1:
            res2 = ara(self.rows, q, "OR")
            if res2:
                self._yaz(res2, q, not_or=True)
                return
        self._yaz(res, q)

    def _yaz(self, res, q, not_or=False):
        self._sonuclar = res
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        if not q.strip():
            self.bilgi.config(text="")
            self.text.config(state="disabled")
            return
        toplam = len(res)
        goster = res[:MAX_GOSTER]
        ek = f" (ilk {MAX_GOSTER} gosteriliyor)" if toplam > MAX_GOSTER else ""
        note = " - AND sonuc yok, OR sonuclar gosteriliyor" if not_or else ""
        self.bilgi.config(text=f"{toplam} sonuc{ek}{note}")
        for r in goster:
            baslik = f"{r['poz_no']}  |  {r.get('birim','') or '-'}  |  {fiyat_goster(r)}  |  {r.get('kitap','')}\n"
            self.text.insert("end", baslik, "baslik")
            self.text.insert("end", (r.get("tanim", "") or "") + "\n", "tanim")
            self.text.insert("end", "-" * 100 + "\n", "ayrac")
        self.text.config(state="disabled")
        self.text.yview_moveto(0)
        self._durum(f"{toplam} eslesme.")

    def _kopyala(self, _e=None):
        try:
            idx = self.text.index(f"@{_e.x},{_e.y}")
            satir = self.text.get(f"{idx} linestart", f"{idx} lineend")
        except Exception:
            return
        m = re.match(r"\s*(\d{2}\.\d{3}\.\d{4})", satir)
        if m:
            self.clipboard_clear()
            self.clipboard_append(m.group(1))
            self._durum(f"Kopyalandi: {m.group(1)}")
        else:
            # tiklanan bloktaki basligi bul (yukari tara)
            try:
                cur = int(float(idx))
            except Exception:
                return
            for ln in range(cur, max(0, cur - 5), -1):
                s = self.text.get(f"{ln}.0", f"{ln}.end")
                m2 = re.match(r"\s*(\d{2}\.\d{3}\.\d{4})", s)
                if m2:
                    self.clipboard_clear()
                    self.clipboard_append(m2.group(1))
                    self._durum(f"Kopyalandi: {m2.group(1)}")
                    return


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
