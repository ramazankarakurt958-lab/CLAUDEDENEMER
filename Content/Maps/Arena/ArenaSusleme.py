# Unreal Engine 5 - Arena susleri: kopru mesaleleri (tas kaide, bronz kase, kor, titreyen alev, isik), hava tribununde
# donen ruzgar seritleri, bolge sancaklari (ates kirmizi, su mavi, orman yesil, hava beyaz) ve arenanin altinda bulut denizi.
# Mesh'ler: Kaynak/SM_Mesale.glb, SM_Alev.glb, SM_Ruzgar.glb, SM_Sancak.glb, SM_BulutDeniz.glb (araclar/bolge_doku/
# mesale3d.py, susleme3d.py uretti; arena ile ayni eksenlerde, arenanin konumuna konur). Yeni kopru eklenmez.
# Calistirma (Output Log -> Python):
#   exec(open(unreal.Paths.project_content_dir() + "Maps/Arena/ArenaSusleme.py", encoding="utf-8").read())
# Tekrar calistirmak zararsiz. Kaldirmak icin KALDIR = True; tek tek kapatmak icin PARCALAR.
# Ayar: ALEV_EFEKT, ALEV_OLCEK, ISIK, KOR_ISIK, ATES_EFEKT (dosya basi); /Game/Maps/Arena/Susleme/MI_* (Alev: AlevGucu; Ruzgar: Opaklik, Hiz; Bulut: Opaklik, Parlaklik, Hiz)
import math
import os
import unreal

ICERIK = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir())
KAYNAK = os.path.join(ICERIK, "Maps", "Arena", "Kaynak")
HEDEF = "/Game/Maps/Arena/Susleme"
ETIKET = "SS_"
KALDIR = False
PARCALAR = {"mesale": True, "ruzgar": True, "sancak": True, "bulut": True, "ates_efekt": True}
ISIK = {"renk": (1.0, 0.5, 0.2), "lumen": 120.0, "yaricap": 550.0}           # mesale isiklari (lumen, cm)
# gercek ates: projedeki Niagara ates efektleri (ilk bulunan); hicbiri yoksa eski capraz alev kartlari kullanilir
ALEV_EFEKT = ["/Game/Vefects/Free_Fire/Shared/Particles/NS_Fire_Small", "/Game/NiagaraExamples/FX_Misc/NS_Fire"]
ALEV_OLCEK = 0.3          # efekt boyu (kase capi ~60 cm)
KOR_ISIK = 1.2            # kor yataginin parlamasi (MI_MesaleKor -> Isik)
# mesale isik konumlari (arena glTF, metre; mesale3d.py -> mesale_konum.json)
MESALE = [[15.714, 24.27, -1.631], [15.714, 24.183, 1.069], [21.164, 24.17, -1.631], [21.164, 24.195, 1.069],
          [-17.486, 24.274, 1.139], [-17.486, 24.335, -1.701], [-22.286, 24.222, 1.139], [-22.286, 24.164, -1.701],
          [-27.086, 24.221, 1.139], [-27.086, 24.181, -1.701], [-31.886, 24.223, 1.139], [-31.886, 24.168, -1.701],
          [-2.106, 24.1, -16.881], [0.334, 24.052, -16.881], [-2.106, 24.035, -20.606], [0.334, 23.982, -20.606],
          [-2.106, 24.02, -24.331], [0.334, 24.078, -24.331]]

# ates tribunu efektleri (arena glTF, metre): lav akintilarinin ustunde, ust taraflari acik noktalar (araclar/bolge_doku/
# ates_efekt_konum.py). Her biri icin projede ilk bulunan Niagara efekti kullanilir; olcekler buradan ayarlanir.
ATES_EFEKT = {
    "LavAtes": dict(yollar=["/Game/Vefects/Free_Fire/Shared/Particles/NS_Fire_Floor_01", "/Game/Vefects/Free_Fire/Shared/Particles/NS_Fire_Medium",
                            "/Game/NiagaraExamples/FX_Misc/NS_Fire"], olcek=0.5,
                    konum=[[-32.81, 33.89, -12.73], [-19.80, 37.48, -31.27], [-33.18, 34.24, -20.09], [-28.36, 34.29, -25.56], [-10.70, 34.46, -42.66], [-24.33, 29.71, -19.16], [-24.28, 45.34, -32.63]]),
    "Kivilcim": dict(yollar=["/Game/NiagaraExamples/FX_Sparks/NS_Spark_Continuous"], olcek=0.6,
                     konum=[[-23.40, 33.93, -31.08], [-34.59, 34.17, -8.91], [-24.22, 45.39, -36.80]]),
    "Duman": dict(yollar=["/Game/NiagaraExamples/FX_Smoke/NS_Smoke_Plume", "/Game/NiagaraExamples/FX_Smoke/NS_Chimney_Smoke"], olcek=0.6,
                  konum=[[-30.91, 51.01, -32.45], [-23.76, 46.01, -37.60], [-11.84, 44.16, -46.66], [-39.27, 43.57, -20.83]]),
}

eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
tools = unreal.AssetToolsHelpers.get_asset_tools()
bag = mel.connect_material_expressions
ST = unreal.MaterialSamplerType
MP = unreal.MaterialProperty


def log(msg):
    unreal.log_warning("[Susleme] " + msg)


def hata(msg):
    unreal.log_error("[Susleme] HATA: " + msg)
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


def meshler(dosya, klasor):
    hedef = HEDEF + "/" + klasor
    aktar(dosya, hedef)
    sonuc = [eal.load_asset(y) for y in eal.list_assets(hedef, recursive=True, include_folder=False)]
    sonuc = [a for a in sonuc if isinstance(a, unreal.StaticMesh)]
    if not sonuc:
        hata(dosya + " aktarilamadi (" + hedef + ").")
    for sm in sonuc:
        carpisma_temizle(sm)
    return sonuc


def carpisma_temizle(mesh):
    """Ice aktarma her mesh'e otomatik kutu carpismasi verir. Mesale mesh'i uc kopruye yayildigi icin kutusu orta
    platformu (PlayerStart, oyuncular) da yutuyordu: oyuncular zeminin altina itiliyordu. Basit carpisma silinir,
    carpisma sadece gercek ucgenlerden (complex as simple) olur; carpismasiz aktorlerde zaten kapalidir."""
    try:
        unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).remove_collisions(mesh)
    except Exception as e:
        log("   basit carpisma silinemedi (%s): %s" % (mesh.get_name(), e))
    try:
        body = mesh.get_editor_property("body_setup")
        if body:
            body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    except Exception as e:
        log("   carpisma ayarlanamadi (%s): %s" % (mesh.get_name(), e))
    eal.save_loaded_asset(mesh)


def doku(ad, srgb=True):
    aktar(ad + ".png", HEDEF)
    d = eal.load_asset(HEDEF + "/" + ad)
    d.set_editor_property("srgb", srgb)
    eal.save_loaded_asset(d)
    return d


