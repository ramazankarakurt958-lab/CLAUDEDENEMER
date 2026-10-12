# Unreal Engine 5 - Arena duvarlarini gercek 3D tas kaplama ile kaplar: kesme tas bloklar (pahli, derzli), plastirlar, profilli
# kornis, dis halka duvarlarinda mazgalli parapet. Kuleler ve selalelerin aktigi yuzeyler kaplanmaz.
# Mesh: Kaynak/SM_Duvar.glb (araclar/duvar/kontur.py + duvar3d.py uretti; arena ile ayni eksenlerde, arenanin konumuna konur).
# Doku: Kaynak/T_DuvarTas_D.png (A = puruzluluk), T_DuvarTas_N.png. Bolge rengi malzeme ornegindeki Ton'dan gelir; blok blok ton
# farki, orman yosunu, ates isi ve su buzu mesh'in kose renginde. Ates derzlerinde seyrek kor parlar (KorGucu).
# Orman duvarlarinda kornisten sarkan sarmasiklar (yuva Orman_Sarmasik, T_Yaprak.png, maskeli iki yuzlu).
# Ates tribununde 3D lav akintilari: Kaynak/SM_Lav.glb + T_Lav_D/E/N.png (soguyan kabuk plakalari, catlaklardan parlayan erimis
# kaya, akis yonunde kayar; MI_Lav: LavGucu, AkisHizi (yon ters ise isaretini degistir), Kirmizi/Turuncu/Sari, Nabiz).
# Calistirma (Output Log -> Python):
#   exec(open(unreal.Paths.project_content_dir() + "Maps/Arena/DuvarKaplama.py", encoding="utf-8").read())
# Tekrar calistirmak zararsiz. Kaldirmak icin KALDIR = True.
# Ayar: /Game/Maps/Arena/Duvar/MI_Duvar_<Bolge>_Blok, _Bezek (Ton, Parlaklik, Olcek, Puruz, NormalGucu), _Harc (HarcRenk, KorGucu),
#       MI_Duvar_Orman_Sarmasik (Ton), MI_Lav (LavGucu, AkisHizi, Kirmizi, Turuncu, Sari)
import os
import unreal

ICERIK = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir())
KAYNAK = os.path.join(ICERIK, "Maps", "Arena", "Kaynak")
HEDEF = "/Game/Maps/Arena/Duvar"
ETIKET = "DK_"
KALDIR = False
# bolge tonlari (dogrusal renk): Blok, Bezek (kornis/plastir/parapet) ve harc; ates derzlerinde kor
TON = {"Ates": (0.8, 0.7, 0.64), "Su": (0.78, 0.92, 1.15), "Orman": (0.72, 0.72, 0.64), "Hava": (1.45, 1.40, 1.28)}
BEZEK_ACIK = 1.12
KOR = {}                 # derz koru: {"Ates": 0.5} gibi (yuksek degerler duvarda parlak seritler yapar)

eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
tools = unreal.AssetToolsHelpers.get_asset_tools()
bag = mel.connect_material_expressions
ST = unreal.MaterialSamplerType
MP = unreal.MaterialProperty


def log(msg):
    unreal.log_warning("[Duvar] " + msg)


def hata(msg):
    unreal.log_error("[Duvar] HATA: " + msg)
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


def doku(ad, normal=False, srgb=None):
    aktar(ad + ".png", HEDEF)
    d = eal.load_asset(HEDEF + "/" + ad)
    d.set_editor_property("srgb", (not normal) if srgb is None else srgb)
    if normal:
        d.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
    d.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_WORLD)
    eal.save_loaded_asset(d)
    return d


def meshler(dosya="SM_Duvar.glb", klasor="Mesh"):
    hedef = HEDEF + "/" + klasor
    aktar(dosya, hedef)
    sonuc = [eal.load_asset(y) for y in eal.list_assets(hedef, recursive=True, include_folder=False)]
    sonuc = [a for a in sonuc if isinstance(a, unreal.StaticMesh)]
    if not sonuc:
        hata(dosya + " aktarilamadi (" + hedef + ").")
    return sonuc


