# Unreal Engine 5 - Arenanin katmanlarini sirayla kurar. HER CALISTIRMADA TEK ADIM: ayni komutu tekrar calistirinca
# siradaki adima gecer (adimlar arasinda Unreal ice aktarma/derlemeyi bitirsin). Her adim, tek tek kullandigin komutlarla
# birebir ayni sekilde calisir: dosyalari duz indirir, betigi Output Log'un kendi Python ortaminda calistirir.
#   1-4 ArenaBolgeDoku, Selaleler, MerkezPlatform, ElementSahasi  (projende zaten kurulu: sadece HEPSI=True ile)
#   5   DuvarKaplama  (3D tas duvarlar, kule govdeleri, orman sarmasiklari, ates tribunu lav akintilari)
#   6   OrmanAgac     (orman tribunu agaclari, kalin kokler)
#   7   ArenaSusleme  (mesale atesi, ruzgar, sancaklar, bulut denizi, ates tribunu efektleri)
#   8   KaliteKademe  (oyun kasmasin)
#   9   Gorunum       (malzeme ince ayarlari: ates derz koru kapali, selale kopugu seffaf)
# Ilerleme Kaynak/hepsi_ilerleme.txt'de. Bir adim yarida kalirsa (cokme) tekrar calistirinca ayni adimi yeniden dener.
# Bastan kurmak icin komutun basina BASTAN=True; ekle.
import os
import unreal
import urllib.request

_HR = globals().get("R") or "https://raw.githubusercontent.com/ramazankarakurt958-lab/CLAUDEDENEMER/claude/glb-dosyasi-duzeltme-m21h38/Content/Maps/Arena/"
_HC = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir()) + "Maps/Arena/"
_HHEPSI = globals().get("HEPSI", False)
_HADIMLAR = [
    ("ArenaBolgeDoku.py", _HHEPSI, ["T_ArenaBolge.jpg", "T_ArenaBolgeMaske.png", "T_SuZemin_D.png", "T_SuZemin_N.png", "T_SuZemin_R.png",
                                    "T_SuZemin_Birikinti.png", "T_SuZemin_Dalga.png", "T_ArenaKaplamaMaske.png", "T_Mermer_D.png",
                                    "T_Mermer_N.png", "T_OrmanTas_D.png", "T_OrmanTas_N.png", "T_Yosun_D.png", "T_AtesTas_D.png",
                                    "T_AtesTas_N.png", "T_AtesCatlak.png"]),
    ("Selaleler.py", _HHEPSI, ["SM_Selale.glb", "T_Selale_Akis.png", "T_Selale_N.png"]),
    ("MerkezPlatform.py", _HHEPSI, ["SM_MerkezZemin.glb", "SM_MerkezRun.glb", "T_Merkez_D.jpg", "T_Merkez_N.png"]),
    ("ElementSahasi.py", _HHEPSI, ["SM_GotikSutun.glb"]),
    ("DuvarKaplama.py", True, ["SM_Duvar.glb", "T_DuvarTas_D.png", "T_DuvarTas_N.png", "T_Yaprak.png", "SM_Lav.glb", "T_LavAkis.png"]),
    ("OrmanAgac.py", True, ["SM_Agac.glb", "T_Kabuk_D.png", "T_Kabuk_N.png", "T_Yaprak.png"]),
    ("ArenaSusleme.py", True, ["SM_EksenIsaret.glb", "SM_Mesale.glb", "SM_Alev.glb", "SM_Ruzgar.glb", "SM_Sancak.glb",
                               "SM_BulutDeniz.glb", "T_Alev.png", "T_Ruzgar.png", "T_Sancak.png", "T_Bulut.png"]),
    ("KaliteKademe.py", True, []),
    ("Gorunum.py", True, []),
]
_HIL = _HC + "Kaynak/hepsi_ilerleme.txt"

_Hsatir = []
if not globals().get("BASTAN", False) and os.path.isfile(_HIL):
    _Hsatir = open(_HIL, encoding="utf-8").read().split("\n")
    if not _Hsatir or _Hsatir[0] != _HR:
        _Hsatir = []
if not _Hsatir:
    open(_HIL, "w", encoding="utf-8").write(_HR + "\n")
_Hbiten = {s[6:] for s in _Hsatir if s.startswith("bitti ")}
_Hyarim = [s[6:] for s in _Hsatir if s.startswith("basla ") and s[6:] not in _Hbiten]
_Hsira = [a for a in _HADIMLAR if a[1] and a[0] not in _Hbiten]

if _Hyarim:
    unreal.log_warning("[Hepsi] ONCEKI CALISMA '%s' sirasinda yarida kaldi - bu adim yeniden deneniyor." % _Hyarim[-1])
if not _Hsira:
    unreal.log_warning("[Hepsi] TAMAM - butun adimlar zaten bitti. Bastan kurmak icin komutun basina BASTAN=True; ekle.")
else:
    _Hbetik, _, _Hdosyalar = _Hsira[0]
    unreal.log_warning("[Hepsi] === %s (%d/%d) === indiriliyor..." % (_Hbetik, len(_Hbiten) + 1, len(_Hbiten) + len(_Hsira)))
    open(_HIL, "a", encoding="utf-8").write("basla " + _Hbetik + "\n")
    for _Hf in _Hdosyalar:
        open(_HC + "Kaynak/" + _Hf, "wb").write(urllib.request.urlopen(_HR + "Kaynak/" + _Hf).read())
    if not (_Hbetik == "ElementSahasi.py" and os.path.isfile(_HC + _Hbetik)):   # saha ayarlarin korunur
        open(_HC + _Hbetik, "wb").write(urllib.request.urlopen(_HR + _Hbetik).read())
    exec(open(_HC + _Hbetik, encoding="utf-8").read())
    open(_HIL, "a", encoding="utf-8").write("bitti " + _Hbetik + "\n")
    if len(_Hsira) > 1:
        unreal.log_warning("[Hepsi] %s bitti. DEVAM - ayni komutu bir kez daha calistir (siradaki: %s)." % (_Hbetik, _Hsira[1][0]))
    else:
        unreal.log_warning("[Hepsi] TAMAM - butun adimlar bitti. Simdi Play ile dene.")
