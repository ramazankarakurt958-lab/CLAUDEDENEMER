# -*- coding: utf-8 -*-
"""
Pota Kacti - "Arena" harita olusturucu (Unreal Engine 5 Editor Python)

Referans gorseldeki duzeni kurar:
  * Ortada desenli, yuvarlak dovus platformu (bosluk ustunde)
  * Etrafinda halka seklinde tribunler + dis sur duvari
  * 4 element bolgesi:  Kuzeybati = ATES,  Kuzeydogu = BUZ/SU,
                        Guneydogu = RUZGAR/BULUT,  Guneybati = DOGA
  * Merkezi halkaya baglayan yan kopruler (kuzey, dogu, bati)
  * Guneyde ana kapi
  * Etrafta ucan kayalar, gokyuzu, bulutlar, isiklar

ORTA ALTTAKI (guney) KOPRU EKLENMEZ  ->  ADD_SOUTH_BRIDGE = False

Kullanim: Arena haritasini ac -> Tools > Execute Python Script -> bu dosyayi sec.
Script yalnizca kendi olusturdugu ("PK_ArenaGen" etiketli) aktorleri siler;
haritadaki diger hicbir seye dokunmaz. Tekrar calistirilirsa eskisini silip
yeniden kurar. Tum islem tek bir Undo (Ctrl+Z) adimidir.
"""

import math
import random

import unreal

# ---------------------------------------------------------------------------
# AYARLAR
# ---------------------------------------------------------------------------
ADD_SOUTH_BRIDGE = False          # Orta alttaki uzun kopru (istenmedi)
ADD_SIDE_BRIDGES = True           # Kuzey / dogu / bati kopruleri
ADD_SKY_AND_LIGHTS = True         # Haritada yoksa gokyuzu, gunes, sis, bulut ekler
ADD_FLOATING_ROCKS = True
RANDOM_SEED = 1907

TAG = "PK_ArenaGen"
FOLDER = "ArenaGen"
MAT_DIR = "/Game/PotaKacti/ArenaGen/Materials"

# Olculer (cm)
CENTER_R = 2200.0                 # Orta platform yaricapi
RING_INNER_R = 4200.0             # Yurume halkasi ic kenari
WALK_OUTER_R = 5000.0             # Yurume halkasi dis kenari / tribun baslangici
STAND_TIERS = 6
STAND_TIER_DEPTH = 500.0
STAND_TIER_RISE = 250.0
WALL_R = WALK_OUTER_R + STAND_TIERS * STAND_TIER_DEPTH   # 8000
WALL_DEPTH = 350.0
WALL_H = 2600.0
SEGMENTS = 90                     # Halka parca sayisi (4 derece)

# Acilar: 0 = kuzey (+X), 90 = dogu (+Y), 180 = guney (kapi), 270 = bati
GATE_ANGLE = 180.0

CUBE = "/Engine/BasicShapes/Cube.Cube"
CYL = "/Engine/BasicShapes/Cylinder.Cylinder"
CONE = "/Engine/BasicShapes/Cone.Cone"
SPHERE = "/Engine/BasicShapes/Sphere.Sphere"

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
rng = random.Random(RANDOM_SEED)

_meshes = {}
_mats = {}


# ---------------------------------------------------------------------------
# Yardimci fonksiyonlar
# ---------------------------------------------------------------------------
def theme_of(angle):
    a = angle % 360.0
    if a >= 270.0:
        return "fire"
    if a < 90.0:
        return "ice"
    if a < 180.0:
        return "wind"
    return "nature"


def polar(r, angle_deg, z=0.0):
    a = math.radians(angle_deg)
    return unreal.Vector(r * math.cos(a), r * math.sin(a), z)


def mesh(path):
    if path not in _meshes:
        _meshes[path] = unreal.EditorAssetLibrary.load_asset(path)
    return _meshes[path]


def _tag_actor(actor, label):
    actor.set_actor_label(label)
    actor.set_folder_path(FOLDER)
    actor.set_editor_property("tags", [unreal.Name(TAG)])


