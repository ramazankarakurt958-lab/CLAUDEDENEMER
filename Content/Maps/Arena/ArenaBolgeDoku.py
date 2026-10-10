# Unreal Engine 5 - Arenayi 4 element bolgesine gore boyar (referans resim dokuya yansitildi).
# Ates: komurlesmis tas + lav catlaklari, Su: buz mavisi, Toprak: yosunlu tas, Hava: beyaz mermer.
# Doku: Kaynak/T_ArenaBolge.jpg (araclar ile referans resimden uretildi). Arenanin normal/ORM dokulari ve
# ArenaDetay'in yakin plan tas detayi aynen kalir; sadece renk dokusu degisir.
# Calistirma (Output Log -> Python):
#   exec(open(unreal.Paths.project_content_dir() + "Maps/Arena/ArenaBolgeDoku.py", encoding="utf-8").read())
# Geri almak icin arenaya tekrar MI_ArenaTas verilir (dosyanin sonundaki GERI_AL'a bak).
import os
import unreal

ICERIK = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir())
KAYNAK = os.path.join(ICERIK, "Maps", "Arena", "Kaynak")
VARLIK = "/Game/Maps/Arena/Varliklar"
DETAY = "/Game/Maps/Arena/Detay"
HEDEF = "/Game/Maps/Arena/Bolge"
GERI_AL = False  # True yapip calistirirsan arena eski dokusuna (MI_ArenaTas) doner

eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
tools = unreal.AssetToolsHelpers.get_asset_tools()
ST = unreal.MaterialSamplerType
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
                return a, sm
    hata("Sahnede arena_game mesh'i bulunamadi (Arena_Map acik mi?).")


def malzeme_ata(aktor, sm, mi):
    c = aktor.static_mesh_component
    for i in range(len(sm.get_editor_property("static_materials"))):
        c.set_material(i, mi)


def arena_dokulari():
    normal = orm = None
    for yol in eal.list_assets(VARLIK, recursive=True, include_folder=False):
        a = eal.load_asset(yol)
        if not isinstance(a, unreal.Texture2D):
            continue
        if a.get_editor_property("compression_settings") == unreal.TextureCompressionSettings.TC_NORMALMAP:
            normal = a
        elif not a.get_editor_property("srgb"):
            orm = a
    return normal, orm


def bolge_dokusu():
    yol = os.path.join(KAYNAK, "T_ArenaBolge.jpg")
    if not os.path.isfile(yol):
        hata("T_ArenaBolge.jpg bulunamadi: " + yol)
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", yol)
    t.set_editor_property("destination_path", HEDEF)
    t.set_editor_property("automated", True)
    t.set_editor_property("replace_existing", True)
    t.set_editor_property("save", True)
    tools.import_asset_tasks([t])
    d = eal.load_asset(HEDEF + "/T_ArenaBolge")
    if not d:
        hata("T_ArenaBolge aktarilamadi.")
    d.set_editor_property("srgb", True)
    d.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_WORLD)
    d.set_editor_property("max_texture_size", 0)
    eal.save_loaded_asset(d)
    return d


