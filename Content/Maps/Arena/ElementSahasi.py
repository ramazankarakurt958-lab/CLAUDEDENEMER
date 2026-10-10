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
ISIN_CAP = 6.0           # cm (cekirdek isin yaricapi)
DUVAR_BOY = 4000.0       # cm - topun isinlarin ustunden asmamasi icin yuksek
DUVAR_KALINLIK = 40.0    # cm
OYUNCULARI_DA_ENGELLE = False   # True: oyuncular da duvardan gecemez
ZEMIN_CIZGISI = True     # sahanin sinirini zeminde parlayan renk gecisli cizgiyle goster
CIZGI_EN = 12.0          # cm

# Koseler saat yonunde: (+X,+Y) -> (+X,-Y) -> (-X,-Y) -> (-X,+Y). Sira degistirilebilir.
ELEMENTLER = [
    ("Ates",   unreal.LinearColor(1.00, 0.22, 0.02, 1)),
    ("Su",     unreal.LinearColor(0.03, 0.40, 1.00, 1)),
    ("Toprak", unreal.LinearColor(0.12, 0.85, 0.15, 1)),
    ("Hava",   unreal.LinearColor(0.80, 0.90, 1.00, 1)),
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
def yeni_malzeme(ad):
    yol = KLASOR + "/" + ad
    if eal.does_asset_exist(yol):
        m = eal.load_asset(yol)
        mel.delete_all_material_expressions(m)
        return m
    return tools.create_asset(ad, KLASOR, unreal.Material, unreal.MaterialFactoryNew())


def ifade(m, sinif, x, y):
    return mel.create_material_expression(m, sinif, x, y)


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


def sabit_carp(m, kaynak, cikis, deger, x, y):
    e = ifade(m, unreal.MaterialExpressionMultiply, x, y)
    mel.connect_material_expressions(kaynak, cikis, e, "A")
    e.set_editor_property("const_b", deger)
    return e


def kaydet(m):
    mel.layout_material_expressions(m)
    mel.recompile_material(m)
    eal.save_loaded_asset(m)


def nabiz(m, faz_kaynak, x, y):
    """0.75 + 0.25*sin(Zaman*4 - faz*12): akan/titreyen parlama carpani."""
    zaman = ifade(m, unreal.MaterialExpressionTime, x, y)
    z4 = sabit_carp(m, zaman, "", 4.0, x + 150, y)
    son = z4
    if faz_kaynak is not None:
        f12 = sabit_carp(m, faz_kaynak, "", 12.0, x + 150, y + 120)
        cik = ifade(m, unreal.MaterialExpressionSubtract, x + 300, y)
        mel.connect_material_expressions(z4, "", cik, "A")
        mel.connect_material_expressions(f12, "", cik, "B")
        son = cik
    sin = ifade(m, unreal.MaterialExpressionSine, x + 450, y)
    mel.connect_material_expressions(son, "", sin, "")
    k = sabit_carp(m, sin, "", 0.25, x + 600, y)
    top = ifade(m, unreal.MaterialExpressionAdd, x + 750, y)
    mel.connect_material_expressions(k, "", top, "A")
    top.set_editor_property("const_b", 0.75)
    return top


def kure_malzemesi():
    m = yeni_malzeme("M_ElementKure")
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    renk = vektor(m, "Renk", unreal.LinearColor(1, 1, 1, 1), -900, 0)
    parlak = skaler(m, "Parlaklik", 25.0, -900, 200)
    c1 = ifade(m, unreal.MaterialExpressionMultiply, -600, 0)
    mel.connect_material_expressions(renk, "", c1, "A")
    mel.connect_material_expressions(parlak, "", c1, "B")
    nb = nabiz(m, None, -1500, 400)
    c2 = ifade(m, unreal.MaterialExpressionMultiply, -300, 0)
    mel.connect_material_expressions(c1, "", c2, "A")
    mel.connect_material_expressions(nb, "", c2, "B")
    mel.connect_material_property(c2, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    kaydet(m)
    return m


def isin_malzemesi():
    """Renk = lerp(RenkA, RenkB, t), t = isin boyunca 0..1 (dunya konumundan)."""
    m = yeni_malzeme("M_ElementIsin")
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
    m.set_editor_property("two_sided", True)
    wp = ifade(m, unreal.MaterialExpressionWorldPosition, -1600, 0)
    p0 = vektor(m, "Baslangic", unreal.LinearColor(0, 0, 0, 0), -1600, 150)
    yon = vektor(m, "Yon", unreal.LinearColor(1, 0, 0, 0), -1600, 300)
    uzun = skaler(m, "Uzunluk", 1000.0, -1600, 450)
    fark = ifade(m, unreal.MaterialExpressionSubtract, -1350, 50)
    mel.connect_material_expressions(wp, "", fark, "A")
    mel.connect_material_expressions(p0, "", fark, "B")
    nokta = ifade(m, unreal.MaterialExpressionDotProduct, -1150, 100)
    mel.connect_material_expressions(fark, "", nokta, "A")
    mel.connect_material_expressions(yon, "", nokta, "B")
    bol = ifade(m, unreal.MaterialExpressionDivide, -950, 150)
    mel.connect_material_expressions(nokta, "", bol, "A")
    mel.connect_material_expressions(uzun, "", bol, "B")
    t = ifade(m, unreal.MaterialExpressionSaturate, -800, 150)
    mel.connect_material_expressions(bol, "", t, "")
    ra = vektor(m, "RenkA", unreal.LinearColor(1, 0, 0, 1), -800, -250)
    rb = vektor(m, "RenkB", unreal.LinearColor(0, 0, 1, 1), -800, -100)
    lr = ifade(m, unreal.MaterialExpressionLinearInterpolate, -550, -150)
    mel.connect_material_expressions(ra, "", lr, "A")
    mel.connect_material_expressions(rb, "", lr, "B")
    mel.connect_material_expressions(t, "", lr, "Alpha")
    parlak = skaler(m, "Parlaklik", 10.0, -550, 50)
    c1 = ifade(m, unreal.MaterialExpressionMultiply, -350, -100)
    mel.connect_material_expressions(lr, "", c1, "A")
    mel.connect_material_expressions(parlak, "", c1, "B")
    nb = nabiz(m, t, -1600, 650)
    c2 = ifade(m, unreal.MaterialExpressionMultiply, -150, -100)
    mel.connect_material_expressions(c1, "", c2, "A")
    mel.connect_material_expressions(nb, "", c2, "B")
    mel.connect_material_property(c2, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    kaydet(m)
    return m


def sutun_malzemesi():
    m = yeni_malzeme("M_ElementSutun")
    renk = vektor(m, "TasRengi", unreal.LinearColor(0.42, 0.40, 0.37, 1), -900, -200)
    dd = eal.load_asset("/Game/Maps/Arena/Detay/T_ArenaDetay_D") if eal.does_asset_exist("/Game/Maps/Arena/Detay/T_ArenaDetay_D") else None
    dn = eal.load_asset("/Game/Maps/Arena/Detay/T_ArenaDetay_N") if eal.does_asset_exist("/Game/Maps/Arena/Detay/T_ArenaDetay_N") else None
    if dd:
        uv = ifade(m, unreal.MaterialExpressionTextureCoordinate, -1300, 100)
        uv.set_editor_property("u_tiling", 2.0)
        uv.set_editor_property("v_tiling", 2.0)
        td = ifade(m, unreal.MaterialExpressionTextureSample, -1000, 50)
        td.set_editor_property("texture", dd)
        td.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
        mel.connect_material_expressions(uv, "", td, "UVs")
        d2 = sabit_carp(m, td, "R", 2.0, -750, 50)
        c = ifade(m, unreal.MaterialExpressionMultiply, -500, -100)
        mel.connect_material_expressions(renk, "", c, "A")
        mel.connect_material_expressions(d2, "", c, "B")
        mel.connect_material_property(c, "", unreal.MaterialProperty.MP_BASE_COLOR)
        if dn:
            tn = ifade(m, unreal.MaterialExpressionTextureSample, -1000, 350)
            tn.set_editor_property("texture", dn)
            tn.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
            mel.connect_material_expressions(uv, "", tn, "UVs")
            mel.connect_material_property(tn, "RGB", unreal.MaterialProperty.MP_NORMAL)
    else:
        mel.connect_material_property(renk, "", unreal.MaterialProperty.MP_BASE_COLOR)
    r = ifade(m, unreal.MaterialExpressionConstant, -500, 250)
    r.set_editor_property("r", 0.8)
    mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
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
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
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
    m_kure = kure_malzemesi()
    m_isin = isin_malzemesi()
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
        if gotik:
            # model tabani 0'da, kure yuvasi 700 cm'de; sivri kuleler kurenin cevresinde yukselir
            s = SUTUN_CAP / 60.0
            yon = math.degrees(math.atan2(y - cy, x - cx))  # kuleler her kosede ayni yone baksin
            koy_mesh("Sutun_" + ad, gotik, V(x, y, taban), unreal.Rotator(0, 0, yon), V(s, s, boy / 700.0), m_sutun)
        else:
            koy_mesh("Sutun_" + ad, silindir, V(x, y, taban + boy / 2), unreal.Rotator(0, 0, 0),
                     V(SUTUN_CAP / 50, SUTUN_CAP / 50, boy / 100), m_sutun)
        mi_k = ornek("MI_Kure_" + ad, m_kure, vektorler={"Renk": renk})
        # kure yuvasinda parlayan ince disk
        halka = koy_mesh("Halka_" + ad, silindir, V(x, y, cz + SUTUN_BOY + 1), unreal.Rotator(0, 0, 0),
                         V(SUTUN_CAP * 0.8 / 50, SUTUN_CAP * 0.8 / 50, 0.02), mi_k)
        carpisma_yok(halka)
        k = koy_mesh("Kure_" + ad, kure, V(x, y, kure_z), unreal.Rotator(0, 0, 0),
                     V(KURE_CAP / 50, KURE_CAP / 50, KURE_CAP / 50), mi_k)
        carpisma_yok(k)
        isik = eas.spawn_actor_from_class(unreal.PointLight, V(x, y, kure_z), unreal.Rotator(0, 0, 0))
        isik.set_actor_label(ON_EK + "Isik_" + ad)
        isik.set_folder_path("ElementSahasi")
        lc = isik.point_light_component
        lc.set_light_color(renk)
        lc.set_intensity(8000.0)
        lc.set_attenuation_radius(1800.0)
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
        mi_c = ornek("MI_Isin_%s_%s" % (ad1, ad2), m_isin, {"Uzunluk": Li, "Parlaklik": 12.0}, ortak)
        mi_p = ornek("MI_IsinParilti_%s_%s" % (ad1, ad2), m_isin, {"Uzunluk": Li, "Parlaklik": 1.5}, ortak)
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
            mi_z = ornek("MI_Zemin_%s_%s" % (ad1, ad2), m_isin, {"Uzunluk": Li, "Parlaklik": 4.0}, ortak)
            z = koy_mesh("Zemin_%s_%s" % (ad1, ad2), kup, V((bx + ex) / 2, (by + ey) / 2, cz + 2),
                         unreal.Rotator(0, 0, math.degrees(math.atan2(dy, dx))),
                         V(Li / 100, CIZGI_EN / 100, 0.02), mi_z)
            carpisma_yok(z)
            z.static_mesh_component.set_editor_property("cast_shadow", False)

    les.save_current_level()
    log("TAMAM - Element sahasi kuruldu. Ayarlar dosyanin basinda (SAHA_BOY, SAHA_EN, SAHA_DONUS...).")


calistir()
