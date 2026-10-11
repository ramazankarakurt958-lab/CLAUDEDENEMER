# Orta platform altin kakmasi: merkez_desen.altin_yollari'ndaki her yol, duz zemin diskiyle ayni hizada (2 mm ustte,
# kabartma yok) duz metal serit. Zemin: merkez_zemin3d.py (y = 23.14).
# Arena glTF eksenlerinde (Y yukari, metre) yazilir; UE'de arena aktorunun konumuna konur (Selaleler gibi).
# Kullanim: python3 merkez_run3d.py - SM_MerkezRun.glb
import sys
import numpy as np
import trimesh
from merkez_desen import altin_yollari

MERKEZ = np.array([-0.886, -0.281])      # platform merkezi (glTF x, z)


Y_DUZ = 23.142


def yukseklik(xz):
    return np.full(len(xz), Y_DUZ)


V, N, F = [], [], []


def yuz(p, n):
    """dortgen (4 kose, ayni normal) - keskin kenar icin kendi koseleri"""
    b = len(V)
    V.extend(p)
    N.extend([n] * 4)
    F.extend([[b, b + 1, b + 2], [b, b + 2, b + 3]])


def g3(xz, y):
    return [xz[0] + MERKEZ[0], y, xz[1] + MERKEZ[1]]


def serit(yol, gen):
    yol = np.array(yol, float)
    kapali = len(yol) > 2 and np.allclose(yol[0], yol[-1])
    # 4 cm'de bir ornekle
    parca = [yol[0]]
    for a, b in zip(yol[:-1], yol[1:]):
        n = max(1, int(np.linalg.norm(b - a) / .04))
        parca.extend(a + (b - a) * t for t in np.linspace(0, 1, n + 1)[1:])
    P = np.array(parca)
    t = np.gradient(P, axis=0)
    t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
    nrm = np.c_[-t[:, 1], t[:, 0]]
    L, R = P + nrm * gen / 2, P - nrm * gen / 2
    hs = yukseklik(P)
    for i in range(len(P) - 1):
        a, b = i, i + 1
        yuz([g3(L[a], hs[a]), g3(L[b], hs[b]), g3(R[b], hs[b]), g3(R[a], hs[a])], [0, 1, 0])


def civi(p, cap):
    p = np.array(p, float)
    a = np.linspace(0, 2 * np.pi, 13)
    halka = p + np.c_[np.cos(a), np.sin(a)] * cap / 2
    for i in range(12):
        yuz([g3(p, Y_DUZ), g3(p, Y_DUZ), g3(halka[i + 1], Y_DUZ), g3(halka[i], Y_DUZ)], [0, 1, 0])


for yol, gen in altin_yollari():
    if len(yol) == 1:
        civi(yol[0], gen)
    else:
        serit(yol, gen)
V = np.array(V, np.float32)
N = np.array(N, np.float32)
F = np.array(F, np.int64)
# sarim yonu normallerle uyumlu olsun
fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
ters = (fn * N[F[:, 0]]).sum(1) < 0
F[ters] = F[ters][:, ::-1]
alan = np.linalg.norm(fn, axis=1) > 1e-10
F = F[alan]
mesh = trimesh.Trimesh(V, F, vertex_normals=N, process=False)
mesh.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
    name="Altin", baseColorFactor=[255, 190, 90, 255], metallicFactor=1.0, roughnessFactor=0.3))
cikti = sys.argv[2] if len(sys.argv) > 2 else "SM_MerkezRun.glb"
mesh.export(cikti)
print("kose", len(V), "ucgen", len(F), "->", cikti)
