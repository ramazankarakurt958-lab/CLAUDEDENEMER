# Unreal Engine 5 - Indirilen hazir merdiven modellerini bulur ve olculerini yazar (hicbir seyi degistirmez).
# Projede (/Game) adinda stair/step/merdiven gecen mesh'ler + Indirilenler klasorundeki merdiven dosyalari.
# Calistirma (Output Log -> Python):
#   exec(open(unreal.Paths.project_content_dir() + "Maps/Arena/MerdivenBul.py", encoding="utf-8").read())
import glob
import os
import unreal

ANAHTARLAR = ("stair", "step", "merdiven", "basamak", "staircase")
ATLA = ("/maps/arena/",)          # bizim urettiklerimiz

eal = unreal.EditorAssetLibrary


def log(msg):
    unreal.log_warning("[Merdiven] " + msg)


def proje():
    bulunan = 0
    for yol in eal.list_assets("/Game", recursive=True, include_folder=False):
        k = yol.lower()
        if not any(a in k for a in ANAHTARLAR) or any(a in k for a in ATLA):
            continue
        veri = eal.find_asset_data(yol)
        try:
            sinif = str(veri.asset_class_path.asset_name)
        except Exception:
            sinif = str(veri.get_editor_property("asset_class"))
        if sinif not in ("StaticMesh", "Blueprint"):
            continue
        a = eal.load_asset(yol)
        if isinstance(a, unreal.StaticMesh):
            kutu = a.get_bounding_box()
            b = kutu.max - kutu.min
            try:
                nanite = a.get_editor_property("nanite_settings").get_editor_property("enabled")
            except Exception:
                nanite = "?"
            log("MESH %s  boyut(cm) X=%.0f Y=%.0f Z=%.0f  malzeme=%d  nanite=%s" % (
                yol.split(".")[0], b.x, b.y, b.z, len(a.get_editor_property("static_materials")), nanite))
        else:
            log("BLUEPRINT %s" % yol.split(".")[0])
        bulunan += 1
    log("Projede %d merdiven varligi bulundu." % bulunan)


def indirilenler():
    ev = os.path.expanduser("~")
    for kok in (os.path.join(ev, "Downloads"), os.path.join(ev, "OneDrive", "Downloads")):
        if not os.path.isdir(kok):
            continue
        for f in glob.glob(os.path.join(kok, "**", "*"), recursive=True):
            ad = os.path.basename(f).lower()
            if any(a in ad for a in ANAHTARLAR) and ad.endswith((".zip", ".fbx", ".glb", ".gltf", ".obj", ".blend", ".uasset")):
                log("DOSYA %s  (%.1f MB)" % (f, os.path.getsize(f) / 1e6))


proje()
indirilenler()
log("TAMAM - yukaridaki [Merdiven] satirlarini kopyalayip gonder.")