def malzeme(renk, normal, orm, detay_d, detay_n):
    """M_ArenaTas ile ayni yapi, renk dokusu degistirilebilir parametre (Renk)."""
    yol = HEDEF + "/M_ArenaBolge"
    if eal.does_asset_exist(yol):
        mat = eal.load_asset(yol)
        mel.delete_all_material_expressions(mat)
    else:
        mat = tools.create_asset("M_ArenaBolge", HEDEF, unreal.Material, unreal.MaterialFactoryNew())

    def ifade(sinif, x, y):
        return mel.create_material_expression(mat, sinif, x, y)

    def doku(tex, tur, x, y, param=None):
        e = ifade(unreal.MaterialExpressionTextureSampleParameter2D if param else unreal.MaterialExpressionTextureSample, x, y)
        if param:
            e.set_editor_property("parameter_name", param)
        e.set_editor_property("texture", tex)
        e.set_editor_property("sampler_type", tur)
        return e

    def skaler(ad, deger, x, y):
        e = ifade(unreal.MaterialExpressionScalarParameter, x, y)
        e.set_editor_property("parameter_name", ad)
        e.set_editor_property("default_value", deger)
        return e

    def carp(a, b, x, y, ca="", cb=""):
        e = ifade(unreal.MaterialExpressionMultiply, x, y)
        bag(a, ca, e, "A")
        bag(b, cb, e, "B")
        return e

    uv = ifade(unreal.MaterialExpressionTextureCoordinate, -1400, 300)
    duv = carp(uv, skaler("DetayTekrar", 150.0, -1400, 450), -1200, 350)
    guc = skaler("DetayGucu", 1.0, -1000, 650)

    # Renk: bolge dokusu * lerp(1, detay*2, DetayGucu*0.7) * Parlaklik
    t_renk = doku(renk, ST.SAMPLERTYPE_COLOR, -900, -400, "Renk")
    renk_d = carp(t_renk, skaler("Parlaklik", 1.0, -900, -200), -650, -350, "RGB")
    if detay_d:
        t_dd = doku(detay_d, ST.SAMPLERTYPE_LINEAR_COLOR, -1000, 100)
        bag(duv, "", t_dd, "UVs")
        dd2 = ifade(unreal.MaterialExpressionMultiply, -750, 100)
        dd2.set_editor_property("const_b", 2.0)
        bag(t_dd, "R", dd2, "A")
        alfa = ifade(unreal.MaterialExpressionMultiply, -750, 250)
        alfa.set_editor_property("const_b", 0.7)
        bag(guc, "", alfa, "A")
        lr = ifade(unreal.MaterialExpressionLinearInterpolate, -550, 100)
        lr.set_editor_property("const_a", 1.0)
        bag(dd2, "", lr, "B")
        bag(alfa, "", lr, "Alpha")
        renk_d = carp(renk_d, lr, -300, -300)
    mel.connect_material_property(renk_d, "", unreal.MaterialProperty.MP_BASE_COLOR)

    if orm:
        t_orm = doku(orm, ST.SAMPLERTYPE_LINEAR_COLOR, -900, -100)
        mel.connect_material_property(t_orm, "G", unreal.MaterialProperty.MP_ROUGHNESS)
    else:
        rc = ifade(unreal.MaterialExpressionConstant, -300, -100)
        rc.set_editor_property("r", 0.85)
        mel.connect_material_property(rc, "", unreal.MaterialProperty.MP_ROUGHNESS)

    if normal or detay_n:
        parcalar = []
        if normal:
            parcalar.append((doku(normal, ST.SAMPLERTYPE_NORMAL, -900, 300), "RGB"))
        if detay_n:
            t_dn = doku(detay_n, ST.SAMPLERTYPE_NORMAL, -1000, 400)
            bag(duv, "", t_dn, "UVs")
            maske = ifade(unreal.MaterialExpressionConstant3Vector, -1000, 800)
            maske.set_editor_property("constant", unreal.LinearColor(1.0, 1.0, 0.0, 0.0))
            parcalar.append((carp(t_dn, carp(maske, guc, -750, 700), -550, 450, "RGB"), ""))
        son, cikis = parcalar[0]
        if len(parcalar) == 2:
            top = ifade(unreal.MaterialExpressionAdd, -350, 350)
            bag(son, cikis, top, "A")
            bag(parcalar[1][0], "", top, "B")
            son, cikis = top, ""
        nrm = ifade(unreal.MaterialExpressionNormalize, -150, 350)
        bag(son, cikis, nrm, "")
        mel.connect_material_property(nrm, "", unreal.MaterialProperty.MP_NORMAL)

    mel.layout_material_expressions(mat)
    mel.recompile_material(mat)
    eal.save_loaded_asset(mat)
    return mat


def calistir():
    aktor, sm = arena_aktoru()
    if GERI_AL:
        malzeme_ata(aktor, sm, eal.load_asset(VARLIK + "/MI_ArenaTas"))
        les.save_current_level()
        log("GERI ALINDI - arena eski dokusunda (MI_ArenaTas).")
        return

    log("1/3 Bolge dokusu aktariliyor (4096, biraz surebilir)...")
    renk = bolge_dokusu()
    normal, orm = arena_dokulari()
    detay_d = eal.load_asset(DETAY + "/T_ArenaDetay_D") if eal.does_asset_exist(DETAY + "/T_ArenaDetay_D") else None
    detay_n = eal.load_asset(DETAY + "/T_ArenaDetay_N") if eal.does_asset_exist(DETAY + "/T_ArenaDetay_N") else None
    log("   normal=%s orm=%s detay=%s" % (normal.get_name() if normal else "-", orm.get_name() if orm else "-",
                                         "var" if detay_d else "yok"))

    log("2/3 Malzeme: M_ArenaBolge")
    mat = malzeme(renk, normal, orm, detay_d, detay_n)
    mi_yol = HEDEF + "/MI_ArenaBolge"
    mi = eal.load_asset(mi_yol) if eal.does_asset_exist(mi_yol) else \
        tools.create_asset("MI_ArenaBolge", HEDEF, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(mi, mat)
    eski = eal.load_asset(VARLIK + "/MI_ArenaTas")
    if eski:  # ArenaDetay'da yaptigin ayarlar korunsun
        for ad in ("DetayTekrar", "DetayGucu"):
            mel.set_material_instance_scalar_parameter_value(mi, ad, mel.get_material_instance_scalar_parameter_value(eski, ad))
    eal.save_loaded_asset(mi)

    log("3/3 Arenaya ataniyor...")
    malzeme_ata(aktor, sm, mi)
    les.save_current_level()
    log("TAMAM - Arena bolgelere gore boyandi. Ayar: " + mi_yol + " (Parlaklik, DetayTekrar, DetayGucu)")


calistir()
