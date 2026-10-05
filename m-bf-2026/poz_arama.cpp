// Poz Arama - C++ konsol uygulamasi (tek dosya, bagimlilik yok).
// Derleme (WinLibs g++):  g++ -O2 -std=c++17 -static -o poz_arama.exe poz_arama.cpp
// Calistirma: poz_arama.exe (poz_index.tsv ayni klasorde olmali)
// Kullanim: arama yaz + Enter. Komutlar: /or /and /q
// Arama: poz no (15.445) veya 1+ kelime; Turkce duyarsiz; tam tanim gosterilir.
#include <algorithm>
#include <cctype>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "poz_veri.h" // gomulu veritabani (veri_uret.py ile uretilir)

#ifdef _WIN32
#include <windows.h>
#endif

struct Kayit {
    std::string poz, tanim, birim, fiyat, kitap;
    std::string n_poz, n_tanim; // normalize edilmis
};

// --- UTF-8 cozucu: bir sonraki kod noktasini okur, pos'u ilerletir ---
static uint32_t utf8_next(const std::string& s, size_t& i) {
    unsigned char c = static_cast<unsigned char>(s[i]);
    if (c < 0x80) { i += 1; return c; }
    uint32_t cp = 0; int n = 0;
    if ((c & 0xE0) == 0xC0) { cp = c & 0x1F; n = 1; }
    else if ((c & 0xF0) == 0xE0) { cp = c & 0x0F; n = 2; }
    else if ((c & 0xF8) == 0xF0) { cp = c & 0x07; n = 3; }
    else { i += 1; return 0xFFFD; }
    i += 1;
    for (int k = 0; k < n && i < s.size(); ++k, ++i)
        cp = (cp << 6) | (static_cast<unsigned char>(s[i]) & 0x3F);
    return cp;
}

static void utf8_ekle(std::string& out, uint32_t cp) {
    if (cp < 0x80) out += (char)cp;
    else if (cp < 0x800) {
        out += (char)(0xC0 | (cp >> 6));
        out += (char)(0x80 | (cp & 0x3F));
    } else if (cp < 0x10000) {
        out += (char)(0xE0 | (cp >> 12));
        out += (char)(0x80 | ((cp >> 6) & 0x3F));
        out += (char)(0x80 | (cp & 0x3F));
    } else {
        out += (char)(0xF0 | (cp >> 18));
        out += (char)(0x80 | ((cp >> 12) & 0x3F));
        out += (char)(0x80 | ((cp >> 6) & 0x3F));
        out += (char)(0x80 | (cp & 0x3F));
    }
}

// Turkce duyarsiz kucultme + ASCII katlama (UTF-8 -> UTF-8)
static std::string norm(const std::string& s) {
    std::string out;
    out.reserve(s.size());
    size_t i = 0;
    while (i < s.size()) {
        uint32_t cp = utf8_next(s, i);
        if (cp >= 'A' && cp <= 'Z') cp += 32;
        else if (cp == 0x130) cp = 'i';          // İ -> i
        else if (cp == 'I') cp = 0x131;          // I -> ı
        else if (cp == 0x15E) cp = 0x15F;        // Ş -> ş
        else if (cp == 0x11E) cp = 0x11F;        // Ğ -> ğ
        else if (cp == 0xDC) cp = 0xFC;          // Ü -> ü
        else if (cp == 0xD6) cp = 0xF6;          // Ö -> ö
        else if (cp == 0xC7) cp = 0xE7;          // Ç -> ç
        // ASCII katlama
        else if (cp == 0x15F) cp = 's';          // ş -> s
        else if (cp == 0x11F) cp = 'g';          // ğ -> g
        else if (cp == 0xFC) cp = 'u';           // ü -> u
        else if (cp == 0xF6) cp = 'o';           // ö -> o
        else if (cp == 0xE7) cp = 'c';           // ç -> c
        else if (cp == 0x131) cp = 'i';          // ı -> i
        utf8_ekle(out, cp);
    }
    return out;
}

static std::string trim(const std::string& s) {
    size_t a = s.find_first_not_of(" \t\r\n");
    if (a == std::string::npos) return "";
    size_t b = s.find_last_not_of(" \t\r\n");
    return s.substr(a, b - a + 1);
}

static std::vector<std::string> bol(const std::string& s, char ayrac) {
    std::vector<std::string> v;
    std::string cur;
    for (char c : s) {
        if (c == ayrac) { v.push_back(cur); cur.clear(); }
        else cur += c;
    }
    v.push_back(cur);
    return v;
}

static bool poz_sorgusu_mu(const std::string& q) {
    if (q.empty()) return false;
    for (unsigned char c : q)
        if (!(c == '.' || c == ' ' || (c >= '0' && c <= '9'))) return false;
    return true;
}

