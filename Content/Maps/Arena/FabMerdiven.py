# Unreal Engine 5 - Fab'dan indirilen "Castle Stairs" (Megascans scfdy) merdivenlerini ates ve su tribunlerine dizer.
# Her oturma diliminde (ara bolmeler arasinda) iki sira modul: on sira 28 m yurume yolundan baslar, arka sira onun
# ustunden duvara cikar. Moduller tribun duvarina diktir, yan yana hafif binerek bosluksuz dizilir.
# Yerlesim: Kaynak/merdiven_yerlesim.json (araclar/bolge_doku/merdiven_yerlesim.py, arena glTF eksenleri, metre).
# Eski uretilmis basamaklar (BK_Basamak) silinir.
# Calistirma (Output Log -> Python):
#   exec(open(unreal.Paths.project_content_dir() + "Maps/Arena/FabMerdiven.py", encoding="utf-8").read())
# Tekrar calistirmak zararsiz. Kaldirmak icin KALDIR = True.
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


def calistir():
    arena = arena_aktoru()
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

    log("1/4 Eksenler olculuyor...")
    harita, birim = eksen_haritasi()
    dunya = dunya_donusumu(arena, harita, birim)
    log("2/4 Fab merdiveni inceleniyor...")
    sm = merdiven_mesh()
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
    malz = bolge_malzemeleri(sm)

    log("3/4 Yerlesim okunuyor (%s)..." % DIZILIS)
    yol = os.path.join(KAYNAK, "merdiven_yerlesim.json")
    if not os.path.isfile(yol):
        hata("merdiven_yerlesim.json bulunamadi: " + KAYNAK)
    with open(yol, encoding="utf-8") as f:
        tum = json.load(f)
    if DIZILIS not in tum:
        hata("DIZILIS '%s' yok; secenekler: %s" % (DIZILIS, ", ".join(tum)))
    moduller = tum[DIZILIS]

    log("4/4 %d modul diziliyor..." % len(moduller))
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
        a = eas.spawn_actor_from_object(sm, V(*konum), unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw))
        a.set_actor_scale3d(V(*olc))
        a.set_actor_label("%s_%s_%d_%d" % (ETIKET, o["dilim"], o["sira"], o["sutun"]))
        a.set_folder_path(KLASOR)
        bolge = o["dilim"].split("_")[0]
        if bolge in malz:
            a.static_mesh_component.set_material(0, malz[bolge])
    les.save_current_level()
    oz = lambda i: "%.2f-%.2f" % (min(o[i] for o in olcekler), max(o[i] for o in olcekler))
    log("   olcek araliklari: X %s, Y %s, Z %s" % (oz(0), oz(1), oz(2)))
    log("   on kenar zemin kontrolu: %d/%d on sira modulunun altinda yurume yolu bulundu" % (uyum, on_sira))
    if uyum < on_sira // 2:
        unreal.log_error("[Merdiven] Modullerin cogu yurume yolunun uzerinde degil - eksenler ters olabilir. Bu satirlari gonder.")
    log("TAMAM - %d Fab merdiveni dizildi (Outliner: %s). Yon ters ise YUKSELIS ayarla; DIZILIS = \"dik\" terasa kadar cikar."
        % (len(moduller), KLASOR))


calistir()