class Malzeme:
    def __init__(self, ad):
        yol = HEDEF + "/" + ad
        if eal.does_asset_exist(yol):
            self.mat = eal.load_asset(yol)
            mel.delete_all_material_expressions(self.mat)
        else:
            self.mat = tools.create_asset(ad, HEDEF, unreal.Material, unreal.MaterialFactoryNew())
        self.y = 0

    def ifade(self, sinif):
        self.y += 120
        return mel.create_material_expression(self.mat, sinif, -700, self.y)

    def skaler(self, ad, v):
        e = self.ifade(unreal.MaterialExpressionScalarParameter)
        e.set_editor_property("parameter_name", ad)
        e.set_editor_property("default_value", v)
        return e

    def vektor(self, ad, v):
        e = self.ifade(unreal.MaterialExpressionVectorParameter)
        e.set_editor_property("parameter_name", ad)
        e.set_editor_property("default_value", unreal.LinearColor(v[0], v[1], v[2], 1.0))
        return e

    def carp(self, a, b, ca="", cb=""):
        e = self.ifade(unreal.MaterialExpressionMultiply)
        bag(a, ca, e, "A")
        bag(b, cb, e, "B")
        return e

    def doku(self, tex, uv, tur):
        e = self.ifade(unreal.MaterialExpressionTextureSample)
        e.set_editor_property("texture", tex)
        e.set_editor_property("sampler_type", tur)
        bag(uv, "", e, "UVs")
        return e

    def bitir(self):
        mel.layout_material_expressions(self.mat)
        mel.recompile_material(self.mat)
        eal.save_loaded_asset(self.mat)
        return self.mat


def tas_malzemesi(tD, tN):
    m = Malzeme("M_DuvarTas")
    uv = m.carp(m.ifade(unreal.MaterialExpressionTextureCoordinate), m.skaler("Olcek", 0.5))     # UV metre: 2 m'de bir tekrar
    d = m.doku(tD, uv, ST.SAMPLERTYPE_COLOR)
    n = m.doku(tN, uv, ST.SAMPLERTYPE_NORMAL)
    kr = m.ifade(unreal.MaterialExpressionVertexColor)
    renk = m.carp(m.carp(m.carp(d, kr, "RGB", ""), m.vektor("Ton", (1, 1, 1)), "", "RGB"), m.skaler("Parlaklik", 1.0))
    mel.connect_material_property(renk, "", MP.MP_BASE_COLOR)
    mel.connect_material_property(m.carp(d, m.skaler("Puruz", 1.0), "A"), "", MP.MP_ROUGHNESS)
    duz = m.ifade(unreal.MaterialExpressionConstant3Vector)
    duz.set_editor_property("constant", unreal.LinearColor(0, 0, 1, 1))
    nl = m.ifade(unreal.MaterialExpressionLinearInterpolate)
    bag(duz, "", nl, "A")
    bag(n, "RGB", nl, "B")
    bag(m.skaler("NormalGucu", 1.0), "", nl, "Alpha")
    mel.connect_material_property(nl, "", MP.MP_NORMAL)
    return m.bitir()


def harc_malzemesi():
    m = Malzeme("M_DuvarHarc")
    mel.connect_material_property(m.vektor("HarcRenk", (0.05, 0.045, 0.04)), "RGB", MP.MP_BASE_COLOR)
    p = m.ifade(unreal.MaterialExpressionConstant)
    p.set_editor_property("r", 1.0)
    mel.connect_material_property(p, "", MP.MP_ROUGHNESS)
    kr = m.ifade(unreal.MaterialExpressionVertexColor)                        # R = kor maskesi
    kor = m.carp(m.carp(kr, m.vektor("KorRenk", (1.0, 0.3, 0.05)), "R", "RGB"), m.skaler("KorGucu", 0.0))
    mel.connect_material_property(kor, "", MP.MP_EMISSIVE_COLOR)
    return m.bitir()


