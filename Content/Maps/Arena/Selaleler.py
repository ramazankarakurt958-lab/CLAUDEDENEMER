# Unreal Engine 5 - Su tribunune 3D selaleler (referans resimdeki yerlerinde).
# Mesh: Kaynak/SM_Selale.glb (araclar/bolge_doku/selale.py uretti; arena ile ayni eksenlerde, arenanin konumuna konur).
# Calistirma (Output Log -> Python):
#   exec(open(unreal.Paths.project_content_dir() + "Maps/Arena/Selaleler.py", encoding="utf-8").read())
# Tekrar calistirmak zararsiz: eski selaleyi silip yeniden koyar. Kaldirmak icin KALDIR = True.
# Ayar: /Game/Maps/Arena/Selale/MI_Selale  (Parlaklik, Opaklik, AkisHizi, RenkSu, RenkKopuk)
import os
import unreal

ICERIK = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir())
KAYNAK = os.path.join(ICERIK, "Maps", "Arena", "Kaynak", "SM_Selale.glb")
HEDEF = "/Game/Maps/Arena/Selale"
ETIKET = "SL_Selale"
KALDIR = False
GURULTU_DOKULARI = [
    "/Game/Vefects/Free_Fire/Shared/Textures/T_VFX_Noise_01",
    "/Game/NiagaraExamples/Textures/Noise/T_HermiteNoise_CenteredTiling",
    "/Engine/EngineMaterials/Good64x64TilingNoiseHighFreq",
]

eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
tools = unreal.AssetToolsHelpers.get_asset_tools()
bag = mel.connect_material_expressions


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


def eskileri_sil():
    n = 0
    for a in eas.get_all_level_actors():
        if a.get_actor_label().startswith(ETIKET):
            eas.destroy_actor(a)
            n += 1
    return n


def mesh_aktar():
    if not os.path.isfile(KAYNAK):
        hata("SM_Selale.glb bulunamadi: " + KAYNAK)
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", KAYNAK)
    t.set_editor_property("destination_path", HEDEF)
    t.set_editor_property("automated", True)
    t.set_editor_property("replace_existing", True)
    t.set_editor_property("save", True)
    tools.import_asset_tasks([t])
    mesh = None
    for yol in eal.list_assets(HEDEF, recursive=True, include_folder=False):
        a = eal.load_asset(yol)
        if isinstance(a, unreal.StaticMesh):
            mesh = a
    if not mesh:
        hata("Selale mesh'i aktarilamadi (" + HEDEF + ").")
    try:  # yari saydam malzeme Nanite ile cizilmez
        ns = mesh.get_editor_property("nanite_settings")
        ns.set_editor_property("enabled", False)
        mesh.set_editor_property("nanite_settings", ns)
    except Exception as e:
        log("   Nanite kapatilamadi (onemsiz): %s" % e)
    eal.save_loaded_asset(mesh)
    return mesh


def gurultu():
    for y in GURULTU_DOKULARI:
        if eal.does_asset_exist(y):
            t = eal.load_asset(y)
            if isinstance(t, unreal.Texture2D):
                return t
    return None


def ornekleyici(t):
    T = unreal.TextureCompressionSettings
    S = unreal.MaterialSamplerType
    cs = t.get_editor_property("compression_settings")
    srgb = t.get_editor_property("srgb")
    if cs == T.TC_NORMALMAP:
        return S.SAMPLERTYPE_NORMAL
    if cs == T.TC_MASKS:
        return S.SAMPLERTYPE_MASKS
    if cs in (T.TC_GRAYSCALE, T.TC_ALPHA):
        return S.SAMPLERTYPE_GRAYSCALE if srgb else S.SAMPLERTYPE_LINEAR_GRAYSCALE
    return S.SAMPLERTYPE_COLOR if srgb else S.SAMPLERTYPE_LINEAR_COLOR


