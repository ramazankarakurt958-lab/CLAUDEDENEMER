# Unreal Engine 5 - Arenayi 4 element bolgesine gore boyar (referans resim dokuya yansitildi).
# Ates: komurlesmis tas + lav catlaklari, Su: buz mavisi, Toprak: yosunlu tas, Hava: beyaz mermer.
# Doku: Kaynak/T_ArenaBolge.jpg (araclar ile referans resimden uretildi). Arenanin normal/ORM dokulari ve
# ArenaDetay'in yakin plan tas detayi aynen kalir; sadece renk dokusu degisir.
# Maske: Kaynak/T_ArenaBolgeMaske.png  R=lav (isik verir, nabiz gibi atar), G=parlaklik (buz/mermer), B=su isiltisi,
#        A=su tribunu zemin bolgesi.
# Su tribunu zemini: yukari bakan yuzlere dunyaya hizali net tas levha (T_SuZemin_*), yuksek teraslarda ve kule
# tepelerinde parlayan/yansitan dalgali su birikintileri.
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


def malzeme(renk, normal, orm, detay_d, detay_n, maske, zemin=None):
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

    def su_zemini(zemin, t_m, renk_in, puruz_in, normal_in, emis_in):
        """Yukari bakan su tribunu yuzeyleri: net tas levha + yuksekte parlayan dalgali su birikintisi."""
        zD, zN, zR, zB, zW = zemin
        X = 1800
        wp = ifade(unreal.MaterialExpressionWorldPosition, X - 1000, 1200)
        wxy = bilesen(wp, ("r", "g"), X - 850, 1200)
        wz = bilesen(wp, ("b",), X - 850, 1350)
        zuv = carp(wxy, sabit(1.0 / 400.0, X - 850, 1280), X - 700, 1200)          # levha dokusu 4 m'de bir tekrar
        t_zd = doku(zD, ST.SAMPLERTYPE_COLOR, X - 500, 1000)
        t_zn = doku(zN, ST.SAMPLERTYPE_NORMAL, X - 500, 1200)
        t_zr = doku(zR, ST.SAMPLERTYPE_LINEAR_COLOR, X - 500, 1400)
        for t in (t_zd, t_zn, t_zr):
            bag(zuv, "", t, "UVs")
        t_zb = doku(zB, ST.SAMPLERTYPE_LINEAR_COLOR, X - 500, 1600)
        bag(carp(wxy, sabit(1.0 / 3000.0, X - 850, 1600), X - 700, 1600), "", t_zb, "UVs")
        # zemin agirligi: bolge (maske.A) * yukari bakma * ZeminGucu
        nz = bilesen(ifade(unreal.MaterialExpressionVertexNormalWS, X - 1000, 1800), ("b",), X - 850, 1800)
        yukari = doygun(carp(topla(nz, sabit(-0.7, X - 850, 1880), X - 700, 1800), sabit(6.0, X - 700, 1880), X - 550, 1800), X - 400, 1800)
        fw = carp(carp(yukari, t_m, X - 250, 1800, "", "A"), skaler("ZeminGucu", 1.0, X - 250, 1900), X - 100, 1800)
        # birikinti: gurultu + yukseklik (teraslar ve kule tepeleri daha cok su tutar)
        hb = doygun(carp(topla(wz, sabit(-3400.0, X - 700, 1430), X - 550, 1350), sabit(1.0 / 300.0, X - 550, 1430), X - 400, 1350), X - 250, 1350)
        bn = topla(topla(t_zb, carp(hb, sabit(0.7, X - 250, 1450), X - 100, 1400), X + 50, 1500, "R"),
                   carp(skaler("BirikintiEsik", 0.68, X - 100, 1650), sabit(-1.0, X - 100, 1720), X + 50, 1650), X + 200, 1550)
        pud = carp(doygun(carp(bn, sabit(3.0, X + 200, 1650), X + 350, 1550), X + 500, 1550), fw, X + 650, 1600)
        # renk
        zrenk = carp(t_zd, skaler("ZeminParlaklik", 1.0, X - 300, 950), X - 150, 1000, "RGB")
        r = karis(renk_in, zrenk, carp(fw, sabit(0.92, X, 1100), X + 150, 1100), X + 300, 1000)
        r = karis(r, vek3(0.01, 0.04, 0.07, X + 300, 900), pud, X + 450, 1000)
        # puruzluluk
        pr = karis(puruz_in[0], t_zr, fw, X + 300, 1300, puruz_in[1], "R")
        pr = karis(pr, sabit(0.03, X + 300, 1400), pud, X + 450, 1300)
        # normal: levha normali dunyadan tegete; birikintide iki yone kayan dalga
        n_in = normal_in if normal_in else vek3(0.0, 0.0, 1.0, X + 300, 1150)
        n1 = karis(n_in, dunyadan_tegete(t_zn, X + 150, 1200, "RGB"), fw, X + 450, 1150)
        zaman = ifade(unreal.MaterialExpressionTime, X - 1000, 2100)

        def kayan(bolen, hx, hy, y):
            hiz = ifade(unreal.MaterialExpressionConstant2Vector, X - 850, y + 80)
            hiz.set_editor_property("r", hx)
            hiz.set_editor_property("g", hy)
            uvs = topla(carp(wxy, sabit(1.0 / bolen, X - 850, y), X - 700, y), carp(zaman, hiz, X - 700, y + 80), X - 550, y)
            t = doku(zW, ST.SAMPLERTYPE_NORMAL, X - 400, y)
            bag(uvs, "", t, "UVs")
            return t
        r1 = kayan(300.0, 0.03, 0.02, 2100)
        r2 = kayan(210.0, -0.02, 0.035, 2300)
        rg = carp(topla(bilesen(r1, ("r", "g"), X - 250, 2100), bilesen(r2, ("r", "g"), X - 250, 2300), X - 100, 2200),
                  sabit(0.15, X - 100, 2300), X + 50, 2200)
        dn = ifade(unreal.MaterialExpressionAppendVector, X + 200, 2200)
        bag(rg, "", dn, "A")
        bag(sabit(1.0, X + 50, 2300), "", dn, "B")
        dnn = ifade(unreal.MaterialExpressionNormalize, X + 350, 2200)
        bag(dn, "", dnn, "")
        n2 = karis(n1, dunyadan_tegete(dnn, X + 500, 2200), pud, X + 650, 1150)
        # birikintide hafif camgobegi isilti (kipirtinin parlak yerlerinde artar)
        kip = doygun(carp(topla(bilesen(r1, ("r",), X - 250, 2400), sabit(-0.1, X - 250, 2480), X - 100, 2400),
                          sabit(4.0, X - 100, 2480), X + 50, 2400), X + 200, 2400)
        isik = carp(carp(vek3(0.05, 0.35, 0.7, X + 200, 2500), carp(topla(sabit(0.18, X + 200, 2600), carp(kip, sabit(0.25, X + 350, 2450), X + 500, 2400),
                                                                          X + 650, 2450), pud, X + 800, 2450), X + 950, 2450),
                    skaler("ZeminSuParilti", 1.0, X + 800, 2550), X + 1100, 2450)
        e = topla(emis_in, isik, X + 1250, 2300) if emis_in else isik
        return r, (pr, ""), n2, e

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
        zemin_katmani = su_zemini(zemin, t_m, taban_renk, puruz_son, normal_son, emis_son)
        taban_renk, puruz_son, normal_son, emis_son = zemin_katmani

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
    log("   su tribunu zemini: %s" % ("var" if zemin else "yok"))
    log("2/3 Malzeme: M_ArenaBolge")
    mat = malzeme(renk, normal, orm, detay_d, detay_n, maske, zemin)
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
    log("TAMAM - Arena bolgelere gore boyandi. Ayar: " + mi_yol + " (Parlaklik, LavGucu, LavHiz, SuIsiltisi, SuHiz, ParlakPuruz, DetayTekrar, DetayGucu, ZeminGucu, ZeminParlaklik, BirikintiEsik, ZeminSuParilti)")


calistir()
