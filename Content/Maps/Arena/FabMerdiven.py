# Unreal Engine 5 - Fab'dan indirilen "Castle Stairs" (Megascans scfdy) merdivenlerini ates ve su tribunlerine dizer.
# Her oturma diliminde (ara bolmeler arasinda) iki sira modul: on sira 28 m yurume yolundan baslar, arka sira onun
# ustunden duvara cikar. Moduller tribun duvarina diktir, yan yana hafif binerek bosluksuz dizilir.
# Yerlesim: dosyanin sonundaki YERLESIM (araclar/bolge_doku/merdiven_yerlesim.py yazar; arena glTF eksenleri, metre).
# Icerik klasorune json koyulmaz (Unreal onu DataTable olarak ice aktarmaya kalkiyordu).
# Eski uretilmis basamaklar (BK_Basamak) silinir.
# Calistirma (Output Log -> Python):
#   exec(open(unreal.Paths.project_content_dir() + "Maps/Arena/FabMerdiven.py", encoding="utf-8").read())
# Tekrar calistirmak zararsiz. Kaldirmak icin KALDIR = True.
# ELLE OTURTMA (hizli yol): bir merdiveni (MR_Merdiven_...) gorus alaninda tasi/dondur/olcekle, secili birak, scripti
# calistir -> butun merdivenler ayni oturusla yeniden dizilir. Oturus Saved/MerdivenOrnek.json'a kaydedilir, sonraki
# calistirmalarda da kullanilir. Unutmak icin SIFIRLA = True.
import json
import math
import os
import unreal

ICERIK = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir())
KAYNAK = os.path.join(ICERIK, "Maps", "Arena", "Kaynak")
HEDEF = "/Game/Maps/Arena/Merdiven"
MODEL = "/Game/Fab/Megascans/3D/Castle_Stairs_scfdy/Medium/scfdy_tier_2/StaticMeshes/scfdy_tier_2"
MODEL_ARA = "scfdy"         # MODEL yolunda yoksa /Game altinda adinda bu gecen mesh kullanilir
DIZILIS = "dogal"           # "dogal": modulun kendi egimine yakin, ustte set duvari kalir; "dik": terasa kadar cikar
YUKSELIS = None             # None = otomatik bulunur; ters cikarsa elle: "+x", "-x", "+y", "-y"
RENK = {"ates": (0.42, 0.33, 0.30), "su": (0.70, 0.82, 1.00)}   # bolge tonu (malzemede Tint varsa); None = dokunma
ETIKET = "MR_Merdiven"
ESKI = ("BK_Basamak",)      # bunlarla baslayan eski aktorler silinir
KLASOR = "Arena/Merdiven"
KALDIR = False
SIFIRLA = False             # True: kayitli elle oturtma silinir, otomatik dizilise donulur
ORNEK_DOSYA = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()), "MerdivenOrnek.json")

eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
tools = unreal.AssetToolsHelpers.get_asset_tools()
V = unreal.Vector


def log(msg):
    unreal.log_warning("[Merdiven] " + msg)


def hata(msg):
    unreal.log_error("[Merdiven] HATA: " + msg)
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
        return False
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", yol)
    t.set_editor_property("destination_path", hedef)
    t.set_editor_property("automated", True)
    t.set_editor_property("replace_existing", True)
    t.set_editor_property("save", True)
    tools.import_asset_tasks([t])
    return True


def ilk_mesh(klasor):
    for yol in eal.list_assets(klasor, recursive=True, include_folder=False):
        a = eal.load_asset(yol)
        if isinstance(a, unreal.StaticMesh):
            return a
    return None


def kutu(sm):
    b = sm.get_bounding_box()
    return (b.min.x, b.min.y, b.min.z), (b.max.x, b.max.y, b.max.z)


