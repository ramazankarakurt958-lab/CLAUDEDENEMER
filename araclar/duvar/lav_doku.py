# Gercekci lav dokulari (2 m x 2 m dikissiz, 1024 px): soguyan bazalt kabuk plakalari (Voronoi), aralarindaki catlaklardan
# parlayan erimis kaya; plakalarin ortasi koyu, kenarlari kizgin. Akis yonunde (v) hafif uzamis.
# Cikti: T_Lav_D.png (kabuk rengi, A = puruzluluk), T_Lav_E.png (R = isima: 1 = beyaz-sari cekirdek, 0 = soguk kabuk),
#        T_Lav_N.png (kabuk plaka normali)
import sys
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
sys.path.insert(0, __file__.rsplit("/", 2)[0] + "/bolge_doku")
from mermer_doku_ortak import fbm

S = 1024
rng = np.random.default_rng(97)
n = 140
P = rng.random((n, 2)) * [1, 1.6]                                  # v yonunde uzamis plakalar
P[:, 1] %= 1
kop = np.concatenate([P + [dx, dy] for dx in (-1, 0, 1) for dy in (-1, 0, 1)])   # dikissiz
yy, xx = np.mgrid[0:S, 0:S] / S
bozul = (fbm(S, 6, 3, 1) - .5) * .05
q = np.c_[(xx + bozul).ravel(), ((yy + bozul * .7) * 1.0).ravel()]
d, _ = cKDTree(kop * [1, 1.6]).query(q * [1, 1.6], k=2)
f1, f2 = d[:, 0].reshape(S, S), d[:, 1].reshape(S, S)
kenar = f2 - f1                                                     # plaka sinirina uzaklik
catlak = np.exp(-(kenar / .012) ** 2)                               # parlak catlak
ic = np.clip(kenar / .06, 0, 1)                                     # plaka ortasina dogru
gur = fbm(S, 12, 4, 2)
sicak = np.clip(catlak * 1.1 + (1 - ic) ** 3 * .45 + (fbm(S, 4, 3, 3) - .55) * .6 * (1 - ic), 0, 1)
sicak = np.clip(sicak * (.75 + .5 * fbm(S, 3, 2, 4)), 0, 1)
kabuk = np.array([30, 24, 22.]) * (.6 + .7 * gur[..., None]) * (.7 + .3 * ic[..., None])
kabuk = kabuk * (1 - sicak[..., None]) + np.array([60, 20, 8.]) * sicak[..., None]
puruz = np.clip(.85 - .5 * sicak + .1 * (gur - .5), .2, 1)
Image.fromarray(np.dstack([np.clip(kabuk, 0, 255), puruz * 255]).astype(np.uint8), "RGBA").save("T_Lav_D.png")
Image.fromarray((sicak * 255).astype(np.uint8)).save("T_Lav_E.png")
H = ic * .6 + gur * .25 - catlak * .4
gx = np.roll(H, -1, 1) - np.roll(H, 1, 1)
gy = np.roll(H, -1, 0) - np.roll(H, 1, 0)
nr = np.dstack([-gx * 10, -gy * 10, np.ones_like(H)])
nr /= np.linalg.norm(nr, axis=2, keepdims=True)
Image.fromarray(((nr * .5 + .5) * 255).astype(np.uint8)).save("T_Lav_N.png")
# onizleme: isima rengi sicakliga gore kirmizi -> turuncu -> sari
renk_isik = np.dstack([np.ones_like(sicak), .25 + .6 * sicak ** 1.5, .05 + .4 * sicak ** 4]) * sicak[..., None] ** 1.3 * 255 * 1.4
Image.fromarray(np.clip(kabuk + renk_isik, 0, 255).astype(np.uint8)).resize((512, 512)).save("T_Lav_onizleme.jpg", quality=88)
print("T_Lav_D/E/N.png, sicak %.0f%%" % ((sicak > .5).mean() * 100))
