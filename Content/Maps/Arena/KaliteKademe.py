# Unreal Engine 5 - Kademeli kalite + performans (oyun kasmasin diye).
# Oyun alani tam kalite; ondan uzaklastikca golgeler, efektler ve kucuk nesneler kademeli olarak azalir.
# Calistirma (Output Log -> Python):
#   exec(open(unreal.Paths.project_content_dir() + "Maps/Arena/KaliteKademe.py", encoding="utf-8").read())
# Yeni agac/kaya/efekt ekledikten sonra tekrar calistir; zarari yok.
import math
import unreal

# ---------------- AYARLAR ----------------
HARITA = "/Game/MAPS/Arena_Map"
ASET_KLASORLERI = ["/Game/MAPS/Asetler"]
YAKIN = 4000.0       # cm - merkezden bu mesafeye kadar 1. halka: tam kalite
ORTA = 10000.0       # cm - 2. halka: kucuk nesnelerin golgesi kapanir; disi 3. halka: efektler de seyrelir
DOKU_SINIRI = 2048   # dekor dokulari en fazla bu cozunurlukte (4K gereksiz bellek yer)
SIS_AYARLA = False   # True: sisi buradan ayarla (BolgeSahasi.py bulut denizi sisini kendisi kurar)
# -----------------------------------------

eal = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)


def log(msg):
    unreal.log_warning("[Arena] " + msg)


def dene(is_, aciklama):
    try:
        is_()
        return True
    except Exception as e:
        log("   %s yapilamadi (onemsiz): %s" % (aciklama, e))
        return False


def aset_listesi(sinif):
    for k in ASET_KLASORLERI:
        if not eal.does_directory_exist(k):
            continue
        for yol in eal.list_assets(k, recursive=True, include_folder=False):
            a = eal.load_asset(yol)
            if isinstance(a, sinif):
                yield a


def nanite_ac():
    """Nanite = geometri icin otomatik, dikissiz kademeli detay (uzaktaki agac az ucgenle cizilir)."""
    n = 0
    for m in aset_listesi(unreal.StaticMesh):
        ns = m.get_editor_property("nanite_settings")
        if ns.get_editor_property("enabled"):
            continue
        ns.set_editor_property("enabled", True)
        m.set_editor_property("nanite_settings", ns)
        eal.save_loaded_asset(m)
        n += 1
    log("   %d mesh'te Nanite acildi" % n)


def dokulari_duzelt():
    """Normal/puruzluluk haritalarini dogru sikistirmaya al, cozunurlugu sinirla (EXR'ler dahil)."""
    T = unreal.TextureCompressionSettings
    n = 0
    for t in aset_listesi(unreal.Texture2D):
        ad = t.get_name().lower()
        if "nor" in ad or "normal" in ad:
            ayar, srgb, grup = T.TC_NORMALMAP, False, unreal.TextureGroup.TEXTUREGROUP_WORLD_NORMAL_MAP
        elif "rough" in ad:
            ayar, srgb, grup = T.TC_MASKS, False, unreal.TextureGroup.TEXTUREGROUP_WORLD
        else:
            ayar, srgb, grup = T.TC_DEFAULT, True, unreal.TextureGroup.TEXTUREGROUP_WORLD
        t.set_editor_property("compression_settings", ayar)
        t.set_editor_property("srgb", srgb)
        t.set_editor_property("lod_group", grup)
        t.set_editor_property("max_texture_size", DOKU_SINIRI)
        eal.save_loaded_asset(t)
        n += 1
    log("   %d doku ayarlandi" % n)


def haritayi_ac():
    dunya = ues.get_editor_world()
    if dunya is None or dunya.get_name() != "Arena_Map":
        log("Arena_Map aciliyor...")
        if not les.load_level(HARITA):
            raise RuntimeError("Harita acilamadi: " + HARITA)