# ---------------------------------------------------------------- glTF (arena dosyasi) -> dunya
def eksen_haritasi():
    """Kaynak/SM_EksenIsaret.glb koseleri glTF'te (10,0,0) (0,20,0) (0,0,30) m. Ice aktarilinca kutusundan her UE
    ekseninin hangi glTF eksenine, hangi isaretle ve kac cm/m ile karsilik geldigi okunur (arena ayni yolla geldi)."""
    hedef = HEDEF + "/Isaret"
    mesh = ilk_mesh(hedef) if eal.does_directory_exist(hedef) else None     # bir kez aktarilir
    if not mesh:
        if not aktar("SM_EksenIsaret.glb", hedef):
            hata("SM_EksenIsaret.glb bulunamadi: " + KAYNAK)
        mesh = ilk_mesh(hedef)
    if not mesh:
        hata("Eksen isareti aktarilamadi (" + hedef + ").")
    mn, mx = kutu(mesh)
    boylar = [mx[i] - mn[i] for i in range(3)]
    birim = min(boylar) / 10.0                                  # glTF 1 m = kac UE birimi
    harita = []
    for i in range(3):
        k = int(round(boylar[i] / birim / 10.0)) - 1             # 10 m -> x, 20 m -> y, 30 m -> z
        isaret = 1.0 if mx[i] > -mn[i] else -1.0
        harita.append((k, isaret))
    if sorted(k for k, _ in harita) != [0, 1, 2] or birim <= 0:
        hata("Eksen isareti okunamadi: kutu %s %s" % (mn, mx))
    ad = "xyz"
    log("   eksenler: UE X = %sglTF %s, UE Y = %sglTF %s, UE Z = %sglTF %s  (1 m = %.1f)" % tuple(
        sum((("+" if s > 0 else "-", ad[k]) for k, s in harita), ()) + (birim,)))
    return harita, birim


def dunya_donusumu(arena, harita, birim):
    """glTF noktasi (m) -> dunya (UE). Arena aktorunun konum/donus/olcegi uygulanir (UE FRotationMatrix)."""
    p0 = arena.get_actor_location()
    r = arena.get_actor_rotation()
    s = arena.get_actor_scale3d()
    P, Y, R = (math.radians(r.pitch), math.radians(r.yaw), math.radians(r.roll))
    SP, CP, SY, CY, SR, CR = math.sin(P), math.cos(P), math.sin(Y), math.cos(Y), math.sin(R), math.cos(R)
    M = ((CP * CY, CP * SY, SP),
         (SR * SP * CY - CR * SY, SR * SP * SY + CR * CY, -SR * CP),
         (-(CR * SP * CY + SR * SY), CY * SR - CR * SP * SY, CR * CP))
    olc = (s.x, s.y, s.z)

    def donustur(g):
        yerel = [harita[i][1] * birim * g[harita[i][0]] * olc[i] for i in range(3)]
        return tuple((p0.x, p0.y, p0.z)[c] + sum(yerel[i] * M[i][c] for i in range(3)) for c in range(3))
    return donustur


# ---------------------------------------------------------------- merdiven modeli
def merdiven_mesh():
    if eal.does_asset_exist(MODEL):
        m = eal.load_asset(MODEL)
        if isinstance(m, unreal.StaticMesh):
            return m
    for yol in eal.list_assets("/Game", recursive=True, include_folder=False):
        if MODEL_ARA in yol.lower() and "/maps/arena/" not in yol.lower():
            a = eal.load_asset(yol)
            if isinstance(a, unreal.StaticMesh):
                log("   model: " + yol.split(".")[0])
                return a
    hata("Fab merdiveni bulunamadi (%s). Fab'dan Castle Stairs'i projeye ekle ya da MODEL yolunu duzelt." % MODEL)


