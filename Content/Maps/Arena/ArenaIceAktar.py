# Unreal Engine 5 - Arena haritasini otomatik olusturur.
# Calistirma: Output Log -> Cmd yerine Python sec ->
#   exec(open(unreal.Paths.project_content_dir() + "Maps/Arena/ArenaIceAktar.py", encoding="utf-8").read())
# Her adim Output Log'a "[Arena]" ile baslayan satir yazar.
import os
import unreal

KAYNAK = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir()),
                      "Maps", "Arena", "Kaynak", "arena_game.glb")
VARLIK_KLASORU = "/Game/Maps/Arena/Varliklar"
HARITA = "/Game/Maps/Arena_Map"
PLATFORM_UST_CM = 2300.0  # orta platformun ust yuzeyi (~23 m)


def log(msg):
    unreal.log_warning("[Arena] " + msg)


def hata(msg):
    unreal.log_error("[Arena] HATA: " + msg)
    raise RuntimeError(msg)


eal = unreal.EditorAssetLibrary

# 1) Dosya kontrolu
log("1/4 Dosya kontrol ediliyor: " + KAYNAK)
if not os.path.isfile(KAYNAK):
    hata("arena_game.glb bulunamadi. Su konumda olmali: " + KAYNAK)

# 2) GLB'yi ice aktar (mesh + malzeme + dokular)
log("2/4 GLB ice aktariliyor (birkac dakika surebilir)...")
task = unreal.AssetImportTask()
task.set_editor_property("filename", KAYNAK)
task.set_editor_property("destination_path", VARLIK_KLASORU)
task.set_editor_property("automated", True)
task.set_editor_property("replace_existing", True)
task.set_editor_property("save", True)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

meshes = []
for yol in eal.list_assets(VARLIK_KLASORU, recursive=True, include_folder=False):
    a = eal.load_asset(yol)
    if isinstance(a, unreal.StaticMesh):
        meshes.append(a)
if not meshes:
    hata("Ice aktarma mesh uretmedi. Edit -> Plugins icinde 'glTF Importer' veya "
         "'Interchange Framework' eklentisini etkinlestirip editoru yeniden baslat.")
log("   %d mesh aktarildi." % len(meshes))

# Carpisma (oyuncu gercek geometri uzerinde yurusun) + Nanite
for m in meshes:
    try:
        body = m.get_editor_property("body_setup")
        if body:
            body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    except Exception as e:
        log("   Carpisma ayarlanamadi (onemsiz): %s" % e)
    try:
        ns = m.get_editor_property("nanite_settings")
        ns.set_editor_property("enabled", True)
        m.set_editor_property("nanite_settings", ns)
    except Exception as e:
        log("   Nanite acilamadi (onemsiz): %s" % e)
    eal.save_loaded_asset(m)

# 3) Harita
log("3/4 Harita olusturuluyor: " + HARITA)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if eal.does_asset_exist(HARITA):
    if not les.load_level(HARITA):
        hata("Mevcut harita acilamadi: " + HARITA)
    for act in eas.get_all_level_actors():
        eas.destroy_actor(act)
elif not les.new_level(HARITA):
    hata("Yeni harita olusturulamadi: " + HARITA)


def koy(sinif, konum, donus=None, etiket=None):
    try:
        a = eas.spawn_actor_from_class(sinif, konum, donus or unreal.Rotator(0, 0, 0))
        if a and etiket:
            a.set_actor_label(etiket)
        return a
    except Exception as e:
        log("   %s eklenemedi (onemsiz): %s" % (etiket, e))
        return None


for m in meshes:
    a = eas.spawn_actor_from_object(m, unreal.Vector(0, 0, 0))
    if not a:
        hata("Arena sahneye eklenemedi.")
    a.set_actor_label("Arena")
    try:
        a.static_mesh_component.set_mobility(unreal.ComponentMobility.STATIC)
    except Exception:
        pass

gunes = koy(unreal.DirectionalLight, unreal.Vector(0, 0, 8000), unreal.Rotator(-15, -40, 0), "Gunes")
if gunes:
    try:
        gunes.light_component.set_editor_property("intensity", 8.0)
        gunes.light_component.set_editor_property("atmosphere_sun_light", True)
    except Exception as e:
        log("   Gunes ayari yapilamadi (onemsiz): %s" % e)
koy(unreal.SkyAtmosphere, unreal.Vector(0, 0, 0), etiket="Atmosfer")
gok = koy(unreal.SkyLight, unreal.Vector(0, 0, 6000), etiket="GokIsigi")
if gok:
    try:
        gok.light_component.set_editor_property("real_time_capture", True)
    except Exception as e:
        log("   Gok isigi ayari yapilamadi (onemsiz): %s" % e)
koy(unreal.ExponentialHeightFog, unreal.Vector(0, 0, -2000), etiket="Sis")
koy(unreal.VolumetricCloud, unreal.Vector(0, 0, 0), etiket="Bulutlar")
koy(unreal.PlayerStart, unreal.Vector(0, 0, PLATFORM_UST_CM + 120), etiket="OyuncuBaslangic")

# 4) Kaydet
log("4/4 Kaydediliyor...")
les.save_current_level()
log("TAMAM - Arena_Map hazir: " + HARITA)