// "1638.89" -> "1.638,89 TL" ; bos ise "-"
static std::string fiyat_goster(const std::string& f) {
    if (f.empty()) return "-";
    double d;
    try { d = std::stod(f); } catch (...) { return f; }
    long long tam = (long long)d;
    int kr = (int)((d - tam) * 100 + 0.5);
    std::string t = std::to_string(tam), g;
    int n = 0;
    for (int i = (int)t.size() - 1; i >= 0; --i) {
        g += t[i];
        if (++n % 3 == 0 && i > 0) g += '.';
    }
    std::reverse(g.begin(), g.end());
    char buf[16];
    std::snprintf(buf, sizeof buf, "%02d", kr);
    return g + "," + buf + " TL";
}

int main() {
#ifdef _WIN32
    SetConsoleCP(65001);
    SetConsoleOutputCP(65001);
#endif
    // gomulu veritabani (exe'nin icinde, harici dosya gerekmez)
    std::string ham(reinterpret_cast<const char*>(POZ_VERI), POZ_VERI_LEN);
    std::vector<Kayit> rows;
    {
        size_t bas = 0;
        bool ilk = true;
        while (bas <= ham.size()) {
            size_t son = ham.find('\n', bas);
            if (son == std::string::npos) son = ham.size();
            std::string satir = ham.substr(bas, son - bas);
            if (!satir.empty() && satir.back() == '\r') satir.pop_back();
            bas = son + 1;
            if (satir.empty()) continue;
            if (ilk) { ilk = false; continue; } // baslik
            auto k = bol(satir, '\t');
            if (k.size() < 5) continue;
            Kayit r{trim(k[0]), trim(k[1]), trim(k[2]), trim(k[3]), trim(k[4]), "", ""};
            if (r.poz.empty()) continue;
            r.n_poz = norm(r.poz);
            r.n_tanim = norm(r.tanim);
            rows.push_back(std::move(r));
        }
    }
    if (rows.empty()) {
        std::cout << "HATA: gomulu veritabani bos.\n";
        std::cout << "Cikmak icin Enter..."; std::string b; std::getline(std::cin, b);
        return 1;
    }
    std::cout << rows.size() << " poz yuklendi (projeBf).\n"
              << "Komutlar: /or (herhangi biri), /and (tumu), /q (cikis)\n\n";

    bool mod_or = false;
    const size_t LIM = 200;
    for (;;) {
        std::cout << "Arama" << (mod_or ? " [OR]" : " [AND]") << ": ";
        std::cout.flush();
        std::string q;
        if (!std::getline(std::cin, q)) break;
        q = trim(q);
        if (q == "/q" || q == "/Q") break;
        if (q == "/or" || q == "/OR") { mod_or = true; std::cout << "Mod: OR\n"; continue; }
        if (q == "/and" || q == "/AND") { mod_or = false; std::cout << "Mod: AND\n"; continue; }
        if (q.empty()) continue;

        std::vector<const Kayit*> res;
        if (poz_sorgusu_mu(q)) {
            for (auto& r : rows)
                if (r.poz.compare(0, q.size(), q) == 0) res.push_back(&r);
        } else {
            std::istringstream ss(norm(q));
            std::vector<std::string> kel;
            std::string w;
            while (ss >> w) kel.push_back(w);
            for (auto& r : rows) {
                std::string blob = r.n_tanim + " " + r.n_poz;
                bool ok = mod_or ? false : true;
                for (auto& kl : kel) {
                    bool var = blob.find(kl) != std::string::npos;
                    if (mod_or) { if (var) { ok = true; break; } }
                    else if (!var) { ok = false; break; }
                }
                if (ok) res.push_back(&r);
            }
            // AND bos ise OR ile tekrar dene
            if (res.empty() && !mod_or && kel.size() > 1) {
                for (auto& r : rows) {
                    std::string blob = r.n_tanim + " " + r.n_poz;
                    for (auto& kl : kel)
                        if (blob.find(kl) != std::string::npos) { res.push_back(&r); break; }
                }
                if (!res.empty()) std::cout << "(AND sonuc yok, OR sonuclar:)\n";
            }
        }
        std::cout << "\n" << res.size() << " sonuc";
        if (res.size() > LIM) std::cout << " (ilk " << LIM << " gosteriliyor)";
        std::cout << ":\n" << std::string(100, '=') << "\n";
        size_t g = res.size() < LIM ? res.size() : LIM;
        for (size_t i = 0; i < g; ++i) {
            auto* r = res[i];
            std::cout << "[" << (i + 1) << "] " << r->poz << "  |  "
                      << (r->birim.empty() ? "-" : r->birim) << "  |  "
                      << fiyat_goster(r->fiyat) << "  |  " << r->kitap << "\n"
                      << r->tanim << "\n"
                      << std::string(100, '-') << "\n";
        }
        std::cout << "\n";
    }
    return 0;
}
