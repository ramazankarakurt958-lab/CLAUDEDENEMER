# Unreal Engine 5 - Oyun alani: kose sutunlari, element kureleri, renk gecisli isinlar, gorunmez duvarlar.
# Calistirma (Output Log -> Python):
#   exec(open(unreal.Paths.project_content_dir() + "Maps/Arena/ElementSahasi.py", encoding="utf-8").read())
# Tekrar calistirilabilir: once eski "ES_" nesnelerini siler, sonra yeniden kurar.
import math
import os
import unreal

# ---------------- AYARLAR ----------------
HARITA = "/Game/MAPS/Arena_Map"
SAHA_BOY = 2400.0        # cm, X yonu (uzun kenar)
SAHA_EN = 1600.0         # cm, Y yonu (kisa kenar)
SAHA_DONUS = 0.0         # derece, sahayi platform uzerinde dondurmek icin
MERKEZ = None            # None = arenanin orta platformu; elle: (x, y, z)  z = zemin yuksekligi
SUTUN_BOY = 700.0        # cm (gotik sutunun kure yuvasina kadar boyu)
SUTUN_CAP = 60.0         # cm - 60 = orijinal gotik sutun kalinligi
KURE_CAP = 60.0          # cm (yaricap)
ISIN_CAP = 3.0           # cm (cekirdek isin yaricapi)
DUVAR_BOY = 4000.0       # cm - topun isinlarin ustunden asmamasi icin yuksek
DUVAR_KALINLIK = 40.0    # cm
OYUNCULARI_DA_ENGELLE = False   # True: oyuncular da duvardan gecemez
ZEMIN_CIZGISI = True     # sahanin sinirini zeminde parlayan renk gecisli cizgiyle goster
CIZGI_EN = 6.0           # cm

# Parlakliklar (dusuk = daha mat)
KURE_PARLAKLIK = 6.0
ISIN_PARLAKLIK = 6.0
PARILTI_PARLAKLIK = 0.7
ZEMIN_PARLAKLIK = 2.0
ISIK_GUCU = 2500.0       # kurelerin cevreye verdigi isik

# Indirilen paketlerden kullanilanlar (yoksa otomatik atlanir)
SUTUN_DOKU = "/Game/MAPS/Asetler/marble_01"     # koyu mermer sutunlar
GURULTU_DOKULARI = [                             # isin ve kurelerde akan enerji deseni
    "/Game/Vefects/Free_Fire/Shared/Textures/T_VFX_Noise_01",
    "/Game/NiagaraExamples/Textures/Noise/T_HermiteNoise_CenteredTiling",
    "/Engine/EngineMaterials/Good64x64TilingNoiseHighFreq",
]
# Kure ustu efektler: element -> [(Niagara yolu, kure merkezine gore yukseklik cm, olcek, renklendir)]
# Listede ilk bulunan kullanilir.
ETKILER = {
    "Ates":   [("/Game/Vefects/Free_Fire/Shared/Particles/NS_Fire_Small", 45, 0.45, False),
               ("/Game/NiagaraExamples/FX_Misc/NS_Fire", 45, 0.45, False)],
    "Su":     [("/Game/NiagaraExamples/FX_PickUp/NS_Pickup_Idle", -40, 0.9, True),
               ("/Game/NiagaraExamples/FX_Player/NS_Player_Buff_Looping", -110, 0.6, True)],
    "Toprak": [("/Game/NiagaraExamples/FX_Player/NS_Player_Buff_Looping", -110, 0.6, True),
               ("/Game/NiagaraExamples/FX_PickUp/NS_Pickup_Idle", -40, 0.9, True)],
    "Hava":   [("/Game/NiagaraExamples/FX_Player/NS_Player_Electricity_Looping", -110, 0.6, True),
               ("/Game/NiagaraExamples/FX_Smoke/NS_Smoke_Plume", 45, 0.25, True)],
}

