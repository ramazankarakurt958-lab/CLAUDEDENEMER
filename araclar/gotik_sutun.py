# Gotik kose sutunu uretir -> Content/Maps/Arena/Kaynak/SM_GotikSutun.glb
# Demet (clustered) govde, sekizgen kaide, can seklinde baslik, ustte 4 sivri kule (pinnacle) ve kure yuvasi.
# Olculer metre, Z yukari; tepe (kure yuvasi) 7.0 m. Calistirma: python3 araclar/gotik_sutun.py
import json
import math
import os
import struct

import numpy as np

CIKTI = os.path.join(os.path.dirname(__file__), "..", "Content", "Maps", "Arena", "Kaynak", "SM_GotikSutun.glb")
TEKRAR = 2.0  # doku her 2 m'de bir tekrar eder (UV birimi)

parcalar = []  # (V, N, UV, F)


def torna(profil, seg, duz=False, don=0.0, ofset=(0.0, 0.0)):
    """Profili (r, z) Z ekseni etrafinda dondurur. duz=True: koseli (sekizgen, kare) yuzeyler."""
    profil = np.asarray(profil, float)
    rmax = profil[:, 0].max()
    # profil parcalarinin 2B normalleri (disari)
    d = np.diff(profil, axis=0)
    sn = np.c_[d[:, 1], -d[:, 0]]
    sn /= np.linalg.norm(sn, axis=1, keepdims=True) + 1e-12
    uz = np.r_[0, np.cumsum(np.linalg.norm(d, axis=1))]
    V, N, UV, F = [], [], [], []
    for s in range(len(d)):
        if np.linalg.norm(d[s]) < 1e-9:
            continue
        # komsu parcayla 35 dereceden az aci varsa yumusat
        ns = []
        for uc, kom in ((0, s - 1), (1, s + 1)):
            n = sn[s].copy()
            if 0 <= kom < len(d) and np.dot(sn[s], sn[kom]) > math.cos(math.radians(35)):
                n = sn[s] + sn[kom]
                n /= np.linalg.norm(n)
            ns.append(n)
        for j in range(seg):
            a0 = don + 2 * math.pi * j / seg
            a1 = don + 2 * math.pi * (j + 1) / seg
            taban = len(V)
            for ai, a in enumerate((a0, a1)):
                for uc in (0, 1):
                    r, z = profil[s + uc]
                    if duz:
                        am = (a0 + a1) / 2
                        nr, nz = sn[s]
                        nx, ny = nr * math.cos(am), nr * math.sin(am)
                    else:
                        nr, nz = ns[uc]
                        nx, ny = nr * math.cos(a), nr * math.sin(a)
                    V.append((ofset[0] + r * math.cos(a), ofset[1] + r * math.sin(a), z))
                    N.append((nx, ny, nz))
                    UV.append(((j + ai) / seg * 2 * math.pi * rmax / TEKRAR, uz[s + uc] / TEKRAR))
            F += [(taban, taban + 2, taban + 3), (taban, taban + 3, taban + 1)]
    V, N, UV, F = map(np.array, (V, N, UV, F))
    # sarim yonunu normale gore duzelt
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    ters = (fn * N[F].mean(1)).sum(1) < 0
    F[ters] = F[ters][:, ::-1]
    parcalar.append((V, N, UV, F))


SEKIZ = math.radians(22.5)

# kaide: iki kademeli sekizgen + yuvarlak silme
torna([(0, 0), (.78, 0), (.78, .28), (.70, .34), (.66, .34), (.66, .52), (.60, .58), (0, .58)], 8, duz=True, don=SEKIZ)
torna([(0, .58), (.56, .58), (.585, .62), (.56, .66), (.50, .68), (.52, .71), (.48, .75), (0, .75)], 40)
# cekirdek govde
torna([(0, .70), (.33, .70), (.33, 6.0), (0, 6.0)], 32)
# 8 ince sutuncuk (demet)
for k in range(8):
    a = k * math.pi / 4
    r = .085 if k % 2 == 0 else .06
    torna([(0, .72), (r + .03, .72), (r + .03, .80), (r, .84), (r, 5.85), (r + .025, 5.90), (r + .025, 5.95), (0, 5.95)],
          14, ofset=(.36 * math.cos(a), .36 * math.sin(a)))