def shape(label, path, loc, size, mat, yaw=0.0, pitch=0.0, roll=0.0):
    """size: santimetre cinsinden (x, y, z) boyut. Temel sekiller 100cm."""
    rot = unreal.Rotator(roll=roll, pitch=pitch, yaw=yaw)
    actor = actor_sub.spawn_actor_from_object(mesh(path), loc, rot)
    actor.set_actor_scale3d(unreal.Vector(size[0] / 100.0, size[1] / 100.0, size[2] / 100.0))
    if mat is not None:
        actor.static_mesh_component.set_material(0, _mats[mat])
    _tag_actor(actor, label)
    return actor


def box(label, loc, size, mat, yaw=0.0, pitch=0.0, roll=0.0):
    return shape(label, CUBE, loc, size, mat, yaw, pitch, roll)


def cyl(label, loc, radius, height, mat):
    return shape(label, CYL, loc, (radius * 2, radius * 2, height), mat)


def cone(label, loc, radius, height, mat, inverted=False):
    return shape(label, CONE, loc, (radius * 2, radius * 2, height), mat,
                 pitch=180.0 if inverted else 0.0)


def sphere(label, loc, size, mat):
    return shape(label, SPHERE, loc, size, mat)


def point_light(label, loc, color, intensity=8000.0, radius=1500.0):
    light = actor_sub.spawn_actor_from_class(unreal.PointLight, loc, unreal.Rotator())
    comp = light.point_light_component
    comp.set_light_color(unreal.LinearColor(*color, 1.0))
    comp.set_intensity(intensity)
    comp.set_attenuation_radius(radius)
    comp.set_editor_property("cast_shadows", False)
    _tag_actor(light, label)
    return light


def arc_box(label, r_in, r_out, a0, a1, z_bottom, z_top, mat):
    """Iki aci arasinda halka parcasi (kutu ile yaklasik)."""
    mid_a = (a0 + a1) * 0.5
    r_mid = (r_in + r_out) * 0.5
    arc = math.radians(a1 - a0) * r_out * 1.04
    return box(label, polar(r_mid, mid_a, (z_bottom + z_top) * 0.5),
               (r_out - r_in, arc, z_top - z_bottom), mat, yaw=mid_a)


