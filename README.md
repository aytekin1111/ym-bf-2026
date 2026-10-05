# Poz Arama — Masaüstü Programı (C++)

Tek dosyalık dağıtım: **`poz_arama.exe`** (3,6 MB). Veritabanı **exe'nin içindedir**,
harici dosya gerekmez — exe'yi herhangi bir klasöre kopyalayıp çalıştırın.

- 6.069 poz: ÇŞB 2026 (inşaat/mekanik/elektrik/rayiç) + **PTT 07/2026 özel (77.xxx, 268 poz)** + **MSB 2026 (48.xxx, 79 poz)**
- Kaynak izlenebilirliği için her sonuçta `kitap` sütunu gösterilir
  (`Insaat_Analiz_TUM_2026`, `Ana_BF_2026`, `PTT_Ozel_07-2026`, `MSB_2026`).

## Yeniden Derleme

Veri veya kod değişirse `build_exe.bat` dosyasına çift tıklayın:
1. `veri_uret.py` → `poz_index.tsv` + `poz_veri.h` üretir
2. `g++ -static` ile `poz_arama.exe` derlenir (derleyici: `H:\mingw64`)

## Kaynak Dosyalar (projeBf)

`projeBf/` klasöründeki 4 PDF'ten otomatik çıkarılmış poz kataloğudur.

## Kaynak Dosyalar