# halka bilezikler
for z in (2.4, 4.2):
    torna([(0, z - .06), (.47, z - .06), (.50, z - .03), (.50, z + .03), (.47, z + .06), (0, z + .06)], 40)
# can seklinde baslik
torna([(0, 5.88), (.47, 5.88), (.49, 5.93), (.47, 5.98), (.42, 6.02), (.43, 6.2), (.48, 6.4), (.58, 6.55), (.70, 6.64), (0, 6.64)], 40)
# sekizgen abakus
torna([(0, 6.64), (.80, 6.64), (.84, 6.70), (.84, 6.82), (.78, 6.88), (0, 6.88)], 8, duz=True, don=SEKIZ)
# kure yuvasi (hafif cukur)
torna([(0, 6.88), (.50, 6.88), (.54, 6.95), (.50, 7.0), (.40, 6.97), (0, 6.97)], 40)
# 4 sivri kule (pinnacle) + tepe topuzu
for k in range(4):
    a = math.pi / 4 + k * math.pi / 2
    o = (.72 * math.cos(a), .72 * math.sin(a))
    torna([(0, 6.88), (.105, 6.88), (.105, 6.96), (.08, 6.98), (.08, 7.55), (.10, 7.57), (.10, 7.63), (.075, 7.65), (0, 8.25)],
          4, duz=True, don=math.pi / 4, ofset=o)
    torna([(0, 8.20), (.03, 8.23), (.035, 8.27), (.02, 8.31), (0, 8.33)], 10, ofset=o)

# birlestir
V, N, UV, F, n = [], [], [], [], 0
for v, nn, uv, f in parcalar:
    V.append(v); N.append(nn); UV.append(uv); F.append(f + n); n += len(v)
V, N, UV, F = (np.concatenate(x) for x in (V, N, UV, F))
# Z yukari -> glTF Y yukari
V = np.c_[V[:, 0], V[:, 2], -V[:, 1]].astype(np.float32)
N = np.c_[N[:, 0], N[:, 2], -N[:, 1]].astype(np.float32)
UV = np.c_[UV[:, 0], 1 - UV[:, 1]].astype(np.float32)
F = F.astype(np.uint32)

bins, views, acc = [], [], []


def ekle(arr, ct, tip, hedef, mm=False):
    b = arr.tobytes()
    views.append({"buffer": 0, "byteOffset": sum(map(len, bins)), "byteLength": len(b), "target": hedef})
    bins.append(b + b"\0" * ((4 - len(b) % 4) % 4))
    a = {"bufferView": len(views) - 1, "componentType": ct, "count": len(arr) if arr.ndim > 1 else arr.size, "type": tip}
    if mm:
        a["min"], a["max"] = arr.min(0).tolist(), arr.max(0).tolist()
    acc.append(a)
    return len(acc) - 1


p = ekle(V, 5126, "VEC3", 34962, True)
nn = ekle(N, 5126, "VEC3", 34962)
t = ekle(UV, 5126, "VEC2", 34962)
i = ekle(F.ravel(), 5125, "SCALAR", 34963)
j = {"asset": {"version": "2.0", "generator": "gotik_sutun.py"}, "scene": 0, "scenes": [{"nodes": [0]}],
     "nodes": [{"mesh": 0, "name": "SM_GotikSutun"}],
     "meshes": [{"name": "SM_GotikSutun", "primitives": [{"attributes": {"POSITION": p, "NORMAL": nn, "TEXCOORD_0": t},
                                                           "indices": i, "material": 0}]}],
     "materials": [{"name": "GotikTas", "pbrMetallicRoughness": {"baseColorFactor": [.42, .40, .37, 1], "metallicFactor": 0,
                                                                 "roughnessFactor": .85}}],
     "accessors": acc, "bufferViews": views, "buffers": [{"byteLength": sum(map(len, bins))}]}
js = json.dumps(j, separators=(",", ":")).encode()
js += b" " * ((4 - len(js) % 4) % 4)
bb = b"".join(bins)
with open(CIKTI, "wb") as f:
    f.write(struct.pack("<III", 0x46546C67, 2, 28 + len(js) + len(bb)))
    f.write(struct.pack("<I4s", len(js), b"JSON") + js + struct.pack("<I4s", len(bb), b"BIN\0") + bb)
print("ucgen:", len(F), "kose:", len(V), "->", os.path.abspath(CIKTI))
