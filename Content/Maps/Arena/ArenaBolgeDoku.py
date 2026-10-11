# Unreal Engine 5 - Arenayi 4 element bolgesine gore boyar (referans resim dokuya yansitildi).
# Ates: komurlesmis tas + lav catlaklari, Su: buz mavisi, Toprak: yosunlu tas, Hava: beyaz mermer.
# Doku: Kaynak/T_ArenaBolge.jpg (araclar ile referans resimden uretildi). Arenanin normal/ORM dokulari ve
# ArenaDetay'in yakin plan tas detayi aynen kalir; sadece renk dokusu degisir.
# Maske: Kaynak/T_ArenaBolgeMaske.png  R=lav (isik verir, nabiz gibi atar), G=parlaklik (buz/mermer), B=su isiltisi,
#        A=su tribunu zemin bolgesi.
# Su tribunu zemini: yukari bakan yuzlere dunyaya hizali net tas levha (T_SuZemin_*), yuksek teraslarda ve kule
# tepelerinde parlayan/yansitan dalgali su birikintileri.
# Kaplamalar (Kaynak/T_ArenaKaplamaMaske.png R = hava, G = orman, B = ates): dunyaya hizali ucyonlu kesme tas, duvarlar dahil
# derzli kusursuz kaplama. Hava: cilali krem mermer (T_Mermer_D/N). Orman: asinmis gri tas (T_OrmanTas_D/N) + yukari
# bakan yuzlerde ve duvarlarda lekeli yosun (T_Yosun_D). Ates: komurlesmis koyu tas (T_AtesTas_D/N), lav akintilarina
# yakin catlak ve derzlerde parlayan lav (T_AtesCatlak). Eski dokunun golgeleri (kemer ici, girintiler) hafifce korunur.
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


def aktar(dosya):
    yol = os.path.join(KAYNAK, dosya)
    if not os.path.isfile(yol):
        return None
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", yol)
    t.set_editor_property("destination_path", HEDEF)
    t.set_editor_property("automated", True)
    t.set_editor_property("replace_existing", True)
    t.set_editor_property("save", True)
    tools.import_asset_tasks([t])
    return eal.load_asset(HEDEF + "/" + os.path.splitext(dosya)[0])


def bolge_dokusu():
    d = aktar("T_ArenaBolge.jpg")
    if not d:
        hata("T_ArenaBolge.jpg bulunamadi/aktarilamadi: " + KAYNAK)
    d.set_editor_property("srgb", True)
    d.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_WORLD)
    d.set_editor_property("max_texture_size", 0)
    eal.save_loaded_asset(d)
    return d


def maske_dokusu():
    d = aktar("T_ArenaBolgeMaske.png")
    if not d:
        log("   T_ArenaBolgeMaske.png yok - lav isigi/parlaklik eklenmeyecek")
        return None
    d.set_editor_property("srgb", False)
    d.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
    d.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_WORLD)
    eal.save_loaded_asset(d)
    return d


def zemin_dokulari():
    """Su tribunu zemin dokulari; biri eksikse zemin katmani atlanir."""
    dosyalar = [("T_SuZemin_D.png", "renk"), ("T_SuZemin_N.png", "normal"), ("T_SuZemin_R.png", "lineer"),
                ("T_SuZemin_Birikinti.png", "lineer"), ("T_SuZemin_Dalga.png", "normal")]
    sonuc = []
    for dosya, tur in dosyalar:
        d = aktar(dosya)
        if not d:
            log("   %s yok - su tribunu zemini eklenmeyecek" % dosya)
            return None
        d.set_editor_property("srgb", tur == "renk")
        if tur == "normal":
            d.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
        d.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_WORLD)
        eal.save_loaded_asset(d)
        sonuc.append(d)
    return sonuc


# Kaplama katmanlari: bolge maskesi Kaplama maskesinin kanali; tas dokusu (RGB + A puruzluluk), normal, istege bagli yosun
KAPLAMA_MASKE = "T_ArenaKaplamaMaske.png"     # R = hava (mermer), G = orman (yosunlu tas), B = ates, A = lava yakinlik
KAPLAMALAR = {
    "mermer": dict(on="Mermer", kanal="R", dosyalar=("T_Mermer_D.png", "T_Mermer_N.png"), parlak=0.42,
                   ton=(1.0, 0.93, 0.82), olcek=600.0, ao=0.3, ao_orta=0.2, ad="hava mermer kaplamasi"),
    "orman": dict(on="Orman", kanal="G", dosyalar=("T_OrmanTas_D.png", "T_OrmanTas_N.png", "T_Yosun_D.png"), parlak=0.75,
                  ton=(1.0, 1.0, 1.0), olcek=500.0, ao=0.35, ao_orta=0.05, ad="orman yosunlu tas kaplamasi", ek="yosun"),
    "ates": dict(on="Ates", kanal="B", dosyalar=("T_AtesTas_D.png", "T_AtesTas_N.png", "T_AtesCatlak.png"), parlak=1.0,
                 ton=(1.0, 1.0, 1.0), olcek=500.0, ao=0.35, ao_orta=0.03, ad="ates komurlesmis tas + lav catlaklari", ek="catlak"),
}


