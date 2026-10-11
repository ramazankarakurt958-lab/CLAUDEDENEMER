# Kaplama bolgeleri: T_ArenaKaplamaMaske.png (arena UV'sinde) R = hava (mermer), G = orman (yosunlu tas).
# Girdi: dump/pos.f32 (bake.html'in UV texel basina dunya konumu, arena glTF eksenleri, metre).
# Bolge: hava x>0, z>0; orman x<0, z>0; ikisinde de orta platform, alttaki kaya sarkitlari (y < ~17 m), uzak adalar disi.
import numpy as np
from PIL import Image
from scipy import ndimage as nd
P = 2048
pos = np.fromfile("dump/pos.f32", np.float32).reshape(P, P, 4)
pc = pos[..., 3] > 0
idx = nd.distance_transform_edt(~pc, return_distances=False, return_indices=True)
pos = pos[idx[0], idx[1]]                                   # bos texeller en yakin dolu texelden
x, y, z = pos[..., 0], pos[..., 1], pos[..., 2]
r = np.hypot(x, z)
K = 2.5
sx, sz = 1 / (1 + np.exp(-x / K)), 1 / (1 + np.exp(-z / K))
merkez = np.clip((r - 20) / 3, 0, 1)                        # orta platform ve kenari mermer degil
kaya = np.clip((y - 15) / 4, 0, 1)                          # tribunun altindaki kaya sarkitlari
ada = np.clip((54 - r) / 4, 0, 1)                           # uzaktaki ucan adalar
ortak = merkez * kaya * ada
hava = nd.gaussian_filter(sx * sz * ortak, 1)
orman = nd.gaussian_filter((1 - sx) * sz * ortak, 1)
bos = np.zeros_like(hava)
m = np.dstack([hava, orman, bos])
Image.fromarray((m * 255).clip(0, 255).astype(np.uint8)).save("T_ArenaKaplamaMaske.png", optimize=True)
print("mermer alani %.1f%%, orman %.1f%%" % ((hava > .5).mean() * 100, (orman > .5).mean() * 100))
