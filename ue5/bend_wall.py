"""
UE5 - Bukulen Duvar (Spline Mesh) olusturucu

Duvar mesh'ini bir spline cizgisi boyunca dizer, her parcayi yumusakca buker
ve arka yuzunu arenanin yan yuzune yaslar. Arenanin cizginin hangi tarafinda
oldugunu ve duvarin cizgiden asagi mi yukari mi uzanacagini kendisi bulur.

KULLANIM:
  1. Sahnede spline'li actor'u (BP_WallPath) sec.
  2. Alttaki Cmd kutusuna:  py "C:\\Users\\...\\bend_wall.py"
Tekrar calistirinca eski duvarlar silinip yeniden olusur. Ctrl+Z geri alir.
"""

import math

import unreal

# ============================ AYARLAR ============================
WALL_MESH_PATH = "/Game/Fab/Megascans/3D/Castle_Wall_sctv3/Medium/sctv3_tier_2/StaticMeshes/sctv3_tier_2.sctv3_tier_2"
MODE = "spline"            # "spline" = secili BP_WallPath cizgisi, "circle" = daire

AUTO_SIDE = True           # Arenanin cizginin hangi tarafinda oldugunu kendisi bulur
FLIP = False               # Sadece AUTO_SIDE = False iken: duvar arenanin icine giriyorsa True
FRONT_FACE = "+"           # Kemerli on yuz arenaya bakiyorsa "-" yap
VERTICAL_ALIGN = "auto"    # "auto", "top" (duvarin ustu cizgide), "bottom" (alti cizgide), "none"
SIDE_OFFSET = 0.0          # cm: + duvari arenadan uzaklastirir, - arenaya yaklastirir
UP_OFFSET = 0.0            # cm: + yukari, - asagi

SEGMENT_LENGTH = 0.0       # Bir parcanin boyu (cm). 0 = duvarin kendi boyu
OVERLAP = 30.0             # cm: parcalar arasinda bosluk kaliyorsa artir (ornek 50)
FORWARD_AXIS = "auto"      # Duvarin uzunlugu hangi eksende: "auto", "X" veya "Y"
ROLL_DEG = "auto"          # Duvar yatik/ters duruyorsa: 0, 90, -90 veya 180 dene

CIRCLE_CENTER = (0.0, 0.0, 0.0)   # circle modu: arenanin merkezi
CIRCLE_RADIUS = 2000.0            # circle modu: yaricap (cm)
CIRCLE_START_DEG = 0.0            # circle modu: baslangic acisi
CIRCLE_END_DEG = 360.0            # circle modu: bitis acisi (360 = tam daire)

FOLDER = "BendWall"        # Her cizginin duvarlari BendWall/<cizgi adi> klasorune konur
CLEAR_PREVIOUS = True      # Ayni cizginin onceki duvarlarini sil (diger cizgilere dokunmaz)
# =================================================================

PROBE_SIDE = 150.0         # Arenayi bulmak icin cizginin iki yanina bakilan mesafe (cm)
PROBE_UP = 3000.0          # Asagi atilan isinlarin baslangic yuksekligi (cm)
PROBE_DEPTH = 20000.0      # Asagi atilan isinlarin uzunlugu (cm)

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
        if mesh is None:
            # Content Browser secimi yoksa: sahnede secili duvar actor'unun mesh'ini al
            for actor in actor_sub.get_selected_level_actors():
                comp = actor.get_component_by_class(unreal.StaticMeshComponent)
                if comp and not isinstance(comp, unreal.SplineMeshComponent) and comp.static_mesh:
                    mesh = comp.static_mesh
                    break
    if not isinstance(mesh, unreal.StaticMesh):
        found = ", ".join("%s (%s)" % (a.get_name(), a.get_class().get_name())
                          for a in unreal.EditorUtilityLibrary.get_selected_assets()) or "hicbir sey"
        raise RuntimeError("Duvar mesh'i bulunamadi. Content Browser'da secili: %s. "
                           "Bir Static Mesh sec veya WALL_MESH_PATH'i doldur." % found)
    return mesh