def kaplama_dokulari():
    """Her kaplama icin (maske, tas, normal[, yosun]); dosyasi eksik olan kaplama atlanir."""
    def al(dosya, tur):
        d = aktar(dosya)
        if not d:
            return None
        d.set_editor_property("srgb", tur == "renk")          # renk dokularinin alfasi zaten dogrusal
        if tur == "normal":
            d.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
        elif tur == "maske":
            d.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
        d.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_WORLD)
        eal.save_loaded_asset(d)
        return d
    maske = al(KAPLAMA_MASKE, "maske")
    if not maske:
        log("   %s yok - kaplamalar eklenmeyecek" % KAPLAMA_MASKE)
        return {}
    sonuc = {}
    for ad, k in KAPLAMALAR.items():
        dl = [maske] + [al(f, "normal" if f.endswith("_N.png") else "maske" if "Catlak" in f else "renk") for f in k["dosyalar"]]
        if all(dl):
            sonuc[ad] = dl
        else:
            log("   %s dokulari eksik - atlanacak" % k["ad"])
    return sonuc


def malzeme(renk, normal, orm, detay_d, detay_n, maske, zemin=None, seviye=3, kaplama=None):
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

    def sabit(v, x, y):
        e = ifade(unreal.MaterialExpressionConstant, x, y)
        e.set_editor_property("r", v)
        return e

    def topla(a, b, x, y, ca="", cb=""):
        e = ifade(unreal.MaterialExpressionAdd, x, y)
        bag(a, ca, e, "A")
        bag(b, cb, e, "B")
        return e

    def karis(a, b, alfa, x, y, ca="", cb="", calfa=""):
        e = ifade(unreal.MaterialExpressionLinearInterpolate, x, y)
        bag(a, ca, e, "A")
        bag(b, cb, e, "B")
        bag(alfa, calfa, e, "Alpha")
        return e

    def doygun(a, x, y, ca=""):
        e = ifade(unreal.MaterialExpressionSaturate, x, y)
        bag(a, ca, e, "")
        return e

    def vek3(r, g, b, x, y):
        e = ifade(unreal.MaterialExpressionConstant3Vector, x, y)
        e.set_editor_property("constant", unreal.LinearColor(r, g, b, 0))
        return e

    def bilesen(a, kanallar, x, y):
        e = ifade(unreal.MaterialExpressionComponentMask, x, y)
        for k in kanallar:
            e.set_editor_property(k, True)
        bag(a, "", e, "")
        return e

    def dunyadan_tegete(a, x, y, ca=""):
        e = ifade(unreal.MaterialExpressionTransform, x, y)
        e.set_editor_property("transform_source_type", unreal.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_WORLD)
        e.set_editor_property("transform_type", unreal.MaterialVectorCoordTransform.TRANSFORM_TANGENT)
        bag(a, ca, e, "")
        return e

    def eksen(kaynak, v, x, y):
        """dunya vektorunun bir ekseni (skaler): kaynak . v"""
        e = ifade(unreal.MaterialExpressionDotProduct, x, y)
        bag(kaynak, "", e, "A")
        bag(vek3(v[0], v[1], v[2], x - 150, y + 60), "", e, "B")
        return e

    def ekle(a, b, x, y, ca="", cb=""):
        e = ifade(unreal.MaterialExpressionAppendVector, x, y)
        bag(a, ca, e, "A")
        bag(b, cb, e, "B")
        return e

    def bol(a, b, x, y):
        e = ifade(unreal.MaterialExpressionDivide, x, y)
        bag(a, "", e, "A")
        bag(b, "", e, "B")
        return e

    def sinirla(a, alt, ust, x, y):
        e1 = ifade(unreal.MaterialExpressionMax, x, y)
        bag(a, "", e1, "A")
        bag(sabit(alt, x - 100, y + 60), "", e1, "B")
        e2 = ifade(unreal.MaterialExpressionMin, x + 100, y)
        bag(e1, "", e2, "A")
        bag(sabit(ust, x, y + 60), "", e2, "B")
        return e2

    def ortak_ornekleyici(t):
        try:
            t.set_editor_property("sampler_source", unreal.SamplerSourceMode.SSM_WRAP_WORLD_GROUP_SETTINGS)
        except Exception:
            pass

    taban_renk = puruz_son = normal_son = emis_son = None

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
    taban_renk = renk_d

    if orm:
        puruz, puruz_c = doku(orm, ST.SAMPLERTYPE_LINEAR_COLOR, -900, -100), "G"
    else:
        puruz, puruz_c = ifade(unreal.MaterialExpressionConstant, -300, -100), ""
        puruz.set_editor_property("r", 0.85)

    t_m = None
    if maske:
        t_m = doku(maske, ST.SAMPLERTYPE_MASKS, -1400, -900)

        def dalga(hiz, egim, x, y):
            """0..1 arasi zamanla kayan dalga: sin(zaman*hiz + dunya_konumu . egim)"""
            zaman = ifade(unreal.MaterialExpressionTime, x - 400, y)
            dk = ifade(unreal.MaterialExpressionWorldPosition, x - 400, y + 100)
            yon = ifade(unreal.MaterialExpressionConstant3Vector, x - 400, y + 200)
            yon.set_editor_property("constant", unreal.LinearColor(egim[0], egim[1], egim[2], 0))
            faz = ifade(unreal.MaterialExpressionDotProduct, x - 250, y + 150)
            bag(dk, "", faz, "A")
            bag(yon, "", faz, "B")
            sn = ifade(unreal.MaterialExpressionSine, x, y)
            bag(topla(carp(zaman, hiz, x - 250, y), faz, x - 120, y), "", sn, "")
            return carp(topla(sn, sabit(1.0, x, y + 80), x + 120, y), sabit(0.5, x + 120, y + 80), x + 240, y)

        # Lav: renk * turuncu * maske.R * LavGucu * (0.6 + 0.4 * dalga)
        turuncu = ifade(unreal.MaterialExpressionConstant3Vector, -900, -1000)
        turuncu.set_editor_property("constant", unreal.LinearColor(1.6, 1.0, 0.6, 0))
        lav = carp(carp(t_renk, turuncu, -650, -1000, "RGB"), t_m, -500, -1000, "", "R")
        nabiz = topla(sabit(0.6, -700, -1300), carp(dalga(skaler("LavHiz", 0.25, -1300, -1350), (0.0005, 0.0005, 0.0003), -900, -1400),
                                                    sabit(0.4, -700, -1250), -600, -1300), -450, -1300)
        lav = carp(carp(lav, nabiz, -350, -1100), skaler("LavGucu", 6.0, -500, -900), -200, -1000)
        # Su: renk * maske.B * SuIsiltisi * dalga (asagi akan bantlar)
        su = carp(carp(t_renk, t_m, -650, -700, "RGB", "B"), skaler("SuIsiltisi", 1.5, -650, -600), -500, -700)
        su = carp(su, dalga(skaler("SuHiz", 0.8, -1300, -750), (0.0, 0.0, 0.004), -900, -800), -350, -700)
        emis_son = topla(lav, su, -100, -900)
        # Parlaklik: puruzluluk -> ParlakPuruz (buz/mermer cilali)
        pl = ifade(unreal.MaterialExpressionLinearInterpolate, -300, -150)
        bag(puruz, puruz_c, pl, "A")
        bag(skaler("ParlakPuruz", 0.22, -500, -150), "", pl, "B")
        bag(t_m, "G", pl, "Alpha")
        puruz, puruz_c = pl, ""
    puruz_son = (puruz, puruz_c)

    def su_zemini(zemin, t_m, renk_in, puruz_in, normal_in, emis_in, seviye):
        """Yukari bakan su tribunu yuzeyleri: net tas levha + yuksekte parlayan dalgali su birikintisi.
        seviye 1: sadece levha  2: + su birikintisi  3: + birikintide kayan dalga ve isilti.
        Butun carpimlar skaler ya da renk x skaler; dunya eksenleri DotProduct ile (lav dalgasinda derlendigi gibi),
        UV'ler iki skalerden AppendVector ile kurulur (UE 5.8'de maske/2'li sabit carpimi float2 x float3 hatasi verdi)."""
        zD, zN, zR, zB, zW = zemin
        X = 1800

        def eksen(kaynak, v, x, y):
            e = ifade(unreal.MaterialExpressionDotProduct, x, y)
            bag(kaynak, "", e, "A")
            bag(vek3(v[0], v[1], v[2], x - 150, y + 60), "", e, "B")
            return e

        def ekle(a, b, x, y):
            e = ifade(unreal.MaterialExpressionAppendVector, x, y)
            bag(a, "", e, "A")
            bag(b, "", e, "B")
            return e

        wp = ifade(unreal.MaterialExpressionWorldPosition, X - 1300, 1250)
        wx = eksen(wp, (1.0, 0.0, 0.0), X - 1100, 1150)
        wy = eksen(wp, (0.0, 1.0, 0.0), X - 1100, 1250)
        wz = eksen(wp, (0.0, 0.0, 1.0), X - 1100, 1350)
        zaman = ifade(unreal.MaterialExpressionTime, X - 1100, 2100) if seviye >= 3 else None

        def dunya_uv(bolen, x, y, hx=0.0, hy=0.0):
            """dunyaya hizali UV (bolen cm'de bir tekrar), istenirse zamanla kayar"""
            u = carp(wx, sabit(1.0 / bolen, x - 150, y + 40), x, y)
            v = carp(wy, sabit(1.0 / bolen, x - 150, y + 120), x, y + 80)
            if zaman:
                u = topla(u, carp(zaman, sabit(hx, x, y + 160), x + 100, y + 160), x + 150, y)
                v = topla(v, carp(zaman, sabit(hy, x, y + 240), x + 100, y + 240), x + 150, y + 80)
            return ekle(u, v, x + 300, y)

        zuv = dunya_uv(400.0, X - 850, 1150)                                         # levha 4 m'de bir tekrar
        t_zd = doku(zD, ST.SAMPLERTYPE_COLOR, X - 500, 1000)
        t_zn = doku(zN, ST.SAMPLERTYPE_NORMAL, X - 500, 1200)
        t_zr = doku(zR, ST.SAMPLERTYPE_LINEAR_COLOR, X - 500, 1400)
        for t in (t_zd, t_zn, t_zr):
            bag(zuv, "", t, "UVs")
            ortak_ornekleyici(t)
        # zemin agirligi: bolge (maske.A) * yukari bakma * ZeminGucu
        nz = eksen(ifade(unreal.MaterialExpressionVertexNormalWS, X - 1300, 1800), (0.0, 0.0, 1.0), X - 1100, 1800)
        yukari = doygun(carp(topla(nz, sabit(-0.7, X - 850, 1880), X - 700, 1800), sabit(6.0, X - 700, 1880), X - 550, 1800), X - 400, 1800)
        fw = carp(carp(yukari, t_m, X - 250, 1800, "", "A"), skaler("ZeminGucu", 1.0, X - 250, 1900), X - 100, 1800)
        # renk, puruzluluk, normal: levha
        zrenk = carp(t_zd, skaler("ZeminParlaklik", 1.0, X - 300, 950), X - 150, 1000, "RGB")
        r = karis(renk_in, zrenk, carp(fw, sabit(0.92, X, 1100), X + 150, 1100), X + 300, 1000)
        pr = karis(puruz_in[0], t_zr, fw, X + 300, 1300, puruz_in[1], "R")
        n_in = normal_in if normal_in else vek3(0.0, 0.0, 1.0, X + 300, 1150)
        n = karis(n_in, dunyadan_tegete(t_zn, X + 150, 1200, "RGB"), fw, X + 450, 1150)
        e = emis_in
        if seviye < 2:
            return r, (pr, ""), n, e

        # birikinti: gurultu + yukseklik (teraslar ve kule tepeleri daha cok su tutar)
        t_zb = doku(zB, ST.SAMPLERTYPE_LINEAR_COLOR, X - 500, 1600)
        ortak_ornekleyici(t_zb)
        bag(dunya_uv(3000.0, X - 850, 1550), "", t_zb, "UVs")
        hb = doygun(carp(topla(wz, sabit(-3400.0, X - 700, 1430), X - 550, 1350), sabit(1.0 / 300.0, X - 550, 1430), X - 400, 1350), X - 250, 1350)
        bn = topla(topla(t_zb, carp(hb, sabit(0.7, X - 250, 1450), X - 100, 1400), X + 50, 1500, "R"),
                   carp(skaler("BirikintiEsik", 0.68, X - 100, 1650), sabit(-1.0, X - 100, 1720), X + 50, 1650), X + 200, 1550)
        pud = carp(doygun(carp(bn, sabit(3.0, X + 200, 1650), X + 350, 1550), X + 500, 1550), fw, X + 650, 1600)
        r = karis(r, vek3(0.01, 0.04, 0.07, X + 300, 900), pud, X + 450, 1000)
        pr = karis(pr, sabit(0.03, X + 300, 1400), pud, X + 450, 1300)
        parilti = sabit(0.18, X + 200, 2600)              # birikintide hafif camgobegi isilti
        if seviye < 3:
            dn = vek3(0.0, 0.0, 1.0, X + 500, 2200)       # dalgasiz duz su yuzeyi (tegette yukari)
        else:
            def kayan(bolen, hx, hy, y):
                t = doku(zW, ST.SAMPLERTYPE_NORMAL, X - 400, y)
                ortak_ornekleyici(t)
                bag(dunya_uv(bolen, X - 850, y, hx, hy), "", t, "UVs")
                return t
            r1 = kayan(300.0, 0.03, 0.02, 2100)
            r2 = kayan(210.0, -0.02, 0.035, 2400)
            # iki dalga normalinin x ve y'si ayri ayri toplanir (skaler), z = 1
            nx = carp(topla(r1, r2, X - 250, 2150, "R", "R"), sabit(0.15, X - 250, 2230), X - 100, 2150)
            ny = carp(topla(r1, r2, X - 250, 2300, "G", "G"), sabit(0.15, X - 250, 2380), X - 100, 2300)
            dn = ifade(unreal.MaterialExpressionNormalize, X + 350, 2200)
            bag(ekle(ekle(nx, ny, X + 50, 2200), sabit(1.0, X + 50, 2300), X + 200, 2200), "", dn, "")
            dn = dunyadan_tegete(dn, X + 500, 2200)
            kip = doygun(carp(topla(r1, sabit(-0.1, X - 250, 2530), X - 100, 2500, "R"), sabit(4.0, X - 100, 2580), X + 50, 2500), X + 200, 2500)
            parilti = topla(parilti, carp(kip, sabit(0.25, X + 350, 2450), X + 500, 2400), X + 650, 2450)
        n = karis(n, dn, pud, X + 650, 1150)
        isik = carp(carp(vek3(0.05, 0.35, 0.7, X + 200, 2500), carp(parilti, pud, X + 800, 2450), X + 950, 2450),
                    skaler("ZeminSuParilti", 1.0, X + 800, 2550), X + 1100, 2450)
        e = topla(e, isik, X + 1250, 2300) if e else isik
        return r, (pr, ""), n, e

    ucyon = {}

    def ucyon_temel():
        """Dunya eksenleri ve ucyonlu agirliklar (n^4, toplami 1); butun kaplamalar paylasir."""
        if ucyon:
            return ucyon
        X, Y0 = 600, 3000
        wp = ifade(unreal.MaterialExpressionWorldPosition, X - 300, Y0)
        ucyon["w"] = [eksen(wp, v, X - 100, Y0 + i * 120) for i, v in enumerate(((1., 0., 0.), (0., 1., 0.), (0., 0., 1.)))]
        nw = ifade(unreal.MaterialExpressionVertexNormalWS, X - 300, Y0 + 500)
        ag, nz = [], None
        for i, v in enumerate(((1., 0., 0.), (0., 1., 0.), (0., 0., 1.))):
            a = eksen(nw, v, X - 100, Y0 + 500 + i * 120)
            nz = a
            a2 = carp(a, a, X + 50, Y0 + 500 + i * 120)                    # kare: isaret gerekmez
            ag.append(carp(a2, a2, X + 150, Y0 + 500 + i * 120))
        top = topla(topla(ag[0], ag[1], X + 250, Y0 + 560), ag[2], X + 350, Y0 + 600)
        ucyon["a"] = dict(zip("XYZ", (bol(a, top, X + 450, Y0 + 500 + i * 120) for i, a in enumerate(ag))))
        ucyon["nz"] = nz
        return ucyon

    def kaplama_katmani(ad, dl, renk_in, puruz_in, normal_in, kseviye, Y0):
        """Bolgeye dunyaya hizali ucyonlu kesme tas kaplama (duvarlar dahil). kseviye 1: renk + puruzluluk,
        2: + blok/derz normali. Yosunlu ise yukari bakan yuzlerde ve buyume gurultusune gore duvarlarda yosun.
        Sadece skaler carpim, DotProduct ve AppendVector (UE 5.8 karisik boyut hatasindan uzak)."""
        k = KAPLAMALAR[ad]
        on = k["on"]
        t_mask, tD, tN = dl[:3]
        tY = dl[3] if k.get("ek") == "yosun" else None
        tC = dl[3] if k.get("ek") == "catlak" else None
        X = 1800
        tem = ucyon_temel()
        wx, wy, wz = tem["w"]
        ag = tem["a"]
        t_hm = doku(t_mask, ST.SAMPLERTYPE_MASKS, X - 600, Y0 - 300)
        ortak_ornekleyici(t_hm)
        w = carp(t_hm, skaler(on + "Gucu", 1.0, X - 600, Y0 - 150), X - 400, Y0 - 300, k["kanal"])
        # UV'ler: zemin (x, y), X'e bakan duvar (y, -z), Y'ye bakan duvar (x, -z); siralar duvarda yatay
        kk = bol(sabit(1.0, X - 1300, Y0 + 400), skaler(on + "Olcek", k["olcek"], X - 1300, Y0 + 460), X - 1150, Y0 + 400)
        u_x, u_y = carp(wx, kk, X - 1000, Y0), carp(wy, kk, X - 1000, Y0 + 100)
        u_z = carp(carp(wz, kk, X - 1000, Y0 + 200), sabit(-1.0, X - 1000, Y0 + 260), X - 900, Y0 + 200)
        uvlar = {"Z": ekle(u_x, u_y, X - 800, Y0), "X": ekle(u_y, u_z, X - 800, Y0 + 100), "Y": ekle(u_x, u_z, X - 800, Y0 + 200)}

        def ornekle(tex, tur, y):
            t = {}
            for i, e in enumerate("XYZ"):
                t[e] = doku(tex, tur, X - 500, y + i * 250)
                bag(uvlar[e], "", t[e], "UVs")
                ortak_ornekleyici(t[e])
            return t

        def karisim(t, kanal, y):
            return topla(topla(carp(t["X"], ag["X"], X - 250, y, kanal), carp(t["Y"], ag["Y"], X - 250, y + 80, kanal), X - 100, y),
                         carp(t["Z"], ag["Z"], X - 250, y + 160, kanal), X + 50, y)
        D = ornekle(tD, ST.SAMPLERTYPE_COLOR, Y0)
        renk_m = karisim(D, "RGB", Y0)
        puruz_m = carp(karisim(D, "A", Y0 + 300), skaler(on + "Puruz", 1.0, X + 50, Y0 + 400), X + 200, Y0 + 300)
        # ton (vektor parametresinin R, G, B'si ayri alinip birlestirilir), parlaklik
        ton = ifade(unreal.MaterialExpressionVectorParameter, X - 100, Y0 - 300)
        ton.set_editor_property("parameter_name", on + "Ton")
        ton.set_editor_property("default_value", unreal.LinearColor(k["ton"][0], k["ton"][1], k["ton"][2], 1.0))
        ton3 = ekle(ekle(ton, ton, X + 50, Y0 - 300, "R", "G"), ton, X + 150, Y0 - 300, "", "B")
        renk_m = carp(carp(renk_m, ton3, X + 300, Y0), skaler(on + "Parlaklik", k["parlak"], X + 300, Y0 + 80), X + 450, Y0)
        yc = None
        if tY:
            # yosun: yukari bakma * YosunUst + buyume gurultusu * 0.9 + YosunMiktar - 1, keskinlestirilmis
            Yd = ornekle(tY, ST.SAMPLERTYPE_COLOR, Y0 + 1600)
            yrenk = carp(karisim(Yd, "RGB", Y0 + 1600), skaler("YosunParlaklik", 0.85, X + 50, Y0 + 1700), X + 200, Y0 + 1600)
            ust = ifade(unreal.MaterialExpressionMax, X - 100, Y0 + 1900)
            bag(tem["nz"], "", ust, "A")
            bag(sabit(0.0, X - 200, Y0 + 1960), "", ust, "B")
            ifd = topla(topla(carp(ust, skaler("YosunUst", 0.45, X - 100, Y0 + 2000), X + 50, Y0 + 1900),
                              carp(karisim(Yd, "A", Y0 + 2100), sabit(0.9, X + 50, Y0 + 2200), X + 200, Y0 + 2100), X + 300, Y0 + 2000),
                        topla(skaler("YosunMiktar", 0.4, X + 200, Y0 + 2300), sabit(-1.0, X + 200, Y0 + 2380), X + 350, Y0 + 2300),
                        X + 450, Y0 + 2100)
            yc = doygun(carp(ifd, sabit(4.0, X + 450, Y0 + 2200), X + 600, Y0 + 2100), X + 750, Y0 + 2100)
            renk_m = karis(renk_m, yrenk, yc, X + 600, Y0)
            puruz_m = karis(puruz_m, sabit(0.92, X + 450, Y0 + 400), yc, X + 600, Y0 + 300)
        isik = None
        if tC:
            # lav catlaklari: lav akintilarina yakin yerde (maske A) parlar, uzakta sonuk kor (AtesKor)
            C = ornekle(tC, ST.SAMPLERTYPE_MASKS, Y0 + 2600)
            yakin = topla(skaler("AtesKor", 0.08, X - 100, Y0 + 2900), t_hm, X + 50, Y0 + 2900, "", "A")
            parla = carp(carp(carp(karisim(C, "R", Y0 + 2600), yakin, X + 200, Y0 + 2700), w, X + 350, Y0 + 2700),
                         skaler("AtesLavGucu", 2.0, X + 350, Y0 + 2800), X + 500, Y0 + 2700)
            isik = carp(vek3(1.0, 0.32, 0.07, X + 500, Y0 + 2600), parla, X + 650, Y0 + 2650)
        # eski dokunun golgesi (kemer ici, girinti) hafifce korunur
        lum = ifade(unreal.MaterialExpressionDotProduct, X - 100, Y0 - 500)
        bag(renk_in, "", lum, "A")
        bag(vek3(0.3, 0.59, 0.11, X - 250, Y0 - 450), "", lum, "B")
        oran = sinirla(bol(lum, skaler(on + "AOOrta", k["ao_orta"], X - 100, Y0 - 400), X + 50, Y0 - 500), 0.35, 1.15, X + 150, Y0 - 500)
        ao = karis(sabit(1.0, X + 300, Y0 - 560), oran, skaler(on + "AO", k["ao"], X + 300, Y0 - 440), X + 450, Y0 - 500)
        renk_m = carp(renk_m, ao, X + 750, Y0)
        r = karis(renk_in, renk_m, w, X + 900, Y0 - 100)
        pr = karis(puruz_in[0], puruz_m, w, X + 900, Y0 + 300, puruz_in[1])
        if kseviye < 2:
            return r, (pr, ""), normal_in, isik
        # normal: her izdusumun dokusal egimi dunya eksenlerine: Z(u->+x, v->+y), X(u->+y, v->-z), Y(u->+x, v->-z)
        N = ornekle(tN, ST.SAMPLERTYPE_NORMAL, Y0 + 800)

        def egim(e, kanal, y):
            return carp(ag[e], N[e], X - 250, y, "", kanal)
        px_ = topla(egim("Z", "R", Y0 + 800), egim("Y", "R", Y0 + 880), X - 100, Y0 + 800)
        py_ = topla(egim("Z", "G", Y0 + 960), egim("X", "R", Y0 + 1040), X - 100, Y0 + 960)
        pz_ = carp(topla(egim("X", "G", Y0 + 1120), egim("Y", "G", Y0 + 1200), X - 100, Y0 + 1120), sabit(-1.0, X - 100, Y0 + 1200), X + 50, Y0 + 1120)
        guc = skaler(on + "Normal", 1.0, X + 250, Y0 + 1050)
        if yc:   # yosunda tas derzleri yumusar
            guc = carp(guc, topla(sabit(1.0, X + 250, Y0 + 1150), carp(yc, sabit(-0.7, X + 250, Y0 + 1230), X + 350, Y0 + 1200), X + 450, Y0 + 1150), X + 550, Y0 + 1100)
        egim3 = carp(ekle(ekle(px_, py_, X + 150, Y0 + 900), pz_, X + 250, Y0 + 950), guc, X + 400, Y0 + 950)
        nd = ifade(unreal.MaterialExpressionNormalize, X + 650, Y0 + 900)
        bag(topla(ifade(unreal.MaterialExpressionVertexNormalWS, X + 400, Y0 + 850), egim3, X + 550, Y0 + 900), "", nd, "")
        n_in = normal_in if normal_in else vek3(0.0, 0.0, 1.0, X + 650, Y0 + 800)
        n = karis(n_in, dunyadan_tegete(nd, X + 800, Y0 + 900), w, X + 950, Y0 + 850)
        return r, (pr, ""), n, isik

    if normal or detay_n:
        parcalar = []
        if normal:
            parcalar.append((doku(normal, ST.SAMPLERTYPE_NORMAL, -900, 300), "RGB"))
        if detay_n:
            t_dn = doku(detay_n, ST.SAMPLERTYPE_NORMAL, -1000, 400)
            bag(duv, "", t_dn, "UVs")
            xy = vek3(1.0, 1.0, 0.0, -1000, 800)
            parcalar.append((carp(t_dn, carp(xy, guc, -750, 700), -550, 450, "RGB"), ""))
        son, cikis = parcalar[0]
        if len(parcalar) == 2:
            top = ifade(unreal.MaterialExpressionAdd, -350, 350)
            bag(son, cikis, top, "A")
            bag(parcalar[1][0], "", top, "B")
            son, cikis = top, ""
        nrm = ifade(unreal.MaterialExpressionNormalize, -150, 350)
        bag(son, cikis, nrm, "")
        normal_son = nrm

    if t_m and zemin:
        zemin_katmani = su_zemini(zemin, t_m, taban_renk, puruz_son, normal_son, emis_son, seviye)
        taban_renk, puruz_son, normal_son, emis_son = zemin_katmani
    for i, (ad, (dl, ks)) in enumerate((kaplama or {}).items()):
        if ks > 0:
            taban_renk, puruz_son, normal_son, isik = kaplama_katmani(ad, dl, taban_renk, puruz_son, normal_son, ks, 3000 + i * 3000)
            if isik:
                emis_son = topla(emis_son, isik, 2800, 3000 + i * 3000) if emis_son else isik

    mel.connect_material_property(taban_renk, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(puruz_son[0], puruz_son[1], unreal.MaterialProperty.MP_ROUGHNESS)
    if normal_son:
        mel.connect_material_property(normal_son, "", unreal.MaterialProperty.MP_NORMAL)
    if emis_son:
        mel.connect_material_property(emis_son, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    mel.layout_material_expressions(mat)
    mel.recompile_material(mat)
    eal.save_loaded_asset(mat)
    return mat


def derlendi_mi(mat):
    """Derleme hatasinda piksel shader komut sayisi 0 olur. Olculemezse derlendi say."""
    try:
        ist = mel.get_statistics(mat)
        n = ist.get_editor_property("num_pixel_shader_instructions")
        log("   piksel shader komutu: %d" % n)
        return n > 0
    except Exception as e:
        log("   derleme kontrol edilemedi (onemsiz): %s" % e)
        return True


ZEMIN_SEVIYE = {3: "tam (dalgali su birikintisi)", 2: "birikintili (dalgasiz)", 1: "sadece tas levha", 0: "EKLENEMEDI (arena zeminsiz kuruldu)"}


KAPLAMA_SEVIYE = {2: "tam (bloklar + derz normali)", 1: "renk ve parlaklik (normalsiz)", 0: "EKLENEMEDI"}


def guvenli_malzeme(renk, normal, orm, detay_d, detay_n, maske, zemin, kaplama_dok):
    """Su zemini ve kaplamalari tam kurmayi dener; derlenmezse her katmani tek basina deneyip sorunluyu sadelestirir,
    sonra calisanlari birlestirir (arena asla dokusuz kalmaz). Doner: (malzeme, {katman: seviye})."""
    seviyeler = {}
    if zemin:
        seviyeler["zemin"] = (3, 2, 1)
    for ad in kaplama_dok:
        seviyeler[ad] = (2, 1)

    def dene(sec):
        try:
            kap = {ad: (kaplama_dok[ad], sec.get(ad, 0)) for ad in kaplama_dok if sec.get(ad, 0)}
            z = sec.get("zemin", 0)
            mat = malzeme(renk, normal, orm, detay_d, detay_n, maske, zemin if z else None, z or 3, kap)
            if derlendi_mi(mat):
                return mat
            unreal.log_error("[Arena] %s derlenemedi - sadelestiriliyor. LogMaterial satirlarini gonder." % sec)
        except Exception as e:
            unreal.log_error("[Arena] %s kurulamadi (%s) - sadelestiriliyor. Bu satiri gonder." % (sec, e))
        return None
    if seviyeler:
        tam = {ad: sv[0] for ad, sv in seviyeler.items()}
        mat = dene(tam)
        if mat:
            return mat, tam
        iyi = {}
        for ad, sv in seviyeler.items():                       # her katman tek basina: calisan en iyi seviye
            iyi[ad] = next((v for v in sv if (len(seviyeler) > 1 or v != sv[0]) and dene({ad: v})), 0)
        sec = {ad: v for ad, v in iyi.items() if v}
        while sec:                                               # birlikte; olmazsa sondakini birakarak
            mat = dene(sec)
            if mat:
                return mat, sec
            sec.pop(list(sec)[-1])
    return malzeme(renk, normal, orm, detay_d, detay_n, maske, None), {}


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

    maske = maske_dokusu()
    zemin = zemin_dokulari() if maske else None
    kaplama_dok = kaplama_dokulari()
    log("   su tribunu zemini: %s, kaplamalar: %s" % ("var" if zemin else "yok", ", ".join(kaplama_dok) or "yok"))
    log("2/3 Malzeme: M_ArenaBolge")
    mat, sec = guvenli_malzeme(renk, normal, orm, detay_d, detay_n, maske, zemin, kaplama_dok)
    log("   su tribunu zemini: %s" % ZEMIN_SEVIYE[sec.get("zemin", 0)])
    for ad, k in KAPLAMALAR.items():
        log("   %s: %s" % (k["ad"], KAPLAMA_SEVIYE[sec.get(ad, 0)] if ad in kaplama_dok else "dokular yok"))
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
    log("TAMAM - Arena bolgelere gore boyandi. Ayar: " + mi_yol + " (Parlaklik, LavGucu, LavHiz, SuIsiltisi, SuHiz, ParlakPuruz, DetayTekrar, DetayGucu, ZeminGucu, ZeminParlaklik, BirikintiEsik, ZeminSuParilti, Mermer*/Orman*/Ates*: Gucu, Parlaklik, Ton, Olcek, AO, AOOrta, Puruz, Normal; YosunMiktar, YosunUst, YosunParlaklik; AtesLavGucu, AtesKor)")


calistir()
