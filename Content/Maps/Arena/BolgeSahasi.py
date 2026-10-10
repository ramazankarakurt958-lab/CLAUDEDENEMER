# Unreal Engine 5 - Dort element bolgesi (referans gorsele gore):
#   Ates: komurlesmis tas + lav catlaklari, alevler, kivilcim, duman, lav kayalari
#   Su:   buz kaplamali tas, buz kristalleri, selaleler
#   Toprak: yosun/orman zemini, agaclar, yosunlu kayalar
#   Hava: beyaz mermer, sis bulutlari, havada asili kayalar
# Ayrica: cevrede ucan adalar, koprulerde mesaleler, arenanin altinda bulut denizi.
# Once ElementSahasi.py calismis olmali: bolgeler kurelerin bulundugu ceyreklere gore boyanir.
# Calistirma (Output Log -> Python):
#   exec(open(unreal.Paths.project_content_dir() + "Maps/Arena/BolgeSahasi.py", encoding="utf-8").read())
# Tekrar calistirilabilir: once eski "BS_" nesnelerini siler.
import math
import os
import random

import unreal

# ElementSahasi.py'deki yardimci fonksiyonlari yukle (sahneyi kurmadan)
SADECE_YARDIMCI = True
exec(open(unreal.Paths.project_content_dir() + "Maps/Arena/ElementSahasi.py", encoding="utf-8").read())
SADECE_YARDIMCI = False

# ---------------- AYARLAR ----------------
KLASOR = "/Game/MAPS/ARENA/Bolgeler"
ON_EK = "BS_"
TOHUM = 7                      # ayni tohum = ayni yerlesim; degistirirsen dekor yerleri degisir
ARENA_MALZEMESI = True         # arenayi bolge renklerine boya
BOLGE_GUCU = 1.0               # 0 = arena oldugu gibi, 1 = tam bolge gorunumu
BOLGE_GECIS = 1500.0           # cm - bolgeler arasi yumusak gecis genisligi
ORTA_YARICAP = 2300.0          # cm - orta platform bolge boyasindan etkilenmez
LAV_GUCU = 6.0                 # lav catlaklarinin parlakligi

ADA_SAYISI = 28
ADA_HALKA = (7500.0, 18000.0)  # cm - merkezden uzaklik
ADA_YUKSEKLIK = (-4000.0, 2500.0)
ADA_OLCEK = (5.0, 20.0)        # model yaricapi 1 m -> 5..20 m
UCAN_KAYA_SAYISI = 24

DEKOR = {                      # bolge basina adet
    "Ates":   {"alev": 8, "kivilcim": 4, "duman": 3, "lav_kaya": 8, "isik": 4},
    "Su":     {"kristal": 12, "selale": 4, "isik": 3},
    "Toprak": {"agac": 10, "kaya": 12},
    "Hava":   {"sis": 3, "esinti": 4, "ucan_kaya": 8},
}
MESALELER = True
BULUT_DENIZI = True
TRIBUN_HALKA = (2800.0, 4700.0)  # cm - dekorlarin konacagi tribun halkasi

PAKET = {
    "alev":     ["/Game/Vefects/Free_Fire/Shared/Particles/NS_Fire_Floor_01",
                 "/Game/Vefects/Free_Fire/Shared/Particles/NS_Fire_Medium", "/Game/NiagaraExamples/FX_Misc/NS_Fire"],
    "mesale":   ["/Game/Vefects/Free_Fire/Shared/Particles/NS_Fire_Small", "/Game/NiagaraExamples/FX_Misc/NS_Fire"],
    "kivilcim": ["/Game/NiagaraExamples/FX_Sparks/NS_Spark_Continuous"],
    "duman":    ["/Game/NiagaraExamples/FX_Smoke/NS_Smoke_Plume", "/Game/NiagaraExamples/FX_Smoke/NS_Chimney_Smoke"],
    "sis":      ["/Game/NiagaraExamples/FX_Fog/BP_FogBankVolume"],
}
AGAC = "/Game/MAPS/Asetler/island_tree_01"
KAYALAR = "/Game/MAPS/Asetler/rock_moss_set_01"
DOKU = {
    "orman": ("/Game/MAPS/Asetler/forest_ground_04", "diff"),
    "yosun": ("/Game/MAPS/Asetler/mossy_stone_wall", "diff"),
    "buz":   ("/Game/MAPS/Asetler/ice001", "color"),
    "mermer": ("/Game/MAPS/Asetler/marble_01", "diff"),
}
# -----------------------------------------

rnd = random.Random(TOHUM)


# ---------- malzeme yardimcilari ----------
def sabit1(m, deger, x, y):
    e = ifade(m, unreal.MaterialExpressionConstant, x, y)
    e.set_editor_property("r", deger)
    return e


def sabit3(m, rgb, x, y):
    e = ifade(m, unreal.MaterialExpressionConstant3Vector, x, y)
    e.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1))
    return e


def maske(m, kaynak, kanallar, x, y, cikis=""):
    e = ifade(m, unreal.MaterialExpressionComponentMask, x, y)
    for k in "rgba":
        e.set_editor_property(k, k in kanallar)
    bagla(kaynak, cikis, e, "")
    return e


def karistir(m, a, b, alfa, x, y):
    """lerp(a, b, alfa); alfa sayi ya da ifade olabilir."""
    e = ifade(m, unreal.MaterialExpressionLinearInterpolate, x, y)
    bagla(a, "", e, "A")
    bagla(b, "", e, "B")
    if isinstance(alfa, (int, float)):
        e.set_editor_property("const_alpha", float(alfa))
    else:
        bagla(alfa, "", e, "Alpha")
    return e


def doyur(m, kaynak, x, y):
    return tek(m, unreal.MaterialExpressionSaturate, kaynak, x, y)


