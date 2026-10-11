# Unreal Engine 5 - Orta platforma duz tas zemin + zeminle ayni hizada altin kakma (halkalar, yildizlar, isinlar, runler).
# Mesh: Kaynak/SM_MerkezZemin.glb (duz disk, eski kabartmalarin ustunde, kenarinda kisa etek) ve SM_MerkezRun.glb (duz altin
# seritler, zeminin 2 mm ustunde). araclar/bolge_doku/merkez_*.py uretti; arena ile ayni eksenlerde, arenanin konumuna konur.
# Kopruler ve kenar bandindaki direkler/mesale kaideleri kaplanmaz.
# Calistirma (Output Log -> Python):
#   exec(open(unreal.Paths.project_content_dir() + "Maps/Arena/MerkezPlatform.py", encoding="utf-8").read())
# Tekrar calistirmak zararsiz. Kaldirmak icin KALDIR = True.
# Ayar: /Game/Maps/Arena/Merkez/MI_MerkezZemin (Parlaklik, Puruzluluk, NormalGucu),
#       /Game/Maps/Arena/Merkez/MI_MerkezAltin (AltinRenk, Puruzluluk, Isik)
# Not: ElementSahasi'nin zemin cizgileri yeni zeminin altinda kalabilir; bundan sonra ElementSahasi.py'yi tekrar calistir.
import os
import unreal

ICERIK = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir())
KAYNAK = os.path.join(ICERIK, "Maps", "Arena", "Kaynak")
HEDEF = "/Game/Maps/Arena/Merkez"
ETIKET = "MP_Merkez"
KALDIR = False

eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
tools = unreal.AssetToolsHelpers.get_asset_tools()
bag = mel.connect_material_expressions
ST = unreal.MaterialSamplerType


def log(msg):
    unreal.log_warning("[Merkez] " + msg)


def hata(msg):
    unreal.log_error("[Merkez] HATA: " + msg)
    raise RuntimeError(msg)


def arena_aktoru():
    for a in eas.get_all_level_actors():
        if isinstance(a, unreal.StaticMeshActor):
            sm = a.static_mesh_component.get_editor_property("static_mesh")
            if sm and "arena_game" in sm.get_name().lower():
                return a
    hata("Sahnede arena_game mesh'i bulunamadi (Arena_Map acik mi?).")


def aktar(dosya, hedef):
    yol = os.path.join(KAYNAK, dosya)
    if not os.path.isfile(yol):
        hata(dosya + " bulunamadi: " + KAYNAK)
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", yol)
    t.set_editor_property("destination_path", hedef)
    t.set_editor_property("automated", True)
    t.set_editor_property("replace_existing", True)
    t.set_editor_property("save", True)
    tools.import_asset_tasks([t])


def mesh_aktar(dosya, klasor, carpisma):
    hedef = HEDEF + "/" + klasor
    aktar(dosya, hedef)
    mesh = None
    for yol in eal.list_assets(hedef, recursive=True, include_folder=False):
        a = eal.load_asset(yol)
        if isinstance(a, unreal.StaticMesh):
            mesh = a
    if not mesh:
        hata(dosya + " aktarilamadi (" + hedef + ").")
    try:
        body = mesh.get_editor_property("body_setup")
        if body:
            body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE if carpisma
                                     else unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
    except Exception as e:
        log("   carpisma ayarlanamadi (onemsiz): %s" % e)
    eal.save_loaded_asset(mesh)
    return mesh


def doku(ad, normal=False, uzanti=".png"):
    yol = HEDEF + "/" + ad
    aktar(ad + uzanti, HEDEF)
    d = eal.load_asset(yol)
    d.set_editor_property("srgb", not normal)
    if normal:
        d.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
    d.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_WORLD)
    d.set_editor_property("max_texture_size", 0)
    eal.save_loaded_asset(d)
    return d


def yeni_malzeme(ad):
    yol = HEDEF + "/" + ad
    if eal.does_asset_exist(yol):
        mat = eal.load_asset(yol)
        mel.delete_all_material_expressions(mat)
    else:
        mat = tools.create_asset(ad, HEDEF, unreal.Material, unreal.MaterialFactoryNew())
    return mat