# ---------------------------------------------------------------------------
# Materyaller
# ---------------------------------------------------------------------------
def build_materials():
    base_path = MAT_DIR + "/M_PK_Base"
    if unreal.EditorAssetLibrary.does_asset_exist(base_path):
        base = unreal.EditorAssetLibrary.load_asset(base_path)
    else:
        base = asset_tools.create_asset("M_PK_Base", MAT_DIR, unreal.Material,
                                        unreal.MaterialFactoryNew())
        color = mel.create_material_expression(base, unreal.MaterialExpressionVectorParameter, -600, -100)
        color.set_editor_property("parameter_name", "Color")
        color.set_editor_property("default_value", unreal.LinearColor(1, 1, 1, 1))
        emissive = mel.create_material_expression(base, unreal.MaterialExpressionScalarParameter, -600, 150)
        emissive.set_editor_property("parameter_name", "Emissive")
        emissive.set_editor_property("default_value", 0.0)
        rough = mel.create_material_expression(base, unreal.MaterialExpressionScalarParameter, -600, 300)
        rough.set_editor_property("parameter_name", "Roughness")
        rough.set_editor_property("default_value", 0.8)
        mul = mel.create_material_expression(base, unreal.MaterialExpressionMultiply, -300, 100)
        mel.connect_material_expressions(color, "", mul, "A")
        mel.connect_material_expressions(emissive, "", mul, "B")
        mel.connect_material_property(color, "", unreal.MaterialProperty.MP_BASE_COLOR)
        mel.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
        mel.recompile_material(base)
        unreal.EditorAssetLibrary.save_loaded_asset(base)

    palette = {
        # ad:          (renk RGB,               emissive, roughness)
        "stone":       ((0.42, 0.40, 0.36), 0.0, 0.85),
        "stone_dark":  ((0.20, 0.19, 0.18), 0.0, 0.90),
        "floor":       ((0.50, 0.45, 0.36), 0.0, 0.75),
        "gold":        ((0.85, 0.62, 0.25), 0.6, 0.35),
        "rock":        ((0.28, 0.26, 0.23), 0.0, 0.95),
        "torch":       ((1.00, 0.55, 0.15), 15.0, 0.5),
        "fire_rock":   ((0.10, 0.05, 0.04), 0.0, 0.90),
        "lava":        ((1.00, 0.28, 0.03), 12.0, 0.5),
        "banner_red":  ((0.45, 0.06, 0.04), 0.0, 0.80),
        "ice_stone":   ((0.22, 0.34, 0.52), 0.0, 0.60),
        "ice_glow":    ((0.20, 0.60, 1.00), 8.0, 0.20),
        "water":       ((0.35, 0.75, 1.00), 3.0, 0.10),
        "banner_blue": ((0.06, 0.15, 0.45), 0.0, 0.80),
        "wind_stone":  ((0.74, 0.76, 0.80), 0.0, 0.70),
        "wind_glow":   ((0.85, 0.93, 1.00), 2.0, 0.30),
        "cloud":       ((0.95, 0.96, 0.98), 0.4, 1.00),
        "nature_stone": ((0.36, 0.37, 0.31), 0.0, 0.90),
        "moss":        ((0.18, 0.33, 0.10), 0.0, 0.95),
        "leaves":      ((0.12, 0.38, 0.08), 0.0, 0.90),
        "wood":        ((0.28, 0.18, 0.10), 0.0, 0.90),
        "banner_green": ((0.08, 0.30, 0.10), 0.0, 0.80),
    }
    for name, (rgb, em, rough) in palette.items():
        path = "{}/MI_PK_{}".format(MAT_DIR, name)
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            mi = unreal.EditorAssetLibrary.load_asset(path)
        else:
            mi = asset_tools.create_asset("MI_PK_" + name, MAT_DIR, unreal.MaterialInstanceConstant,
                                          unreal.MaterialInstanceConstantFactoryNew())
            mel.set_material_instance_parent(mi, base)
        mel.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
        mel.set_material_instance_scalar_parameter_value(mi, "Emissive", em)
        mel.set_material_instance_scalar_parameter_value(mi, "Roughness", rough)
        mel.update_material_instance(mi)
        unreal.EditorAssetLibrary.save_loaded_asset(mi)
        _mats[name] = mi


THEME_MATS = {
    "fire":   {"stand": "fire_rock",    "wall": "fire_rock",    "accent": "lava",      "banner": "banner_red"},
    "ice":    {"stand": "ice_stone",    "wall": "ice_stone",    "accent": "ice_glow",  "banner": "banner_blue"},
    "wind":   {"stand": "wind_stone",   "wall": "wind_stone",   "accent": "wind_glow", "banner": "banner_blue"},
    "nature": {"stand": "nature_stone", "wall": "nature_stone", "accent": "moss",      "banner": "banner_green"},
}


# ---------------------------------------------------------------------------
# Temizlik
# ---------------------------------------------------------------------------
def clear_previous():
    old = [a for a in actor_sub.get_all_level_actors() if unreal.Name(TAG) in a.tags]
    for a in old:
        actor_sub.destroy_actor(a)
    unreal.log("[ArenaGen] {} eski aktor silindi".format(len(old)))


# ---------------------------------------------------------------------------
# Orta platform
# ---------------------------------------------------------------------------
def build_center():
    cyl("Center_Platform", unreal.Vector(0, 0, -200), CENTER_R, 400, "floor")
    cyl("Center_Rim", unreal.Vector(0, 0, -450), CENTER_R + 80, 300, "stone_dark")
    cone("Center_Underside", unreal.Vector(0, 0, -600 - 1800), CENTER_R * 0.95, 3600, "rock", inverted=True)

    # Zemindeki es merkezli halkalar (altin cizgiler)
    z = 1.0
    for r_gold in (CENTER_R - 250, 1400.0, 750.0):
        cyl("Center_RingGold", unreal.Vector(0, 0, z), r_gold, 2, "gold")
        z += 1.0
        cyl("Center_RingFill", unreal.Vector(0, 0, z), r_gold - 50, 2, "floor")
        z += 1.0
    cyl("Center_Core", unreal.Vector(0, 0, z), 160, 2, "gold")

    # Yildiz deseni: 8 isin
    for i in range(8):
        box("Center_StarRay", unreal.Vector(0, 0, z + 1), (2 * (CENTER_R - 250), 30, 2), "gold", yaw=i * 22.5)

    # Kenar mesaleleri
    for i in range(8):
        a = 22.5 + i * 45.0
        p = polar(CENTER_R - 80, a)
        box("Center_TorchPost", unreal.Vector(p.x, p.y, 120), (80, 80, 240), "stone_dark", yaw=a)
        sphere("Center_TorchFlame", unreal.Vector(p.x, p.y, 280), (50, 50, 80), "torch")
        point_light("Center_TorchLight", unreal.Vector(p.x, p.y, 320), (1.0, 0.55, 0.2), 6000, 1400)

    # Alttaki destek kolonlari
    for i in range(12):
        a = i * 30.0
        p = polar(CENTER_R - 300, a)
        box("Center_SupportPillar", unreal.Vector(p.x, p.y, -1600), (250, 250, 2400), "stone_dark", yaw=a)


