# Kopru mesaleleri: tas kaide + bronz kase + kor (SM_Mesale.glb) ve capraz alev kartlari (SM_Alev.glb), arena glTF
# eksenlerinde (Y yukari, metre). Konumlar: mevcut uc koprunun iki kenari, uclarda ve ~5.5 m arayla (yeni kopru yok).
# Ayrica T_Alev.png (alev sekli: RGB renk, A = opaklik) ve mesale_konum.json (isik konumlari) yazar.
# Kullanim: python3 mesale3d.py game.glb
import json
import sys
import numpy as np
import trimesh
from PIL import Image
from scipy import ndimage as nd
from mermer_doku_ortak import fbm

MERKEZ = np.array([-0.886, -0.281])
KOPRULER = {0: (16.2, 22.45, 1.65), 180: (16.2, 31.4, 1.72), 270: (16.2, 24.45, 1.52)}   # aci: (r bas, r son, yari genislik)
m = trimesh.load(sys.argv[1] if len(sys.argv) > 1 else "game.glb", force="mesh")


def zemin(p):
    """kopru guvertesi: ustteki kapi/kemer yapilarini atlayip 22-23.4 m arasindaki ilk yuzey"""
    loc, ri, _ = m.ray.intersects_location([[p[0], 60., p[1]]], [[0, -1., 0]], multiple_hits=True)
    ys = sorted((float(y) for y in loc[:, 1] if 22.0 < y < 23.4), reverse=True)
    return ys[0] if ys else 22.7


konumlar = []
for aci, (r0, r1, yg) in KOPRULER.items():
    th = np.radians(aci)
    d = np.array([np.cos(th), np.sin(th)])
    n = np.array([-d[1], d[0]])
    sayi = max(2, int(round((r1 - r0) / 5.5)) + 1)
    for r in np.linspace(r0 + .4, r1 - .4, sayi):
        for s in (-1, 1):
            p = MERKEZ + d * r + n * s * (yg - .3)
            konumlar.append(dict(kopru=aci, xz=[float(p[0]), float(p[1])], y=zemin(p)))
print("mesale", len(konumlar))

parca = {"Tas": [], "Bronz": [], "Kor": [], "Alev": []}


def kutu(ad, merkez, boy):
    b = trimesh.creation.box(extents=boy)
    b.apply_translation(merkez)
    parca[ad].append(b)


def kase(merkez, r_alt, r_ust, h, ad, seg=20):
    c = trimesh.creation.cone(radius=1, height=1, sections=seg)       # sonra kesik koni yapilir
    v = c.vertices.copy()
    t = v[:, 2]                                                         # 0 taban, 1 tepe
    rad = r_alt + (r_ust - r_alt) * t
    nrm = np.linalg.norm(v[:, :2], axis=1)
    v[:, :2] = np.where(nrm[:, None] > 1e-6, v[:, :2] / np.maximum(nrm[:, None], 1e-6) * rad[:, None], 0)
    v[:, 2] = t * h
    k = trimesh.Trimesh(np.c_[v[:, 0], v[:, 2], v[:, 1]] + merkez, c.faces[:, ::-1], process=False)
    parca[ad].append(k)


for k in konumlar:
    x, z, y = k["xz"][0], k["xz"][1], k["y"]
    kutu("Tas", [x, y + .05, z], [.5, .1, .5])                  # taban
    kutu("Tas", [x, y + .5, z], [.32, .8, .32])                  # govde
    kutu("Tas", [x, y + .95, z], [.46, .1, .46])                 # baslik
    kase([x, y + 1.0, z], .12, .3, .24, "Bronz")                 # bronz kase
    kutu("Kor", [x, y + 1.2, z], [.4, .03, .4])                  # kor yatagi
    for i in range(3):                                           # capraz alev kartlari
        a = i * np.pi / 3
        kart = trimesh.Trimesh([[-.28, 0, 0], [.28, 0, 0], [.28, .85, 0], [-.28, .85, 0]], [[0, 1, 2], [0, 2, 3]], process=False)
        kart.visual = trimesh.visual.TextureVisuals(uv=[[0, 0], [1, 0], [1, 1], [0, 1]])
        R = trimesh.transformations.rotation_matrix(a, [0, 1, 0])
        kart.apply_transform(R)
        kart.apply_translation([x, y + 1.18, z])
        parca["Alev"].append(kart)

RENK = {"Tas": [120, 108, 92, 255], "Bronz": [150, 95, 45, 255], "Kor": [255, 120, 40, 255]}
sahne = trimesh.Scene()
for ad in ("Tas", "Bronz", "Kor"):
    g = trimesh.util.concatenate(parca[ad])
    g.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
        name=ad, baseColorFactor=RENK[ad], metallicFactor=1.0 if ad == "Bronz" else 0.0, roughnessFactor=.45 if ad == "Bronz" else .85))
    _ = g.vertex_normals
    sahne.add_geometry(g, geom_name=ad)
sahne.export("SM_Mesale.glb")
alev = trimesh.util.concatenate(parca["Alev"])
uv = np.concatenate([p.visual.uv for p in parca["Alev"]])
alev.visual = trimesh.visual.TextureVisuals(uv=uv, material=trimesh.visual.material.PBRMaterial(name="Alev"))
_ = alev.vertex_normals
alev.export("SM_Alev.glb")
json.dump([dict(kopru=k["kopru"], p=[k["xz"][0], k["y"] + 1.45, k["xz"][1]]) for k in konumlar], open("mesale_konum.json", "w"))

# --- alev dokusu: alttan genis, uca sivri damla; ic beyaz-sari, dis turuncu-kirmizi ---
S = 256
yy, xx = np.mgrid[0:S, 0:S] / (S - 1)
v = 1 - yy                                                     # 0 alt, 1 ust (goruntu satiri asagi)
u = (xx - .5) * 2
genis = np.clip(.75 * np.sin(np.clip(v, 0, 1) * np.pi * .85) * (1 - v) ** .35 + .05, 0, 1)
gur = fbm(S, 6, 3, 61)
icerde = np.clip(1 - np.abs(u + (gur - .5) * .35 * v) / np.maximum(genis, 1e-3), 0, 1)
sekil = np.clip(icerde * 1.6, 0, 1) * np.clip(v * 8, 0, 1) * np.clip((1 - v) * 3, 0, 1)
sicak = np.clip(icerde ** .8 * (1 - v) ** .6, 0, 1)
renk = np.dstack([np.full_like(sicak, 1.0), .25 + .7 * sicak, .05 + .6 * sicak ** 2])
a = nd.gaussian_filter(sekil, 1.2)
Image.fromarray((np.dstack([renk, a]) * 255).clip(0, 255).astype(np.uint8), "RGBA").save("T_Alev.png")
print("SM_Mesale.glb, SM_Alev.glb, T_Alev.png, mesale_konum.json")
