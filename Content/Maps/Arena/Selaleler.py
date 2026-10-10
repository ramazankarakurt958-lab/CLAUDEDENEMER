# Unreal Engine 5 - Su tribunune 3D selaleler (referans resimdeki yerlerinde).
# Mesh: Kaynak/SM_Selale.glb (araclar/bolge_doku/selale.py uretti; arena ile ayni eksenlerde, arenanin konumuna konur).
# Calistirma (Output Log -> Python):
#   exec(open(unreal.Paths.project_content_dir() + "Maps/Arena/Selaleler.py", encoding="utf-8").read())
# Tekrar calistirmak zararsiz: eski selaleyi silip yeniden koyar. Kaldirmak icin KALDIR = True.
# Hacimli: Govde (yuvarlak kesitli su), Serpinti (genisleyen kopuk kabugu), Sis (buyuk selalelerin dibinde).
# Ayar: /Game/Maps/Arena/Selale/MI_Selale_Govde, _Serpinti, _Sis  (Parlaklik, Opaklik, AkisHizi, KopukEsik, KenarYumusak, RenkSu, RenkKopuk...)
import os
import unreal

ICERIK = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir())
KAYNAK = os.path.join(ICERIK, "Maps", "Arena", "Kaynak", "SM_Selale.glb")
HEDEF = "/Game/Maps/Arena/Selale"
ETIKET = "SL_Selale"
KALDIR = False

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


def doku_aktar(dosya, normal=False):
    yol = os.path.join(os.path.dirname(KAYNAK), dosya)
    if not os.path.isfile(yol):
        hata(dosya + " bulunamadi: " + yol)
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", yol)
    t.set_editor_property("destination_path", HEDEF)
    t.set_editor_property("automated", True)
    t.set_editor_property("replace_existing", True)
    t.set_editor_property("save", True)
    tools.import_asset_tasks([t])
    d = eal.load_asset(HEDEF + "/" + os.path.splitext(dosya)[0])
    if not d:
        hata(dosya + " aktarilamadi.")
    d.set_editor_property("srgb", False)
    if normal:
        d.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
    eal.save_loaded_asset(d)
    return d


# Malzeme ornekleri: ayni ana malzeme, uc katman (onizlemede kullanilan degerler)
KATMANLAR = {
    "Govde":    dict(Parlaklik=0.2, Opaklik=1.0, AkisHizi=1.0, KopukEsik=0.58, KopukEk=0.0, KenarYumusak=0.6, OlcekU=0.45, OlcekV=0.06, TabanOpak=0.6),
    "Serpinti": dict(Parlaklik=0.45, Opaklik=0.3, AkisHizi=1.6, KopukEsik=0.35, KopukEk=0.5, KenarYumusak=1.5, OlcekU=0.7, OlcekV=0.09, TabanOpak=0.0),
    "Sis":      dict(Parlaklik=0.55, Opaklik=0.2, AkisHizi=0.08, KopukEsik=0.0, KopukEk=1.0, KenarYumusak=3.0, OlcekU=0.5, OlcekV=0.5, TabanOpak=0.35),
}