# ---------------------------------------------------------------------------
# Kopruler
# ---------------------------------------------------------------------------
def build_bridge(angle, label):
    length = RING_INNER_R - CENTER_R + 200
    r_mid = (RING_INNER_R + CENTER_R) * 0.5
    box(label + "_Deck", polar(r_mid, angle, -60), (length, 450, 120), "stone", yaw=angle)
    for side in (-1, 1):
        off = polar(240, angle + 90 * side)
        base = polar(r_mid, angle)
        box(label + "_Rail", unreal.Vector(base.x + off.x, base.y + off.y, 40),
            (length, 40, 80), "stone_dark", yaw=angle)
        for r in (CENTER_R + 150, RING_INNER_R - 150):
            p = polar(r, angle)
            loc = unreal.Vector(p.x + off.x, p.y + off.y, 0)
            box(label + "_TorchPost", unreal.Vector(loc.x, loc.y, 100), (60, 60, 200), "stone_dark")
            sphere(label + "_TorchFlame", unreal.Vector(loc.x, loc.y, 230), (40, 40, 60), "torch")
            point_light(label + "_TorchLight", unreal.Vector(loc.x, loc.y, 260), (1.0, 0.55, 0.2), 3000, 900)
    # Kopru alti kemerleri
    for t in (0.33, 0.66):
        p = polar(CENTER_R + (RING_INNER_R - CENTER_R) * t, angle)
        box(label + "_Support", unreal.Vector(p.x, p.y, -900), (200, 300, 1600), "stone_dark", yaw=angle)


def build_bridges():
    if ADD_SIDE_BRIDGES:
        build_bridge(0.0, "Bridge_North")
        build_bridge(90.0, "Bridge_East")
        build_bridge(270.0, "Bridge_West")
    if ADD_SOUTH_BRIDGE:
        build_bridge(GATE_ANGLE, "Bridge_South")