def sarmasik_malzemesi(tY):
    m = Malzeme("M_DuvarSarmasik")
    m.mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
    m.mat.set_editor_property("two_sided", True)
    d = m.doku(tY, m.ifade(unreal.MaterialExpressionTextureCoordinate), ST.SAMPLERTYPE_COLOR)
    kr = m.ifade(unreal.MaterialExpressionVertexColor)
    mel.connect_material_property(m.carp(m.carp(d, kr, "RGB", ""), m.vektor("Ton", (1, 1, 1)), "", "RGB"), "", MP.MP_BASE_COLOR)
    mel.connect_material_property(d, "A", MP.MP_OPACITY_MASK)
    p = m.ifade(unreal.MaterialExpressionConstant)
    p.set_editor_property("r", 0.8)
    mel.connect_material_property(p, "", MP.MP_ROUGHNESS)
    return m.bitir()


def lav_malzemesi(tD, tE, tN):
    """gercekci lav: soguyan bazalt kabuk plakalari (T_Lav_D/N), aralarindaki catlaklardan parlayan erimis kaya (T_Lav_E).
    Doku akis yonunde kayar; isima sicakliga gore koyu kirmizi -> turuncu -> sari; buyuk olcekli ikinci ornek sicakligi dalgalandirir."""
    m = Malzeme("M_Lav")

    def topla(a, b, ca="", cb=""):
        e = m.ifade(unreal.MaterialExpressionAdd)
        bag(a, ca, e, "A")
        bag(b, cb, e, "B")
        return e
    zaman = m.ifade(unreal.MaterialExpressionTime)
    kay = m.ifade(unreal.MaterialExpressionAppendVector)
    sifir = m.ifade(unreal.MaterialExpressionConstant)
    bag(sifir, "", kay, "A")
    bag(m.carp(zaman, m.skaler("AkisHizi", -0.05)), "", kay, "B")
    uv = topla(m.carp(m.ifade(unreal.MaterialExpressionTextureCoordinate), m.skaler("Olcek", 0.5)), kay)
    d = m.doku(tD, uv, ST.SAMPLERTYPE_COLOR)
    n = m.doku(tN, uv, ST.SAMPLERTYPE_NORMAL)
    e = m.doku(tE, uv, ST.SAMPLERTYPE_LINEAR_COLOR)
    uv2 = topla(m.carp(uv, m.skaler("DalgaOlcek", 0.37)), m.carp(kay, m.skaler("DalgaHiz", 0.4)))
    e2 = m.doku(tE, uv2, ST.SAMPLERTYPE_LINEAR_COLOR)
    sicak = m.carp(e, topla(m.carp(e2, m.skaler("Dalga", 0.8), "R"), m.skaler("DalgaTaban", 0.6)), "R")
    renk = m.ifade(unreal.MaterialExpressionLinearInterpolate)
    bag(m.vektor("Kirmizi", (0.6, 0.04, 0.005)), "RGB", renk, "A")
    bag(m.vektor("Turuncu", (1.0, 0.32, 0.03)), "RGB", renk, "B")
    bag(sicak, "", renk, "Alpha")
    s2 = m.carp(sicak, sicak)
    renk = topla(renk, m.carp(m.vektor("Sari", (1.0, 0.75, 0.3)), m.carp(s2, s2), "RGB"))
    nabiz = m.ifade(unreal.MaterialExpressionSine)
    bag(m.carp(zaman, m.skaler("NabizHizi", 0.7)), "", nabiz, "")
    nb = topla(m.carp(nabiz, m.skaler("Nabiz", 0.12)), m.skaler("NabizTaban", 1.0))
    isik = m.carp(m.carp(m.carp(renk, s2), m.skaler("LavGucu", 12.0)), nb)
    mel.connect_material_property(isik, "", MP.MP_EMISSIVE_COLOR)
    mel.connect_material_property(d, "RGB", MP.MP_BASE_COLOR)
    mel.connect_material_property(d, "A", MP.MP_ROUGHNESS)
    mel.connect_material_property(n, "RGB", MP.MP_NORMAL)
    return m.bitir()


