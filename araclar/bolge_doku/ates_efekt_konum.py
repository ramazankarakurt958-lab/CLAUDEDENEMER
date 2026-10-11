# Ates tribunu efekt konumlari (ArenaSusleme.py -> ATES_EFEKT): arena yuzeyinden ornek noktalar alinir, arena UV'sinden
# T_ArenaBolgeMaske (R = lav) ve T_ArenaKaplamaMaske (B = ates bolgesi) okunur.
#   LavAtes : lav ustunde, yukari bakan, en az 7 m arali 8 nokta (ustu kapali olanlar atilir)
#   Kivilcim: lav ustunde, ateslerden uzak 3 nokta;  Duman: ates bolgesinin en yuksek, en az 10 m arali 4 noktasi
# Kullanim: python3 ates_efekt_konum.py arena_game.glb T_ArenaBolgeMaske.png T_ArenaKaplamaMaske.png
import sys
import numpy as np
import trimesh
from PIL import Image

g = trimesh.load(sys.argv[1], force="mesh")
lav = np.array(Image.open(sys.argv[2]).convert("RGB"), np.float32)[..., 0] / 255
km = np.array(Image.open(sys.argv[3]), np.float32) / 255
pts, fi = trimesh.sample.sample_surface(g, 400000, seed=3)
bc = trimesh.triangles.points_to_barycentric(g.triangles[fi], pts)
uv = (g.visual.uv[g.faces[fi]] * bc[:, :, None]).sum(1)


def oku(t):
    h = t.shape[0]
    return t[np.clip((1 - uv[:, 1] % 1) * h, 0, h - 1).astype(int), np.clip((uv[:, 0] % 1) * h, 0, h - 1).astype(int)]


L, A = oku(lav), oku(km)
MERKEZ = np.array([-0.886, -0.281])
r = np.hypot(pts[:, 0] - MERKEZ[0], pts[:, 2] - MERKEZ[1])
ates, ust = A[:, 2] > .5, g.face_normals[fi][:, 1] > .6


def sec(idx, k, dmin, puan, haric=()):
    s = []
    for i in idx[np.argsort(-puan[idx])]:
        if all(np.linalg.norm(pts[i] - pts[j]) >= dmin for j in s) and all(np.linalg.norm(pts[i] - pts[j]) > 3 for j in haric):
            s.append(i)
        if len(s) >= k:
            break
    return s


def acik(s):
    o = pts[s] + [0, .1, 0]
    return [i for i, k in zip(s, g.ray.intersects_any(o, np.tile([0, 1., 0], (len(o), 1)))) if not k]


lavi = np.where((L > .5) & ates & ust)[0]
a = acik(sec(lavi, 8, 7, L + np.random.default_rng(0).uniform(0, .3, len(L))))
k = sec(lavi, 3, 5, np.random.default_rng(2).uniform(0, 1, len(L)), a)
d = acik(sec(np.where(ates & ust & (r < 52))[0], 4, 10, pts[:, 1]))
for ad, s in (("LavAtes", a), ("Kivilcim", k), ("Duman", d)):
    print(ad, "[" + ", ".join("[%.2f, %.2f, %.2f]" % tuple(pts[i]) for i in s) + "]")
