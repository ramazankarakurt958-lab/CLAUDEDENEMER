# Orta platform zemin kaplamasi 3D: tamamen DUZ tas zemin diski (eski kabartmalarin hemen ustunde, y = 23.14), kenarinda
# platforma inen kisa etek. Kenar bandindaki direk ve mesale kaideleri (r > 15.05) kaplanmaz.
# UV: T_Merkez_D/N dokusu (sutun = glTF x, satir = glTF z; 4096 px = 2R). Kopruler kaplanmaz (R = 15.70 m).
# Kullanim: python3 merkez_zemin3d.py game.glb SM_MerkezZemin.glb
import sys
import numpy as np
import trimesh

MERKEZ = np.array([-0.886, -0.281])
R = 15.70                 # doku olcegi (4096 px = 2R)
R_DISK, Y_DUZ, Y_ETEK = 15.05, 23.14, 22.84
NA = 720
rs = np.r_[0.0, np.arange(0.5, R_DISK, 0.5), R_DISK]
P = [np.zeros(2)]
a = np.arange(NA) / NA * 2 * np.pi
for r in rs[1:]:
    P.extend(np.c_[r * np.cos(a), r * np.sin(a)])
P = np.array(P)
n_ust = len(P)
P = np.r_[P, P[-NA:]]                                    # etek alt halkasi
V = np.c_[P[:, 0] + MERKEZ[0], np.r_[np.full(n_ust, Y_DUZ), np.full(NA, Y_ETEK)], P[:, 1] + MERKEZ[1]]
NR = np.r_[np.tile([0, 1., 0], (n_ust, 1)), np.c_[np.cos(a), np.zeros(NA), np.sin(a)]]
F = []
for j in range(NA):                                      # merkez yelpaze
    F.append([0, 1 + j, 1 + (j + 1) % NA])
for i in range(len(rs) - 2):
    b0, b1 = 1 + i * NA, 1 + (i + 1) * NA
    for j in range(NA):
        j2 = (j + 1) % NA
        F.append([b0 + j, b1 + j, b1 + j2])
        F.append([b0 + j, b1 + j2, b0 + j2])
F = np.array(F)
fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
F[fn[:, 1] < 0] = F[fn[:, 1] < 0][:, ::-1]
# etek: ust kenar halkasinin ayri kopyasi (dik normal) + alt halka
kenar = len(V)
V = np.r_[V, V[n_ust - NA:n_ust]]
NR = np.r_[NR, np.c_[np.cos(a), np.zeros(NA), np.sin(a)]]
P = np.r_[P, P[n_ust - NA:n_ust]]
E = []
for j in range(NA):
    j2 = (j + 1) % NA
    E += [[kenar + j, n_ust + j, n_ust + j2], [kenar + j, n_ust + j2, kenar + j2]]
E = np.array(E)
en = np.cross(V[E[:, 1]] - V[E[:, 0]], V[E[:, 2]] - V[E[:, 0]])
disa = (en[:, 0] * np.cos(a[np.arange(len(E)) // 2]) + en[:, 2] * np.sin(a[np.arange(len(E)) // 2])) < 0
E[disa] = E[disa][:, ::-1]
F = np.r_[F, E]
h = V[:, 1]
u = P[:, 0] / (2 * R) + .5
v = P[:, 1] / (2 * R) + .5
mesh = trimesh.Trimesh(V, F, vertex_normals=NR, process=False)
mesh.visual = trimesh.visual.TextureVisuals(uv=np.c_[u, 1 - v],          # trimesh V'yi ters yazar: goruntu satiri = v
                                            material=trimesh.visual.material.PBRMaterial(name="MerkezZemin", roughnessFactor=.7))
cikti = sys.argv[2] if len(sys.argv) > 2 else "SM_MerkezZemin.glb"
mesh.export(cikti)
print("kose", len(V), "ucgen", len(F), "yukseklik %.2f-%.2f" % (h.min(), h.max()), "->", cikti)