# ---------------------------------------------------------------------------
# Halka: yurume yolu, tribunler, dis duvar
# ---------------------------------------------------------------------------
def build_ring():
    step = 360.0 / SEGMENTS
    for i in range(SEGMENTS):
        a0 = i * step
        a1 = a0 + step
        mid = a0 + step * 0.5
        th = theme_of(mid)
        tm = THEME_MATS[th]
        gate = abs(((mid - GATE_ANGLE) + 180) % 360 - 180) < step * 1.6

        # Ic yurume yolu
        arc_box("Ring_Walk", RING_INNER_R, WALK_OUTER_R, a0, a1, -300, 0, "stone")
        arc_box("Ring_WalkLip", RING_INNER_R, RING_INNER_R + 120, a0, a1, 0, 120, "stone_dark")

        # Tribun basamaklari
        for t in range(STAND_TIERS):
            r_in = WALK_OUTER_R + t * STAND_TIER_DEPTH
            top = (t + 1) * STAND_TIER_RISE
            if gate:
                top = 60.0  # kapi koridoru alcak kalir
            arc_box("Ring_Stand_" + th, r_in, r_in + STAND_TIER_DEPTH, a0, a1, -300, top, tm["stand"])

        # Dis duvar (kapida bosluk)
        if not gate:
            arc_box("Ring_Wall_" + th, WALL_R, WALL_R + WALL_DEPTH, a0, a1, -300, WALL_H, tm["wall"])
            arc_box("Ring_WallCap", WALL_R - 40, WALL_R + WALL_DEPTH + 40, a0, a1, WALL_H, WALL_H + 120, "stone_dark")
            # Kemer/pencere gorunumu icin dis yuze koyu girintiler
            if i % 2 == 0:
                p = polar(WALL_R + WALL_DEPTH + 5, mid)
                box("Ring_Arch", unreal.Vector(p.x, p.y, 700), (20, 260, 900), "stone_dark", yaw=mid)

        # Alt govde: duvar sutunlari ve asagi sarkan kaya
        arc_box("Ring_Base", RING_INNER_R, WALL_R + WALL_DEPTH, a0, a1, -1500, -300, "stone_dark")
        if i % 3 == 0:
            r = rng.uniform(RING_INNER_R + 800, WALL_R)
            depth = rng.uniform(2500, 6000)
            rock_mat = "fire_rock" if th == "fire" else "rock"
            cone("Ring_HangingRock", polar(r, mid, -1500 - depth * 0.5), rng.uniform(900, 1600), depth,
                 rock_mat, inverted=True)

    # Bolge sancaklari (dis duvarda)
    for th, angles in (("fire", (300, 330)), ("ice", (30, 60)), ("wind", (120, 150)), ("nature", (210, 240))):
        for a in angles:
            p = polar(WALL_R + WALL_DEPTH + 25, a)
            box("Banner_" + th, unreal.Vector(p.x, p.y, 1300), (10, 450, 1500), THEME_MATS[th]["banner"], yaw=a)
            box("Banner_Emblem_" + th, unreal.Vector(p.x, p.y, 1450), (12, 200, 260), "gold", yaw=a)


def build_gate():
    a = GATE_ANGLE
    for side in (-1, 1):
        p = polar(WALL_R + WALL_DEPTH * 0.5, a + side * 5.5)
        box("Gate_Tower", unreal.Vector(p.x, p.y, (WALL_H + 600) * 0.5 - 300), (700, 700, WALL_H + 900), "stone", yaw=a)
        sphere("Gate_TorchFlame", unreal.Vector(p.x, p.y, WALL_H + 750), (80, 80, 120), "torch")
        point_light("Gate_TorchLight", unreal.Vector(p.x, p.y, WALL_H + 800), (1.0, 0.55, 0.2), 10000, 2500)
    p = polar(WALL_R + WALL_DEPTH * 0.5, a)
    box("Gate_Lintel", unreal.Vector(p.x, p.y, 1700), (WALL_DEPTH + 200, 1300, 600), "stone", yaw=a)
    box("Gate_Door", polar(WALL_R + WALL_DEPTH + 20, a, 700), (40, 900, 1400), "wood", yaw=a)
    # Kapi disindaki kisa sahanlik (orta kopru YOK)
    box("Gate_Landing", polar(WALL_R + WALL_DEPTH + 700, a, -150), (1200, 1100, 300), "stone", yaw=a)


# ---------------------------------------------------------------------------
# Element bolgeleri
# ---------------------------------------------------------------------------
def tower(label, r, a, radius, height, body_mat, cap_mat, cap_kind="disc", z0=-300.0):
    p = polar(r, a)
    cyl(label + "_Body", unreal.Vector(p.x, p.y, z0 + height * 0.5), radius, height, body_mat)
    top = z0 + height
    if cap_kind == "disc":
        cyl(label + "_Cap", unreal.Vector(p.x, p.y, top + 60), radius * 1.45, 120, cap_mat)
        cone(label + "_Under", unreal.Vector(p.x, p.y, top - 350), radius * 1.45, 700, body_mat, inverted=True)
    elif cap_kind == "spire":
        cone(label + "_Spire", unreal.Vector(p.x, p.y, top + radius * 1.5), radius * 1.1, radius * 3, cap_mat)
    return top