# Koseler saat yonunde: (+X,+Y) -> (+X,-Y) -> (-X,-Y) -> (-X,+Y). Sira degistirilebilir.
# Siralama arenanin tribunlerine gore: kuleli iki tribun Ates ve Su, alcak olanlar Toprak ve Hava.
# BolgeSahasi.py bolgeleri kurelerin yerine gore boyar; sirayi degistirirsen ikisini de yeniden calistir.
ELEMENTLER = [
    ("Toprak", unreal.LinearColor(0.12, 0.85, 0.15, 1)),
    ("Hava",   unreal.LinearColor(0.80, 0.90, 1.00, 1)),
    ("Su",     unreal.LinearColor(0.03, 0.40, 1.00, 1)),
    ("Ates",   unreal.LinearColor(1.00, 0.22, 0.02, 1)),
]
KLASOR = "/Game/MAPS/ARENA/ElementSahasi"
ON_EK = "ES_"
# -----------------------------------------

eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)


def log(msg):
    unreal.log_warning("[Arena] " + msg)


def hata(msg):
    unreal.log_error("[Arena] HATA: " + msg)
    raise RuntimeError(msg)


def V(x, y, z):
    return unreal.Vector(float(x), float(y), float(z))


# ---------- malzemeler ----------
def yeni_malzeme(ad, golgeleme=None, karisim=None, iki_yuz=False):
    yol = KLASOR + "/" + ad
    if eal.does_asset_exist(yol):
        m = eal.load_asset(yol)
        mel.delete_all_material_expressions(m)
    else:
        m = tools.create_asset(ad, KLASOR, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("shading_model", golgeleme or unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    m.set_editor_property("blend_mode", karisim or unreal.BlendMode.BLEND_OPAQUE)
    m.set_editor_property("two_sided", iki_yuz)
    return m


def ifade(m, sinif, x, y):
    return mel.create_material_expression(m, sinif, x, y)


def bagla(a, a_cikis, b, b_giris):
    mel.connect_material_expressions(a, a_cikis, b, b_giris)


def skaler(m, ad, deger, x, y):
    e = ifade(m, unreal.MaterialExpressionScalarParameter, x, y)
    e.set_editor_property("parameter_name", ad)
    e.set_editor_property("default_value", deger)
    return e


def vektor(m, ad, renk, x, y):
    e = ifade(m, unreal.MaterialExpressionVectorParameter, x, y)
    e.set_editor_property("parameter_name", ad)
    e.set_editor_property("default_value", renk)
    return e


def iki(m, sinif, a, b, x, y, a_cikis="", b_cikis=""):
    """Iki girisli islem (Multiply/Add/Subtract/Divide)."""
    e = ifade(m, sinif, x, y)
    bagla(a, a_cikis, e, "A")
    bagla(b, b_cikis, e, "B")
    return e


def carp(m, a, b, x, y, a_cikis="", b_cikis=""):
    return iki(m, unreal.MaterialExpressionMultiply, a, b, x, y, a_cikis, b_cikis)


def sabit_carp(m, kaynak, cikis, deger, x, y):
    e = ifade(m, unreal.MaterialExpressionMultiply, x, y)
    bagla(kaynak, cikis, e, "A")
    e.set_editor_property("const_b", deger)
    return e


def sabit_ekle(m, kaynak, cikis, deger, x, y):
    e = ifade(m, unreal.MaterialExpressionAdd, x, y)
    bagla(kaynak, cikis, e, "A")
    e.set_editor_property("const_b", deger)
    return e


def tek(m, sinif, kaynak, x, y, cikis=""):
    e = ifade(m, sinif, x, y)
    bagla(kaynak, cikis, e, "")
    return e


def fresnel(m, us, x, y):
    e = ifade(m, unreal.MaterialExpressionFresnel, x, y)
    e.set_editor_property("exponent", us)
    e.set_editor_property("base_reflect_fraction", 0.0)
    return e


def kaydet(m):
    mel.layout_material_expressions(m)
    mel.recompile_material(m)
    eal.save_loaded_asset(m)


def doku_yukle(yollar):
    for y in yollar:
        if eal.does_asset_exist(y):
            t = eal.load_asset(y)
            if isinstance(t, unreal.Texture2D):
                return t
    return None


def klasorden_doku(klasor, ipucu):
    if not eal.does_directory_exist(klasor):
        return None
    for y in eal.list_assets(klasor, recursive=True, include_folder=False):
        if ipucu in y.lower():
            t = eal.load_asset(y)
            if isinstance(t, unreal.Texture2D):
                return t
    return None


def normal_yap(t):
    """EXR olarak gelen normal haritalarini normal map sikistirmasina al (yoksa malzeme derlenmez)."""
    if t.get_editor_property("compression_settings") != unreal.TextureCompressionSettings.TC_NORMALMAP:
        t.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
        t.set_editor_property("srgb", False)
        eal.save_loaded_asset(t)
    return t


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


def doku_ornegi(m, t, uv, x, y, uv_cikis=""):
    e = ifade(m, unreal.MaterialExpressionTextureSample, x, y)
    e.set_editor_property("texture", t)
    e.set_editor_property("sampler_type", ornekleyici(t))
    if uv is not None:
        bagla(uv, uv_cikis, e, "UVs")
    return e


def uv(m, tekrar, x, y):
    e = ifade(m, unreal.MaterialExpressionTextureCoordinate, x, y)
    e.set_editor_property("u_tiling", tekrar)
    e.set_editor_property("v_tiling", tekrar)
    return e


def kaydir(m, kaynak, hx, hy, x, y):
    e = ifade(m, unreal.MaterialExpressionPanner, x, y)
    e.set_editor_property("speed_x", hx)
    e.set_editor_property("speed_y", hy)
    bagla(kaynak, "", e, "Coordinate")
    return e


def nabiz(m, faz_kaynak, x, y, hiz=4.0, derinlik=0.25):
    """(1-derinlik) + derinlik*sin(Zaman*hiz - faz*12): akan/titreyen parlama carpani."""
    zaman = ifade(m, unreal.MaterialExpressionTime, x, y)
    son = sabit_carp(m, zaman, "", hiz, x + 150, y)
    if faz_kaynak is not None:
        f12 = sabit_carp(m, faz_kaynak, "", 12.0, x + 150, y + 120)
        son = iki(m, unreal.MaterialExpressionSubtract, son, f12, x + 300, y)
    sin = tek(m, unreal.MaterialExpressionSine, son, x + 450, y)
    k = sabit_carp(m, sin, "", derinlik, x + 600, y)
    return sabit_ekle(m, k, "", 1.0 - derinlik, x + 750, y)


def gurultu_uv(m, gur, kaynak_uv, x, y):
    """Iki zit yonde kayan gurultunun carpimi -> akan enerji deseni (0..~1.5). Doku yoksa sabit."""
    if not gur:
        e = ifade(m, unreal.MaterialExpressionConstant, x, y)
        e.set_editor_property("r", 0.75)
        return e
    p1 = kaydir(m, kaynak_uv, 0.12, 0.05, x, y)
    p2 = kaydir(m, sabit_carp(m, kaynak_uv, "", 0.7, x, y + 150), -0.08, 0.11, x + 150, y + 150)
    s1 = doku_ornegi(m, gur, p1, x + 300, y)
    s2 = doku_ornegi(m, gur, p2, x + 300, y + 200)
    c = carp(m, s1, s2, x + 550, y, "R", "R")
    return sabit_carp(m, c, "", 3.0, x + 700, y)


def kure_malzemesi(gur):
    """Enerji kuresi: renk x parlaklik x kayan gurultu x nabiz."""
    m = yeni_malzeme("M_ElementKure", unreal.MaterialShadingModel.MSM_UNLIT)
    renk = vektor(m, "Renk", unreal.LinearColor(1, 1, 1, 1), -900, 0)
    parlak = skaler(m, "Parlaklik", KURE_PARLAKLIK, -900, 200)
    n = gurultu_uv(m, gur, uv(m, 2.0, -1900, 400), -1700, 400)
    n = sabit_ekle(m, n, "", 0.45, -1000, 400)
    c = carp(m, carp(m, renk, parlak, -600, 0), n, -450, 0)
    c = carp(m, c, nabiz(m, None, -1500, 800, 3.0, 0.2), -300, 0)
    mel.connect_material_property(c, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    kaydet(m)
    return m


def aura_malzemesi(gur):
    """Kurenin etrafinda donen, kenarda parlayan saydam enerji kabugu."""
    m = yeni_malzeme("M_ElementAura", unreal.MaterialShadingModel.MSM_UNLIT, unreal.BlendMode.BLEND_ADDITIVE)
    renk = vektor(m, "Renk", unreal.LinearColor(1, 1, 1, 1), -900, 0)
    guc = skaler(m, "Parlaklik", 2.5, -900, 200)
    n = gurultu_uv(m, gur, uv(m, 3.0, -1900, 400), -1700, 400)
    n = sabit_ekle(m, n, "", 0.2, -1000, 400)
    kenar = fresnel(m, 2.5, -1000, 650)
    c = carp(m, carp(m, renk, guc, -600, 0), n, -450, 0)
    c = carp(m, c, kenar, -300, 0)
    c = carp(m, c, nabiz(m, None, -1500, 900, 2.0, 0.3), -150, 0)
    mel.connect_material_property(c, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    kaydet(m)
    return m


def isin_malzemesi(gur):
    """Renk = lerp(RenkA, RenkB, t), t = isin boyunca 0..1. Uzerinde akan enerji ve yumusak kenar."""
    m = yeni_malzeme("M_ElementIsin", unreal.MaterialShadingModel.MSM_UNLIT, unreal.BlendMode.BLEND_ADDITIVE, True)
    wp = ifade(m, unreal.MaterialExpressionWorldPosition, -2000, 0)
    p0 = vektor(m, "Baslangic", unreal.LinearColor(0, 0, 0, 0), -2000, 150)
    yon = vektor(m, "Yon", unreal.LinearColor(1, 0, 0, 0), -2000, 300)
    uzun = skaler(m, "Uzunluk", 1000.0, -2000, 450)
    fark = iki(m, unreal.MaterialExpressionSubtract, wp, p0, -1750, 50)
    boyunca = iki(m, unreal.MaterialExpressionDotProduct, fark, yon, -1550, 100)  # cm
    t = tek(m, unreal.MaterialExpressionSaturate, iki(m, unreal.MaterialExpressionDivide, boyunca, uzun, -1350, 150), -1200, 150)
    lr = ifade(m, unreal.MaterialExpressionLinearInterpolate, -950, -150)
    bagla(vektor(m, "RenkA", unreal.LinearColor(1, 0, 0, 1), -1200, -250), "", lr, "A")
    bagla(vektor(m, "RenkB", unreal.LinearColor(0, 0, 1, 1), -1200, -100), "", lr, "B")
    bagla(t, "", lr, "Alpha")
    c = carp(m, lr, skaler(m, "Parlaklik", ISIN_PARLAKLIK, -950, 50), -750, -100)
    # gurultu koordinati: (isin boyunca, yukseklik) -> isin boyunca akan elektrik
    z = ifade(m, unreal.MaterialExpressionComponentMask, -1750, 600)
    for kanal, acik in (("r", False), ("g", False), ("b", True), ("a", False)):
        z.set_editor_property(kanal, acik)
    bagla(wp, "", z, "")
    ek = ifade(m, unreal.MaterialExpressionAppendVector, -1350, 500)
    bagla(sabit_carp(m, boyunca, "", 0.003, -1550, 450), "", ek, "A")
    bagla(sabit_carp(m, z, "", 0.02, -1550, 600), "", ek, "B")
    n = gurultu_uv(m, gur, ek, -1200, 500)
    n = sabit_ekle(m, n, "", 0.25, -400, 500)
    yumusak = tek(m, unreal.MaterialExpressionOneMinus, fresnel(m, 1.5, -700, 750), -550, 750)
    c = carp(m, c, n, -550, -100)
    c = carp(m, c, yumusak, -400, -100)
    c = carp(m, c, nabiz(m, t, -2000, 950), -250, -100)
    mel.connect_material_property(c, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    kaydet(m)
    return m


def sutun_malzemesi():
    """Koyu (siyah mermer gorunumlu) tas; kenarlarinda elementin renginde hafif parlama."""
    m = yeni_malzeme("M_ElementSutun")
    koyu = vektor(m, "KoyuRenk", unreal.LinearColor(0.018, 0.018, 0.022, 1), -900, -300)
    damar = vektor(m, "DamarRenk", unreal.LinearColor(0.16, 0.15, 0.14, 1), -900, -150)
    kok = SUTUN_DOKU
    renk_d = klasorden_doku(kok, "diff") or doku_yukle(["/Game/Maps/Arena/Detay/T_ArenaDetay_D"])
    norm_d = klasorden_doku(kok, "nor") or doku_yukle(["/Game/Maps/Arena/Detay/T_ArenaDetay_N"])
    puruz_d = klasorden_doku(kok, "rough")
    k = uv(m, 1.5, -1500, 100)
    if renk_d:
        rd = doku_ornegi(m, renk_d, k, -1250, 0)
        # acik zeminli mermeri ters cevir: koyu tas, acik damarlar
        v = tek(m, unreal.MaterialExpressionOneMinus, rd, -1050, 0, "R")
        v = carp(m, v, v, -900, 0)
        lr = ifade(m, unreal.MaterialExpressionLinearInterpolate, -650, -200)
        bagla(koyu, "", lr, "A")
        bagla(damar, "", lr, "B")
        bagla(v, "", lr, "Alpha")
        mel.connect_material_property(lr, "", unreal.MaterialProperty.MP_BASE_COLOR)
    else:
        mel.connect_material_property(koyu, "", unreal.MaterialProperty.MP_BASE_COLOR)
    if norm_d:
        nd = doku_ornegi(m, normal_yap(norm_d), k, -1250, 300)
        mel.connect_material_property(nd, "RGB", unreal.MaterialProperty.MP_NORMAL)
    puruz = skaler(m, "Puruzluluk", 0.35, -900, 500)
    if puruz_d:
        pd = doku_ornegi(m, puruz_d, k, -1250, 600)
        puruz = carp(m, pd, puruz, -650, 550, "R")
        puruz = sabit_ekle(m, puruz, "", 0.12, -500, 550)
    mel.connect_material_property(puruz, "", unreal.MaterialProperty.MP_ROUGHNESS)
    parlama = carp(m, vektor(m, "Parlama", unreal.LinearColor(1, 1, 1, 1), -900, 800),
                   skaler(m, "ParlamaGucu", 0.35, -900, 950), -650, 850)
    parlama = carp(m, parlama, fresnel(m, 5.0, -900, 1100), -450, 850)
    mel.connect_material_property(parlama, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    kaydet(m)
    return m


def ornek(ad, ana, skalerler=None, vektorler=None):
    yol = KLASOR + "/" + ad
    mi = eal.load_asset(yol) if eal.does_asset_exist(yol) else \
        tools.create_asset(ad, KLASOR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(mi, ana)
    for k, v in (skalerler or {}).items():
        mel.set_material_instance_scalar_parameter_value(mi, k, v)
    for k, v in (vektorler or {}).items():
        mel.set_material_instance_vector_parameter_value(mi, k, v)
    eal.save_loaded_asset(mi)
    return mi


# ---------- kure ustu efektler (indirilen paketlerden) ----------
def efekt_koy(ad, renk, x, y, kz):
    for yol, dz, olcek, boya in ETKILER.get(ad, []):
        if not eal.does_asset_exist(yol):
            continue
        a = eas.spawn_actor_from_object(eal.load_asset(yol), V(x, y, kz + dz), unreal.Rotator(0, 0, 0))
        if not a:
            continue
        a.set_actor_label(ON_EK + "Efekt_" + ad)
        a.set_folder_path("ElementSahasi")
        a.set_actor_scale3d(V(olcek, olcek, olcek))
        if boya:
            nc = a.get_component_by_class(unreal.NiagaraComponent)
            for degisken in ("Color", "User.Color", "Colour"):
                try:
                    nc.set_variable_linear_color(degisken, renk)
                except Exception:
                    pass
        log("   %s efekti: %s" % (ad, yol.split("/")[-1]))
        return
    log("   %s icin efekt paketi bulunamadi (sadece aura var)" % ad)


# ---------- gotik sutun modeli ----------
def gotik_sutun():
    """Kaynak/SM_GotikSutun.glb'yi bir kez ice aktarir; yoksa None (duz silindir kullanilir)."""
    hedef = KLASOR + "/Gotik"
    bul = lambda: [a for a in (eal.load_asset(y) for y in eal.list_assets(hedef, recursive=True, include_folder=False))
                   if isinstance(a, unreal.StaticMesh)] if eal.does_directory_exist(hedef) else []
    mesh = bul()
    if not mesh:
        dosya = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir()),
                             "Maps", "Arena", "Kaynak", "SM_GotikSutun.glb")
        if not os.path.isfile(dosya):
            log("   UYARI: SM_GotikSutun.glb yok, duz silindir kullaniliyor: " + dosya)
            return None
        t = unreal.AssetImportTask()
        t.set_editor_property("filename", dosya)
        t.set_editor_property("destination_path", hedef)
        t.set_editor_property("automated", True)
        t.set_editor_property("replace_existing", True)
        t.set_editor_property("save", True)
        tools.import_asset_tasks([t])
        mesh = bul()
        if not mesh:
            log("   UYARI: gotik sutun aktarilamadi, duz silindir kullaniliyor")
            return None
        try:
            body = mesh[0].get_editor_property("body_setup")
            body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
            eal.save_loaded_asset(mesh[0])
        except Exception as e:
            log("   carpisma ayarlanamadi (onemsiz): %s" % e)
    return mesh[0]


# ---------- sahne ----------
def haritayi_ac():
    dunya = ues.get_editor_world()
    if dunya is None or dunya.get_name() != "Arena_Map":
        log("Arena_Map aciliyor...")
        if not les.load_level(HARITA):
            hata("Harita acilamadi: " + HARITA)


def merkez_bul():
    if MERKEZ:
        return MERKEZ
    for a in eas.get_all_level_actors():
        if isinstance(a, unreal.StaticMeshActor):
            sm = a.static_mesh_component.get_editor_property("static_mesh")
            if sm and "arena_game" in sm.get_name().lower():
                p = a.get_actor_location()
                s = a.get_actor_scale3d()
                # orta platformun ust yuzeyi model icinde ~2300 cm yukseklikte
                return (p.x, p.y, p.z + 2300.0 * s.z)
    hata("Arena bulunamadi. MERKEZ ayarini elle gir.")


def zemin_z(x, y, tahmin):
    """(x, y) noktasinda zemine isin atar; bulamazsa tahmini dondurur."""
    try:
        hit = unreal.SystemLibrary.line_trace_single(
            ues.get_editor_world(), V(x, y, tahmin + 1500), V(x, y, tahmin - 1500),
            getattr(unreal.TraceTypeQuery, "ECC_VISIBILITY", unreal.TraceTypeQuery.TRACE_TYPE_QUERY1), True, [], unreal.DrawDebugTrace.NONE, True)
        if hit:
            alanlar = hit.to_tuple()
            if alanlar[0]:  # blocking_hit
                for v in alanlar:
                    if isinstance(v, unreal.Vector):  # ilk vektor = carpma noktasi
                        return v.z
    except Exception as e:
        log("   zemin olculemedi (onemsiz): %s" % e)
    return tahmin


def eskileri_sil():
    n = 0
    for a in eas.get_all_level_actors():
        if a.get_actor_label().startswith(ON_EK):
            eas.destroy_actor(a)
            n += 1
    if n:
        log("   %d eski nesne silindi" % n)


def koy_mesh(etiket, mesh, konum, donus, olcek, malzeme):
    a = eas.spawn_actor_from_object(mesh, konum, donus)
    a.set_actor_label(ON_EK + etiket)
    a.set_folder_path("ElementSahasi")
    a.set_actor_scale3d(olcek)
    if malzeme:
        a.static_mesh_component.set_material(0, malzeme)
    return a


def carpisma_yok(a):
    a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)


def gorunmez_duvar(a):
    c = a.static_mesh_component
    c.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    c.set_collision_object_type(unreal.CollisionChannel.ECC_WORLD_STATIC)
    c.set_collision_response_to_all_channels(unreal.CollisionResponseType.ECR_BLOCK)
    for kanal in (unreal.CollisionChannel.ECC_CAMERA, unreal.CollisionChannel.ECC_VISIBILITY):
        c.set_collision_response_to_channel(kanal, unreal.CollisionResponseType.ECR_IGNORE)
    if not OYUNCULARI_DA_ENGELLE:
        c.set_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN, unreal.CollisionResponseType.ECR_IGNORE)
    c.set_editor_property("cast_shadow", False)
    c.set_visibility(False, True)  # editorde de oyunda da gorunmez; carpisma calismaya devam eder
    a.set_actor_hidden_in_game(True)


def calistir():
    log("1/4 Malzemeler hazirlaniyor...")
    gur = doku_yukle(GURULTU_DOKULARI)
    log("   enerji deseni: %s" % (gur.get_name() if gur else "yok (duz parlama)"))
    m_kure = kure_malzemesi(gur)
    m_aura = aura_malzemesi(gur)
    m_isin = isin_malzemesi(gur)
    m_sutun = sutun_malzemesi()
    gotik = gotik_sutun()

    log("2/4 Harita ve konum...")
    haritayi_ac()
    cx, cy, cz = merkez_bul()
    log("   saha merkezi: (%.0f, %.0f, %.0f)" % (cx, cy, cz))
    eskileri_sil()

    silindir = eal.load_asset("/Engine/BasicShapes/Cylinder")
    kure = eal.load_asset("/Engine/BasicShapes/Sphere")
    kup = eal.load_asset("/Engine/BasicShapes/Cube")

    a = math.radians(SAHA_DONUS)
    ca, sa = math.cos(a), math.sin(a)
    hx, hy = SAHA_BOY / 2.0, SAHA_EN / 2.0
    yerel = [(hx, hy), (hx, -hy), (-hx, -hy), (-hx, hy)]
    koseler = [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in yerel]
    cz = zemin_z(cx, cy, cz)
    log("   zemin yuksekligi: %.0f" % cz)
    kure_z = cz + SUTUN_BOY + KURE_CAP

    log("3/4 Sutunlar ve kureler...")
    for (ad, renk), (x, y) in zip(ELEMENTLER, koseler):
        # sutun kosedeki zeminden baslar, ustu her kosede ayni yukseklikte biter
        taban = min(zemin_z(x, y, cz), cz)
        boy = cz + SUTUN_BOY - taban
        mi_s = ornek("MI_Sutun_" + ad, m_sutun, vektorler={"Parlama": renk})
        if gotik:
            # model tabani 0'da, kure yuvasi 700 cm'de; sivri kuleler kurenin cevresinde yukselir
            s = SUTUN_CAP / 60.0
            yon = math.degrees(math.atan2(y - cy, x - cx))  # kuleler her kosede ayni yone baksin
            koy_mesh("Sutun_" + ad, gotik, V(x, y, taban), unreal.Rotator(0, 0, yon), V(s, s, boy / 700.0), mi_s)
        else:
            koy_mesh("Sutun_" + ad, silindir, V(x, y, taban + boy / 2), unreal.Rotator(0, 0, 0),
                     V(SUTUN_CAP / 50, SUTUN_CAP / 50, boy / 100), mi_s)
        mi_k = ornek("MI_Kure_" + ad, m_kure, vektorler={"Renk": renk})
        # kure yuvasinda parlayan ince disk
        halka = koy_mesh("Halka_" + ad, silindir, V(x, y, cz + SUTUN_BOY + 1), unreal.Rotator(0, 0, 0),
                         V(SUTUN_CAP * 0.8 / 50, SUTUN_CAP * 0.8 / 50, 0.02), mi_k)
        carpisma_yok(halka)
        k = koy_mesh("Kure_" + ad, kure, V(x, y, kure_z), unreal.Rotator(0, 0, 0),
                     V(KURE_CAP / 50, KURE_CAP / 50, KURE_CAP / 50), mi_k)
        carpisma_yok(k)
        mi_a = ornek("MI_Aura_" + ad, m_aura, vektorler={"Renk": renk})
        au = koy_mesh("Aura_" + ad, kure, V(x, y, kure_z), unreal.Rotator(0, 0, 0),
                      V(KURE_CAP * 1.4 / 50, KURE_CAP * 1.4 / 50, KURE_CAP * 1.4 / 50), mi_a)
        carpisma_yok(au)
        au.static_mesh_component.set_editor_property("cast_shadow", False)
        efekt_koy(ad, renk, x, y, kure_z)
        isik = eas.spawn_actor_from_class(unreal.PointLight, V(x, y, kure_z), unreal.Rotator(0, 0, 0))
        isik.set_actor_label(ON_EK + "Isik_" + ad)
        isik.set_folder_path("ElementSahasi")
        lc = isik.point_light_component
        lc.set_light_color(renk)
        lc.set_intensity(ISIK_GUCU)
        lc.set_attenuation_radius(1500.0)
        lc.set_cast_shadows(False)

    log("4/4 Isinlar ve gorunmez duvarlar...")
    for i in range(4):
        (ad1, r1), (ad2, r2) = ELEMENTLER[i], ELEMENTLER[(i + 1) % 4]
        (x1, y1), (x2, y2) = koseler[i], koseler[(i + 1) % 4]
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        # isin kurelerin yuzeyinden baslar
        bx, by = x1 + ux * KURE_CAP, y1 + uy * KURE_CAP
        ex, ey = x2 - ux * KURE_CAP, y2 - uy * KURE_CAP
        Li = L - 2 * KURE_CAP
        orta = V((bx + ex) / 2, (by + ey) / 2, kure_z)
        donus = unreal.MathLibrary.make_rot_from_z(V(ux, uy, 0))
        ortak = {"Baslangic": unreal.LinearColor(bx, by, kure_z, 0), "Yon": unreal.LinearColor(ux, uy, 0, 0),
                 "RenkA": r1, "RenkB": r2}
        mi_c = ornek("MI_Isin_%s_%s" % (ad1, ad2), m_isin, {"Uzunluk": Li, "Parlaklik": ISIN_PARLAKLIK}, ortak)
        mi_p = ornek("MI_IsinParilti_%s_%s" % (ad1, ad2), m_isin, {"Uzunluk": Li, "Parlaklik": PARILTI_PARLAKLIK}, ortak)
        c = koy_mesh("Isin_%s_%s" % (ad1, ad2), silindir, orta, donus, V(ISIN_CAP / 50, ISIN_CAP / 50, Li / 100), mi_c)
        carpisma_yok(c)
        p = koy_mesh("IsinParilti_%s_%s" % (ad1, ad2), silindir, orta, donus,
                     V(ISIN_CAP * 5 / 50, ISIN_CAP * 5 / 50, Li / 100), mi_p)
        carpisma_yok(p)
        # duvar zeminin 5 m altindan baslar: zemin cukursa top alttan kacamasin
        d = koy_mesh("Duvar_%s_%s" % (ad1, ad2), kup, V((x1 + x2) / 2, (y1 + y2) / 2, cz - 500 + (DUVAR_BOY + 500) / 2),
                     unreal.Rotator(0, 0, math.degrees(math.atan2(dy, dx))),
                     V(L / 100, DUVAR_KALINLIK / 100, (DUVAR_BOY + 500) / 100), None)
        gorunmez_duvar(d)
        if ZEMIN_CIZGISI:
            mi_z = ornek("MI_Zemin_%s_%s" % (ad1, ad2), m_isin, {"Uzunluk": Li, "Parlaklik": ZEMIN_PARLAKLIK}, ortak)
            z = koy_mesh("Zemin_%s_%s" % (ad1, ad2), kup, V((bx + ex) / 2, (by + ey) / 2, cz + 2),
                         unreal.Rotator(0, 0, math.degrees(math.atan2(dy, dx))),
                         V(Li / 100, CIZGI_EN / 100, 0.02), mi_z)
            carpisma_yok(z)
            z.static_mesh_component.set_editor_property("cast_shadow", False)

    les.save_current_level()
    log("TAMAM - Element sahasi kuruldu. Ayarlar dosyanin basinda (SAHA_BOY, SAHA_EN, SAHA_DONUS...).")


# BolgeSahasi.py bu dosyayi sadece yardimci fonksiyonlari icin yukler (SADECE_YARDIMCI=True)
if not globals().get("SADECE_YARDIMCI"):
    calistir()