def dunya_baglami(m, x, y):
    """Dunya-hizali doku koordinatlari: ust yuzeyler XY'den, yanlar (X+Y, Z)'den. UV gerektirmez."""
    wp = ifade(m, unreal.MaterialExpressionWorldPosition, x, y)
    xy = maske(m, wp, "rg", x + 200, y)
    yan = ifade(m, unreal.MaterialExpressionAppendVector, x + 400, y + 150)
    bagla(iki(m, unreal.MaterialExpressionAdd, maske(m, wp, "r", x + 200, y + 100), maske(m, wp, "g", x + 200, y + 200),
              x + 300, y + 150), "", yan, "A")
    bagla(maske(m, wp, "b", x + 200, y + 300), "", yan, "B")
    nz = maske(m, ifade(m, unreal.MaterialExpressionVertexNormalWS, x, y + 450), "b", x + 200, y + 450)
    ust = doyur(m, sabit_carp(m, sabit_ekle(m, nz, "", -0.45, x + 350, y + 450), "", 4.0, x + 500, y + 450), x + 650, y + 450)
    return {"wp": wp, "xy": xy, "yan": yan, "ust": ust}


def dunya_ornek(m, ctx, t, tekrar, x, y, sadece=None):
    """Dokuyu dunya koordinatlariyla ornekle (tekrar = cm cinsinden bir doku boyu)."""
    k = 1.0 / tekrar
    ust = doku_ornegi(m, t, sabit_carp(m, ctx["xy"], "", k, x, y), x + 150, y) if sadece != "yan" else None
    yan = doku_ornegi(m, t, sabit_carp(m, ctx["yan"], "", k, x, y + 200), x + 150, y + 200) if sadece != "ust" else None
    if ust and yan:
        return karistir(m, yan, ust, ctx["ust"], x + 400, y + 100)
    return ust or yan


def katman_doku(ad):
    klasor, ipucu = DOKU[ad]
    return klasorden_doku(klasor, ipucu)


def lav_catlak(m, ctx, gur, guc, x, y):
    """Gurultuden esiklenmis parlak catlaklar (yavasca akan)."""
    if not gur:
        return None
    ust = doku_ornegi(m, gur, kaydir(m, sabit_carp(m, ctx["xy"], "", 1 / 900.0, x, y), 0.01, 0.006, x + 100, y), x + 250, y)
    yan = doku_ornegi(m, gur, kaydir(m, sabit_carp(m, ctx["yan"], "", 1 / 900.0, x, y + 200), 0.0, 0.015, x + 100, y + 200),
                      x + 250, y + 200)
    n = karistir(m, yan, ust, ctx["ust"], x + 450, y + 100)
    n = maske(m, n, "r", x + 550, y + 100)
    c = doyur(m, sabit_carp(m, sabit_ekle(m, n, "", -0.55, x + 600, y + 100), "", 5.0, x + 750, y + 100), x + 900, y + 100)
    c = carp(m, c, c, x + 1050, y + 100)
    renk = carp(m, sabit3(m, (1.0, 0.28, 0.04), x + 1050, y + 250), guc, x + 1200, y + 250)
    return carp(m, c, renk, x + 1350, y + 100)


def bolge_gorunumu(m, ad, ctx, B, gur, x, y):
    """Bir bolgenin (taban rengi, puruzluluk, isima) ifadeleri."""
    if ad == "Ates":
        taban = carp(m, B, sabit3(m, (0.30, 0.17, 0.13), x, y + 100), x + 200, y)
        return taban, sabit1(m, 0.85, x, y + 200), lav_catlak(m, ctx, gur, skaler(m, "LavGucu", LAV_GUCU, x, y + 300), x, y + 400)
    if ad == "Su":
        buz = katman_doku("buz")
        soguk = carp(m, B, sabit3(m, (0.55, 0.72, 0.95), x, y + 100), x + 200, y)
        if buz:
            b = carp(m, dunya_ornek(m, ctx, buz, 500.0, x, y + 300), sabit3(m, (0.75, 0.9, 1.15), x, y + 600), x + 600, y + 300)
            taban = karistir(m, soguk, b, 0.6, x + 800, y)
            pirilti = tek(m, unreal.MaterialExpressionSaturate,
                          sabit_carp(m, sabit_ekle(m, b, "", -0.75, x + 800, y + 400), "", 3.0, x + 950, y + 400), x + 1100, y + 400)
            isima = carp(m, maske(m, pirilti, "b", x + 1200, y + 400), sabit3(m, (0.05, 0.35, 1.0), x + 1200, y + 550),
                         x + 1350, y + 400)
        else:
            taban, isima = soguk, None
        return taban, sabit1(m, 0.18, x, y + 200), isima
    if ad == "Toprak":
        orman, yosun = katman_doku("orman"), katman_doku("yosun")
        ust = dunya_ornek(m, ctx, orman, 350.0, x, y + 300, "ust") if orman else sabit3(m, (0.2, 0.3, 0.1), x, y + 300)
        yan = dunya_ornek(m, ctx, yosun, 400.0, x, y + 600, "yan") if yosun else sabit3(m, (0.25, 0.3, 0.2), x, y + 600)
        kat = carp(m, karistir(m, yan, ust, ctx["ust"], x + 500, y + 400), sabit3(m, (0.85, 1.05, 0.75), x + 500, y + 600),
                   x + 700, y + 400)
        return karistir(m, B, kat, 0.7, x + 900, y), sabit1(m, 0.92, x, y + 200), None
    # Hava
    mermer = katman_doku("mermer")
    acik = carp(m, B, sabit3(m, (1.25, 1.3, 1.4), x, y + 100), x + 200, y)
    if mermer:
        mm = carp(m, dunya_ornek(m, ctx, mermer, 600.0, x, y + 300), sabit3(m, (0.95, 0.98, 1.05), x, y + 600), x + 600, y + 300)
        acik = karistir(m, acik, mm, 0.55, x + 800, y)
    return acik, sabit1(m, 0.45, x, y + 200), None