def build_fire():
    # Volkanik sivri kayalar
    for _ in range(26):
        a = rng.uniform(275, 355)
        r = rng.uniform(WALL_R + 600, WALL_R + 3200)
        h = rng.uniform(2500, 6500)
        cone("Fire_Spire", polar(r, a, -300 + h * 0.5), rng.uniform(300, 800), h, "fire_rock")
    # Kale bloklari
    for a in (295, 315, 335):
        r = WALL_R + 1400
        h = rng.uniform(3500, 4500)
        box("Fire_Keep", polar(r, a, -300 + h * 0.5), (1600, 1400, h), "fire_rock", yaw=a)
        box("Fire_KeepGlow", polar(r - 810, a, h * 0.4), (20, 500, 900), "lava", yaw=a)
        point_light("Fire_KeepLight", polar(r - 1000, a, h * 0.4), (1.0, 0.3, 0.05), 20000, 3000)
    # Yuvarlak kule platformlari
    for a, r in ((282, WALL_R + 900), (350, WALL_R + 700), (320, WALL_R + 2600)):
        top = tower("Fire_Tower", r, a, 350, rng.uniform(2800, 3600), "fire_rock", "fire_rock")
        p = polar(r, a)
        sphere("Fire_Brazier", unreal.Vector(p.x, p.y, top + 250), (200, 200, 300), "lava")
        point_light("Fire_BrazierLight", unreal.Vector(p.x, p.y, top + 400), (1.0, 0.4, 0.1), 15000, 2500)
    # Tribunlerden ve duvardan akan lav catlaklari
    for _ in range(14):
        a = rng.uniform(272, 358)
        box("Fire_LavaCrack", polar(rng.uniform(WALK_OUTER_R + 200, WALL_R - 100), a, STAND_TIER_RISE * 3),
            (rng.uniform(800, 2400), rng.uniform(40, 90), STAND_TIER_RISE * 6), "lava", yaw=a + rng.uniform(-20, 20))
    for _ in range(8):
        a = rng.uniform(275, 355)
        h = rng.uniform(3000, 7000)
        box("Fire_LavaFall", polar(WALL_R + WALL_DEPTH + 30, a, WALL_H - h * 0.5), (40, rng.uniform(80, 200), h),
            "lava", yaw=a)
        point_light("Fire_LavaGlow", polar(WALL_R + WALL_DEPTH + 300, a, 0), (1.0, 0.3, 0.05), 8000, 2000)


def build_ice():
    # Uzun buz kuleleri
    for _ in range(14):
        a = rng.uniform(8, 82)
        r = rng.uniform(WALL_R + 500, WALL_R + 2600)
        top = tower("Ice_Tower", r, a, rng.uniform(220, 420), rng.uniform(3500, 6500), "ice_stone", "ice_glow",
                    cap_kind="spire")
    # Fiskiyeli yuvarlak platformlar
    for a, r in ((15, WALL_R + 800), (45, WALL_R + 1600), (75, WALL_R + 900)):
        top = tower("Ice_Fountain", r, a, 450, rng.uniform(2800, 3800), "ice_stone", "ice_stone")
        p = polar(r, a)
        cyl("Ice_FountainRing", unreal.Vector(p.x, p.y, top + 125), 520, 10, "ice_glow")
        cyl("Ice_FountainWater", unreal.Vector(p.x, p.y, top + 130), 450, 10, "water")
        point_light("Ice_FountainLight", unreal.Vector(p.x, p.y, top + 400), (0.3, 0.7, 1.0), 12000, 2500)
        # Platformdan dusen selale
        box("Ice_Waterfall", polar(r - 500, a, top - 2500), (60, 500, 5000), "water", yaw=a)
    # Dis duvardan dokulen selaleler
    for a in (12, 28, 52, 68, 84):
        box("Ice_WallFall", polar(WALL_R + WALL_DEPTH + 40, a, WALL_H - 3500), (60, rng.uniform(250, 500), 7000),
            "water", yaw=a)
    # Tribunlerdeki parlayan seritler
    for t in range(1, STAND_TIERS, 2):
        r = WALK_OUTER_R + t * STAND_TIER_DEPTH + 5
        for k in range(10):
            a0 = 2 + k * 8.6
            arc_box("Ice_StandGlow", r - 15, r + 15, a0, a0 + 8.0, (t + 1) * STAND_TIER_RISE, (t + 1) * STAND_TIER_RISE + 10,
                    "ice_glow")