def arena_ve_merkez():
    for a in eas.get_all_level_actors():
        if isinstance(a, unreal.StaticMeshActor):
            sm = a.static_mesh_component.get_editor_property("static_mesh")
            if sm and "arena_game" in sm.get_name().lower():
                p = a.get_actor_location()
                return a, (p.x, p.y, p.z + 2300.0 * a.get_actor_scale3d().z)
    return None, (0.0, 0.0, 2300.0)


def uzaklik(a, cx, cy):
    p = a.get_actor_location()
    return math.hypot(p.x - cx, p.y - cy)


def cizim_mesafesi(boyut):
    """Kucuk nesne erken kaybolur, buyuk nesne hic kaybolmaz (0 = sinirsiz)."""
    if boyut >= 1500:
        return 0.0
    return max(4000.0, min(30000.0, boyut * 40.0))


NIAGARA = getattr(unreal, "NiagaraActor", type(None))


def sahneyi_kademele(arena, cx, cy, cz):
    sayac = {"mesh": 0, "golge": 0, "efekt": 0, "isik": 0}
    for a in eas.get_all_level_actors():
        if a == arena or a.get_actor_label().startswith("ES_"):
            continue  # arena Nanite ile zaten kademeli; oyun alani nesneleri tam kalite kalir
        d = uzaklik(a, cx, cy)

        if isinstance(a, unreal.StaticMeshActor):
            c = a.static_mesh_component
            _, ext = a.get_actor_bounds(False)
            boyut = 2.0 * max(ext.x, ext.y, ext.z)
            dene(lambda: c.set_editor_property("ld_max_draw_distance", cizim_mesafesi(boyut)), "cizim mesafesi")
            if d > ORTA and boyut < 500:
                c.set_editor_property("cast_shadow", False)
                sayac["golge"] += 1
            sayac["mesh"] += 1

        elif isinstance(a, NIAGARA):
            c = a.niagara_component
            c.set_editor_property("cast_shadow", False)
            if d > YAKIN:
                # oyun alanindan uzaktaki efektler kamera uzaklasinca cizilmez
                dene(lambda: c.set_editor_property("ld_max_draw_distance", 6000.0 if d > ORTA else 12000.0), "efekt mesafesi")
            sayac["efekt"] += 1

        elif isinstance(a, (unreal.PointLight, unreal.SpotLight)):
            lc = a.light_component
            if d > YAKIN:
                lc.set_cast_shadows(False)
            dene(lambda: lc.set_editor_property("max_draw_distance", 8000.0 if d > YAKIN else 15000.0), "isik mesafesi")
            dene(lambda: lc.set_editor_property("max_distance_fade_range", 1500.0), "isik solma")
            sayac["isik"] += 1

        elif SIS_AYARLA and isinstance(a, unreal.ExponentialHeightFog):
            fc = a.component
            a.set_actor_location(unreal.Vector(cx, cy, cz - 1000.0), False, False)
            dene(lambda: fc.set_editor_property("start_distance", YAKIN), "sis baslangici")
            dene(lambda: fc.set_editor_property("fog_density", 0.02), "sis yogunlugu")
            dene(lambda: fc.set_editor_property("fog_height_falloff", 0.2), "sis dususu")
            dene(lambda: fc.set_editor_property("enable_volumetric_fog", False), "hacimsel sis")
            log("   sis ayarlandi (oyun alani net, uzak cevre yumusak)")
    log("   %d mesh (%d golgesi kapatildi), %d efekt, %d isik" %
        (sayac["mesh"], sayac["golge"], sayac["efekt"], sayac["isik"]))


def calistir():
    log("1/4 Dekor mesh'lerinde Nanite (birkac dakika surebilir)...")
    nanite_ac()
    log("2/4 Dokular...")
    dokulari_duzelt()
    log("3/4 Sahne halkalara gore kademeleniyor...")
    haritayi_ac()
    arena, (cx, cy, cz) = arena_ve_merkez()
    sahneyi_kademele(arena, cx, cy, cz)
    log("4/4 Kaydediliyor...")
    les.save_current_level()
    log("TAMAM - Kademeli kalite uygulandi. Halka mesafeleri dosyanin basinda (YAKIN, ORTA).")


calistir()