def mesh_layout(mesh):
    """Duvarin uzunluk eksenini secer.
    (eksen, uzunluk, yan_min, yan_max, alt_z, ust_z, roll_derece, yan_isaret)
    yan_isaret: mesh'in yan ekseni dunyada cizginin sagina (+1) mi soluna (-1) mi gidiyor."""
    box = mesh.get_bounding_box()
    size_x = box.max.x - box.min.x
    size_y = box.max.y - box.min.y
    forward = FORWARD_AXIS.upper()
    if forward not in ("X", "Y"):
        forward = "X" if size_x >= size_y else "Y"
    unreal.log("Bend Wall: mesh boyutu X=%.0f Y=%.0f Z=%.0f cm, uzunluk ekseni=%s"
               % (size_x, size_y, box.max.z - box.min.z, forward))
    if forward == "Y":
        # Spline mesh Y ileri iken mesh'in Z'si yana duser; -90 roll duvari dik tutar
        # ve mesh'in X ekseni cizginin soluna bakar.
        roll = -90.0 if ROLL_DEG == "auto" else float(ROLL_DEG)
        return (unreal.SplineMeshAxis.Y, size_y, box.min.x, box.max.x,
                box.min.z, box.max.z, roll, -1)
    roll = 0.0 if ROLL_DEG == "auto" else float(ROLL_DEG)
    return (unreal.SplineMeshAxis.X, size_x, box.min.y, box.max.y,
            box.min.z, box.max.z, roll, 1)


def spline_path():
    """(toplam uzunluk, sample(d) -> (konum, birim yon), tangent_boyu(seg), cizgi adi)"""
    spline = None
    for actor in actor_sub.get_selected_level_actors():
        spline = actor.get_component_by_class(unreal.SplineComponent)
        if spline:
            name = actor.get_actor_label()
            break
    if not spline:
        raise RuntimeError("Sahnede Spline component'i olan bir actor sec (ornek: BP_WallPath).")

    world = unreal.SplineCoordinateSpace.WORLD

    def sample(d):
        loc = spline.get_location_at_distance_along_spline(d, world)
        tan = spline.get_tangent_at_distance_along_spline(d, world)
        return loc, tan.normal()

    return spline.get_spline_length(), sample, lambda seg: seg, name


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

    return r * abs(a1 - a0), sample, tangent_len, "Daire"


def editor_world():
    try:
        return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    except Exception:
        return unreal.EditorLevelLibrary.get_editor_world()


def ground_z(world, x, y, z):
    """(x, y) noktasinda yukaridan asagi isin atar, carptigi yuzeyin yuksekligini dondurur."""
    start = unreal.Vector(x, y, z + PROBE_UP)
    end = unreal.Vector(x, y, z - PROBE_DEPTH)
    channel = getattr(unreal.TraceTypeQuery, "ECC_VISIBILITY", None) or unreal.TraceTypeQuery.TRACE_TYPE_QUERY1
    for complex_trace in (True, False):
        hit = unreal.SystemLibrary.line_trace_single(
            world, start, end, channel, complex_trace, [], unreal.DrawDebugTrace.NONE, True)
        if isinstance(hit, tuple):  # bazi surumler (bool, HitResult) dondurur
            hit = hit[1] if hit and hit[0] else None
        if not hit:
            continue
        # HitResult.to_tuple(): (blocking_hit, initial_overlap, time, distance, location, ...)
        parts = hit.to_tuple()
        if isinstance(parts[0], bool) and not parts[0]:  # blocking_hit yok
            continue
        location = next((v for v in parts if isinstance(v, unreal.Vector)), None)
        if location is not None:
            return location.z
    return None


def right_of(direction):
    """Cizgi yonune gore yatay sag vektor (spline mesh'in +Y yonu)."""
    r = unreal.Vector(-direction.y, direction.x, 0.0)
    size = math.sqrt(r.x * r.x + r.y * r.y)
    return None if size < 1e-4 else r * (1.0 / size)