def ornek(mat, ad, skalerler, vektorler):
    yol = HEDEF + "/" + ad
    mi = eal.load_asset(yol) if eal.does_asset_exist(yol) else \
        tools.create_asset(ad, HEDEF, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(mi, mat)
    for k, v in skalerler.items():
        mel.set_material_instance_scalar_parameter_value(mi, k, v)
    for k, v in vektorler.items():
        mel.set_material_instance_vector_parameter_value(mi, k, unreal.LinearColor(v[0], v[1], v[2], 1.0))
    eal.save_loaded_asset(mi)
    return mi


def ornekler(tas, harc, sar):
    mis = {"Orman_Sarmasik": ornek(sar, "MI_Duvar_Orman_Sarmasik", {}, {"Ton": (0.9, 1.0, 0.85)})}
    for b, t in TON.items():
        mis[b + "_Blok"] = ornek(tas, "MI_Duvar_%s_Blok" % b, {}, {"Ton": t})
        mis[b + "_Bezek"] = ornek(tas, "MI_Duvar_%s_Bezek" % b, {}, {"Ton": tuple(c * BEZEK_ACIK for c in t)})
        mis[b + "_Harc"] = ornek(harc, "MI_Duvar_%s_Harc" % b, {"KorGucu": KOR.get(b, 0.0)},
                                 {"HarcRenk": tuple(c * 0.12 for c in t)})
    return mis


def yuva_malzemesi(mis, ad):
    """yuva adi 'Ates_Blok' gibi; aktarici on/son ek koyabilir"""
    for k, mi in mis.items():
        if k.lower() in ad.lower():
            return mi
    return None


def calistir():
    arena = arena_aktoru()
    n = 0
    for a in eas.get_all_level_actors():
        if a.get_actor_label().startswith(ETIKET):
            eas.destroy_actor(a)
            n += 1
    if n:
        log("   %d eski kaplama aktoru silindi" % n)
    if KALDIR:
        les.save_current_level()
        log("KALDIRILDI.")
        return
    log("1/3 Mesh ve dokular aktariliyor...")
    ms = meshler()
    tD, tN = doku("T_DuvarTas_D"), doku("T_DuvarTas_N", normal=True)
    tY = doku("T_Yaprak")
    tLD, tLE, tLN = doku("T_Lav_D"), doku("T_Lav_E", srgb=False), doku("T_Lav_N", normal=True)
    lav = meshler("SM_Lav.glb", "Lav")
    log("2/3 Malzemeler: M_DuvarTas, M_DuvarHarc, M_DuvarSarmasik, M_Lav")
    mis = ornekler(tas_malzemesi(tD, tN), harc_malzemesi(), sarmasik_malzemesi(tY))
    mi_lav = ornek(lav_malzemesi(tLD, tLE, tLN), "MI_Lav", {}, {})
    for sm in lav:
        for j in range(len(sm.get_editor_property("static_materials"))):
            sm.set_material(j, mi_lav)
        eal.save_loaded_asset(sm)
    ms = ms + lav
    log("3/3 Sahneye konuyor (arenayla ayni konum)...")
    eksik = []
    for i, sm in enumerate(ms):
        for j, s in enumerate(sm.get_editor_property("static_materials") if sm not in lav else []):
            ad = str(s.get_editor_property("material_slot_name"))
            mi = yuva_malzemesi(mis, ad) or yuva_malzemesi(mis, sm.get_name())
            if mi:
                sm.set_material(j, mi)
            else:
                eksik.append(ad)
        eal.save_loaded_asset(sm)
        a = eas.spawn_actor_from_object(sm, arena.get_actor_location())
        a.set_actor_label("%s%s" % (ETIKET, sm.get_name()))
        a.set_actor_rotation(arena.get_actor_rotation(), False)
        a.set_actor_scale3d(arena.get_actor_scale3d())
        a.set_folder_path("Arena/DuvarKaplama")
        a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    if eksik:
        log("   malzemesi bulunamayan yuvalar: " + ", ".join(eksik))
    les.save_current_level()
    log("TAMAM - %d kaplama parcasi kondu (duvar, sarmasik, lav; Outliner: Arena/DuvarKaplama). Ayar: %s/MI_Duvar_*, MI_Lav"
        % (len(ms), HEDEF))


calistir()
