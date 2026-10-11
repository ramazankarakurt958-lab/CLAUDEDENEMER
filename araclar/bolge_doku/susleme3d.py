# Arena susleri (arena glTF eksenleri, Y yukari, metre):
#   SM_Ruzgar.glb   : hava tribunu uzerinde donen yari saydam ruzgar seritleri (sarmal; UV u = boy, v = en)
#   SM_Sancak.glb   : her bolgenin sahaya bakan ic duvarina asili sancaklar (malzeme yuvalari: Ates, Su, Orman, Hava)
#   SM_BulutDeniz.glb: arenanin altinda katmanli bulut denizi (uc halka katman, ortasi acik degil; UV dunya olcekli)
# Dokular: T_Ruzgar.png (serit cizgileri, A = opaklik), T_Sancak.png (4 sancak yan yana: ates, su, orman, hava),
#          T_Bulut.png (dikissiz bulut gurultusu, gri = yogunluk).
# Kullanim: python3 susleme3d.py game.glb
import math
import sys
import numpy as np
import trimesh
from PIL import Image, ImageDraw
from scipy import ndimage as nd
from mermer_doku_ortak import fbm

MERKEZ = np.array([-0.886, -0.281])
m = trimesh.load(sys.argv[1] if len(sys.argv) > 1 else "game.glb", force="mesh")
rng = np.random.default_rng(5)


def mesh_uv(V, F, UV, ad):
    t = trimesh.Trimesh(np.array(V, float), np.array(F), process=False)
    t.visual = trimesh.visual.TextureVisuals(uv=np.c_[np.array(UV)[:, 0], 1 - np.array(UV)[:, 1]],
                                             material=trimesh.visual.material.PBRMaterial(name=ad))
    _ = t.vertex_normals                 # normaller glb'ye yazilsin (onbellekte olunca yazilir)
    return t


# ------------------------------------------------------------------ ruzgar seritleri
def serit_sarmal(c, y0, H, R, a0, tur, gen, V, F, UV):
    n = 120
    b = len(V)
    for i in range(n + 1):
        t = i / n
        a = a0 + t * tur * 2 * math.pi
        r = R * (.55 + .45 * math.sin(math.pi * t))
        p = np.array([c[0] + r * math.cos(a), y0 + t * H, c[1] + r * math.sin(a)])
        teg = np.array([-math.sin(a), H / (tur * 2 * math.pi * max(r, .5)), math.cos(a)])
        teg /= np.linalg.norm(teg)
        yuk = np.array([0, 1., 0]) - teg * teg[1]
        yuk /= np.linalg.norm(yuk)
        w = gen * (.3 + .7 * math.sin(math.pi * t))               # uclarda incelir
        V += [p - yuk * w / 2, p + yuk * w / 2]
        UV += [[t, 0], [t, 1]]
        if i:
            F += [[b + 2 * i - 2, b + 2 * i - 1, b + 2 * i + 1], [b + 2 * i - 2, b + 2 * i + 1, b + 2 * i]]


V, F, UV = [], [], []
for aci, r, y0 in ((12, 33, 33), (25, 37, 30), (38, 36, 31), (52, 38, 29), (66, 37, 30), (80, 36, 31)):
    c = MERKEZ + r * np.array([math.cos(math.radians(aci)), math.sin(math.radians(aci))])
    for k in range(2):
        serit_sarmal(c, y0 + k * 1.8, 5 + rng.uniform(-1, 2), 3.4 + k * 1.1, rng.uniform(0, 6.3), .75 + .2 * k, 1.5, V, F, UV)   # az sarmal, genis bicak
mesh_uv(V, F, UV, "Ruzgar").export("SM_Ruzgar.glb")