def detect_side(sample, length):
    """Cizginin hangi yani bos (alcak): +1 = sag, -1 = sol, 0 = bulunamadi.
    Ayrica bos taraftaki zeminin cizgiden ne kadar asagida oldugu (cm)."""
    world = editor_world()
    votes = 0
    drops = []
    hits_r = hits_l = 0
    n = 16
    for k in range(n):
        p, t = sample(length * (k + 0.5) / n)
        r = right_of(t)
        if r is None:
            continue
        zr = ground_z(world, p.x + r.x * PROBE_SIDE, p.y + r.y * PROBE_SIDE, p.z)
        zl = ground_z(world, p.x - r.x * PROBE_SIDE, p.y - r.y * PROBE_SIDE, p.z)
        hits_r += zr is not None
        hits_l += zl is not None
        low = -1.0e9
        hr = zr if zr is not None else low
        hl = zl if zl is not None else low
        if abs(hr - hl) < 20.0:
            continue
        open_side = 1 if hr < hl else -1
        votes += open_side
        lower = min(hr, hl)
        drops.append(p.z - lower if lower > low else PROBE_DEPTH)
    unreal.log("Bend Wall: isin carpmalari sag=%d/%d sol=%d/%d" % (hits_r, n, hits_l, n))
    drops.sort()
    drop = drops[len(drops) // 2] if drops else None
    return (1 if votes > 0 else -1 if votes < 0 else 0), drop


def clear_previous(folder):
    for actor in actor_sub.get_all_level_actors():
        if isinstance(actor, unreal.SplineMeshActor) and str(actor.get_folder_path()) == folder:
            actor_sub.destroy_actor(actor)


def main():
    mesh = load_mesh()

    try:
        if mesh.get_editor_property("nanite_settings").get_editor_property("enabled"):
            unreal.log_warning("Mesh Nanite acik. Bukulme gorunmezse mesh'te Nanite'i kapat "
                               "veya Project Settings > Nanite > Allow Nanite on Spline Meshes ac.")
    except Exception:
        pass

    length, sample, tangent_len, path_name = circle_path() if MODE == "circle" else spline_path()
    folder = "%s/%s" % (FOLDER, path_name)
    axis, mesh_len, side_min, side_max, bottom_z, top_z, roll_deg, sigma = mesh_layout(mesh)
    roll = math.radians(roll_deg)

    target = SEGMENT_LENGTH if SEGMENT_LENGTH > 0 else mesh_len
    if target <= 0:
        raise RuntimeError("Mesh uzunlugu 0 cikti; FORWARD_AXIS ayarini kontrol et.")
    count = max(1, round(length / target))
    seg = length / count  # parcalar yolu tam doldursun diye hafifce esnetilir

    with unreal.ScopedEditorTransaction("Bend Wall"):
        if CLEAR_PREVIOUS:
            clear_previous(folder)

        # Kemerli on yuz bos tarafa, arka yuz arenaya baksin
        front = -1 if FRONT_FACE.startswith("-") else 1
        flip = FLIP
        vertical = VERTICAL_ALIGN
        if AUTO_SIDE or vertical == "auto":
            open_side, drop = detect_side(sample, length)
            if AUTO_SIDE:
                if open_side == 0:
                    unreal.log_warning("Bend Wall: arena bulunamadi (collision yok mu?). FLIP ayari kullaniliyor.")
                else:
                    flip = sigma * front != open_side
            if vertical == "auto":
                vertical = "none" if drop is None else ("top" if drop > 50.0 else "bottom")
            unreal.log("Bend Wall: bos taraf=%s, zemin farki=%s cm, flip=%s, dikey=%s"
                       % ({1: "sag", -1: "sol", 0: "?"}[open_side], drop, flip, vertical))

        back = side_min if front == 1 else side_max     # arka yuz cizgiye oturur
        side = -sigma * back + SIDE_OFFSET * sigma * front
        up = {"top": -top_z, "bottom": -bottom_z}.get(vertical, 0.0) + UP_OFFSET
        offset = unreal.Vector2D(side, up)

        def point(d):
            if flip:
                loc, direction = sample(length - d)
                return loc, direction * -1.0
            return sample(d)

        for i in range(count):
            # Megascans parcalarinin uclari kirik; parcalari biraz uzatip ust uste bindiriyoruz
            d0 = max(0.0, i * seg - OVERLAP)
            d1 = min(length, (i + 1) * seg + OVERLAP)
            tan_len = tangent_len(d1 - d0)
            p0, t0 = point(d0)
            p1, t1 = point(d1)

            actor = actor_sub.spawn_actor_from_class(unreal.SplineMeshActor, p0)
            actor.set_actor_label("%s_Duvar_%03d" % (path_name, i))
            actor.set_folder_path(folder)

            comp = actor.get_component_by_class(unreal.SplineMeshComponent)
            comp.set_static_mesh(mesh)
            comp.set_forward_axis(axis, False)
            comp.set_start_offset(offset, False)
            comp.set_end_offset(offset, False)
            comp.set_start_roll(roll, False)
            comp.set_end_roll(roll, False)
            # Actor p0'da ve donmesiz duruyor, bu yuzden konumlar p0'a gore yerel
            comp.set_start_and_end(unreal.Vector(0.0, 0.0, 0.0), t0 * tan_len,
                                   p1 - p0, t1 * tan_len, True)

    unreal.log("Bend Wall: %d parca olusturuldu (parca boyu %.1f cm), klasor: %s." % (count, seg, folder))


main()