def agirlikli_toplam(m, parcalar, x, y):
    """sum(agirlik * deger); deger None olanlar atlanir."""
    toplam = None
    for i, (w, v) in enumerate(parcalar):
        if v is None:
            continue
        p = carp(m, w, v, x, y + i * 120)
        toplam = p if toplam is None else iki(m, unreal.MaterialExpressionAdd, toplam, p, x + 200, y + i * 120)
    return toplam


def arena_dokulari():
    renk = normal = orm = None
    for yol in eal.list_assets("/Game/Maps/Arena/Varliklar", recursive=True, include_folder=False):
        a = eal.load_asset(yol)
        if isinstance(a, unreal.Texture2D):
            if a.get_editor_property("compression_settings") == unreal.TextureCompressionSettings.TC_NORMALMAP:
                normal = a
            elif a.get_editor_property("srgb"):
                renk = a
            else:
                orm = a
    return renk, normal, orm


def arena_bolge_malzemesi(ceyrekler, merkez, gur):
    """Arenanin kendi dokusu + ceyreklere gore bolge gorunumu (orta platform haric)."""
    renk_t, normal_t, orm_t = arena_dokulari()
    if not renk_t:
        log("   UYARI: arena dokulari bulunamadi, arena boyanmadi")
        return None
    m = yeni_malzeme("M_ArenaBolge")
    B = doku_ornegi(m, renk_t, None, -3000, -600)
    detay = doku_yukle(["/Game/Maps/Arena/Detay/T_ArenaDetay_D"])
    if detay:  # ArenaDetay.py'deki yakin plan tas detayi korunsun
        d = doku_ornegi(m, detay, uv(m, 150.0, -3300, -400), -3000, -400)
        B = carp(m, B, karistir(m, sabit1(m, 1.0, -2800, -300), sabit_carp(m, d, "R", 2.0, -2800, -400), 0.7, -2600, -400),
                 -2400, -600)
    orm = doku_ornegi(m, orm_t, None, -3000, 1400) if orm_t else None
    ctx = dunya_baglami(m, -3600, 200)
    # ceyrek agirliklari (oyun alani eksenlerine gore, yumusak gecisli)
    P = iki(m, unreal.MaterialExpressionSubtract, ctx["wp"],
            vektor(m, "Merkez", unreal.LinearColor(merkez[0], merkez[1], merkez[2], 0), -3600, 900), -3300, 900)
    a = math.radians(SAHA_DONUS)
    ex = sabit3(m, (math.cos(a), math.sin(a), 0), -3300, 1000)
    ey = sabit3(m, (-math.sin(a), math.cos(a), 0), -3300, 1100)
    wx = doyur(m, sabit_ekle(m, sabit_carp(m, iki(m, unreal.MaterialExpressionDotProduct, P, ex, -3100, 1000), "",
                                           1.0 / BOLGE_GECIS, -2950, 1000), "", 0.5, -2800, 1000), -2650, 1000)
    wy = doyur(m, sabit_ekle(m, sabit_carp(m, iki(m, unreal.MaterialExpressionDotProduct, P, ey, -3100, 1100), "",
                                           1.0 / BOLGE_GECIS, -2950, 1100), "", 0.5, -2800, 1100), -2650, 1100)
    wx_ = tek(m, unreal.MaterialExpressionOneMinus, wx, -2500, 1000)
    wy_ = tek(m, unreal.MaterialExpressionOneMinus, wy, -2500, 1100)
    pxy = maske(m, P, "rg", -3100, 1250)
    r = tek(m, unreal.MaterialExpressionSquareRoot, iki(m, unreal.MaterialExpressionDotProduct, pxy, pxy, -2950, 1250), -2800, 1250)
    h = doyur(m, sabit_carp(m, sabit_ekle(m, r, "", -ORTA_YARICAP, -2650, 1250), "", 1 / 600.0, -2500, 1250), -2350, 1250)
    h = carp(m, h, skaler(m, "BolgeGucu", BOLGE_GUCU, -2350, 1350), -2200, 1250)

    tabanlar, puruzler, isimalar = [], [], []
    for i, (ad, (sx, sy)) in enumerate(ceyrekler.items()):
        w = carp(m, wx if sx > 0 else wx_, wy if sy > 0 else wy_, -2300, 1500 + i * 120)
        t, p, e = bolge_gorunumu(m, ad, ctx, B, gur, -2000, -1600 + i * 1000)
        tabanlar.append((w, t))
        puruzler.append((w, p))
        isimalar.append((w, e))
    taban = karistir(m, B, agirlikli_toplam(m, tabanlar, 0, -800), h, 400, -800)
    mel.connect_material_property(taban, "", unreal.MaterialProperty.MP_BASE_COLOR)
    puruz_arena = maske(m, orm, "g", -2700, 1400) if orm else sabit1(m, 0.8, -2700, 1400)
    puruz = karistir(m, puruz_arena, agirlikli_toplam(m, puruzler, 0, 0), h, 400, 0)
    mel.connect_material_property(puruz, "", unreal.MaterialProperty.MP_ROUGHNESS)
    isima = agirlikli_toplam(m, isimalar, 0, 600)
    if isima is not None:
        mel.connect_material_property(carp(m, isima, h, 400, 600), "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    if orm:
        mel.connect_material_property(maske(m, orm, "r", -2700, 1500), "", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    if normal_t:
        mel.connect_material_property(doku_ornegi(m, normal_t, None, -3000, 1700), "RGB", unreal.MaterialProperty.MP_NORMAL)
    kaydet(m)
    return m


def ada_malzemesi(gur):
    """Ucan ada / dekor kayasi: ust yuzey cimen-orman (ya da acik tas), yanlar yosunlu kaya. UV gerektirmez."""
    m = yeni_malzeme("M_Ada")
    ctx = dunya_baglami(m, -2400, 0)
    orman, yosun, mermer = katman_doku("orman"), katman_doku("yosun"), katman_doku("mermer")
    ust = dunya_ornek(m, ctx, orman, 400.0, -1800, -400, "ust") if orman else sabit3(m, (0.2, 0.3, 0.1), -1800, -400)
    if mermer:
        ust = karistir(m, ust, dunya_ornek(m, ctx, mermer, 600.0, -1800, -200, "ust"),
                       skaler(m, "AcikTepe", 0.0, -1500, -150), -1300, -300)
    yan = dunya_ornek(m, ctx, yosun, 500.0, -1800, 200, "yan") if yosun else sabit3(m, (0.3, 0.3, 0.28), -1800, 200)
    ust = carp(m, ust, vektor(m, "TepeRenk", unreal.LinearColor(1, 1, 1, 1), -1300, -100), -1100, -300)
    yan = carp(m, yan, vektor(m, "YanRenk", unreal.LinearColor(1, 1, 1, 1), -1300, 300), -1100, 200)
    keskin = doyur(m, sabit_carp(m, sabit_ekle(m, ctx["ust"], "", -0.5, -1300, 500), "", 3.0, -1150, 500), -1000, 500)
    mel.connect_material_property(karistir(m, yan, ust, keskin, -800, 0), "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(skaler(m, "Puruzluluk", 0.9, -800, 300), "", unreal.MaterialProperty.MP_ROUGHNESS)
    lav = lav_catlak(m, ctx, gur, skaler(m, "LavGucu", 0.0, -2400, 900), -2400, 700)
    if lav:
        mel.connect_material_property(carp(m, lav, tek(m, unreal.MaterialExpressionOneMinus, keskin, -800, 800), -600, 700),
                                      "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    kaydet(m)
    return m


def buz_malzemesi():
    """Buz kristali: parlak, mavi, kenarlarda isildayan."""
    m = yeni_malzeme("M_Buz")
    ctx = dunya_baglami(m, -2000, 0)
    buz = katman_doku("buz")
    renk = sabit3(m, (0.30, 0.55, 0.85), -900, -300)
    if buz:
        renk = carp(m, dunya_ornek(m, ctx, buz, 300.0, -1500, -400), renk, -900, -400)
    mel.connect_material_property(renk, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(sabit1(m, 0.06, -900, 0), "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(sabit1(m, 0.8, -900, 100), "", unreal.MaterialProperty.MP_SPECULAR)
    kenar = carp(m, fresnel(m, 3.0, -900, 300), sabit3(m, (0.1, 0.55, 1.6), -900, 450), -700, 300)
    mel.connect_material_property(kenar, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    kaydet(m)
    return m


def selale_malzemesi(gur):
    """Asagi akan su perdesi: saydam, kenarlari ve alti yumusak."""
    m = yeni_malzeme("M_Selale", unreal.MaterialShadingModel.MSM_UNLIT, unreal.BlendMode.BLEND_TRANSLUCENT, True)
    wp = ifade(m, unreal.MaterialExpressionWorldPosition, -2000, 0)
    tc = ifade(m, unreal.MaterialExpressionTextureCoordinate, -2000, 300)
    yatay = maske(m, tc, "g", -1800, 300)
    zaman = ifade(m, unreal.MaterialExpressionTime, -2000, 500)
    akis = iki(m, unreal.MaterialExpressionAdd, sabit_carp(m, maske(m, wp, "b", -1800, 0), "", 1 / 500.0, -1650, 0),
               sabit_carp(m, zaman, "", 1.3, -1650, 500), -1500, 200)
    ek = ifade(m, unreal.MaterialExpressionAppendVector, -1350, 300)
    bagla(sabit_carp(m, yatay, "", 4.0, -1600, 300), "", ek, "A")
    bagla(akis, "", ek, "B")
    if gur:
        n = maske(m, doku_ornegi(m, gur, ek, -1200, 300), "r", -1000, 300)
    else:
        n = sabit1(m, 0.6, -1000, 300)
    kenar = doyur(m, sabit_carp(m, carp(m, yatay, tek(m, unreal.MaterialExpressionOneMinus, yatay, -1600, 450), -1450, 450),
                                "", 6.0, -1300, 450), -1150, 450)
    # alttan sonme: nesnenin alt ucuna yaklastikca saydamlasir
    obj = ifade(m, unreal.MaterialExpressionObjectPositionWS, -2000, 700)
    sinir = ifade(m, unreal.MaterialExpressionObjectBounds, -2000, 850)
    boy = iki(m, unreal.MaterialExpressionMax, iki(m, unreal.MaterialExpressionMax, maske(m, sinir, "r", -1850, 800),
                                                   maske(m, sinir, "g", -1850, 850), -1750, 820), maske(m, sinir, "b", -1850, 900),
              -1650, 850)  # en uzun kenar = selale boyu
    alt = iki(m, unreal.MaterialExpressionSubtract, maske(m, obj, "b", -1800, 700), sabit_carp(m, boy, "", 0.5, -1650, 850),
              -1500, 700)
    alttan = doyur(m, iki(m, unreal.MaterialExpressionDivide, iki(m, unreal.MaterialExpressionSubtract, maske(m, wp, "b", -1500, 600),
                                                                   alt, -1350, 650), sabit_carp(m, boy, "", 0.35, -1500, 900),
                          -1200, 700), -1050, 700)
    opak = carp(m, carp(m, sabit_ekle(m, sabit_carp(m, n, "", 0.8, -850, 300), "", 0.25, -700, 300), kenar, -550, 350),
                alttan, -400, 400)
    mel.connect_material_property(sabit_carp(m, opak, "", 0.85, -250, 400), "", unreal.MaterialProperty.MP_OPACITY)
    renk = carp(m, sabit3(m, (0.55, 0.8, 1.0), -700, 0), sabit_ekle(m, n, "", 0.6, -850, 100), -500, 0)
    mel.connect_material_property(sabit_carp(m, renk, "", 1.6, -300, 0), "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    kaydet(m)
    return m


# ---------- sahne yardimcilari ----------
def mesh_listesi(klasor):
    if not eal.does_directory_exist(klasor):
        return []
    return [a for a in (eal.load_asset(y) for y in eal.list_assets(klasor, recursive=True, include_folder=False))
            if isinstance(a, unreal.StaticMesh)]


def glb_mesh(dosya_adi, hedef):
    """Kaynak klasorundeki bir GLB'yi bir kez ice aktarir ve mesh'ini dondurur."""
    m = mesh_listesi(hedef)
    if m:
        return m[0]
    dosya = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir()),
                         "Maps", "Arena", "Kaynak", dosya_adi)
    if not os.path.isfile(dosya):
        log("   UYARI: %s yok" % dosya)
        return None
    t = unreal.AssetImportTask()
    for k, v in (("filename", dosya), ("destination_path", hedef), ("automated", True), ("replace_existing", True), ("save", True)):
        t.set_editor_property(k, v)
    tools.import_asset_tasks([t])
    m = mesh_listesi(hedef)
    if not m:
        return None
    try:
        ns = m[0].get_editor_property("nanite_settings")
        ns.set_editor_property("enabled", True)
        m[0].set_editor_property("nanite_settings", ns)
        eal.save_loaded_asset(m[0])
    except Exception as e:
        log("   Nanite acilamadi (onemsiz): %s" % e)
    return m[0]


def ilk_varlik(yollar):
    for y in yollar:
        if eal.does_asset_exist(y):
            return eal.load_asset(y)
    return None


def etiketle(a, ad):
    a.set_actor_label(ON_EK + ad)
    a.set_folder_path("Bolgeler")
    return a


def efekt(paket, ad, konum, olcek=1.0, renk=None):
    v = ilk_varlik(PAKET.get(paket, []))
    if not v:
        return None
    a = eas.spawn_actor_from_object(v, konum, unreal.Rotator(0, 0, rnd.uniform(0, 360)))
    if not a:
        return None
    etiketle(a, ad)
    a.set_actor_scale3d(V(olcek, olcek, olcek))
    if renk is not None:
        nc = a.get_component_by_class(unreal.NiagaraComponent)
        if nc:
            for d in ("Color", "User.Color", "Colour"):
                try:
                    nc.set_variable_linear_color(d, renk)
                except Exception:
                    pass
    return a


def isik(ad, konum, renk, guc, yaricap):
    a = eas.spawn_actor_from_class(unreal.PointLight, konum, unreal.Rotator(0, 0, 0))
    etiketle(a, ad)
    lc = a.point_light_component
    lc.set_light_color(renk)
    lc.set_intensity(guc)
    lc.set_attenuation_radius(yaricap)
    lc.set_cast_shadows(False)
    return a


def kaya_koy(ad, mesh, konum, olcek, malzeme=None, egim=0.0):
    a = koy_mesh(ad, mesh, konum, unreal.Rotator(rnd.uniform(-egim, egim), rnd.uniform(-egim, egim), rnd.uniform(0, 360)),
                 olcek, malzeme)
    a.set_folder_path("Bolgeler")
    return a


def isin_at(x, y, ust, alt):
    """Yukaridan asagi isin; (nokta, normal_z) ya da None."""
    try:
        hit = unreal.SystemLibrary.line_trace_single(
            ues.get_editor_world(), V(x, y, ust), V(x, y, alt),
            getattr(unreal.TraceTypeQuery, "ECC_VISIBILITY", unreal.TraceTypeQuery.TRACE_TYPE_QUERY1),
            True, [], unreal.DrawDebugTrace.NONE, True)
        if not hit:
            return None
        alanlar = hit.to_tuple()
        if not alanlar[0]:
            return None
        vek = [v for v in alanlar if isinstance(v, unreal.Vector)]
        return vek[0], (vek[3].z if len(vek) > 3 else 1.0)
    except Exception:
        return None


# ---------- bolge geometrisi ----------
def bolge_ceyrekleri(cx, cy):
    """Her elementin hangi ceyrekte oldugu (oyun alani eksenlerine gore isaretler), kure aktorlerinden."""
    a = math.radians(SAHA_DONUS)
    ca, sa = math.cos(a), math.sin(a)
    sonuc = {}
    for akt in eas.get_all_level_actors():
        lb = akt.get_actor_label()
        if lb.startswith("ES_Kure_"):
            p = akt.get_actor_location()
            dx, dy = p.x - cx, p.y - cy
            lx, ly = dx * ca + dy * sa, -dx * sa + dy * ca
            sonuc[lb[len("ES_Kure_"):]] = (1 if lx > 0 else -1, 1 if ly > 0 else -1)
    if len(sonuc) != 4 or len(set(sonuc.values())) != 4:
        log("   UYARI: ES_Kure aktorleri bulunamadi; ElementSahasi.py sirasi kullaniliyor")
        isaret = [(1, 1), (1, -1), (-1, -1), (-1, 1)]
        sonuc = {ad: isaret[i] for i, (ad, _) in enumerate(ELEMENTLER)}
    return sonuc


def dunya_noktasi(cx, cy, lx, ly):
    a = math.radians(SAHA_DONUS)
    return cx + lx * math.cos(a) - ly * math.sin(a), cy + lx * math.sin(a) + ly * math.cos(a)


def tribun_noktalari(cx, cy, cz, isaret, adet, yassi=0.7, deneme=40):
    """Bir ceyrekteki tribun halkasinda, yuzey uzerinde rastgele noktalar (kopru eksenlerinden uzak)."""
    sx, sy = isaret
    temel = math.atan2(sy, sx)
    sonuc = []
    for _ in range(adet * deneme):
        if len(sonuc) >= adet:
            break
        a = temel + math.radians(rnd.uniform(-36, 36))
        r = rnd.uniform(*TRIBUN_HALKA)
        x, y = dunya_noktasi(cx, cy, r * math.cos(a), r * math.sin(a))
        h = isin_at(x, y, cz + 6000, cz - 3000)
        if not h or h[1] < yassi or not (cz - 800 < h[0].z < cz + 3500):
            continue
        if any(math.hypot(h[0].x - p.x, h[0].y - p.y) < 450 for p in sonuc):
            continue
        sonuc.append(h[0])
    return sonuc


def dis_kenar_noktalari(cx, cy, cz, isaret, adet):
    """Ceyregin dis duvar kenari (selaleler icin): disaridan iceri ilerleyip ilk yuzeyi bulur."""
    sx, sy = isaret
    temel = math.atan2(sy, sx)
    sonuc = []
    for i in range(adet):
        a = temel + math.radians(-28 + 56 * (i + 0.5) / adet)
        for r in range(5800, 3000, -100):
            x, y = dunya_noktasi(cx, cy, r * math.cos(a), r * math.sin(a))
            h = isin_at(x, y, cz + 6000, cz - 3000)
            if h and cz - 500 < h[0].z < cz + 4000:
                sonuc.append((h[0], a))
                break
    return sonuc


# ---------- kurulum adimlari ----------
def ceyrek_adi(ceyrek, lx, ly):
    for e, (sx, sy) in ceyrek.items():
        if (lx > 0) == (sx > 0) and (ly > 0) == (sy > 0):
            return e
    return "Hava"


def arena_aktoru():
    for a in eas.get_all_level_actors():
        if isinstance(a, unreal.StaticMeshActor):
            sm = a.static_mesh_component.get_editor_property("static_mesh")
            if sm and "arena_game" in sm.get_name().lower():
                return a
    return None


def ucan_adalar(cx, cy, cz, ceyrek, mi_ada, agac):
    modeller = [glb_mesh("SM_UcanAda_%d.glb" % i, KLASOR + "/Ada%d" % i) for i in (1, 2, 3)]
    modeller = [m for m in modeller if m]
    if not modeller:
        log("   UYARI: ucan ada modelleri yok, adalar atlandi")
        return
    for k in range(ADA_SAYISI):
        a = 2 * math.pi * (k + rnd.uniform(0.15, 0.85)) / ADA_SAYISI
        oran = rnd.random()
        r = ADA_HALKA[0] + (ADA_HALKA[1] - ADA_HALKA[0]) * oran
        s = ADA_OLCEK[0] + (ADA_OLCEK[1] - ADA_OLCEK[0]) * (0.3 * rnd.random() + 0.7 * oran)
        lx, ly = r * math.cos(a), r * math.sin(a)
        x, y = dunya_noktasi(cx, cy, lx, ly)
        z = cz + rnd.uniform(*ADA_YUKSEKLIK)
        ad = ceyrek_adi(ceyrek, lx, ly)
        kaya_koy("Ada_%s_%d" % (ad, k), rnd.choice(modeller), V(x, y, z), V(s, s, s * rnd.uniform(0.8, 1.3)), mi_ada[ad], 4)
        tepe = z + 0.09 * s * 100
        if ad == "Toprak" and agac:
            for j in range(rnd.randint(1, 3)):
                ox, oy = rnd.uniform(-0.45, 0.45) * s * 100, rnd.uniform(-0.45, 0.45) * s * 100
                ao = max(0.5, min(1.6, s / 10.0)) * rnd.uniform(0.8, 1.2)
                kaya_koy("AdaAgac_%d_%d" % (k, j), agac, V(x + ox, y + oy, tepe - 20), V(ao, ao, ao))
        elif ad == "Ates" and rnd.random() < 0.6:
            efekt("alev", "AdaAlev_%d" % k, V(x, y, tepe), max(0.6, s / 10.0))
    log("   %d ucan ada yerlestirildi" % ADA_SAYISI)


def ucan_kayalar(cx, cy, cz, ceyrek, mi_ada, kayalar):
    if not kayalar:
        return
    for k in range(UCAN_KAYA_SAYISI):
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(5900, 9500)
        lx, ly = r * math.cos(a), r * math.sin(a)
        x, y = dunya_noktasi(cx, cy, lx, ly)
        ad = ceyrek_adi(ceyrek, lx, ly)
        s = rnd.uniform(2.0, 6.0)
        kaya_koy("UcanKaya_%d" % k, rnd.choice(kayalar), V(x, y, cz + rnd.uniform(-2500, 3500)), V(s, s, s),
                 None if ad == "Toprak" else mi_ada[ad], 180)


def ates_bolgesi(cx, cy, cz, isaret, mi_lav, kayalar):
    d = DEKOR["Ates"]
    for i, p in enumerate(tribun_noktalari(cx, cy, cz, isaret, d["alev"])):
        efekt("alev", "Alev_%d" % i, p, rnd.uniform(0.8, 1.4))
    for i, p in enumerate(tribun_noktalari(cx, cy, cz, isaret, d["kivilcim"])):
        efekt("kivilcim", "Kivilcim_%d" % i, p, 1.0)
    for i, p in enumerate(tribun_noktalari(cx, cy, cz, isaret, d["duman"])):
        efekt("duman", "Duman_%d" % i, p, rnd.uniform(1.0, 1.8))
    if kayalar:
        for i, p in enumerate(tribun_noktalari(cx, cy, cz, isaret, d["lav_kaya"], 0.5)):
            s = rnd.uniform(1.5, 3.0)
            kaya_koy("LavKaya_%d" % i, rnd.choice(kayalar), V(p.x, p.y, p.z - 30), V(s, s, s * rnd.uniform(1.5, 3.0)), mi_lav, 12)
    for i, p in enumerate(tribun_noktalari(cx, cy, cz, isaret, d["isik"])):
        isik("AtesIsik_%d" % i, V(p.x, p.y, p.z + 250), unreal.LinearColor(1.0, 0.35, 0.08, 1), 2500, 2500)


def su_bolgesi(cx, cy, cz, isaret, m_buz, m_selale, kayalar):
    d = DEKOR["Su"]
    if kayalar:
        for i, p in enumerate(tribun_noktalari(cx, cy, cz, isaret, d["kristal"], 0.5)):
            s = rnd.uniform(0.6, 1.4)
            kaya_koy("Kristal_%d" % i, rnd.choice(kayalar), V(p.x, p.y, p.z - 20), V(s, s, s * rnd.uniform(3.0, 5.0)), m_buz, 18)
    duzlem = eal.load_asset("/Engine/BasicShapes/Plane")
    for i, (p, a) in enumerate(dis_kenar_noktalari(cx, cy, cz, isaret, d["selale"])):
        boy, en = rnd.uniform(3000, 4500), rnd.uniform(500, 900)
        a_dunya = a + math.radians(SAHA_DONUS)
        disari = V(math.cos(a_dunya), math.sin(a_dunya), 0)
        dz = unreal.MathLibrary.make_rot_from_zx(disari, V(0, 0, 1))
        merkez = V(p.x + disari.x * 60, p.y + disari.y * 60, p.z - boy / 2 + 50)
        s = koy_mesh("Selale_%d" % i, duzlem, merkez, dz, V(boy / 100, en / 100, 1), m_selale)
        s.set_folder_path("Bolgeler")
        carpisma_yok(s)
        s.static_mesh_component.set_editor_property("cast_shadow", False)
        efekt("duman", "SelaleSis_%d" % i, V(merkez.x, merkez.y, p.z - boy + 200), 2.0, unreal.LinearColor(0.8, 0.9, 1.0, 1))
    for i, p in enumerate(tribun_noktalari(cx, cy, cz, isaret, d["isik"])):
        isik("SuIsik_%d" % i, V(p.x, p.y, p.z + 300), unreal.LinearColor(0.15, 0.5, 1.0, 1), 2000, 2500)


def toprak_bolgesi(cx, cy, cz, isaret, agac, kayalar):
    d = DEKOR["Toprak"]
    if agac:
        for i, p in enumerate(tribun_noktalari(cx, cy, cz, isaret, d["agac"], 0.8)):
            s = rnd.uniform(0.7, 1.2)
            kaya_koy("Agac_%d" % i, agac, V(p.x, p.y, p.z - 10), V(s, s, s))
    if kayalar:
        for i, p in enumerate(tribun_noktalari(cx, cy, cz, isaret, d["kaya"], 0.5)):
            s = rnd.uniform(0.8, 2.0)
            kaya_koy("YosunKaya_%d" % i, rnd.choice(kayalar), V(p.x, p.y, p.z - 15), V(s, s, s), None, 15)


def hava_bolgesi(cx, cy, cz, isaret, mi_hava, kayalar):
    d = DEKOR["Hava"]
    for i, (p, _) in enumerate(dis_kenar_noktalari(cx, cy, cz, isaret, d["sis"])):
        efekt("sis", "Sis_%d" % i, V(p.x, p.y, p.z - 300), 3.0)
    beyaz = unreal.LinearColor(0.9, 0.95, 1.0, 1)
    for i, p in enumerate(tribun_noktalari(cx, cy, cz, isaret, d["esinti"])):
        efekt("duman", "Esinti_%d" % i, p, rnd.uniform(1.2, 2.0), beyaz)
    if kayalar:
        for i, p in enumerate(tribun_noktalari(cx, cy, cz, isaret, d["ucan_kaya"], 0.3)):
            s = rnd.uniform(0.6, 1.5)
            kaya_koy("HavaKaya_%d" % i, rnd.choice(kayalar), V(p.x, p.y, p.z + rnd.uniform(400, 1400)), V(s, s, s), mi_hava, 180)


def mesaleler(cx, cy, cz):
    """Koprulerin iki yanina gotik mesaleler: kopru, dar (en < 9 m) yuzey olarak isinlarla bulunur."""
    gotik = (mesh_listesi("/Game/MAPS/ARENA/ElementSahasi/Gotik") or [None])[0]
    mi_s = ilk_varlik(["/Game/MAPS/ARENA/ElementSahasi/MI_Sutun_Ates", "/Game/MAPS/ARENA/ElementSahasi/M_ElementSutun"])
    n = 0
    for eksen in range(4):
        a = math.radians(SAHA_DONUS + 90 * eksen)
        ux, uy, vx, vy = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
        for r in range(2500, 5700, 650):
            orta = isin_at(cx + ux * r, cy + uy * r, cz + 3000, cz - 2000)
            if not orta or abs(orta[0].z - cz) > 600:
                continue
            kenar = []
            for yan in (1, -1):
                w = 0
                while w < 500:
                    h = isin_at(cx + ux * r + vx * yan * (w + 20), cy + uy * r + vy * yan * (w + 20), cz + 3000, cz - 2000)
                    if not h or abs(h[0].z - orta[0].z) > 80:
                        break
                    w += 20
                kenar.append(w)
            if min(kenar) >= 500 or min(kenar) < 60:  # kopru degil (genis alan) ya da cok dar
                continue
            for yan, w in zip((1, -1), kenar):
                x, y = cx + ux * r + vx * yan * (w - 35), cy + uy * r + vy * yan * (w - 35)
                if gotik:
                    m = koy_mesh("Mesale_%d" % n, gotik, V(x, y, orta[0].z), unreal.Rotator(0, 0, math.degrees(a)),
                                 V(0.2, 0.2, 0.2), mi_s)
                    m.set_folder_path("Bolgeler")
                ust = orta[0].z + (700 * 0.2 + 25 if gotik else 30)
                efekt("mesale", "MesaleAlev_%d" % n, V(x, y, ust), 0.3)
                isik("MesaleIsik_%d" % n, V(x, y, ust + 40), unreal.LinearColor(1.0, 0.55, 0.2, 1), 600, 700)
                n += 1
    log("   %d mesale" % n)


def bulut_denizi(cx, cy, cz):
    sis = next((a for a in eas.get_all_level_actors() if isinstance(a, unreal.ExponentialHeightFog)), None)
    if sis:
        sis.set_actor_location(V(cx, cy, cz - 4500), False, False)
        fc = sis.component
        for k, v in (("fog_density", 0.08), ("fog_height_falloff", 0.4), ("start_distance", 2500.0),
                     ("fog_max_opacity", 0.95), ("enable_volumetric_fog", False)):
            try:
                fc.set_editor_property(k, v)
            except Exception:
                pass
        for k in ("fog_inscattering_luminance", "fog_inscattering_color"):
            try:
                fc.set_editor_property(k, unreal.LinearColor(0.55, 0.65, 0.8, 1))
                break
            except Exception:
                pass
    for i in range(8):
        a = 2 * math.pi * i / 8 + rnd.uniform(-0.2, 0.2)
        r = rnd.uniform(3000, 11000)
        efekt("sis", "BulutKumesi_%d" % i, V(cx + r * math.cos(a), cy + r * math.sin(a), cz - rnd.uniform(3000, 4500)), 8.0)
    log("   bulut denizi (sis + sis kumeleri) ayarlandi")


def calistir_bolge():
    log("1/5 Malzemeler...")
    gur = doku_yukle(GURULTU_DOKULARI)
    m_ada = ada_malzemesi(gur)
    mi_ada = {
        "Ates":   ornek("MI_Ada_Ates", m_ada, {"LavGucu": LAV_GUCU, "AcikTepe": 0.0},
                        {"TepeRenk": unreal.LinearColor(0.25, 0.15, 0.12, 1), "YanRenk": unreal.LinearColor(0.32, 0.22, 0.2, 1)}),
        "Su":     ornek("MI_Ada_Su", m_ada, {"AcikTepe": 1.0},
                        {"TepeRenk": unreal.LinearColor(0.7, 0.85, 1.1, 1), "YanRenk": unreal.LinearColor(0.55, 0.68, 0.85, 1)}),
        "Toprak": ornek("MI_Ada_Toprak", m_ada, {"AcikTepe": 0.0},
                        {"TepeRenk": unreal.LinearColor(0.85, 1.05, 0.7, 1), "YanRenk": unreal.LinearColor(0.9, 0.9, 0.85, 1)}),
        "Hava":   ornek("MI_Ada_Hava", m_ada, {"AcikTepe": 1.0},
                        {"TepeRenk": unreal.LinearColor(1.1, 1.1, 1.15, 1), "YanRenk": unreal.LinearColor(1.0, 1.0, 1.05, 1)}),
    }
    mi_lav = ornek("MI_LavKaya", m_ada, {"LavGucu": LAV_GUCU * 1.5, "AcikTepe": 0.0},
                   {"TepeRenk": unreal.LinearColor(0.12, 0.07, 0.06, 1), "YanRenk": unreal.LinearColor(0.15, 0.09, 0.08, 1)})
    m_buz = buz_malzemesi()
    m_selale = selale_malzemesi(gur)

    log("2/5 Harita, merkez ve bolgeler...")
    haritayi_ac()
    cx, cy, cz = merkez_bul()
    cz = zemin_z(cx, cy, cz)
    eskileri_sil()
    ceyrek = bolge_ceyrekleri(cx, cy)
    log("   bolgeler: " + ", ".join("%s(%+d,%+d)" % (k, v[0], v[1]) for k, v in ceyrek.items()))
    agac = (mesh_listesi(AGAC) or [None])[0]
    kayalar = mesh_listesi(KAYALAR)
    if not agac:
        log("   UYARI: agac modeli yok (%s)" % AGAC)
    if not kayalar:
        log("   UYARI: kaya modelleri yok (%s)" % KAYALAR)

    if ARENA_MALZEMESI:
        log("3/5 Arena bolge malzemesi...")
        m_arena = arena_bolge_malzemesi(ceyrek, (cx, cy, cz), gur)
        arena = arena_aktoru()
        if m_arena and arena:
            c = arena.static_mesh_component
            for i in range(c.get_num_materials()):
                c.set_material(i, m_arena)

    log("4/5 Bolge dekorlari ve ucan adalar...")
    ates_bolgesi(cx, cy, cz, ceyrek["Ates"], mi_lav, kayalar)
    su_bolgesi(cx, cy, cz, ceyrek["Su"], m_buz, m_selale, kayalar)
    toprak_bolgesi(cx, cy, cz, ceyrek["Toprak"], agac, kayalar)
    hava_bolgesi(cx, cy, cz, ceyrek["Hava"], mi_ada["Hava"], kayalar)
    ucan_adalar(cx, cy, cz, ceyrek, mi_ada, agac)
    ucan_kayalar(cx, cy, cz, ceyrek, mi_ada, kayalar)

    log("5/5 Mesaleler ve bulut denizi...")
    if MESALELER:
        mesaleler(cx, cy, cz)
    if BULUT_DENIZI:
        bulut_denizi(cx, cy, cz)
    les.save_current_level()
    n = sum(1 for a in eas.get_all_level_actors() if a.get_actor_label().startswith(ON_EK))
    log("TAMAM - %d bolge nesnesi kuruldu. Ayarlar dosyanin basinda (DEKOR, ADA_SAYISI, BOLGE_GUCU...)." % n)


calistir_bolge()