# ------------------------------------------------------------------ sancaklar
BOLGE = {"Ates": (-135, 0), "Su": (-45, 1), "Orman": (135, 2), "Hava": (45, 3)}     # bolge orta acisi, doku sirasi
S_GEN, S_BOY = 2.0, 4.6
yuvalar = {ad: ([], [], []) for ad in BOLGE}
for ad, (orta, sira) in BOLGE.items():
    secilen = []
    for da in (0, -24, 24, -12, 12, -34, 34, -6, 6, -18, 18, -28, 28):
        if len(secilen) >= 3 or any(abs(da - x) < 15 for x in secilen):
            continue
        a = math.radians(orta + da)
        d = np.array([math.cos(a), math.sin(a)])
        p = None
        for yy_ in (26.5, 25.5, 27.5, 24.5):                         # sahadan disa yatay isin: ic duvara ilk carpma
            o = np.array([MERKEZ[0] + d[0] * 18, yy_, MERKEZ[1] + d[1] * 18])
            loc, ri, fi = m.ray.intersects_location([o], [[d[0], 0, d[1]]], multiple_hits=False)
            if len(loc) and abs(m.face_normals[fi[0]][1]) < .5 and np.hypot(loc[0][0] - MERKEZ[0], loc[0][2] - MERKEZ[1]) < 40:
                p = loc[0]
                break
        if p is None:
            continue
        secilen.append(da)
        ic = -np.array([d[0], 0, d[1]])                              # sahaya bakan yon
        yan = np.array([-ic[2], 0, ic[0]])
        ust = p + ic * .12 + np.array([0, 1.0, 0])                    # duvarin 12 cm onunde, ust kenar 1 m yukarda
        Vv, Ff, Uu = yuvalar[ad]
        b = len(Vv)
        nx, ny = 6, 12
        for j in range(ny + 1):
            for i in range(nx + 1):
                u, v = i / nx, j / ny
                dalga = .08 * math.sin(u * math.pi * 2 + v * 3) * v           # hafif kumas dalgasi
                q = ust + yan * (u - .5) * S_GEN - np.array([0, v * S_BOY, 0]) + ic * dalga
                Vv.append(q)
                Uu.append([(sira + u) / 4, v])
        for j in range(ny):
            for i in range(nx):
                a0 = b + j * (nx + 1) + i
                Ff += [[a0, a0 + 1, a0 + nx + 2], [a0, a0 + nx + 2, a0 + nx + 1]]
        print("sancak", ad, "aci %d" % (orta + da), "duvar r %.1f" % np.hypot(p[0] - MERKEZ[0], p[2] - MERKEZ[1]))
sahne = trimesh.Scene()
for ad, (Vv, Ff, Uu) in yuvalar.items():
    if Vv:
        sahne.add_geometry(mesh_uv(Vv, Ff, Uu, ad), geom_name="Sancak_" + ad)
sahne.export("SM_Sancak.glb")

# sancak dokusu: 4 sancak (ates kirmizi/altin alev, su mavi/gumus dalga, orman yesil/altin yaprak, hava beyaz/mavi girdap)
W, Hh = 256, 600
renkler = {"Ates": ((140, 22, 18), (230, 170, 70)), "Su": ((24, 58, 130), (200, 215, 230)),
           "Orman": ((30, 90, 40), (220, 190, 90)), "Hava": ((225, 228, 232), (70, 120, 190))}
