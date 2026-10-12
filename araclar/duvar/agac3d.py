# Orman tribunu agaclari (arena glTF eksenleri, metre): kalin, yere yayilip egilerek inen kokler, kivrik govde, 2 kademe dal,
# dal uclarinda yaprak kumeleri (capraz kartlar; T_Yaprak 2x2 atlasi). Yerler: orman bolgesinde duz, ustu acik, en az 6.5 m arali
# noktalar (kopru ve saha cevresindeki yuruyus halkasi haric).
# Cikti: SM_Agac.glb (yuvalar "Agac_Kabuk", "Agac_Yaprak"), T_Kabuk_D.png / T_Kabuk_N.png (dikey lifli kabuk, dikissiz).
# Kullanim: python3 agac3d.py arena_game.glb hmap.npz T_ArenaKaplamaMaske.png SM_Agac.glb
import math
import sys
import numpy as np
import trimesh
from PIL import Image
sys.path.insert(0, __file__.rsplit("/", 2)[0] + "/bolge_doku")
from mermer_doku_ortak import fbm

ARENA, HMAP, MASKE = sys.argv[1:4]
CIKTI = sys.argv[4] if len(sys.argv) > 4 else "SM_Agac.glb"
MERKEZ = np.array([-0.886, -0.281])
rng = np.random.default_rng(31)
g = trimesh.load(ARENA, force="mesh")
d = np.load(HMAP)
H, G, O = d["H"], float(d["G"]), float(d["O"])
km = np.array(Image.open(MASKE), np.float32) / 255

# ---------------------------------------------------------------- yer secimi
pts, fi = trimesh.sample.sample_surface(g, 300000, seed=8)
bc = trimesh.triangles.points_to_barycentric(g.triangles[fi], pts)
uv = (g.visual.uv[g.faces[fi]] * bc[:, :, None]).sum(1)
h = km.shape[0]
A = km[np.clip((1 - uv[:, 1] % 1) * h, 0, h - 1).astype(int), np.clip((uv[:, 0] % 1) * h, 0, h - 1).astype(int)]
dx, dz = pts[:, 0] - MERKEZ[0], pts[:, 2] - MERKEZ[1]
r = np.hypot(dx, dz)
kopru = (-dx > 14) & (-dx < 32) & (np.abs(dz) < 2.6)              # 180 derece koprusu (orman-ates arasi)
aday = np.where((A[:, 1] > .5) & (g.face_normals[fi][:, 1] > .85) & (r > 26) & (r < 50) & ~kopru)[0]
rng.shuffle(aday)


def duz(p):
    i, j = int((p[0] - O) / G), int((p[2] - O) / G)
    w = H[j - 7:j + 8, i - 7:i + 8]
    return np.nanmax(w) - np.nanmin(w) < .6 and abs(np.nanmax(w) - p[1]) < .4


yerler = []
for i in aday:
    p = pts[i]
    if any(np.linalg.norm(p - q) < 6.5 for q in yerler) or not duz(p):
        continue
    if g.ray.intersects_any([p + [0, .3, 0]], [[0, 1, 0]])[0]:
        continue
    yerler.append(p)
    if len(yerler) >= 14:
        break
print("agac", len(yerler))


# ---------------------------------------------------------------- geometri
class Yuva:
    def __init__(self):
        self.V, self.U, self.F, self.C = [], [], [], []


kabuk, yaprak = Yuva(), Yuva()


def tup(yol, yaricap, kenar=9, v0=0.0):
    """yol: (n,3) noktalar, yaricap: (n,) -> kapali olmayan tup; UV u = cevre (m), v = boy (m)"""
    yol = np.asarray(yol, float)
    b = len(kabuk.V)
    T = np.gradient(yol, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-9
    ref = np.array([1., 0, 0]) if abs(T[0][1]) > .9 else np.array([0, 1., 0])
    nrm = np.cross(T[0], ref)
    nrm /= np.linalg.norm(nrm)
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(yol, axis=0), axis=1))] + v0
    for i in range(len(yol)):
        nrm = nrm - T[i] * np.dot(nrm, T[i])                       # paralel tasima
        nrm /= np.linalg.norm(nrm) + 1e-9
        bn = np.cross(T[i], nrm)
        cevre = 2 * math.pi * yaricap[i]
        for k in range(kenar + 1):
            a = 2 * math.pi * k / kenar
            kabuk.V.append(yol[i] + (nrm * math.cos(a) + bn * math.sin(a)) * yaricap[i])
            kabuk.U.append([k / kenar * max(cevre, .3), s[i]])
            kabuk.C.append([1, 1, 1, 1])
    for i in range(len(yol) - 1):
        for k in range(kenar):
            a0 = b + i * (kenar + 1) + k
            a1 = a0 + kenar + 1
            kabuk.F += [[a0, a1, a0 + 1], [a0 + 1, a1, a1 + 1]]


def yaprak_kumesi(c, boy):
    """capraz kartlardan kuresel yaprak kumesi"""
    for _ in range(int(9 + boy * 6)):
        n = rng.normal(size=3)
        n /= np.linalg.norm(n)
        p = c + n * boy * rng.uniform(.2, .75) * np.array([1, .7, 1])
        w = rng.uniform(.6, 1.0) * boy * .55
        e1 = np.cross(n, [0, 1, 0])
        if np.linalg.norm(e1) < .1:
            e1 = np.array([1., 0, 0])
        e1 /= np.linalg.norm(e1)
        e2 = np.cross(n, e1)
        hx, hy = rng.integers(0, 2) * .5, rng.integers(0, 2) * .5
        t = rng.uniform(.7, 1.15)
        b = len(yaprak.V)
        yaprak.V += [p - e1 * w - e2 * w, p + e1 * w - e2 * w, p + e1 * w + e2 * w, p - e1 * w + e2 * w]
        yaprak.U += [[hx, hy + .5], [hx + .5, hy + .5], [hx + .5, hy], [hx, hy]]
        yaprak.C += [[t, t, t, 1]] * 4
        yaprak.F += [[b, b + 1, b + 2], [b, b + 2, b + 3]]