def build_wind():
    # Ince kolonlar uzerinde yuvarlak platformlar
    for _ in range(9):
        a = rng.uniform(98, 172)
        r = rng.uniform(WALL_R + 400, WALL_R + 3000)
        h = rng.uniform(2200, 4800)
        top = tower("Wind_Pillar", r, a, 150, h, "wind_stone", "wind_stone")
        # Ruzgar girdabi: kolonun etrafinda spiral seritler
        p = polar(r, a)
        for k in range(18):
            ang = k * 40.0
            z = top - 200 - k * 120
            off = polar(650, ang)
            box("Wind_Swirl", unreal.Vector(p.x + off.x, p.y + off.y, z), (400, 25, 120), "wind_glow",
                yaw=ang + 90, roll=-25)
    # Bulut obekleri (bolge tabani ve tribunler)
    for _ in range(45):
        a = rng.uniform(92, 178)
        r = rng.uniform(WALK_OUTER_R + 1000, WALL_R + 3500)
        s = rng.uniform(800, 2200)
        sphere("Wind_Cloud", polar(r, a, rng.uniform(-1500, 600)), (s, s * 0.9, s * 0.6), "cloud")
    point_light("Wind_Fill", polar(WALL_R, 135, 2500), (0.85, 0.92, 1.0), 20000, 6000)


def tree(label, loc, scale=1.0):
    h = 600 * scale
    cyl(label + "_Trunk", unreal.Vector(loc.x, loc.y, loc.z + h * 0.5), 45 * scale, h, "wood")
    for _ in range(3):
        s = rng.uniform(350, 550) * scale
        off = unreal.Vector(rng.uniform(-150, 150) * scale, rng.uniform(-150, 150) * scale, rng.uniform(-80, 150) * scale)
        sphere(label + "_Leaves", unreal.Vector(loc.x + off.x, loc.y + off.y, loc.z + h + off.z), (s, s, s * 0.8), "leaves")


def build_nature():
    # Yosunlu yuvarlak kuleler
    for a, r in ((195, WALL_R + 800), (225, WALL_R + 1300), (255, WALL_R + 700), (238, WALL_R + 2700)):
        top = tower("Nature_Tower", r, a, 450, rng.uniform(3000, 4000), "nature_stone", "moss")
        p = polar(r, a)
        tree("Nature_TowerTree", unreal.Vector(p.x, p.y, top + 120), 1.3)
        box("Nature_TowerBanner", polar(r - 470, a, top - 900), (10, 300, 1200), "banner_green", yaw=a)
    # Tribunlerin ustunde agaclar ve yosun
    for _ in range(30):
        a = rng.uniform(185, 265)
        t = rng.randrange(STAND_TIERS)
        r = WALK_OUTER_R + t * STAND_TIER_DEPTH + STAND_TIER_DEPTH * 0.5
        tree("Nature_Tree", polar(r, a, (t + 1) * STAND_TIER_RISE), rng.uniform(0.7, 1.4))
    for _ in range(25):
        a = rng.uniform(182, 268)
        r = rng.uniform(WALK_OUTER_R, WALL_R)
        s = rng.uniform(400, 1000)
        sphere("Nature_Moss", polar(r, a, rng.uniform(200, 1200)), (s, s, s * 0.35), "moss")
    # Disaridaki agaclar ve duvardan sarkan sarmasiklar
    for _ in range(20):
        a = rng.uniform(183, 267)
        tree("Nature_OuterTree", polar(rng.uniform(WALL_R + 600, WALL_R + 3200), a, -300), rng.uniform(1.2, 2.2))
    for _ in range(22):
        a = rng.uniform(182, 268)
        h = rng.uniform(1500, 4500)
        box("Nature_Vine", polar(WALL_R + WALL_DEPTH + 15, a, WALL_H - h * 0.5), (20, rng.uniform(60, 160), h),
            "leaves", yaw=a)