class Malzeme:
    """kucuk malzeme kurucu: skaler parametre, carpim, doku"""

    def __init__(self, ad, karisim=None, isiksiz=False, iki_yuz=False):
        yol = HEDEF + "/" + ad
        if eal.does_asset_exist(yol):
            self.mat = eal.load_asset(yol)
            mel.delete_all_material_expressions(self.mat)
        else:
            self.mat = tools.create_asset(ad, HEDEF, unreal.Material, unreal.MaterialFactoryNew())
        if karisim is not None:
            self.mat.set_editor_property("blend_mode", karisim)
        if isiksiz:
            self.mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
        self.mat.set_editor_property("two_sided", iki_yuz)
        self.ad = ad
        self.y = 0

    def ifade(self, sinif):
        self.y += 120
        return mel.create_material_expression(self.mat, sinif, -600, self.y)

    def skaler(self, ad, v):
        e = self.ifade(unreal.MaterialExpressionScalarParameter)
        e.set_editor_property("parameter_name", ad)
        e.set_editor_property("default_value", v)
        return e

    def sabit3(self, r, g, b):
        e = self.ifade(unreal.MaterialExpressionConstant3Vector)
        e.set_editor_property("constant", unreal.LinearColor(r, g, b, 1))
        return e

    def carp(self, a, b, ca="", cb=""):
        e = self.ifade(unreal.MaterialExpressionMultiply)
        bag(a, ca, e, "A")
        bag(b, cb, e, "B")
        return e

    def topla(self, a, b, ca="", cb=""):
        e = self.ifade(unreal.MaterialExpressionAdd)
        bag(a, ca, e, "A")
        bag(b, cb, e, "B")
        return e

    def doku(self, tex, uv=None, tur=ST.SAMPLERTYPE_COLOR):
        e = self.ifade(unreal.MaterialExpressionTextureSample)
        e.set_editor_property("texture", tex)
        e.set_editor_property("sampler_type", tur)
        if uv:
            bag(uv, "", e, "UVs")
        return e

    def kaydir(self, hx, hy):
        """zamanla kayan UV (Panner)"""
        e = self.ifade(unreal.MaterialExpressionPanner)
        e.set_editor_property("speed_x", hx)
        e.set_editor_property("speed_y", hy)
        return e

    def bagla(self, ifd, prop, cikis=""):
        mel.connect_material_property(ifd, cikis, prop)

    def bitir(self, varsayilan=None):
        mel.layout_material_expressions(self.mat)
        mel.recompile_material(self.mat)
        eal.save_loaded_asset(self.mat)
        yol = HEDEF + "/MI_" + self.ad[2:]
        mi = eal.load_asset(yol) if eal.does_asset_exist(yol) else \
            tools.create_asset("MI_" + self.ad[2:], HEDEF, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        mel.set_material_instance_parent(mi, self.mat)
        eal.save_loaded_asset(mi)
        return mi


def duz(ad, renk, puruz, metal=0.0, isik=None):
    m = Malzeme(ad)
    m.bagla(m.sabit3(*renk), MP.MP_BASE_COLOR)
    p = m.ifade(unreal.MaterialExpressionConstant)
    p.set_editor_property("r", puruz)
    m.bagla(p, MP.MP_ROUGHNESS)
    if metal:
        k = m.ifade(unreal.MaterialExpressionConstant)
        k.set_editor_property("r", metal)
        m.bagla(k, MP.MP_METALLIC)
    if isik:
        m.bagla(m.carp(m.sabit3(*isik[0]), m.skaler("Isik", isik[1])), MP.MP_EMISSIVE_COLOR)
    return m.bitir()


def alev_malzemesi(t):
    m = Malzeme("M_Alev", unreal.BlendMode.BLEND_ADDITIVE, isiksiz=True, iki_yuz=True)
    d = m.doku(t)
    zaman = m.ifade(unreal.MaterialExpressionTime)
    # titreme: 0.8 + 0.2 * sin(9 t) * sin(13.7 t)
    s1, s2 = m.ifade(unreal.MaterialExpressionSine), m.ifade(unreal.MaterialExpressionSine)
    bag(m.carp(zaman, m.skaler("TitremeHizi", 1.4)), "", s1, "")
    bag(m.carp(zaman, m.skaler("TitremeHizi2", 2.2)), "", s2, "")
    tit = m.topla(m.carp(m.carp(s1, s2), m.skaler("Titreme", 0.2)), m.skaler("TabanIsik", 0.8))
    e = m.carp(m.carp(m.carp(d, d, "RGB", "A"), m.skaler("AlevGucu", 6.0)), tit)
    m.bagla(e, MP.MP_EMISSIVE_COLOR)
    return m.bitir()


def ruzgar_malzemesi(t):
    m = Malzeme("M_Ruzgar", unreal.BlendMode.BLEND_TRANSLUCENT, isiksiz=True, iki_yuz=True)
    d = m.doku(t, m.kaydir(-0.25, 0.0))
    m.bagla(m.carp(m.sabit3(1.0, 1.02, 1.05), m.skaler("Parlaklik", 1.5)), MP.MP_EMISSIVE_COLOR)
    m.bagla(m.carp(d, m.skaler("Opaklik", 0.55), "A"), MP.MP_OPACITY)
    return m.bitir()


def sancak_malzemesi(t):
    m = Malzeme("M_Sancak", unreal.BlendMode.BLEND_MASKED, iki_yuz=True)
    d = m.doku(t)
    m.bagla(d, MP.MP_BASE_COLOR, "RGB")
    m.bagla(d, MP.MP_OPACITY_MASK, "A")
    p = m.ifade(unreal.MaterialExpressionConstant)
    p.set_editor_property("r", 0.9)
    m.bagla(p, MP.MP_ROUGHNESS)
    return m.bitir()


def bulut_malzemesi(t):
    m = Malzeme("M_Bulut", unreal.BlendMode.BLEND_TRANSLUCENT, isiksiz=True, iki_yuz=True)
    d1 = m.doku(t, m.kaydir(0.004, 0.002), ST.SAMPLERTYPE_LINEAR_COLOR)       # T_Bulut sRGB kapali: Linear Color
    d2 = m.doku(t, m.kaydir(-0.003, 0.005), ST.SAMPLERTYPE_LINEAR_COLOR)
    m.bagla(m.carp(m.sabit3(0.82, 0.85, 0.9), m.skaler("Parlaklik", 1.2)), MP.MP_EMISSIVE_COLOR)
    m.bagla(m.carp(m.carp(d1, d2, "R", "R"), m.skaler("Opaklik", 1.4)), MP.MP_OPACITY)
    return m.bitir()


def koy(mesh, mi, etiket, arena, carpisma=False, yuvalar=None):
    if yuvalar is not None:
        for i, s in enumerate(mesh.get_editor_property("static_materials")):
            ad = str(s.get_editor_property("material_slot_name"))
            mesh.set_material(i, yuvalar.get(ad, mi) if mi else yuvalar.get(ad))
    elif mi:
        for i in range(len(mesh.get_editor_property("static_materials"))):
            mesh.set_material(i, mi)
    eal.save_loaded_asset(mesh)
    a = eas.spawn_actor_from_object(mesh, arena.get_actor_location())
    a.set_actor_label(ETIKET + etiket)
    a.set_actor_rotation(arena.get_actor_rotation(), False)
    a.set_actor_scale3d(arena.get_actor_scale3d())
    a.set_folder_path("Arena/Susleme")
    if not carpisma:
        a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    a.static_mesh_component.set_cast_shadow(carpisma)
    return a


# ---------------------------------------------------------------- glTF -> dunya (isiklar icin)
def eksen_haritasi():
    hedef = HEDEF + "/Isaret"
    mesh = None
    if eal.does_directory_exist(hedef):
        mesh = next((a for a in (eal.load_asset(y) for y in eal.list_assets(hedef, recursive=True, include_folder=False))
                     if isinstance(a, unreal.StaticMesh)), None)
    if not mesh:
        aktar("SM_EksenIsaret.glb", hedef)
        mesh = next((a for a in (eal.load_asset(y) for y in eal.list_assets(hedef, recursive=True, include_folder=False))
                     if isinstance(a, unreal.StaticMesh)), None)
    b = mesh.get_bounding_box()
    mn, mx = (b.min.x, b.min.y, b.min.z), (b.max.x, b.max.y, b.max.z)
    boy = [mx[i] - mn[i] for i in range(3)]
    birim = min(boy) / 10.0
    harita = [(int(round(boy[i] / birim / 10.0)) - 1, 1.0 if mx[i] > -mn[i] else -1.0) for i in range(3)]
    if sorted(k for k, _ in harita) != [0, 1, 2]:
        hata("Eksen isareti okunamadi.")
    return harita, birim


def dunya_donusumu(arena, harita, birim):
    p0, r, s = arena.get_actor_location(), arena.get_actor_rotation(), arena.get_actor_scale3d()
    P, Y, R = math.radians(r.pitch), math.radians(r.yaw), math.radians(r.roll)
    SP, CP, SY, CY, SR, CR = math.sin(P), math.cos(P), math.sin(Y), math.cos(Y), math.sin(R), math.cos(R)
    M = ((CP * CY, CP * SY, SP), (SR * SP * CY - CR * SY, SR * SP * SY + CR * CY, -SR * CP),
         (-(CR * SP * CY + SR * SY), CY * SR - CR * SP * SY, CR * CP))
    olc = (s.x, s.y, s.z)

    def donustur(g):
        yerel = [harita[i][1] * birim * g[harita[i][0]] * olc[i] for i in range(3)]
        return tuple((p0.x, p0.y, p0.z)[c] + sum(yerel[i] * M[i][c] for i in range(3)) for c in range(3))
    return donustur


def isiklar(arena):
    harita, birim = eksen_haritasi()
    dunya = dunya_donusumu(arena, harita, birim)
    for i, p in enumerate(MESALE):
        w = dunya(p)
        a = eas.spawn_actor_from_class(unreal.PointLight, unreal.Vector(*w))
        a.set_actor_label("%sIsik_%02d" % (ETIKET, i))
        a.set_folder_path("Arena/Susleme/Isiklar")
        c = a.get_component_by_class(unreal.PointLightComponent)
        c.set_mobility(unreal.ComponentMobility.MOVABLE)          # pisirilmis isik gerektirmesin
        try:
            c.set_editor_property("intensity_units", unreal.LightUnits.LUMENS)
        except Exception:
            pass
        c.set_intensity(ISIK["lumen"])
        c.set_light_color(unreal.LinearColor(ISIK["renk"][0], ISIK["renk"][1], ISIK["renk"][2], 1.0))
        c.set_attenuation_radius(ISIK["yaricap"])
        c.set_cast_shadows(False)
    log("   %d mesale isigi" % len(MESALE))


def niagara_koy(arena, yollar, konumlar, olcek, etiket, klasor):
    """Verilen glTF konumlarina projede ilk bulunan Niagara efektini koyar. Doner: kullanilan efekt adi ya da None."""
    yol = next((y for y in yollar if eal.does_asset_exist(y)), None)
    if not yol:
        return None
    harita, birim = eksen_haritasi()
    dunya = dunya_donusumu(arena, harita, birim)
    efekt = eal.load_asset(yol)
    for i, p in enumerate(konumlar):
        a = eas.spawn_actor_from_object(efekt, unreal.Vector(*dunya(p)), unreal.Rotator(0, 0, 0))
        if not a:
            return None
        a.set_actor_label("%s%s_%02d" % (ETIKET, etiket, i))
        a.set_folder_path("Arena/Susleme/" + klasor)
        a.set_actor_scale3d(unreal.Vector(olcek, olcek, olcek))
    return yol.split("/")[-1]


def niagara_ates(arena):
    """Her mesale kasesine gercek (parcacikli) ates koyar (isik kasenin 25 cm ustunde; ates kor yataginda)."""
    ad = niagara_koy(arena, ALEV_EFEKT, [[p[0], p[1] - 0.25, p[2]] for p in MESALE], ALEV_OLCEK, "Ates", "Ates")
    if ad:
        log("   %d mesaleye ates efekti: %s" % (len(MESALE), ad))
    return bool(ad)


def calistir():
    arena = arena_aktoru()
    n = 0
    for a in eas.get_all_level_actors():
        if a.get_actor_label().startswith(ETIKET):
            eas.destroy_actor(a)
            n += 1
    if n:
        log("   %d eski sus aktoru silindi" % n)
    if KALDIR:
        les.save_current_level()
        log("KALDIRILDI.")
        return
    if PARCALAR["mesale"]:
        log("Mesaleler...")
        yuva = {"Tas": duz("M_MesaleTas", (0.2, 0.18, 0.15), 0.85),
                "Bronz": duz("M_MesaleBronz", (0.55, 0.33, 0.14), 0.4, metal=1.0),
                "Kor": duz("M_MesaleKor", (0.05, 0.02, 0.01), 0.9, isik=((1.0, 0.35, 0.08), KOR_ISIK))}
        for i, sm in enumerate(meshler("SM_Mesale.glb", "Mesale")):
            koy(sm, None, "Mesale_%d" % i, arena, carpisma=True, yuvalar=yuva)
        if not niagara_ates(arena):
            log("   Niagara ates efekti bulunamadi - alev kartlari kullaniliyor")
            alev = alev_malzemesi(doku("T_Alev"))
            for sm in meshler("SM_Alev.glb", "Alev"):
                koy(sm, alev, "Alev", arena)
        isiklar(arena)
    if PARCALAR["ruzgar"]:
        log("Ruzgar seritleri...")
        mi = ruzgar_malzemesi(doku("T_Ruzgar"))
        for sm in meshler("SM_Ruzgar.glb", "Ruzgar"):
            koy(sm, mi, "Ruzgar", arena)
    if PARCALAR["sancak"]:
        log("Sancaklar...")
        mi = sancak_malzemesi(doku("T_Sancak"))
        for i, sm in enumerate(meshler("SM_Sancak.glb", "Sancak")):
            koy(sm, mi, "Sancak_%d" % i, arena)
    if PARCALAR["bulut"]:
        log("Bulut denizi...")
        mi = bulut_malzemesi(doku("T_Bulut", srgb=False))
        for sm in meshler("SM_BulutDeniz.glb", "Bulut"):
            koy(sm, mi, "BulutDeniz", arena)
    if PARCALAR["ates_efekt"]:
        log("Ates tribunu efektleri...")
        for ad, e in ATES_EFEKT.items():
            kullanilan = niagara_koy(arena, e["yollar"], e["konum"], e["olcek"], ad, "AtesTribunu")
            log("   %s: %s" % (ad, "%d adet, %s" % (len(e["konum"]), kullanilan) if kullanilan else "efekt bulunamadi, atlandi"))
    les.save_current_level()
    log("TAMAM - susler eklendi (Outliner: Arena/Susleme). Ayar: " + HEDEF + "/MI_* ; kapatmak icin PARCALAR.")


calistir()