| Dosya | İçerik | Sayfa |
|-------|--------|-------|
| `projeBf/1-BF-...unlocked.pdf` | Ana Birim Fiyat Listesi (741 sayfa) | İşçilik + inşaat/mekanik/elektrik pozları + birim fiyatlar |
| `projeBf/2026-İNŞAAT-ANALİZ-TUM.pdf` | İnşaat Genel Fiyat Analizleri (1410 sayfa) | İnşaat pozları detaylı analiz (15.xxxx) |
| `projeBf/in-aat-analiz-1-...unlocked.pdf` | İnşaat Analiz Cilt 1 | İnşaat pozları (15.xxxx) |
| `projeBf/in-aat-analiz-2-...unlocked.pdf` | İnşaat Analiz Cilt 2 | İnşaat pozları (15.xxxx) |
| `projeBf/PTT (1).pdf` | PTT Yapı Daire Bşk. Proje Poz Analizleri (286 sayfa) | **77.xxxx özel pozlar** (tanım + analiz toplamı) |
| `projeBf/PTT (2).pdf` | PTT 07/2026 Özel Birim Fiyat Listesi | 77.xxxx fiyat listesi (çapraz kontrol) |
| `projeBf/PTT (3).pdf` | PTT 07/2026 rayiçleri + TÜİK eşleştirme | 10.xxxx rayiç (2026 güncel; ana DB'ye **karıştırılmadı**) |

## PTT Pozları (77.xxx) — Notlar

- 268 PTT özel pozu veritabanında (`kitap = PTT_Ozel_07-2026`).
- Fiyat = analiz paftasındaki "Toplam Tutar" (208 poz). **60 pozun paftası taslak** (toplam hesaplanmamış) → fiyatı boş gelir, uydurma yazılmaz.
- PTT (2) fiyat listesi tablo kayması içerdiğinden **fiyat kaynağı olarak kullanılmadı**; yalnızca PTT (1) analiz toplamları alındı.
- PTT (3) rayiçleri (örn. usta 348,20 TL vs ÇŞB 310 TL) mevcut ÇŞB fiyatlarıyla çakıştığından DB'ye eklenmedi.

## Çıktılar

- `poz_katalog.csv` — Birleşik katalog (5522 poz)
- `poz_arama.py` — CLI arama aracı
- `rawtxt/` — Ham metin çıktıları (PDF → text)

## Kullanım

```bash
# Tam poz numarası ile arama
python poz_arama.py 15.225.1010

# Kategori altındaki tüm pozlar
python poz_arama.py 15.225         # gazbeton duvar
python poz_arama.py 15.106         # yıkım-söküm
python poz_arama.py 15.550         # kapı/pencere doğrama

# Anahtar kelime ile arama (Türkçe karakter duyarsız değil!)
python poz_arama.py "asma tavan"
python poz_arama.py "demir kapı"
python poz_arama.py "boya"
```

## Kategoriler

- **10.xxxx** (3.186) — İşçilik + malzeme rayiçleri (saat/Adet/TL)
- **15.xxxx** (777) — İnşaat birim fiyat/analiz pozları
- **19.xxxx** (93) — Araç/iş makinesi rayiçleri
- **25.xxxx** (547) — Mekanik tesisat pozları (ısıtma, sıhhi tesisat, vb.)
- **35.xxxx** (919) — Asansör, zayıf akım, otomatik kontrol, vb.

## Mevcut Projede Kullanılan Pozlar (21 adet 15.xxx)

| Poz No | Birim | Tanım |
|--------|-------|-------|
| 15.105.1103 | Ad | El ile ağaç kesilmesi ve sökme |
| 15.106.1003 | m³ | Patlayıcı kullanmadan kargir yıkım |
| 15.106.1117 | m² | Seramik, fayans söküm |
| 15.106.1119 | m² | PVC döşeme söküm |
| 15.106.1129 | m² | Asma tavan söküm |
| 15.106.1130 | m² | Alüminyum/PVC kapı-pencere söküm |
| 15.106.1131 | m² | Ahşap kapı/pencere söküm |
| 15.106.1132 | Kg | Her türlü demir imalat söküm |
| 15.165.1001 | Ton | Profil demir hazırlama/tespit |
| 15.225.1007 | m² | 15 cm gazbeton duvar |
| 15.225.1010 | m² | 20 cm gazbeton duvar |
| 15.225.1016 | m² | 35 cm gazbeton duvar |
| 15.280.1011 | — | — |
| 15.380.1055 | — | — |
| 15.390.1028 | — | — |
| 15.410.1503 | — | (kurum içi özel poz) |
| 15.460.1010 | — | — |
| 15.530.1928 | m² | Alçı levha asma tavan |
| 15.540.1501 | — | — |
| 15.540.1517 | — | — |
| 15.550.1001 | Kg | Kare/dikdörtgen profil kapı-pencere |

## Y. Eski Poz Sistemi (CSV'lerde kullanılan)

Proje CSV'lerinde `Y.27.581`, `Y.25.003/24` gibi eski poz kodları geçiyor. Bunlar ÇŞB'nin eski (2005-2014) poz sisteminden kalma. Yeni sistemde karşılıkları:

| Eski Poz | Karşılığı (yeni) | Nerede |
|----------|------------------|--------|
| Y.25.003 (boya) | 25.x veya 27.x (katalogda yok) | — |
| Y.26.005 (seramik) | 26.x (katalogda yok) | — |
| Y.26.007 (granit) | 26.x (katalogda yok) | — |
| Y.26.015 (mermer) | **26.015** var! | mekanik analiz TUM |
| Y.27.581 (tesviye) | 27.x (katalogda yok) | — |
| Y.27.583 (şap) | 27.x (katalogda yok) | — |

**NOT:** Y. eski poz numaraları proje CSV'lerinde hâlâ kullanılıyor. Yeni sistemdeki karşılıkları ÇŞB'nin resmi eşleme tablosundan alınmalı; bu katalogda Y. pozlara doğrudan eşleşme **yok**.

## Yeniden Oluşturma

```bash
mkdir -p bfKatalog/rawtxt
cd bfKatalog/rawtxt

# PDF → metin
pdftotext -layout -enc UTF-8 \
  "../bfKitaplari/projeBf/1-BF-...unlocked.pdf" \
  "01_Ana_BF.txt"

# (diğer 3 PDF için tekrarla)

# Kataloğu oluştur
python poz_katalog_olustur.py
```
