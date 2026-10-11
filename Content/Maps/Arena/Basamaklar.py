# Unreal Engine 5 - Ates ve su tribunlerinin egik oturma yuzeylerine gercek 3D basamaklar.
# Mesh: Kaynak/SM_Basamak.glb (araclar/bolge_doku/basamak3d.py uretti; arena ile ayni eksenlerde, arenanin konumuna konur).
# Renk: her basamagin kose rengi kendi bolgesinin rengi (ates: komur, su: gri-mavi) x net tas dokusu (T_SuZemin_*).
# Calistirma (Output Log -> Python):
#   exec(open(unreal.Paths.project_content_dir() + "Maps/Arena/Basamaklar.py", encoding="utf-8").read())
# Tekrar calistirmak zararsiz. Kaldirmak icin KALDIR = True.
# Ayar: /Game/Maps/Arena/Basamak/MI_Basamak  (Parlaklik, DokuTekrar, Puruzluluk)
import os
import unreal

ICERIK = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir())
KAYNAK = os.path.join(ICERIK, "Maps", "Arena", "Kaynak")
HEDEF = "/Game/Maps/Arena/Basamak"
DOKU_KLASORU = "/Game/Maps/Arena/Bolge"     # ArenaBolgeDoku.py zemin dokularini buraya aktarir
ETIKET = "BK_Basamak"   # BS_ on eki eski BolgeSahasi icin kullanildi
KALDIR = False

eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
tools = unreal.AssetToolsHelpers.get_asset_tools()
bag = mel.connect_material_expressions
ST = unreal.MaterialSamplerType


def log(msg):
    unreal.log_warning("[Arena] " + msg)


def hata(msg):
    unreal.log_error("[Arena] HATA: " + msg)
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
        return None
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", yol)
    t.set_editor_property("destination_path", hedef)
    t.set_editor_property("automated", True)
    t.set_editor_property("replace_existing", True)
    t.set_editor_property("save", True)
    tools.import_asset_tasks([t])
    return True


def doku(ad, normal=False, srgb=True):
    yol = DOKU_KLASORU + "/" + ad
    if not eal.does_asset_exist(yol):
        if not aktar(ad + ".png", DOKU_KLASORU):
            hata(ad + ".png bulunamadi: " + KAYNAK)
        d = eal.load_asset(yol)
        d.set_editor_property("srgb", srgb and not normal)
        if normal:
            d.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
        eal.save_loaded_asset(d)
    return eal.load_asset(yol)


def mesh_aktar():
    if not aktar("SM_Basamak.glb", HEDEF):
        hata("SM_Basamak.glb bulunamadi: " + KAYNAK)
    mesh = None
    for yol in eal.list_assets(HEDEF, recursive=True, include_folder=False):
        a = eal.load_asset(yol)
        if isinstance(a, unreal.StaticMesh):
            mesh = a
    if not mesh:
        hata("Basamak mesh'i aktarilamadi (" + HEDEF + ").")
    try:  # oyuncu basamaklarin ustunde yurusun
        body = mesh.get_editor_property("body_setup")
        if body:
            body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    except Exception as e:
        log("   carpisma ayarlanamadi (onemsiz): %s" % e)
    eal.save_loaded_asset(mesh)
    return mesh


def malzeme(d, n, r):
    yol = HEDEF + "/M_Basamak"
    if eal.does_asset_exist(yol):
        mat = eal.load_asset(yol)
        mel.delete_all_material_expressions(mat)
    else:
        mat = tools.create_asset("M_Basamak", HEDEF, unreal.Material, unreal.MaterialFactoryNew())

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

    def ornek(tex, tur, uvs, x, y):
        e = ifade(unreal.MaterialExpressionTextureSample, x, y)
        e.set_editor_property("texture", tex)
        e.set_editor_property("sampler_type", tur)
        bag(uvs, "", e, "UVs")
        return e

    uv = carp(ifade(unreal.MaterialExpressionTextureCoordinate, -1000, 0), skaler("DokuTekrar", 1.0, -1000, 100), -850, 0)
    td = ornek(d, ST.SAMPLERTYPE_COLOR, uv, -650, -200)
    tn = ornek(n, ST.SAMPLERTYPE_NORMAL, uv, -650, 100)
    tr = ornek(r, ST.SAMPLERTYPE_LINEAR_COLOR, uv, -650, 350)
    vc = ifade(unreal.MaterialExpressionVertexColor, -650, -400)
    renk = carp(carp(vc, td, -400, -300, "", "RGB"), skaler("Parlaklik", 2.8, -400, -150), -250, -300)
    mel.connect_material_property(renk, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(tn, "RGB", unreal.MaterialProperty.MP_NORMAL)
    mel.connect_material_property(carp(tr, skaler("Puruzluluk", 1.0, -400, 450), -250, 350, "R"), "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.layout_material_expressions(mat)
    mel.recompile_material(mat)
    eal.save_loaded_asset(mat)

    mi_yol = HEDEF + "/MI_Basamak"
    mi = eal.load_asset(mi_yol) if eal.does_asset_exist(mi_yol) else \
        tools.create_asset("MI_Basamak", HEDEF, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(mi, mat)
    eal.save_loaded_asset(mi)
    return mi


def calistir():
    arena = arena_aktoru()
    n = 0
    for a in eas.get_all_level_actors():
        if a.get_actor_label().startswith(ETIKET):
            eas.destroy_actor(a)
            n += 1
    if KALDIR:
        les.save_current_level()
        log("KALDIRILDI - %d basamak aktoru silindi." % n)
        return
    log("1/3 Basamak mesh'i aktariliyor...")
    mesh = mesh_aktar()
    log("2/3 Malzeme: M_Basamak")
    mi = malzeme(doku("T_SuZemin_D"), doku("T_SuZemin_N", normal=True), doku("T_SuZemin_R", srgb=False))
    for i in range(len(mesh.get_editor_property("static_materials"))):
        mesh.set_material(i, mi)
    eal.save_loaded_asset(mesh)
    log("3/3 Sahneye konuyor (arenayla ayni konum)...")
    a = eas.spawn_actor_from_object(mesh, arena.get_actor_location())
    a.set_actor_label(ETIKET)
    a.set_actor_rotation(arena.get_actor_rotation(), False)
    a.set_actor_scale3d(arena.get_actor_scale3d())
    les.save_current_level()
    log("TAMAM - ates ve su tribunlerine 3D basamaklar eklendi. Ayar: " + HEDEF + "/MI_Basamak (Parlaklik, DokuTekrar, Puruzluluk)")


calistir()
