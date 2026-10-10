# Unreal Engine 5 - Arena haritasini otomatik olusturur.
# Calistirma: Editor'de  Tools -> Execute Python Script...  ve bu dosyayi sec.
# (Gerekirse once Edit -> Plugins -> "Python Editor Script Plugin" etkinlestirilip editor yeniden baslatilir.)
import os
import unreal

KAYNAK = os.path.join(unreal.Paths.project_content_dir(), "Maps", "Arena", "Kaynak", "arena_game.glb")
VARLIK_KLASORU = "/Game/Maps/Arena/Varliklar"
HARITA = "/Game/Maps/Arena_Map"
PLATFORM_UST_CM = 2300.0  # orta platformun ust yuzeyi (~23 m)

eal = unreal.EditorAssetLibrary
if not os.path.isfile(KAYNAK):
    raise RuntimeError("GLB bulunamadi: " + KAYNAK)

# 1) GLB'yi ice aktar (mesh + malzeme + dokular)
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
    raise RuntimeError("Ice aktarma sonrasi StaticMesh bulunamadi: " + VARLIK_KLASORU)

# 2) Carpisma: oyuncu gercek geometri uzerinde yuruyebilsin; Nanite ile performans
for m in meshes:
    body = m.get_editor_property("body_setup")
    if body:
        body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    try:
        ns = m.get_editor_property("nanite_settings")
        ns.set_editor_property("enabled", True)
        m.set_editor_property("nanite_settings", ns)
    except Exception as e:
        unreal.log_warning("Nanite ayarlanamadi: %s" % e)
    eal.save_loaded_asset(m)

# 3) Yeni harita olustur ve sahneyi kur
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if eal.does_asset_exist(HARITA):
    les.load_level(HARITA)
    for act in eas.get_all_level_actors():
        eas.destroy_actor(act)
else:
    les.new_level(HARITA)

def koy(sinif, konum, donus=unreal.Rotator(0, 0, 0), etiket=None):
    a = eas.spawn_actor_from_class(sinif, konum, donus)
    if etiket:
        a.set_actor_label(etiket)
    return a

for m in meshes:
    a = eas.spawn_actor_from_object(m, unreal.Vector(0, 0, 0))
    a.set_actor_label("Arena")
    a.set_mobility(unreal.ComponentMobility.STATIC)

gunes = koy(unreal.DirectionalLight, unreal.Vector(0, 0, 8000), unreal.Rotator(-15, -40, 0), "Gunes")
gunes.light_component.set_editor_property("intensity", 8.0)
gunes.light_component.set_editor_property("atmosphere_sun_light", True)
koy(unreal.SkyAtmosphere, unreal.Vector(0, 0, 0), etiket="Atmosfer")
gok = koy(unreal.SkyLight, unreal.Vector(0, 0, 6000), etiket="GokIsigi")
gok.light_component.set_editor_property("real_time_capture", True)
koy(unreal.ExponentialHeightFog, unreal.Vector(0, 0, -2000), etiket="Sis")
koy(unreal.VolumetricCloud, unreal.Vector(0, 0, 0), etiket="Bulutlar")
koy(unreal.PlayerStart, unreal.Vector(0, 0, PLATFORM_UST_CM + 120), etiket="OyuncuBaslangic")

les.save_current_level()
unreal.log("Arena_Map hazir: " + HARITA)
