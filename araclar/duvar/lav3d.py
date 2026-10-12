# Ates tribununde 3D lav akintilari: lav lekelerinin (T_ArenaBolgeMaske R) oldugu teras kenarlarindan baslayip duvar kaplamasi
# dahil yuzeyi takip ederek asagi akan, cikintidan dokulen yuvarlak kesitli serit (akinti.py'nin yol izleme/tup kodu).
# Cikti: SM_Lav.glb (yuva "Lav"; UV0: u = kesit, v = akis boyunca metre), T_LavAkis.png (R = kor/kabuk, akis yonunde uzamis)
# Kullanim: python3 lav3d.py arena_game.glb SM_Duvar.glb T_ArenaBolgeMaske.png T_ArenaKaplamaMaske.png hmap.npz
import sys
import numpy as np
import trimesh
from PIL import Image
sys.path.insert(0, __file__.rsplit("/", 2)[0] + "/bolge_doku")
import akinti
from mermer_doku_ortak import fbm

arena = trimesh.load(sys.argv[1], force="mesh")
m = trimesh.util.concatenate([arena, trimesh.load(sys.argv[2], force="mesh")])
lav = np.array(Image.open(sys.argv[3]).convert("RGB"), np.float32)[..., 0] / 255
km = np.array(Image.open(sys.argv[4]), np.float32) / 255
hm = np.load(sys.argv[5])
H, G, O = hm["H"], float(hm["G"]), float(hm["O"])
rng = np.random.default_rng(23)
pts, fi = trimesh.sample.sample_surface(arena, 300000, seed=4)
bc = trimesh.triangles.points_to_barycentric(arena.triangles[fi], pts)
uv = (arena.visual.uv[arena.faces[fi]] * bc[:, :, None]).sum(1)


def oku(t):
    h = t.shape[0]
    return t[np.clip((1 - uv[:, 1] % 1) * h, 0, h - 1).astype(int), np.clip((uv[:, 0] % 1) * h, 0, h - 1).astype(int)]


def Hs(x, z):
    i, j = int((x - O) / G), int((z - O) / G)
    if 0 <= i < H.shape[1] and 0 <= j < H.shape[0] and not np.isnan(H[j, i]):
        return H[j, i]
    return -50.0


L, A = oku(lav), oku(km)
ust = arena.face_normals[fi][:, 1] > .6
aday = np.where((L > .45) & (A[:, 2] > .5) & ust)[0]
rng.shuffle(aday)
# kaynak: lav lekesinden 2.5 m icinde en dik dusus yonunde kenar
kaynak = []
for i in aday:
    p = pts[i]
    if any(np.linalg.norm(p - q) < 4.5 for q, _ in kaynak):
        continue
    en = None
    for a in np.linspace(0, 2 * np.pi, 24, endpoint=False):
        d = np.array([np.cos(a), np.sin(a)])
        for r in np.arange(.3, 2.6, .2):
            h = Hs(p[0] + d[0] * r, p[2] + d[1] * r)
            if p[1] - h > 2.0:
                if en is None or r < en[0]:
                    en = (r, d)
                break
    if en is None:
        continue
    r, d = en
    kenar = np.array([p[0] + d[0] * (r - .15), p[1] - .05, p[2] + d[1] * (r - .15)])
    kaynak.append((kenar, np.array([d[0], 0, d[1]])))
    if len(kaynak) >= 14:
        break
print("lav kaynagi", len(kaynak))

parca = []
for p, n in kaynak:
    P, D, NN, _ = akinti.yol_izle(m, p, n)
    if len(P) < 8:
        continue
    gen = rng.uniform(.5, 1.0)
    r = akinti.tup_yol(P, D, NN, gen, NR=10)
    if r is None:
        continue
    V, U0, U1, F, Ps, kab = r
    parca.append((V, U1, F))
    print("akinti %.1f m, dusus %d" % (np.linalg.norm(np.diff(Ps, axis=0), axis=1).sum(), kab.sum()))
V = np.concatenate([p[0] for p in parca])
UV = np.concatenate([p[1] for p in parca])
ofs = np.cumsum([0] + [len(p[0]) for p in parca[:-1]])
F = np.concatenate([p[2] + o for p, o in zip(parca, ofs)])
t = trimesh.Trimesh(V, F, process=False)
t.visual = trimesh.visual.TextureVisuals(uv=np.c_[UV[:, 0], -UV[:, 1]], material=trimesh.visual.material.PBRMaterial(name="Lav"))
_ = t.vertex_normals
t.export(sys.argv[6] if len(sys.argv) > 6 else "SM_Lav.glb")
print("lav serit", len(parca), "ucgen", len(F))

# akis dokusu: akis yonunde (v) uzamis kor damarlari + koyu kabuk adalari, dikissiz
S = 512
a = fbm(S, 4, 4, 51)
b = fbm(S, 10, 3, 52)
yy, xx = np.mgrid[0:S, 0:S] / S
damar = np.clip(1 - np.abs(np.sin((xx + a * .6) * np.pi * 6)) * 1.6, 0, 1) ** 2
kabuk = np.clip((b - .55) * 4, 0, 1)
k = np.clip(.35 + .9 * damar - .8 * kabuk + (a - .5) * .5, 0, 1)
Image.fromarray((k * 255).astype(np.uint8)).save("T_LavAkis.png")