def ornek(mat, ad):
    yol = HEDEF + "/" + ad
    mi = eal.load_asset(yol) if eal.does_asset_exist(yol) else \
        tools.create_asset(ad, HEDEF, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(mi, mat)
    eal.save_loaded_asset(mi)
    return mi


def bitir(mat):
    mel.layout_material_expressions(mat)
    mel.recompile_material(mat)
    eal.save_loaded_asset(mat)


def zemin_malzemesi(tD, tN):
    mat = yeni_malzeme("M_MerkezZemin")

    def ifade(sinif, x, y):
        return mel.create_material_expression(mat, sinif, x, y)

    def skaler(ad, v, x, y):
        e = ifade(unreal.MaterialExpressionScalarParameter, x, y)
        e.set_editor_property("parameter_name", ad)
        e.set_editor_property("default_value", v)
        return e

    def carp(a, b, x, y, ca="", cb=""):
        e = ifade(unreal.MaterialExpressionMultiply, x, y)
        bag(a, ca, e, "A")
        bag(b, cb, e, "B")
        return e
    d = ifade(unreal.MaterialExpressionTextureSample, -700, -200)
    d.set_editor_property("texture", tD)
    d.set_editor_property("sampler_type", ST.SAMPLERTYPE_COLOR)
    n = ifade(unreal.MaterialExpressionTextureSample, -700, 200)
    n.set_editor_property("texture", tN)
    n.set_editor_property("sampler_type", ST.SAMPLERTYPE_NORMAL)
    mel.connect_material_property(carp(d, skaler("Parlaklik", 0.75, -500, -50), -300, -200, "RGB"), "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(skaler("Puruzluluk", 0.72, -500, 50), "", unreal.MaterialProperty.MP_ROUGHNESS)
    # normal gucu: (R * g, G * g, B) - skaler carpim + AppendVector
    g = skaler("NormalGucu", 1.0, -700, 450)

    def ekle(a, b, x, y, ca="", cb=""):
        e = ifade(unreal.MaterialExpressionAppendVector, x, y)
        bag(a, ca, e, "A")
        bag(b, cb, e, "B")
        return e
    nrm = ekle(ekle(carp(n, g, -450, 200, "R"), carp(n, g, -450, 300, "G"), -300, 250), n, -150, 250, "", "B")
    mel.connect_material_property(nrm, "", unreal.MaterialProperty.MP_NORMAL)
    bitir(mat)
    return ornek(mat, "MI_MerkezZemin")


def altin_malzemesi():
    mat = yeni_malzeme("M_MerkezAltin")

    def ifade(sinif, x, y):
        return mel.create_material_expression(mat, sinif, x, y)
    renk = ifade(unreal.MaterialExpressionVectorParameter, -600, -200)
    renk.set_editor_property("parameter_name", "AltinRenk")
    renk.set_editor_property("default_value", unreal.LinearColor(1.0, 0.71, 0.29, 1.0))
    mel.connect_material_property(renk, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    met = ifade(unreal.MaterialExpressionConstant, -400, 0)
    met.set_editor_property("r", 1.0)
    mel.connect_material_property(met, "", unreal.MaterialProperty.MP_METALLIC)
    pr = ifade(unreal.MaterialExpressionScalarParameter, -400, 100)
    pr.set_editor_property("parameter_name", "Puruzluluk")
    pr.set_editor_property("default_value", 0.3)
    mel.connect_material_property(pr, "", unreal.MaterialProperty.MP_ROUGHNESS)
    isik = ifade(unreal.MaterialExpressionScalarParameter, -600, 250)
    isik.set_editor_property("parameter_name", "Isik")
    isik.set_editor_property("default_value", 0.4)
    e = ifade(unreal.MaterialExpressionMultiply, -300, 250)
    bag(renk, "RGB", e, "A")
    bag(isik, "", e, "B")
    mel.connect_material_property(e, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    bitir(mat)
    return ornek(mat, "MI_MerkezAltin")


def koy(mesh, mi, etiket, arena, carpisma):
    for i in range(len(mesh.get_editor_property("static_materials"))):
        mesh.set_material(i, mi)
    eal.save_loaded_asset(mesh)
    a = eas.spawn_actor_from_object(mesh, arena.get_actor_location())
    a.set_actor_label(etiket)
    a.set_actor_rotation(arena.get_actor_rotation(), False)
    a.set_actor_scale3d(arena.get_actor_scale3d())
    a.set_folder_path("Arena/Merkez")
    if not carpisma:
        a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    return a


def calistir():
    arena = arena_aktoru()
    n = 0
    for a in eas.get_all_level_actors():
        if a.get_actor_label().startswith(ETIKET):
            eas.destroy_actor(a)
            n += 1
    if KALDIR:
        les.save_current_level()
        log("KALDIRILDI - %d aktor silindi." % n)
        return
    log("1/3 Mesh'ler ve dokular aktariliyor...")
    zemin = mesh_aktar("SM_MerkezZemin.glb", "Zemin", True)        # oyuncu ve top yeni duz zeminde yurur
    run = mesh_aktar("SM_MerkezRun.glb", "Altin", False)
    tD, tN = doku("T_Merkez_D", uzanti=".jpg"), doku("T_Merkez_N", normal=True)
    log("2/3 Malzemeler: M_MerkezZemin, M_MerkezAltin")
    mz, ma = zemin_malzemesi(tD, tN), altin_malzemesi()
    log("3/3 Sahneye konuyor (arenayla ayni konum)...")
    koy(zemin, mz, ETIKET + "Zemin", arena, True)
    koy(run, ma, ETIKET + "Altin", arena, False)
    les.save_current_level()
    log("TAMAM - orta platform duz zemin + altin kakma eklendi. Ayar: " + HEDEF + "/MI_MerkezZemin, MI_MerkezAltin. "
        "ElementSahasi cizgileri gorunmuyorsa ElementSahasi.py'yi tekrar calistir.")


calistir()