def dal(bas, yon, boy, r0, kademe):
    n = max(4, int(boy / .35))
    yol, rr = [bas], [r0]
    p, y = bas.copy(), yon / np.linalg.norm(yon)
    for i in range(1, n + 1):
        y = y + rng.normal(scale=.12, size=3) + np.array([0, .05, 0])
        y /= np.linalg.norm(y)
        p = p + y * boy / n
        yol.append(p.copy())
        rr.append(r0 * (1 - .75 * i / n))
    tup(yol, rr, kenar=7 if kademe else 9)
    if kademe < 2:
        for t in np.linspace(.45, .9, 2 + kademe):
            j = int(t * n)
            yy = yol[j + 1] - yol[j]
            yan = np.cross(yy, rng.normal(size=3))
            yan /= np.linalg.norm(yan) + 1e-9
            dal(yol[j], yy / np.linalg.norm(yy) * .6 + yan * .8 + [0, .25, 0], boy * rng.uniform(.45, .65), rr[j] * .6, kademe + 1)
    yaprak_kumesi(yol[-1], 1.3 if kademe == 2 else 1.7)


def agac(taban):
    boy = rng.uniform(4.5, 7.5)
    r0 = rng.uniform(.28, .42)
    # kokler: govdeden disa yayilip egilerek yere giren kalin kokler
    for k in range(rng.integers(5, 8)):
        a = 2 * math.pi * k / 7 + rng.uniform(-.3, .3)
        yon = np.array([math.cos(a), 0, math.sin(a)])
        uz = rng.uniform(1.4, 2.6)
        yol, rr = [], []
        for t in np.linspace(0, 1, 9):
            yol.append(taban + yon * (r0 * .6 + uz * t) + [0, .55 * (1 - t) ** 1.6 - .12 * t, 0])
            rr.append(r0 * .55 * (1 - .8 * t) + .03)
        tup(yol, rr, kenar=7)
    # govde: kivrik, tabanda genis
    n = 10
    yol, rr = [], []
    egik = rng.normal(scale=.12, size=3) * [1, 0, 1]
    for i in range(n + 1):
        t = i / n
        yol.append(taban + [0, -.2 + boy * .62 * t, 0] + egik * boy * t * t + np.r_[np.sin(t * 5 + boy), 0, np.cos(t * 4)] * .12)
        rr.append(r0 * (1.5 - .5 * t if t < .15 else 1.0 - .35 * t))
    tup(yol, rr)
    tepe = yol[-1]
    for k in range(rng.integers(3, 5)):
        a = 2 * math.pi * k / 4 + rng.uniform(-.4, .4)
        dal(tepe - [0, rng.uniform(0, .8), 0], np.array([math.cos(a), rng.uniform(.6, 1.1), math.sin(a)]),
            boy * rng.uniform(.35, .5), r0 * .55, 0)
    yaprak_kumesi(tepe + [0, .8, 0], 2.0)


for p in yerler:
    agac(np.array(p))

sahne = trimesh.Scene()
for ad, y_ in (("Agac_Kabuk", kabuk), ("Agac_Yaprak", yaprak)):
    m = trimesh.Trimesh(np.array(y_.V), np.array(y_.F), process=False)
    m.visual = trimesh.visual.TextureVisuals(uv=np.array(y_.U), material=trimesh.visual.material.PBRMaterial(name=ad))
    m.visual.vertex_attributes["color"] = (np.clip(np.array(y_.C), 0, 1) * 255).astype(np.uint8)
    _ = m.vertex_normals
    sahne.add_geometry(m, geom_name=ad)
    print(ad, len(y_.F), "ucgen")
sahne.export(CIKTI)

# kabuk dokusu: dikey lifler + catlaklar (1 m x 1 m, 512 px)
S = 512
yy, xx = np.mgrid[0:S, 0:S] / S
lif = fbm(S, 3, 4, 71)
cat = np.abs(np.sin((xx + fbm(S, 2, 3, 72) * .25) * np.pi * 9))
hk = .6 * lif + .4 * np.clip(cat * 1.4, 0, 1)
renk = np.dstack([.30 + .25 * hk, .22 + .18 * hk, .15 + .12 * hk]) * (.8 + .3 * fbm(S, 6, 3, 73)[..., None])
Image.fromarray((np.dstack([np.clip(renk, 0, 1), np.full((S, S), .85)]) * 255).astype(np.uint8), "RGBA").save("T_Kabuk_D.png")
gx = (np.roll(hk, -1, 1) - np.roll(hk, 1, 1)) * 6
gy = (np.roll(hk, -1, 0) - np.roll(hk, 1, 0)) * 6
n = np.dstack([-gx, gy, np.ones_like(hk)])
n /= np.linalg.norm(n, axis=2, keepdims=True)
Image.fromarray(((n * .5 + .5) * 255).astype(np.uint8)).save("T_Kabuk_N.png")
print("->", CIKTI, "T_Kabuk_D.png T_Kabuk_N.png")