def malzeme(gur):
    """Yari saydam, kendinden aydinlik su perdesi. UV0: (enine 0..1, boyuna 0..1), UV1: metre."""
    yol = HEDEF + "/M_Selale"
    if eal.does_asset_exist(yol):
        mat = eal.load_asset(yol)
        mel.delete_all_material_expressions(mat)
    else:
        mat = tools.create_asset("M_Selale", HEDEF, unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("two_sided", True)

    def ifade(sinif, x, y):
        return mel.create_material_expression(mat, sinif, x, y)

    def sabit(v, x, y):
        e = ifade(unreal.MaterialExpressionConstant, x, y)
        e.set_editor_property("r", v)
        return e

    def skaler(ad, v, x, y):
        e = ifade(unreal.MaterialExpressionScalarParameter, x, y)
        e.set_editor_property("parameter_name", ad)
        e.set_editor_property("default_value", v)
        return e

    def vektor(ad, r, g, b, x, y):
        e = ifade(unreal.MaterialExpressionVectorParameter, x, y)
        e.set_editor_property("parameter_name", ad)
        e.set_editor_property("default_value", unreal.LinearColor(r, g, b, 1))
        return e

    def iki(sinif, a, b, x, y, ca="", cb=""):
        e = ifade(sinif, x, y)
        bag(a, ca, e, "A")
        bag(b, cb, e, "B")
        return e

    def tek(sinif, a, x, y, ca=""):
        e = ifade(sinif, x, y)
        bag(a, ca, e, "")
        return e

    M, A, S = unreal.MaterialExpressionMultiply, unreal.MaterialExpressionAdd, unreal.MaterialExpressionSubtract

    uv0 = ifade(unreal.MaterialExpressionTextureCoordinate, -1800, 400)
    uv1 = ifade(unreal.MaterialExpressionTextureCoordinate, -1800, -200)
    uv1.set_editor_property("coordinate_index", 1)
    hiz = skaler("AkisHizi", 1.0, -1800, -50)

    # Akan desen: iki farkli olcek ve hizda asagi kayan gurultu (0..1)
    def akis(olcek_u, olcek_v, h, y):
        olc = ifade(unreal.MaterialExpressionConstant2Vector, -1600, y + 60)
        olc.set_editor_property("r", olcek_u)
        olc.set_editor_property("g", olcek_v)
        uv = iki(M, uv1, olc, -1450, y)
        zaman = ifade(unreal.MaterialExpressionTime, -1600, y + 140)
        kay = iki(M, iki(M, zaman, hiz, -1450, y + 140), sabit(-h, -1450, y + 220), -1300, y + 140)
        ek = ifade(unreal.MaterialExpressionAppendVector, -1150, y + 140)
        bag(sabit(0.0, -1300, y + 240), "", ek, "A")
        bag(kay, "", ek, "B")
        son = iki(A, uv, ek, -1000, y)
        if gur:
            t = ifade(unreal.MaterialExpressionTextureSample, -850, y)
            t.set_editor_property("texture", gur)
            t.set_editor_property("sampler_type", ornekleyici(gur))
            bag(son, "", t, "UVs")
            return t, "R"
        return sabit(0.6, -850, y), ""

    a1, c1 = akis(1.2, 0.12, 0.35, -400)
    a2, c2 = akis(2.7, 0.25, 0.6, -100)
    s = iki(A, iki(M, a1, sabit(0.6, -650, -350), -550, -400, c1), iki(M, a2, sabit(0.4, -650, -50), -550, -100, c2), -400, -250)

    # Renk: su mavisi -> kopuk beyazi (desen parlak yerlerde kopuk)
    kopuk = tek(unreal.MaterialExpressionSaturate, iki(M, iki(S, s, sabit(0.5, -400, -150), -300, -250), sabit(2.5, -300, -150), -200, -250), -100, -250)
    renk = ifade(unreal.MaterialExpressionLinearInterpolate, 0, -400)
    bag(vektor("RenkSu", 0.18, 0.5, 1.0, -200, -500), "", renk, "A")
    bag(vektor("RenkKopuk", 0.9, 0.97, 1.0, -200, -350), "", renk, "B")
    bag(kopuk, "", renk, "Alpha")
    mel.connect_material_property(iki(M, renk, skaler("Parlaklik", 1.6, 0, -200), 200, -400), "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    # Opaklik: desen * kenarlarda incelme * altta sise karisma * tepede yumusak baslangic
    ux = ifade(unreal.MaterialExpressionComponentMask, -1600, 400)
    ux.set_editor_property("r", True)
    bag(uv0, "", ux, "")
    vy = ifade(unreal.MaterialExpressionComponentMask, -1600, 550)
    vy.set_editor_property("g", True)
    bag(uv0, "", vy, "")
    kenar = iki(unreal.MaterialExpressionMin, ux, tek(unreal.MaterialExpressionOneMinus, ux, -1450, 450), -1300, 400)
    kenar = tek(unreal.MaterialExpressionSaturate, iki(M, kenar, sabit(5.5, -1200, 480), -1100, 400), -1000, 400)
    alt = tek(unreal.MaterialExpressionSaturate, iki(M, tek(unreal.MaterialExpressionOneMinus, vy, -1450, 600), sabit(2.2, -1300, 680), -1200, 600), -1100, 600)
    ust = tek(unreal.MaterialExpressionSaturate, iki(M, vy, sabit(30.0, -1300, 780), -1200, 750), -1100, 750)
    desen = iki(A, iki(M, s, sabit(0.55, -400, 100), -300, 50), sabit(0.45, -300, 150), -200, 50)
    op = iki(M, iki(M, iki(M, desen, kenar, -100, 200), alt, 0, 300), ust, 100, 400)
    op = iki(M, op, skaler("Opaklik", 0.85, 100, 550), 250, 400)
    mel.connect_material_property(op, "", unreal.MaterialProperty.MP_OPACITY)

    mel.layout_material_expressions(mat)
    mel.recompile_material(mat)
    eal.save_loaded_asset(mat)

    mi_yol = HEDEF + "/MI_Selale"
    mi = eal.load_asset(mi_yol) if eal.does_asset_exist(mi_yol) else \
        tools.create_asset("MI_Selale", HEDEF, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(mi, mat)
    eal.save_loaded_asset(mi)
    return mi


def calistir():
    arena = arena_aktoru()
    n = eskileri_sil()
    if KALDIR:
        les.save_current_level()
        log("KALDIRILDI - %d selale silindi." % n)
        return
    log("1/3 Selale mesh'i aktariliyor...")
    mesh = mesh_aktar()
    log("2/3 Malzeme: M_Selale")
    gur = gurultu()
    log("   akis deseni: %s" % (gur.get_name() if gur else "yok (duz su)"))
    mi = malzeme(gur)
    for i in range(len(mesh.get_editor_property("static_materials"))):
        mesh.set_material(i, mi)
    eal.save_loaded_asset(mesh)

    log("3/3 Sahneye konuyor (arenayla ayni konum)...")
    a = eas.spawn_actor_from_object(mesh, arena.get_actor_location())
    a.set_actor_label(ETIKET)
    a.set_actor_rotation(arena.get_actor_rotation(), False)
    a.set_actor_scale3d(arena.get_actor_scale3d())
    c = a.static_mesh_component
    c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    c.set_editor_property("cast_shadow", False)
    les.save_current_level()
    log("TAMAM - 8 selale eklendi. Ayar: " + HEDEF + "/MI_Selale (Parlaklik, Opaklik, AkisHizi, RenkSu, RenkKopuk)")


calistir()
