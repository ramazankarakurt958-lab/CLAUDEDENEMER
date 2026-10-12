# Unreal Engine 5 - Arenanin butun katmanlarini tek seferde, dogru sirayla kurar:
#   1 Bolge kaplamalari (su zemini, mermer, orman, ates)   ArenaBolgeDoku.py
#   2 Selaleler                                             Selaleler.py
#   3 Orta platform (duz zemin + altin kakma)               MerkezPlatform.py
#   4 Element sahasi (zemin yuksekligini olcer, 3'ten sonra) ElementSahasi.py
#   5 Duvar kaplama (3D tas bloklar, kuleler haric)        DuvarKaplama.py
#   6 Susler (mesale atesi, ruzgar, sancak, bulut, ates tribunu efektleri)  ArenaSusleme.py
#   7 Kademeli kalite (oyun kasmasin)                      KaliteKademe.py
# Dosyalari GitHub'dan indirir (ayni boyutta olanlari tekrar indirmez), sonra adimlari calistirir. Bir adim hata verirse
# digerleri devam eder; sonda ozet yazar. ElementSahasi.py projende varsa uzerine yazilmaz (saha ayarlarin korunur).
# Coker ise: her adim bitince kaydedilir ve Kaynak/hepsi_ilerleme.txt'ye yazilir; ayni komutu tekrar calistirinca biten
# adimlar atlanir, kalan yerden devam eder (cokme aninda calisan adim log'un basinda yazar). Bastan kurmak icin BASTAN = True.
# Projede zaten kurulu olan adimlar (1-4) varsayilan olarak kapali; yeniden kurmak icin ADIMLAR'da True yap.
# Calistirma: GitHub'daki tek satirlik komut (R degiskenini o tanimlar).
import os
import time
import traceback
import urllib.request
import unreal

R = globals().get("R") or "https://raw.githubusercontent.com/ramazankarakurt958-lab/CLAUDEDENEMER/claude/glb-dosyasi-duzeltme-m21h38/Content/Maps/Arena/"
C = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir()) + "Maps/Arena/"

ADIMLAR = [
    ("ArenaBolgeDoku.py", globals().get("HEPSI", False), ["T_ArenaBolge.jpg", "T_ArenaBolgeMaske.png", "T_SuZemin_D.png", "T_SuZemin_N.png", "T_SuZemin_R.png",
                                 "T_SuZemin_Birikinti.png", "T_SuZemin_Dalga.png", "T_ArenaKaplamaMaske.png", "T_Mermer_D.png",
                                 "T_Mermer_N.png", "T_OrmanTas_D.png", "T_OrmanTas_N.png", "T_Yosun_D.png", "T_AtesTas_D.png",
                                 "T_AtesTas_N.png", "T_AtesCatlak.png"]),
    ("Selaleler.py", globals().get("HEPSI", False), ["SM_Selale.glb", "T_Selale_Akis.png", "T_Selale_N.png"]),
    ("MerkezPlatform.py", globals().get("HEPSI", False), ["SM_MerkezZemin.glb", "SM_MerkezRun.glb", "T_Merkez_D.jpg", "T_Merkez_N.png"]),
    ("ElementSahasi.py", globals().get("HEPSI", False), ["SM_GotikSutun.glb"]),
    ("DuvarKaplama.py", True, ["SM_Duvar.glb", "T_DuvarTas_D.png", "T_DuvarTas_N.png"]),
    ("ArenaSusleme.py", True, ["SM_EksenIsaret.glb", "SM_Mesale.glb", "SM_Alev.glb", "SM_Ruzgar.glb", "SM_Sancak.glb",
                               "SM_BulutDeniz.glb", "T_Alev.png", "T_Ruzgar.png", "T_Sancak.png", "T_Bulut.png"]),
    ("KaliteKademe.py", True, []),
]
KORUNAN = {"ElementSahasi.py"}          # projede varsa indirilmez
BASTAN = globals().get("BASTAN", False)
ILERLEME = C + "Kaynak/hepsi_ilerleme.txt"


def log(msg):
    unreal.log_warning("[Hepsi] " + msg)


def indir(yol, koru=False):
    hedef = C + yol
    os.makedirs(os.path.dirname(hedef), exist_ok=True)
    if koru and os.path.isfile(hedef):
        return "korundu"
    try:
        boy = int(urllib.request.urlopen(urllib.request.Request(R + yol, method="HEAD"), timeout=30).headers.get("Content-Length", -1))
    except Exception:
        boy = -1
    if boy > 0 and os.path.isfile(hedef) and os.path.getsize(hedef) == boy:
        return "ayni"
    veri = urllib.request.urlopen(R + yol, timeout=300).read()
    with open(hedef, "wb") as f:
        f.write(veri)
    return "%.1f MB" % (len(veri) / 1e6)


def ilerleme_oku():
    """biten adimlar ve (varsa) cokme aninda calisan adim; baska bir surumun kaydi yok sayilir"""
    if BASTAN or not os.path.isfile(ILERLEME):
        return set(), None
    satirlar = open(ILERLEME, encoding="utf-8").read().split("\n")
    if not satirlar or satirlar[0] != R:
        return set(), None
    biten = {s[6:] for s in satirlar if s.startswith("bitti ")}
    yarim = next((s[6:] for s in reversed(satirlar) if s.startswith("basla ") and s[6:] not in biten), None)
    return biten, yarim


def ilerleme_yaz(satir, yeni=False):
    with open(ILERLEME, "w" if yeni else "a", encoding="utf-8") as f:
        f.write((R + "\n" if yeni else "") + satir + "\n")


def calistir():
    sonuc = []
    t0 = time.time()
    biten, yarim = ilerleme_oku()
    if yarim:
        log("ONCEKI CALISMA '%s' sirasinda kesildi/coktu - o adimdan devam ediliyor." % yarim)
    if not biten and not yarim:
        ilerleme_yaz("", yeni=True)
    for betik, acik, kaynaklar in ADIMLAR:
        if not acik:
            sonuc.append((betik, "kapali"))
            continue
        if betik in biten:
            sonuc.append((betik, "zaten bitti (atlandi)"))
            continue
        log("=== %s ===" % betik)
        ilerleme_yaz("basla " + betik)
        try:
            for k in kaynaklar:
                durum = indir("Kaynak/" + k)
                if durum not in ("ayni", "korundu"):
                    log("   indirildi Kaynak/%s (%s)" % (k, durum))
            durum = indir(betik, koru=betik in KORUNAN)
            if durum == "korundu":
                log("   %s projedeki haliyle calisiyor (ayarlarin korunur)" % betik)
            t = time.time()
            exec(open(C + betik, encoding="utf-8").read(), {"__name__": "__main__", "__file__": C + betik})
            sonuc.append((betik, "tamam (%d sn)" % (time.time() - t)))
            ilerleme_yaz("bitti " + betik)
            unreal.SystemLibrary.collect_garbage()
        except Exception as e:
            unreal.log_error("[Hepsi] %s HATA: %s" % (betik, e))
            unreal.log_error(traceback.format_exc())
            sonuc.append((betik, "HATA: %s" % e))
    log("================ OZET (%d sn) ================" % (time.time() - t0))
    for b, s in sonuc:
        log("   %-20s %s" % (b, s))
    if all(s.startswith(("tamam", "kapali", "zaten")) for _, s in sonuc):
        log("TAMAM - secili adimlar bitti. Simdi Play ile dene.")
    else:
        log("Bazi adimlar hata verdi - yukaridaki HATA satirlarini gonder.")


calistir()