# ---------------------------------------------------------------------------
# Ucan kayalar
# ---------------------------------------------------------------------------
def build_floating_rocks():
    for i in range(70):
        a = rng.uniform(0, 360)
        r = rng.uniform(15000, 45000)
        z = rng.uniform(-9000, 5000)
        rad = rng.uniform(600, 3000)
        depth = rad * rng.uniform(1.5, 3.5)
        rock_mat = "fire_rock" if theme_of(a) == "fire" else "rock"
        cone("FloatRock", polar(r, a, z - depth * 0.5), rad, depth, rock_mat, inverted=True)
        cyl("FloatRock_Top", polar(r, a, z + 40), rad * 0.95, 80, "moss")
        if rng.random() < 0.5:
            tree("FloatRock_Tree", polar(r, a, z + 80), rad / 900.0)


# ---------------------------------------------------------------------------
# Gokyuzu / isik
# ---------------------------------------------------------------------------
def build_sky():
    existing = actor_sub.get_all_level_actors()

    def has(cls):
        return any(isinstance(a, cls) for a in existing)

    def spawn(cls, label, loc=unreal.Vector(0, 0, 0), rot=unreal.Rotator()):
        a = actor_sub.spawn_actor_from_class(cls, loc, rot)
        _tag_actor(a, label)
        return a

    if not has(unreal.DirectionalLight):
        sun = spawn(unreal.DirectionalLight, "Sky_Sun", rot=unreal.Rotator(roll=0, pitch=-35, yaw=-130))
        comp = sun.get_component_by_class(unreal.DirectionalLightComponent)
        comp.set_intensity(8.0)
        try:
            comp.set_editor_property("atmosphere_sun_light", True)
        except Exception:
            pass
    if not has(unreal.SkyAtmosphere):
        # Gezegen yuzeyini arenanin 3 km altina indir: bulutlar arenanin altinda kalsin
        atm = spawn(unreal.SkyAtmosphere, "Sky_Atmosphere", unreal.Vector(0, 0, -300000))
        try:
            atm.get_component_by_class(unreal.SkyAtmosphereComponent).set_editor_property(
                "transform_mode", unreal.SkyAtmosphereTransformMode.PLANET_TOP_AT_COMPONENT_TRANSFORM)
        except Exception as e:
            unreal.log_warning("[ArenaGen] Atmosfer ayari yapilamadi: {}".format(e))
    if not has(unreal.SkyLight):
        sl = spawn(unreal.SkyLight, "Sky_Light")
        try:
            sl.get_component_by_class(unreal.SkyLightComponent).set_editor_property("real_time_capture", True)
        except Exception:
            pass
    if not has(unreal.VolumetricCloud):
        vc = spawn(unreal.VolumetricCloud, "Sky_Clouds")
        try:
            c = vc.get_component_by_class(unreal.VolumetricCloudComponent)
            c.set_editor_property("layer_bottom_altitude", 0.3)   # km (gezegen yuzeyinden)
            c.set_editor_property("layer_height", 2.2)
        except Exception as e:
            unreal.log_warning("[ArenaGen] Bulut ayari yapilamadi: {}".format(e))
    if not has(unreal.ExponentialHeightFog):
        fog = spawn(unreal.ExponentialHeightFog, "Sky_Fog", unreal.Vector(0, 0, -6000))
        try:
            f = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
            f.set_editor_property("fog_density", 0.02)
            f.set_editor_property("volumetric_fog", True)
        except Exception:
            pass
    if not has(unreal.PlayerStart):
        spawn(unreal.PlayerStart, "Arena_PlayerStart", unreal.Vector(0, 0, 150))


# ---------------------------------------------------------------------------
def main():
    with unreal.ScopedEditorTransaction("Pota Kacti - Arena olustur"):
        build_materials()
        clear_previous()
        build_center()
        build_bridges()
        build_ring()
        build_gate()
        build_fire()
        build_ice()
        build_wind()
        build_nature()
        if ADD_FLOATING_ROCKS:
            build_floating_rocks()
        if ADD_SKY_AND_LIGHTS:
            build_sky()
    count = len([a for a in actor_sub.get_all_level_actors() if unreal.Name(TAG) in a.tags])
    unreal.log("[ArenaGen] Tamamlandi: {} aktor olusturuldu (klasor: {})".format(count, FOLDER))


main()