def kose_noktalari(sm, en_cok=8000):
    """Modelin yerel koseleri (ornekleme). Olmazsa bos liste."""
    try:
        md = sm.get_static_mesh_description(0)
        n = int(md.get_vertex_count())
    except Exception as e:
        log("   koseler okunamadi (%s) - isinla olculecek" % e)
        return []

    def kimlik(i):
        for yap in (lambda: unreal.VertexID(i), lambda: unreal.VertexID(id_value=i)):
            try:
                return yap()
            except Exception:
                pass
        v = unreal.VertexID()
        v.set_editor_property("id_value", i)
        return v
    out = []
    adim = max(1, n // en_cok)
    try:
        for i in range(0, n, adim):
            p = md.get_vertex_position(kimlik(i))
            out.append((p.x, p.y, p.z))
    except Exception as e:
        log("   kose okuma yarida kaldi (%s)" % e)
    return out


def isin(dunya, bas, son):
    """Asagi isin: carptigi noktanin z'si ya da None."""
    try:
        hit = unreal.SystemLibrary.line_trace_single(
            dunya, V(*bas), V(*son), getattr(unreal.TraceTypeQuery, "ECC_VISIBILITY", unreal.TraceTypeQuery.TRACE_TYPE_QUERY1),
            True, [], unreal.DrawDebugTrace.NONE, True)
        if hit:
            alanlar = hit.to_tuple()
            if alanlar[0]:
                for v in alanlar:
                    if isinstance(v, unreal.Vector):
                        return v.z
    except Exception as e:
        log("   isin atilamadi (onemsiz): %s" % e)
    return None


def isinla_olc(sm):
    """Yedek: modeli uzaga gecici koyup ustten isin atarak yuzey noktalarini toplar."""
    dunya = ues.get_editor_world()
    m0 = (0.0, 0.0, -300000.0)
    a = eas.spawn_actor_from_object(sm, V(*m0))
    out = []
    try:
        mn, mx = kutu(sm)
        for i in range(10):
            for j in range(10):
                x = mn[0] + (i + .5) / 10 * (mx[0] - mn[0])
                y = mn[1] + (j + .5) / 10 * (mx[1] - mn[1])
                z = isin(dunya, (m0[0] + x, m0[1] + y, m0[2] + mx[2] + 100), (m0[0] + x, m0[1] + y, m0[2] + mn[2] - 100))
                if z is not None:
                    out.append((x, y, z - m0[2]))
    finally:
        eas.destroy_actor(a)
    return out


def yukselis_yonu(sm):
    """Basamaklarin yerel olarak hangi eksende ve yonde yukseldigi: ('x' | 'y', +1 | -1)."""
    if YUKSELIS:
        return YUKSELIS[1], (1 if YUKSELIS[0] == "+" else -1)
    pts = kose_noktalari(sm)
    kaynak = "koseler"
    if len(pts) < 50:
        pts, kaynak = isinla_olc(sm), "isin"
    if len(pts) < 20:
        log("   UYARI: merdivenin yonu olculemedi, +x varsayildi. Ters ise YUKSELIS = \"-x\" yap.")
        return "x", 1
    mn, mx = kutu(sm)
    sonuc = {}
    for ek, i in (("x", 0), ("y", 1)):
        tepe = []
        for b in range(6):
            lo, hi = mn[i] + (mx[i] - mn[i]) * b / 6, mn[i] + (mx[i] - mn[i]) * (b + 1) / 6
            zs = sorted(p[2] for p in pts if lo <= p[i] <= hi)
            tepe.append(zs[int(len(zs) * 0.9)] if zs else None)
        dolu = [t for t in tepe if t is not None]
        sonuc[ek] = ((dolu[-1] - dolu[0]) if len(dolu) > 1 else 0.0, tepe)
    ek = max(sonuc, key=lambda k: abs(sonuc[k][0]))
    isaret = 1 if sonuc[ek][0] > 0 else -1
    for k in ("x", "y"):
        log("   %s boyunca basamak tepeleri (cm): %s" % (k, " ".join("-" if t is None else "%.0f" % t for t in sonuc[k][1])))
    log("   yukselis yonu: %s%s (%s, %d nokta)" % ("+" if isaret > 0 else "-", ek, kaynak, len(pts)))
    return ek, isaret


def bolge_malzemeleri(sm):
    """Bolge tonlu malzeme ornekleri (modelin malzemesinde 'Tint' gecen renk parametresi varsa)."""
    if not RENK:
        return {}
    temel = sm.get_material(0)
    if not temel:
        return {}
    try:
        adlar = [str(n) for n in mel.get_vector_parameter_names(temel)]
    except Exception as e:
        log("   malzeme parametreleri okunamadi (%s)" % e)
        adlar = []
    log("   malzeme %s renk parametreleri: %s" % (temel.get_name(), ", ".join(adlar) or "-"))
    tonlar = [n for n in adlar if "tint" in n.lower()]
    if not tonlar:
        log("   ton parametresi yok - merdivenler kendi renginde kalir")
        return {}
    sonuc = {}
    for bolge, (r, g, b) in RENK.items():
        ad = "MI_Merdiven_" + bolge.capitalize()
        yol = HEDEF + "/" + ad
        mi = eal.load_asset(yol) if eal.does_asset_exist(yol) else \
            tools.create_asset(ad, HEDEF, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        mel.set_material_instance_parent(mi, temel)
        for n in tonlar:
            mel.set_material_instance_vector_parameter_value(mi, n, unreal.LinearColor(r, g, b, 1.0))
        eal.save_loaded_asset(mi)
        sonuc[bolge] = mi
    log("   bolge tonlari: %s (%s)" % (", ".join(HEDEF + "/MI_Merdiven_" + b.capitalize() for b in sonuc), ", ".join(tonlar)))
    return sonuc


# ---------------------------------------------------------------- dizme
def topla(a, b, k=1.0):
    return tuple(a[i] + k * b[i] for i in range(3))


def fark(a, b):
    return tuple(a[i] - b[i] for i in range(3))


def nokta(a, b):
    return sum(a[i] * b[i] for i in range(3))


def eksenler(r):
    """Aktorun yerel X, Y, Z eksenlerinin dunyadaki yonleri (UE FRotationMatrix satirlari)."""
    P, Y, R = math.radians(r[0]), math.radians(r[1]), math.radians(r[2])
    SP, CP, SY, CY, SR, CR = math.sin(P), math.cos(P), math.sin(Y), math.cos(Y), math.sin(R), math.cos(R)
    return ((CP * CY, CP * SY, SP),
            (SR * SP * CY - CR * SY, SR * SP * SY + CR * CY, -SR * CP),
            (-(CR * SP * CY + SR * SY), CY * SR - CR * SP * SY, CR * CP))


def cerceve(o, dunya):
    """Modulun dunyadaki cercevesi: on-alt-orta nokta F, yukselis yonu a, yan yon v, olculeri (cm)."""
    yon = o["yon"]
    F = dunya(o["on"])
    D = fark(dunya(topla(o["on"], yon, o["derinlik"])), F)
    derin = math.hypot(D[0], D[1])
    a = (D[0] / derin, D[1] / derin, 0.0)
    gen = math.sqrt(sum(c * c for c in fark(dunya(topla(o["on"], (-yon[2], 0.0, yon[0]), o["genislik"])), F)))
    yuk = dunya(topla(o["on"], (0.0, 1.0, 0.0), o["yukseklik"]))[2] - F[2]
    return dict(F=F, a=a, v=(-a[1], a[0], 0.0), olcu=(derin, gen, yuk), yaw=math.degrees(math.atan2(a[1], a[0])))


def secili_ornek():
    """Secili tek MR_Merdiven aktoru: elle oturtulmus ornek."""
    try:
        secili = [a for a in eas.get_selected_level_actors() if a.get_actor_label().startswith(ETIKET + "_")]
    except Exception:
        return None
    if len(secili) != 1:
        if secili:
            log("   %d merdiven secili - ornek icin sadece birini sec" % len(secili))
        return None
    a = secili[0]
    parca = a.get_actor_label()[len(ETIKET) + 1:].rsplit("_", 2)
    try:
        anahtar = (parca[0], int(parca[1]), int(parca[2]))
    except Exception:
        log("   secili aktorun adi taninmadi: " + a.get_actor_label())
        return None
    p, r, s = a.get_actor_location(), a.get_actor_rotation(), a.get_actor_scale3d()
    return dict(anahtar=anahtar, konum=(p.x, p.y, p.z), donus=(r.pitch, r.yaw, r.roll), olcek=(s.x, s.y, s.z))


def oturus_olc(ornek, c):
    """Ornegin kendi modul cercevesine gore oturusu, modul olculerine bolunmus (baska modullere tasinabilir)."""
    d = fark(ornek["konum"], c["F"])
    M = eksenler(ornek["donus"])
    yonler = (c["a"], c["v"], (0.0, 0.0, 1.0))
    # her yerel eksen hangi cerceve eksenine denk (en iyi eslesme, tekrarsiz)
    puan = sorted(((abs(nokta(M[i], yonler[j])), i, j) for i in range(3) for j in range(3)), reverse=True)
    es, kullanilan = {}, set()
    for _, i, j in puan:
        if i not in es and j not in kullanilan:
            es[i] = j
            kullanilan.add(j)
    olcu = c["olcu"]
    return dict(ileri=nokta(d, c["a"]) / olcu[0], yan=nokta(d, c["v"]) / olcu[1], yukari=d[2] / olcu[2],
                yaw=ornek["donus"][1] - c["yaw"], pitch=ornek["donus"][0], roll=ornek["donus"][2],
                es=[es[i] for i in range(3)], olcek=[ornek["olcek"][i] / olcu[es[i]] for i in range(3)])


def oturus_uygula(ot, c):
    """Kayitli oturusu bir modulun cercevesine uygular: konum, donus, olcek."""
    olcu = c["olcu"]
    konum = topla(topla(topla(c["F"], c["a"], ot["ileri"] * olcu[0]), c["v"], ot["yan"] * olcu[1]),
                  (0.0, 0.0, 1.0), ot["yukari"] * olcu[2])
    donus = unreal.Rotator(roll=ot["roll"], pitch=ot["pitch"], yaw=c["yaw"] + ot["yaw"])
    return konum, donus, [ot["olcek"][i] * olcu[ot["es"][i]] for i in range(3)]


def eski_json_temizle():
    """Onceki surumun Kaynak'a indirdigi json'u ve Unreal'in ondan yaptigi varligi kaldir (DataTable sorusu cikmasin)."""
    yol = os.path.join(KAYNAK, "merdiven_yerlesim.json")
    if os.path.isfile(yol):
        os.remove(yol)
        log("   Kaynak/merdiven_yerlesim.json silindi (artik scriptin icinde)")
    for v in ("/Game/Maps/Arena/Kaynak/merdiven_yerlesim",):
        if eal.does_asset_exist(v):
            eal.delete_asset(v)


def koy(sm, o, konum, donus, olc, malz):
    a = eas.spawn_actor_from_object(sm, V(*konum), donus)
    a.set_actor_scale3d(V(*olc))
    a.set_actor_label("%s_%s_%d_%d" % (ETIKET, o["dilim"], o["sira"], o["sutun"]))
    a.set_folder_path(KLASOR)
    bolge = o["dilim"].split("_")[0]
    if bolge in malz:
        a.static_mesh_component.set_material(0, malz[bolge])
    return a


def calistir():
    eski_json_temizle()
    arena = arena_aktoru()
    ornek = None if KALDIR else secili_ornek()     # silmeden once
    n = 0
    for a in eas.get_all_level_actors():
        etiket = a.get_actor_label()
        if etiket.startswith(ETIKET) or etiket.startswith(ESKI):
            eas.destroy_actor(a)
            n += 1
    if n:
        log("   %d eski merdiven/basamak aktoru silindi" % n)
    if KALDIR:
        les.save_current_level()
        log("KALDIRILDI.")
        return

    log("1/3 Eksenler...")
    harita, birim = eksen_haritasi()
    dunya = dunya_donusumu(arena, harita, birim)
    if DIZILIS not in YERLESIM:
        hata("DIZILIS '%s' yok; secenekler: %s" % (DIZILIS, ", ".join(YERLESIM)))
    moduller = [dict(zip(ALANLAR, m)) for m in YERLESIM[DIZILIS]]
    sm = merdiven_mesh()
    malz = bolge_malzemeleri(sm)

    # elle oturtma: secili ornek > kayitli oturus > otomatik
    ot = None
    if SIFIRLA and os.path.isfile(ORNEK_DOSYA):
        os.remove(ORNEK_DOSYA)
        log("   kayitli elle oturtma silindi")
    if ornek:
        o = next((m for m in moduller if (m["dilim"], m["sira"], m["sutun"]) == ornek["anahtar"]), None)
        if o is None:
            log("   ornek bu dizilisde yok (%s) - otomatik dizilecek" % (ornek["anahtar"],))
        else:
            ot = oturus_olc(ornek, cerceve(o, dunya))
            ot["dizilis"] = DIZILIS
            with open(ORNEK_DOSYA, "w", encoding="utf-8") as f:
                json.dump(ot, f)
            c = cerceve(o, dunya)
            log("   ornek %s_%d_%d: ileri %+.0f cm, yana %+.0f cm, yukari %+.0f cm, donus %+.0f, olcek %s" % (
                ornek["anahtar"][0], ornek["anahtar"][1], ornek["anahtar"][2], ot["ileri"] * c["olcu"][0],
                ot["yan"] * c["olcu"][1], ot["yukari"] * c["olcu"][2], ot["yaw"],
                " ".join("%.2f" % x for x in ornek["olcek"])))
    elif not SIFIRLA and os.path.isfile(ORNEK_DOSYA):
        with open(ORNEK_DOSYA, encoding="utf-8") as f:
            ot = json.load(f)
        if ot.get("dizilis") != DIZILIS:
            ot = None
        else:
            log("   kayitli elle oturtma kullaniliyor (Saved/MerdivenOrnek.json)")
    if ot:
        log("3/3 %d merdiven elle oturtulan ornege gore diziliyor..." % len(moduller))
        for o in moduller:
            konum, donus, olc = oturus_uygula(ot, cerceve(o, dunya))
            koy(sm, o, konum, donus, olc, malz)
        les.save_current_level()
        log("TAMAM - %d merdiven ornege gore dizildi. Birini yine elle duzeltip secili birakarak tekrar calistirabilirsin."
            % len(moduller))
        return

    log("2/3 Fab merdiveni inceleniyor...")
    mn, mx = kutu(sm)
    ek, isaret = yukselis_yonu(sm)
    yan = "y" if ek == "x" else "x"
    ie, iy = "xyz".index(ek), "xyz".index(yan)
    boy = (mx[ie] - mn[ie], mx[iy] - mn[iy], mx[2] - mn[2])     # derinlik, genislik, yukseklik (cm)
    log("   model %s: derinlik %.0f, genislik %.0f, yukseklik %.0f cm" % (sm.get_name(), boy[0], boy[1], boy[2]))
    yerel_on = [0.0, 0.0, mn[2]]                                  # en alt basamagin onu, ortada, tabanda
    yerel_on[ie] = mn[ie] if isaret > 0 else mx[ie]
    yerel_on[iy] = (mn[iy] + mx[iy]) / 2
    alfa = math.atan2(isaret if ek == "y" else 0.0, isaret if ek == "x" else 0.0)

    log("3/3 %d modul diziliyor (%s)..." % (len(moduller), DIZILIS))
    dw = ues.get_editor_world()
    uyum, on_sira, olcekler = 0, 0, []
    for o in moduller:
        yon = o["yon"]
        gen_yon = (-yon[2], 0.0, yon[0])
        F = dunya(o["on"])
        A = dunya(topla(o["on"], yon, o["derinlik"]))
        U = dunya(topla(o["on"], (0.0, 1.0, 0.0), o["yukseklik"]))
        G = dunya(topla(o["on"], gen_yon, o["genislik"]))
        D = fark(A, F)
        derin = math.hypot(D[0], D[1])
        gen = math.sqrt(sum(c * c for c in fark(G, F)))
        yuk = U[2] - F[2]
        if o["sira"] == 0:      # on siranin altinda yurume yolu olmali (eksenlerin dogrulugu icin)
            z = isin(dw, (F[0], F[1], F[2] + 300), (F[0], F[1], F[2] - 300))
            if z is not None and abs(z - F[2]) < 80:
                uyum += 1
            on_sira += 1
        yaw = math.degrees(math.atan2(D[1], D[0]) - alfa)
        olc = [1.0, 1.0, yuk / boy[2]]
        olc[ie], olc[iy] = derin / boy[0], gen / boy[1]
        olcekler.append(olc)
        c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        px, py, pz = (yerel_on[0] * olc[0], yerel_on[1] * olc[1], yerel_on[2] * olc[2])
        konum = (F[0] - (px * c - py * s), F[1] - (px * s + py * c), F[2] - pz)
        koy(sm, o, konum, unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw), olc, malz)
    les.save_current_level()
    oz = lambda i: "%.2f-%.2f" % (min(o[i] for o in olcekler), max(o[i] for o in olcekler))
    log("   olcek araliklari: X %s, Y %s, Z %s" % (oz(0), oz(1), oz(2)))
    log("   on kenar zemin kontrolu: %d/%d on sira modulunun altinda yurume yolu bulundu" % (uyum, on_sira))
    if uyum < on_sira // 2:
        unreal.log_error("[Merdiven] Modullerin cogu yurume yolunun uzerinde degil - eksenler ters olabilir. Bu satirlari gonder.")
    log("TAMAM - %d Fab merdiveni dizildi (Outliner: %s). Oturmadiysa birini elle oturt, secili birakip tekrar calistir."
        % (len(moduller), KLASOR))


# --- YERLESIM BASI (araclar/bolge_doku/merdiven_yerlesim.py yazar, elle degistirme) ---
ALANLAR = ('dilim', 'sira', 'sutun', 'on', 'yon', 'derinlik', 'genislik', 'yukseklik')
YERLESIM = {
    'dogal': [
        ("ates_1", 0, 0, [-24.519, 27.97, -15.311], [-0.987, 0.0, -0.1607], 1.902, 5.554, 1.734),
        ("ates_1", 1, 0, [-26.389, 29.674, -15.615], [-0.987, 0.0, -0.1607], 1.902, 5.907, 1.704),
        ("ates_2", 0, 0, [-19.975, 27.97, -20.627], [-0.8259, 0.0, -0.5638], 2.761, 4.479, 1.933),
        ("ates_2", 1, 0, [-22.243, 29.873, -22.179], [-0.8259, 0.0, -0.5638], 2.761, 5.018, 1.903),
        ("ates_2", 0, 1, [-17.527, 27.97, -23.561], [-0.7043, 0.0, -0.7099], 2.762, 4.492, 1.933),
        ("ates_2", 1, 1, [-19.467, 29.873, -25.51], [-0.7043, 0.0, -0.7099], 2.762, 5.018, 1.903),
        ("ates_3", 0, 0, [-11.744, 27.97, -29.039], [-0.5516, 0.0, -0.8341], 2.893, 4.656, 1.983),
        ("ates_3", 1, 0, [-13.335, 29.923, -31.451], [-0.5516, 0.0, -0.8341], 2.893, 4.965, 1.953),
        ("ates_3", 0, 1, [-8.477, 27.97, -31.886], [-0.4612, 0.0, -0.8873], 2.493, 4.701, 1.983),
        ("ates_3", 1, 1, [-9.626, 29.923, -34.094], [-0.4612, 0.0, -0.8873], 2.493, 4.965, 1.953),
        ("su_1", 0, 0, [6.897, 27.97, -31.682], [0.4281, 0.0, -0.9037], 2.531, 4.522, 1.983),
        ("su_1", 1, 0, [7.981, 29.923, -33.961], [0.4281, 0.0, -0.9037], 2.531, 4.92, 1.953),
        ("su_1", 0, 1, [9.873, 27.97, -29.01], [0.5651, 0.0, -0.825], 2.951, 4.439, 1.983),
        ("su_1", 1, 1, [11.533, 29.923, -31.439], [0.5651, 0.0, -0.825], 2.951, 4.92, 1.953),
        ("su_2", 0, 0, [15.736, 27.97, -23.618], [0.6909, 0.0, -0.723], 2.729, 4.702, 1.909),
        ("su_2", 1, 0, [17.613, 29.849, -25.575], [0.6909, 0.0, -0.723], 2.729, 5.337, 1.879),
        ("su_2", 0, 1, [18.405, 27.97, -20.732], [0.8393, 0.0, -0.5437], 2.622, 4.706, 1.909),
        ("su_2", 1, 1, [20.589, 29.849, -22.15], [0.8393, 0.0, -0.5437], 2.622, 5.336, 1.879),
        ("su_3", 0, 0, [22.228, 27.97, -14.909], [0.9414, 0.0, -0.3373], 2.27, 4.528, 1.655),
        ("su_3", 1, 0, [24.359, 29.595, -15.672], [0.9414, 0.0, -0.3373], 2.27, 4.879, 1.625),
    ],
    'dik': [
        ("ates_1", 0, 0, [-24.519, 27.97, -15.311], [-0.987, 0.0, -0.1607], 1.902, 5.554, 3.135),
        ("ates_1", 1, 0, [-26.389, 31.075, -15.615], [-0.987, 0.0, -0.1607], 1.902, 5.907, 3.105),
        ("ates_2", 0, 0, [-19.975, 27.97, -20.627], [-0.8259, 0.0, -0.5638], 2.761, 4.479, 2.971),
        ("ates_2", 1, 0, [-22.243, 30.911, -22.179], [-0.8259, 0.0, -0.5638], 2.761, 5.018, 2.941),
        ("ates_2", 0, 1, [-17.527, 27.97, -23.561], [-0.7043, 0.0, -0.7099], 2.762, 4.492, 2.971),
        ("ates_2", 1, 1, [-19.467, 30.911, -25.51], [-0.7043, 0.0, -0.7099], 2.762, 5.018, 2.941),
        ("ates_3", 0, 0, [-11.744, 27.97, -29.039], [-0.5516, 0.0, -0.8341], 2.893, 4.656, 3.067),
        ("ates_3", 1, 0, [-13.335, 31.007, -31.451], [-0.5516, 0.0, -0.8341], 2.893, 4.965, 3.037),
        ("ates_3", 0, 1, [-8.477, 27.97, -31.886], [-0.4612, 0.0, -0.8873], 2.493, 4.701, 3.067),
        ("ates_3", 1, 1, [-9.626, 31.007, -34.094], [-0.4612, 0.0, -0.8873], 2.493, 4.965, 3.037),
        ("su_1", 0, 0, [6.897, 27.97, -31.682], [0.4281, 0.0, -0.9037], 2.531, 4.522, 3.074),
        ("su_1", 1, 0, [7.981, 31.014, -33.961], [0.4281, 0.0, -0.9037], 2.531, 4.92, 3.044),
        ("su_1", 0, 1, [9.873, 27.97, -29.01], [0.5651, 0.0, -0.825], 2.951, 4.439, 3.074),
        ("su_1", 1, 1, [11.533, 31.014, -31.439], [0.5651, 0.0, -0.825], 2.951, 4.92, 3.044),
        ("su_2", 0, 0, [15.736, 27.97, -23.618], [0.6909, 0.0, -0.723], 2.729, 4.702, 2.807),
        ("su_2", 1, 0, [17.613, 30.747, -25.575], [0.6909, 0.0, -0.723], 2.729, 5.337, 2.777),
        ("su_2", 0, 1, [18.405, 27.97, -20.732], [0.8393, 0.0, -0.5437], 2.622, 4.706, 2.807),
        ("su_2", 1, 1, [20.589, 30.747, -22.15], [0.8393, 0.0, -0.5437], 2.622, 5.336, 2.777),
        ("su_3", 0, 0, [22.228, 27.97, -14.909], [0.9414, 0.0, -0.3373], 2.27, 4.528, 2.787),
        ("su_3", 1, 0, [24.359, 30.727, -15.672], [0.9414, 0.0, -0.3373], 2.27, 4.879, 2.757),
    ],
}
# --- YERLESIM SONU ---

calistir()