atlas = Image.new("RGBA", (W * 4, Hh), (0, 0, 0, 0))
for ad, (orta, sira) in BOLGE.items():
    zemin_r, amb = renkler[ad]
    im = Image.new("RGBA", (W, Hh), zemin_r + (255,))
    d = ImageDraw.Draw(im)
    d.rectangle([8, 0, W - 9, Hh - 60], outline=amb + (255,), width=6)
    d.polygon([(0, Hh - 60), (W // 2, Hh), (W, Hh - 60)], fill=zemin_r + (255,))          # sivri alt uc
    d.line([(8, Hh - 60), (W // 2, Hh - 6), (W - 9, Hh - 60)], fill=amb + (255,), width=6)
    cx, cy = W // 2, 250
    if ad == "Ates":
        d.polygon([(cx, cy - 95), (cx + 45, cy - 10), (cx + 30, cy + 70), (cx, cy + 40), (cx - 30, cy + 70), (cx - 45, cy - 10)], fill=amb + (255,))
        d.polygon([(cx, cy - 30), (cx + 18, cy + 20), (cx, cy + 45), (cx - 18, cy + 20)], fill=zemin_r + (255,))
    elif ad == "Su":
        for k in range(3):
            pts = [(cx - 80 + t, cy - 40 + k * 45 + 18 * math.sin(t / 160 * 2 * math.pi)) for t in range(0, 161, 8)]
            d.line(pts, fill=amb + (255,), width=12)
    elif ad == "Orman":
        d.ellipse([cx - 55, cy - 95, cx + 55, cy + 95], fill=amb + (255,))
        d.line([(cx, cy - 85), (cx, cy + 120)], fill=zemin_r + (255,), width=8)
        for k in range(5):
            y = cy - 60 + k * 30
            d.line([(cx, y + 18), (cx - 40, y - 8)], fill=zemin_r + (255,), width=5)
            d.line([(cx, y + 18), (cx + 40, y - 8)], fill=zemin_r + (255,), width=5)
    else:
        for k in range(3):
            r = 30 + k * 28
            d.arc([cx - r, cy - r, cx + r, cy + r], 200 + k * 40, 200 + k * 40 + 230, fill=amb + (255,), width=10)
    # kumas dokusu ve hafif kirlilik
    a = np.array(im).astype(np.float32)
    g = fbm(256, 30, 3, sira + 70)
    g = np.array(Image.fromarray((g * 255).astype(np.uint8)).resize((W, Hh)), np.float32) / 255
    a[..., :3] *= (.82 + .3 * g)[..., None]
    a[..., :3] *= (1 - .06 * (np.arange(W) % 4 < 1))[None, :, None]
    atlas.paste(Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA"), (sira * W, 0))
atlas.save("T_Sancak.png")

# ------------------------------------------------------------------ bulut denizi
V, F, UV = [], [], []
for y, R0, R1 in ((4.0, 0.0, 420.0), (9.0, 30.0, 420.0), (14.0, 60.0, 420.0)):
    nr, na = 24, 96
    b = len(V)
    for i in range(nr + 1):
        r = R0 + (R1 - R0) * (i / nr) ** 1.5
        for j in range(na):
            a = j / na * 2 * math.pi
            x, z = MERKEZ[0] + r * math.cos(a), MERKEZ[1] + r * math.sin(a)
            V.append([x, y + rng.uniform(-.5, .5), z])
            UV.append([x / 120, z / 120])
    for i in range(nr):
        for j in range(na):
            a0, a1 = b + i * na + j, b + i * na + (j + 1) % na
            c0, c1 = a0 + na, a1 + na
            F += [[a0, c0, c1], [a0, c1, a1]]
mesh_uv(V, F, UV, "Bulut").export("SM_BulutDeniz.glb")
b_ = fbm(512, 3, 5, 81)
b_ = np.clip((b_ - .5) * 2.6, 0, 1) ** 1.2          # aralikli kumeler: arada bosluk kalsin
Image.fromarray((b_ * 255).astype(np.uint8)).save("T_Bulut.png")

# ------------------------------------------------------------------ ruzgar dokusu (boyuna cizgiler)
S = 256
yy, xx = np.mgrid[0:S, 0:S] / S
cizgi = np.clip(np.sin(yy * 2 * np.pi * 7 + fbm(S, 4, 2, 91) * 4) * .5 + .5, 0, 1) ** 3
kenar = np.sin(yy * np.pi) ** 1.5
alfa = np.clip((.35 + .65 * cizgi) * kenar, 0, 1)
Image.fromarray(np.dstack([np.full((S, S), 240), np.full((S, S), 248), np.full((S, S), 255), alfa * 255]).astype(np.uint8), "RGBA").save("T_Ruzgar.png")
print("SM_Ruzgar.glb SM_Sancak.glb SM_BulutDeniz.glb T_Ruzgar.png T_Sancak.png T_Bulut.png")
