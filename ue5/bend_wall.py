"""
UE5 - Bukulen Duvar (Spline Mesh) olusturucu

Indirdigin duvar mesh'ini bir spline boyunca (veya bir daire etrafinda)
art arda dizer ve her parcayi yumusakca buker.

KURULUM (bir kere):
  1. Edit > Plugins > "Python Editor Script Plugin" ac, editoru yeniden baslat.

KULLANIM - "spline" modu (arenanin seklini sen cizersin):
  1. Content Browser > sag tik > Blueprint Class > Actor. Adi: BP_WallPath
     Ac, sol ustten Add > Spline ekle, Compile, Save. Sahneye surukle.
  2. Spline noktalarini arenanin kenari boyunca yerlestir
     (Alt + surukle = yeni nokta). Noktalar zemine otursun istersen
     noktaya sag tik > Snap to Floor.
  3. Sahnede BP_WallPath'i sec, Content Browser'da duvar mesh'ini sec.
  4. Tools > Execute Python Script... > bu dosyayi sec.

KULLANIM - "circle" modu (yuvarlak arena):
  MODE = "circle" yap, CIRCLE_CENTER ve CIRCLE_RADIUS'u arenana gore gir,
  duvar mesh'ini Content Browser'da sec ve scripti calistir.

Script tekrar calistirildiginda onceki duvarlari silip yeniden olusturur.
Ctrl+Z ile geri alinabilir.
"""

import math

import unreal

# ============================ AYARLAR ============================
WALL_MESH_PATH = ""        # Bos = Content Browser'da secili mesh. Ya da: "/Game/Walls/SM_Wall"
MODE = "spline"            # "spline" veya "circle"
SEGMENT_LENGTH = 0.0       # Bir parcanin boyu (cm). 0 = duvarin kendi boyu
FORWARD_AXIS = "X"         # Duvarin uzunlugu hangi eksende: "X" veya "Y"
FLIP = False               # Duvarin on yuzu ters tarafa bakiyorsa True yap

CIRCLE_CENTER = (0.0, 0.0, 0.0)   # circle modu: arenanin merkezi
CIRCLE_RADIUS = 2000.0            # circle modu: yaricap (cm)
CIRCLE_START_DEG = 0.0            # circle modu: baslangic acisi
CIRCLE_END_DEG = 360.0            # circle modu: bitis acisi (360 = tam daire)

FOLDER = "BendWall"        # Olusan actor'lar World Outliner'da bu klasore konur
CLEAR_PREVIOUS = True      # Onceki calistirmadan kalan duvarlari sil
# =================================================================

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def load_mesh():
    if WALL_MESH_PATH:
        path = WALL_MESH_PATH
        if "'" in path:  # "Copy Reference" formati: /Script/Engine.StaticMesh'/Game/X.X'
            path = path.split("'")[1]
        mesh = unreal.load_asset(path)
    else:
        selected = unreal.EditorUtilityLibrary.get_selected_assets()
        mesh = next((a for a in selected if isinstance(a, unreal.StaticMesh)), None)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError("Duvar mesh'i bulunamadi: Content Browser'da bir Static Mesh sec "
                           "veya WALL_MESH_PATH'i doldur.")
    return mesh


def mesh_length(mesh):
    box = mesh.get_bounding_box()
    if FORWARD_AXIS.upper() == "Y":
        return box.max.y - box.min.y
    return box.max.x - box.min.x


def spline_path():
    """(toplam uzunluk, sample(d) -> (konum, birim yon), tangent_boyu(seg))"""
    spline = None
    for actor in actor_sub.get_selected_level_actors():
        spline = actor.get_component_by_class(unreal.SplineComponent)
        if spline:
            break
    if not spline:
        raise RuntimeError("Sahnede Spline component'i olan bir actor sec (ornek: BP_WallPath).")

    world = unreal.SplineCoordinateSpace.WORLD

    def sample(d):
        loc = spline.get_location_at_distance_along_spline(d, world)
        tan = spline.get_tangent_at_distance_along_spline(d, world)
        return loc, tan.normal()

    return spline.get_spline_length(), sample, lambda seg: seg


def circle_path():
    center = unreal.Vector(*CIRCLE_CENTER)
    r = CIRCLE_RADIUS
    a0 = math.radians(CIRCLE_START_DEG)
    a1 = math.radians(CIRCLE_END_DEG)

    def sample(d):
        a = a0 + d / r
        loc = center + unreal.Vector(math.cos(a) * r, math.sin(a) * r, 0.0)
        return loc, unreal.Vector(-math.sin(a), math.cos(a), 0.0)

    # Hermite tangent boyu: yay icin 4 * R * tan(aci / 4) neredeyse kusursuz daire verir
    def tangent_len(seg):
        return 4.0 * r * math.tan((seg / r) / 4.0)

    return r * abs(a1 - a0), sample, tangent_len


def clear_previous():
    for actor in actor_sub.get_all_level_actors():
        if isinstance(actor, unreal.SplineMeshActor) and str(actor.get_folder_path()) == FOLDER:
            actor_sub.destroy_actor(actor)


def main():
    mesh = load_mesh()

    try:
        if mesh.get_editor_property("nanite_settings").get_editor_property("enabled"):
            unreal.log_warning("Mesh Nanite acik. Bukulme gorunmezse mesh'te Nanite'i kapat "
                               "veya konsola 'r.Nanite.AllowSplineMeshes 1' yaz.")
    except Exception:
        pass

    length, sample, tangent_len = circle_path() if MODE == "circle" else spline_path()

    target = SEGMENT_LENGTH if SEGMENT_LENGTH > 0 else mesh_length(mesh)
    if target <= 0:
        raise RuntimeError("Mesh uzunlugu 0 cikti; FORWARD_AXIS ayarini kontrol et.")
    count = max(1, round(length / target))
    seg = length / count  # parcalar yolu tam doldursun diye hafifce esnetilir
    tan_len = tangent_len(seg)
    axis = unreal.SplineMeshAxis.Y if FORWARD_AXIS.upper() == "Y" else unreal.SplineMeshAxis.X

    def point(d):
        if FLIP:
            loc, direction = sample(length - d)
            return loc, direction * -1.0
        return sample(d)

    with unreal.ScopedEditorTransaction("Bend Wall"):
        if CLEAR_PREVIOUS:
            clear_previous()

        for i in range(count):
            p0, t0 = point(i * seg)
            p1, t1 = point((i + 1) * seg)

            actor = actor_sub.spawn_actor_from_class(unreal.SplineMeshActor, p0)
            actor.set_actor_label("BendWall_%03d" % i)
            actor.set_folder_path(FOLDER)

            comp = actor.get_component_by_class(unreal.SplineMeshComponent)
            comp.set_static_mesh(mesh)
            comp.set_forward_axis(axis, False)
            # Actor p0'da ve donmesiz duruyor, bu yuzden konumlar p0'a gore yerel
            comp.set_start_and_end(unreal.Vector(0.0, 0.0, 0.0), t0 * tan_len,
                                   p1 - p0, t1 * tan_len, True)

    unreal.log("Bend Wall: %d parca olusturuldu (parca boyu %.1f cm)." % (count, seg))


main()