def malzeme(akis, nrm):
    """Isik alan yari saydam su. UV0: (cevre 0..1, boyuna 0..1), UV1: metre. Katmanlar MI parametreleriyle ayrilir."""
    yol = HEDEF + "/M_Selale"
    if eal.does_asset_exist(yol):
        mat = eal.load_asset(yol)
        mel.delete_all_material_expressions(mat)
    else:
        mat = tools.create_asset("M_Selale", HEDEF, unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    mat.set_editor_property("two_sided", True)
    try:  # yuzeyde gercek isik + yansima (hacim hissi)
        mat.set_editor_property("translucency_lighting_mode", unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
    except Exception as e:
        log("   isiklandirma modu ayarlanamadi (onemsiz): %s" % e)

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

    def doku(tex, uvs, x, y, tur):
        e = ifade(unreal.MaterialExpressionTextureSample, x, y)
        e.set_editor_property("texture", tex)
        e.set_editor_property("sampler_type", tur)
        bag(uvs, "", e, "UVs")
        return e

    def iki_v(a, b, x, y):
        e = ifade(unreal.MaterialExpressionAppendVector, x, y)
        bag(a, "", e, "A")
        bag(b, "", e, "B")
        return e

    M, A, S = unreal.MaterialExpressionMultiply, unreal.MaterialExpressionAdd, unreal.MaterialExpressionSubtract
    ST = unreal.MaterialSamplerType
    sat = unreal.MaterialExpressionSaturate

    uv0 = ifade(unreal.MaterialExpressionTextureCoordinate, -2200, 600)
    uv1 = ifade(unreal.MaterialExpressionTextureCoordinate, -2200, -300)
    uv1.set_editor_property("coordinate_index", 1)
    olcek = iki_v(skaler("OlcekU", 0.45, -2200, -200), skaler("OlcekV", 0.06, -2200, -120), -2050, -160)
    u = iki(M, uv1, olcek, -1900, -300)
    t = iki(M, ifade(unreal.MaterialExpressionTime, -2050, -20), skaler("AkisHizi", 1.0, -2050, 60), -1900, 0)
    # A: u - (0, t*0.35)   B: u*(1.7,1.9) + (0.37, -t*0.6)
    kayA = iki_v(sabit(0.0, -1750, 40), iki(M, t, sabit(-0.35, -1750, 120), -1650, 80), -1550, 40)
    uvA = iki(A, u, kayA, -1400, -300)
    c2 = ifade(unreal.MaterialExpressionConstant2Vector, -1750, -150)
    c2.set_editor_property("r", 1.7)
    c2.set_editor_property("g", 1.9)
    kayB = iki_v(sabit(0.37, -1750, 200), iki(M, t, sabit(-0.6, -1750, 280), -1650, 240), -1550, 200)
    uvB = iki(A, iki(M, u, c2, -1550, -150), kayB, -1400, -100)
    tA = doku(akis, uvA, -1200, -400, ST.SAMPLERTYPE_LINEAR_COLOR)
    tB = doku(akis, uvB, -1200, -100, ST.SAMPLERTYPE_LINEAR_COLOR)
    s = iki(A, iki(M, tA, sabit(0.6, -1000, -350), -900, -400, "R"), iki(M, tB, sabit(0.4, -1000, -50), -900, -100, "R"), -750, -250)

    # Renk: derin mavi su -> kopuk beyazi
    kop = iki(A, iki(M, iki(S, s, skaler("KopukEsik", 0.58, -750, -150), -600, -250), sabit(2.5, -600, -150), -450, -250),
              skaler("KopukEk", 0.0, -450, -150), -300, -250)
    kop = tek(sat, kop, -150, -250)
    renk = ifade(unreal.MaterialExpressionLinearInterpolate, 0, -450)
    bag(vektor("RenkSu", 0.05, 0.25, 0.62, -200, -600), "", renk, "A")
    bag(vektor("RenkKopuk", 0.9, 0.97, 1.0, -200, -450), "", renk, "B")
    bag(kop, "", renk, "Alpha")
    mel.connect_material_property(renk, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(iki(M, renk, skaler("Parlaklik", 0.2, 0, -300), 200, -350), "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.connect_material_property(sabit(0.12, 200, -200), "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(sabit(0.6, 200, -130), "", unreal.MaterialProperty.MP_SPECULAR)
    # Akan dalga normali (gucu %60)
    tN = doku(nrm, uvA, -1200, 250, ST.SAMPLERTYPE_NORMAL)
    duz = ifade(unreal.MaterialExpressionConstant3Vector, -1000, 400)
    duz.set_editor_property("constant", unreal.LinearColor(0, 0, 1, 0))
    nl = ifade(unreal.MaterialExpressionLinearInterpolate, -800, 300)
    bag(duz, "", nl, "A")
    bag(tN, "RGB", nl, "B")
    bag(sabit(0.6, -1000, 480), "", nl, "Alpha")
    mel.connect_material_property(nl, "", unreal.MaterialProperty.MP_NORMAL)

    # Opaklik: (taban + desen) * kenarda incelme (bakis acisi) * altta kaybolma * tepede yumusak baslangic
    sk = tek(sat, iki(M, iki(S, s, sabit(0.3, -750, 0), -600, 0), sabit(2.0, -600, 80), -450, 0), -300, 0)
    yog = ifade(unreal.MaterialExpressionLinearInterpolate, -150, 50)
    bag(sk, "", yog, "A")
    bag(tA, "G", yog, "B")
    bag(sabit(0.25, -300, 120), "", yog, "Alpha")
    taban = skaler("TabanOpak", 0.6, -150, 200)
    desen = iki(A, taban, iki(M, tek(unreal.MaterialExpressionOneMinus, taban, 0, 250), yog, 100, 150), 250, 150)
    bak = tek(unreal.MaterialExpressionAbs, iki(unreal.MaterialExpressionDotProduct, ifade(unreal.MaterialExpressionVertexNormalWS, -600, 600),
                                                ifade(unreal.MaterialExpressionCameraVectorWS, -600, 700), -450, 650), -300, 650)
    kenar = ifade(unreal.MaterialExpressionPower, -150, 650)
    bag(bak, "", kenar, "Base")
    bag(skaler("KenarYumusak", 0.6, -300, 750), "", kenar, "Exp")
    vy = ifade(unreal.MaterialExpressionComponentMask, -2000, 600)
    vy.set_editor_property("g", True)
    bag(uv0, "", vy, "")
    alt = tek(sat, iki(M, tek(unreal.MaterialExpressionOneMinus, vy, -1850, 650), sabit(2.2, -1850, 730), -1700, 650), -1550, 650)
    ust = tek(sat, iki(M, vy, sabit(30.0, -1850, 830), -1700, 800), -1550, 800)
    op = iki(M, iki(M, iki(M, desen, kenar, 400, 300), alt, 550, 400), ust, 700, 500)
    op = iki(M, op, skaler("Opaklik", 1.0, 700, 650), 850, 500)
    # Duvara/kayaya degdigi yerde sert cizgi olmasin
    df = ifade(unreal.MaterialExpressionDepthFade, 1000, 500)
    if bag(op, "", df, "Opacity") or bag(op, "", df, "InOpacity"):
        try:
            df.set_editor_property("fade_distance_default", 120.0)
        except Exception:
            pass
        op = df
    mel.connect_material_property(op, "", unreal.MaterialProperty.MP_OPACITY)

    mel.layout_material_expressions(mat)
    mel.recompile_material(mat)
    eal.save_loaded_asset(mat)

    mis = {}
    for ad, degerler in KATMANLAR.items():
        mi_yol = HEDEF + "/MI_Selale_" + ad
        mi = eal.load_asset(mi_yol) if eal.does_asset_exist(mi_yol) else \
            tools.create_asset("MI_Selale_" + ad, HEDEF, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        mel.set_material_instance_parent(mi, mat)
        for k, v in degerler.items():
            mel.set_material_instance_scalar_parameter_value(mi, k, v)
        eal.save_loaded_asset(mi)
        mis[ad] = mi
    return mis


def calistir():
    arena = arena_aktoru()
    n = eskileri_sil()
    if KALDIR:
        les.save_current_level()
        log("KALDIRILDI - %d selale silindi." % n)
        return
    log("1/3 Selale mesh'i aktariliyor...")
    mesh = mesh_aktar()
    log("2/3 Malzeme: M_Selale (govde, serpinti, sis)")
    mis = malzeme(doku_aktar("T_Selale_Akis.png"), doku_aktar("T_Selale_N.png", normal=True))
    sira = list(KATMANLAR)
    for i, sm in enumerate(mesh.get_editor_property("static_materials")):
        ad = str(sm.get_editor_property("material_slot_name"))
        kat = next((k for k in sira if k.lower() in ad.lower()), sira[min(i, len(sira) - 1)])
        mesh.set_material(i, mis[kat])
        log("   yuva %d (%s) -> %s" % (i, ad, kat))
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
    log("TAMAM - 8 hacimli selale eklendi. Ayar: " + HEDEF + "/MI_Selale_Govde, _Serpinti, _Sis")


calistir()
