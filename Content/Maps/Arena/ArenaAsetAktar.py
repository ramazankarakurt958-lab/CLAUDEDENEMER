# Unreal Engine 5 - Chrome'dan indirilen asetleri (Poly Haven / ambientCG) otomatik aktarir.
# Indirilenler klasorundeki zip'leri acar, gereken dosyalari bulur, /Game/MAPS/Asetler altina aktarir.
# Calistirma (Output Log -> Python):
#   exec(open(unreal.Paths.project_content_dir() + "Maps/Arena/ArenaAsetAktar.py", encoding="utf-8").read())
import os
import re
import zipfile

try:
    import unreal
except ImportError:  # Unreal disinda test icin
    unreal = None

HEDEF = "/Game/MAPS/Asetler"

# anahtar -> tur ("model" ya da "doku")
ASETLER = {
    "island_tree_01": "model",
    "island_tree_02": "model",
    "island_tree_03": "model",
    "rock_moss_set_01": "model",
    "boulder_01": "model",
    "rock_09": "model",
    "marble_01": "doku",
    "mossy_stone_wall": "doku",
    "mossy_rock": "doku",
    "forest_ground_04": "doku",
    "rock_pitted_mossy": "doku",
    "rock_wall_08": "doku",
    "ice001": "doku",
    "ice003": "doku",
    "lava004": "doku",
    "lava005": "doku",
}

MODEL_UZANTI = (".fbx", ".glb", ".gltf", ".obj")
RESIM_UZANTI = (".jpg", ".jpeg", ".png", ".tga", ".exr")
ROLLER = {
    "renk": ("_diff", "_color", "basecolor", "albedo", "_col"),
    "normal": ("nor_gl", "normalgl"),
    "puruz": ("_rough", "roughness"),
}
CIKAR = ("nor_dx", "normaldx", "_disp", "displacement", "_arm", "_ao", "ambientocclusion", "_spec", "_bump", "preview")


def log(msg):
    if unreal:
        unreal.log_warning("[Arena] " + msg)
    else:
        print("[Arena] " + msg)


def indirme_klasorleri():
    ev = os.path.expanduser("~")
    adaylar = [os.path.join(ev, "Downloads"), os.path.join(ev, "OneDrive", "Downloads"),
               os.path.join(ev, "İndirilenler")]
    return [k for k in adaylar if os.path.isdir(k)]


def anahtar_bul(ad):
    ad = ad.lower()
    # en uzun anahtar once (rock_moss_set_01, mossy_rock'tan once eslesmesin diye)
    for k in sorted(ASETLER, key=len, reverse=True):
        if k in ad:
            return k
    return None


def cozunurluk_puani(yol):
    m = re.search(r"(\d+)k", os.path.basename(yol).lower())
    k = int(m.group(1)) if m else 0
    return {4: 0, 2: 1, 8: 2, 1: 3}.get(k, 4)  # 4K tercih, sonra 2K, 8K, 1K


def kaynaklari_topla(kok):
    """anahtar -> [klasor/dosya yollari]; zip'ler gerekirse acilir."""
    acilan = os.path.join(kok, "_arena_ayiklanan")
    sonuc = {}
    for ad in os.listdir(kok):
        yol = os.path.join(kok, ad)
        k = anahtar_bul(ad)
        if not k:
            continue
        if ad.lower().endswith(".zip"):
            hedef = os.path.join(acilan, os.path.splitext(ad)[0])
            if not os.path.isdir(hedef):
                try:
                    with zipfile.ZipFile(yol) as z:
                        z.extractall(hedef)
                    log("   zip acildi: " + ad)
                except Exception as e:
                    log("   zip acilamadi (%s): %s" % (ad, e))
                    continue
            yol = hedef
        sonuc.setdefault(k, []).append(yol)
    return sonuc


def dosyalar(yollar):
    for y in yollar:
        if os.path.isfile(y):
            yield y
        else:
            for a, _, fs in os.walk(y):
                for f in fs:
                    yield os.path.join(a, f)


def secim_yap(k, yollar):
    tum = list(dosyalar(yollar))
    if ASETLER[k] == "model":
        modeller = [f for f in tum if f.lower().endswith(MODEL_UZANTI)]
        modeller.sort(key=lambda f: (MODEL_UZANTI.index(os.path.splitext(f)[1].lower()), cozunurluk_puani(f)))
        return modeller[:1]
    secilen = []
    for rol, ipuclari in ROLLER.items():
        aday = [f for f in tum if f.lower().endswith(RESIM_UZANTI)
                and any(i in os.path.basename(f).lower() for i in ipuclari)
                and not any(c in os.path.basename(f).lower() for c in CIKAR)]
        aday.sort(key=cozunurluk_puani)
        if aday:
            secilen.append(aday[0])
    return secilen


def aktar(dosya_listesi, hedef):
    gorevler = []
    for f in dosya_listesi:
        t = unreal.AssetImportTask()
        t.set_editor_property("filename", f)
        t.set_editor_property("destination_path", hedef)
        t.set_editor_property("automated", True)
        t.set_editor_property("replace_existing", True)
        t.set_editor_property("save", True)
        gorevler.append(t)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(gorevler)


def calistir():
    klasorler = indirme_klasorleri()
    if not klasorler:
        log("HATA: Indirilenler klasoru bulunamadi.")
        return
    bulunan = {}
    for kok in klasorler:
        log("Taraniyor: " + kok)
        for k, y in kaynaklari_topla(kok).items():
            bulunan.setdefault(k, []).extend(y)

    aktarilan, eksik = [], []
    for i, k in enumerate(sorted(bulunan), 1):
        secim = secim_yap(k, bulunan[k])
        if not secim:
            eksik.append(k)
            continue
        log("%d/%d %s -> %s" % (i, len(bulunan), k, ", ".join(os.path.basename(s) for s in secim)))
        if unreal:
            aktar(secim, HEDEF + "/" + k)
        aktarilan.append(k)

    yok = [k for k in ASETLER if k not in bulunan]
    log("TAMAM - aktarilan: %d (%s)" % (len(aktarilan), ", ".join(aktarilan) or "-"))
    if eksik:
        log("Dosyasi bulunamayan (zip bozuk ya da yanlis format): " + ", ".join(eksik))
    log("Indirilenler'de olmayan (indirmediysen sorun degil): " + ", ".join(yok))


calistir()
