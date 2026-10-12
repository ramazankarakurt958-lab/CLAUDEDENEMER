# Unreal Engine 5 - Orman tribunune 3D agaclar: kalin, yere yayilip egilerek inen kokler, kivrik govde, dallar, yaprak kumeleri.
# Mesh: Kaynak/SM_Agac.glb (araclar/duvar/agac3d.py uretti; arena ile ayni eksenlerde, arenanin konumuna konur).
# Doku: Kaynak/T_Kabuk_D.png, T_Kabuk_N.png (kabuk), T_Yaprak.png (yaprak atlasi; DuvarKaplama ile ortak).
# Calistirma (Output Log -> Python):
#   exec(open(unreal.Paths.project_content_dir() + "Maps/Arena/OrmanAgac.py", encoding="utf-8").read())
# Tekrar calistirmak zararsiz. Kaldirmak icin KALDIR = True.
# Ayar: /Game/Maps/Arena/Agac/MI_Agac_Kabuk (Ton, Olcek), MI_Agac_Yaprak (Ton)
import os
import unreal

ICERIK = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir())
KAYNAK = os.path.join(ICERIK, "Maps", "Arena", "Kaynak")
HEDEF = "/Game/Maps/Arena/Agac"
ETIKET = "OA_"
KALDIR = False
KABUK_TON = (0.5, 0.45, 0.4)
YAPRAK_TON = (0.85, 1.0, 0.8)

eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
tools = unreal.AssetToolsHelpers.get_asset_tools()
bag = mel.connect_material_expressions
ST = unreal.MaterialSamplerType
MP = unreal.MaterialProperty


def log(msg):
    unreal.log_warning("[Agac] " + msg)


def hata(msg):
    unreal.log_error("[Agac] HATA: " + msg)
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


def doku(ad, normal=False):
    aktar(ad + ".png", HEDEF)
    d = eal.load_asset(HEDEF + "/" + ad)
    d.set_editor_property("srgb", not normal)
    if normal:
        d.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
    eal.save_loaded_asset(d)
    return d


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


def kabuk_malzemesi(tD, tN):
    m = Malzeme("M_AgacKabuk")
    uv = m.carp(m.ifade(unreal.MaterialExpressionTextureCoordinate), m.skaler("Olcek", 1.0))
    d = m.doku(tD, uv, ST.SAMPLERTYPE_COLOR)
    n = m.doku(tN, uv, ST.SAMPLERTYPE_NORMAL)
    mel.connect_material_property(m.carp(d, m.vektor("Ton", KABUK_TON), "RGB", "RGB"), "", MP.MP_BASE_COLOR)
    mel.connect_material_property(n, "RGB", MP.MP_NORMAL)
    p = m.ifade(unreal.MaterialExpressionConstant)
    p.set_editor_property("r", 0.9)
    mel.connect_material_property(p, "", MP.MP_ROUGHNESS)
    return m.bitir()


def yaprak_malzemesi(tY):
    m = Malzeme("M_AgacYaprak")
    m.mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
    m.mat.set_editor_property("two_sided", True)
    d = m.doku(tY, m.ifade(unreal.MaterialExpressionTextureCoordinate), ST.SAMPLERTYPE_COLOR)
    kr = m.ifade(unreal.MaterialExpressionVertexColor)
    mel.connect_material_property(m.carp(m.carp(d, kr, "RGB", ""), m.vektor("Ton", YAPRAK_TON), "", "RGB"), "", MP.MP_BASE_COLOR)
    mel.connect_material_property(d, "A", MP.MP_OPACITY_MASK)
    p = m.ifade(unreal.MaterialExpressionConstant)
    p.set_editor_property("r", 0.8)
    mel.connect_material_property(p, "", MP.MP_ROUGHNESS)
    return m.bitir()


def ornek(mat, ad):
    yol = HEDEF + "/" + ad
    mi = eal.load_asset(yol) if eal.does_asset_exist(yol) else \
        tools.create_asset(ad, HEDEF, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
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
    if n:
        log("   %d eski agac aktoru silindi" % n)
    if KALDIR:
        les.save_current_level()
        log("KALDIRILDI.")
        return
    log("1/3 Mesh ve dokular aktariliyor...")
    aktar("SM_Agac.glb", HEDEF + "/Mesh")
    ms = [eal.load_asset(y) for y in eal.list_assets(HEDEF + "/Mesh", recursive=True, include_folder=False)]
    ms = [a for a in ms if isinstance(a, unreal.StaticMesh)]
    if not ms:
        hata("SM_Agac.glb aktarilamadi.")
    tD, tN, tY = doku("T_Kabuk_D"), doku("T_Kabuk_N", normal=True), doku("T_Yaprak")
    log("2/3 Malzemeler: M_AgacKabuk, M_AgacYaprak")
    mis = {"kabuk": ornek(kabuk_malzemesi(tD, tN), "MI_Agac_Kabuk"), "yaprak": ornek(yaprak_malzemesi(tY), "MI_Agac_Yaprak")}
    log("3/3 Sahneye konuyor (arenayla ayni konum)...")
    for sm in ms:
        for j, s in enumerate(sm.get_editor_property("static_materials")):
            ad = (str(s.get_editor_property("material_slot_name")) + sm.get_name()).lower()
            sm.set_material(j, mis["yaprak"] if "yaprak" in ad else mis["kabuk"])
        eal.save_loaded_asset(sm)
        a = eas.spawn_actor_from_object(sm, arena.get_actor_location())
        a.set_actor_label(ETIKET + sm.get_name())
        a.set_actor_rotation(arena.get_actor_rotation(), False)
        a.set_actor_scale3d(arena.get_actor_scale3d())
        a.set_folder_path("Arena/OrmanAgac")
        a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    les.save_current_level()
    log("TAMAM - orman agaclari kondu (Outliner: Arena/OrmanAgac). Ayar: %s/MI_Agac_Kabuk, MI_Agac_Yaprak" % HEDEF)


calistir()
