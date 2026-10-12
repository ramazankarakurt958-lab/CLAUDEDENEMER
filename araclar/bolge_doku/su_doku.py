# Su tribunu duvar kaplamasi: islak, mavi-gri kesme tas (4 m x 4 m dikissiz, 2048 px). Yukaridan suzulen su izleri (koyu, parlak
# dikey seritler), derzlerde yesil-turkuaz mineral/yosun birikintisi, kenarlari asinmis bloklar.
# Cikti: T_SuTas_D.png (RGB renk, A = puruzluluk: islak yerler parlak), T_SuTas_N.png
import numpy as np
from PIL import Image
from scipy import ndimage as nd
from mermer_doku_ortak import fbm, blok_duzeni

rng = np.random.default_rng(83)
S, M = 2048, 4.0
lab, dmin, bu, bv, k = blok_duzeni(S, M, 0.5, [.6, .8, 1.0, 1.2], rng)
L = lab
ton = rng.uniform(.82, 1.15, k)
tane = fbm(S, 80, 5, 41)
leke = fbm(S, 6, 4, 42)
taban = np.array([98, 112, 124.])                                   # mavi-gri granit
renk = taban * ton[L][..., None] * (.75 + .4 * tane[..., None]) * (.8 + .35 * leke[..., None])
# yukaridan suzulen su izleri: dikeyde uzamis gurultu (goruntu satiri = asagi)
iz = fbm(S, 3, 4, 43)
iz = nd.zoom(nd.zoom(iz, (1, 1)), 1)
iz = nd.gaussian_filter1d(nd.gaussian_filter1d(fbm(S, 12, 3, 44), 40, axis=0, mode="wrap"), 1.5, axis=1, mode="wrap")
iz = np.clip((iz - iz.mean()) / iz.std() * .5 + .3, 0, 1) ** 2
islak = np.clip(iz * 1.4 + (leke - .5) * .4, 0, 1)
renk = renk * (1 - .38 * islak[..., None])                          # islak tas koyulasir
pah = 0.012 + 0.03 * fbm(S, 40, 3, 45)
h = np.clip((dmin - 0.007) / pah, 0, 1) ** .7
# derzlerde mineral/yosun birikintisi
birikinti = (1 - h) * np.clip((fbm(S, 8, 3, 46) - .4) * 3, 0, 1)
renk = renk * h[..., None] + np.array([28, 40, 44.]) * (1 - h[..., None])
renk = renk * (1 - birikinti[..., None] * .6) + np.array([40, 92, 84.]) * birikinti[..., None] * .6
asinma = np.clip((.05 - dmin) / .05, 0, 1) * fbm(S, 60, 2, 47)
renk = renk * (1 - .25 * asinma[..., None])
rough = np.clip(.72 - .5 * islak + .1 * (tane - .5) + .15 * (1 - h), .12, 1)
Image.fromarray(np.dstack([np.clip(renk, 0, 255), rough * 255]).astype(np.uint8), "RGBA").save("T_SuTas_D.png", optimize=True)
H = h * (1 + rng.uniform(-.2, .2, k)[L] * .25) + tane * .1 + leke * .05
gx = np.roll(H, -1, 1) - np.roll(H, 1, 1)
gy = np.roll(H, -1, 0) - np.roll(H, 1, 0)
n = np.dstack([-gx * 4, -gy * 4, np.ones_like(H)])
n /= np.linalg.norm(n, axis=2, keepdims=True)
Image.fromarray(((n * .5 + .5) * 255).astype(np.uint8)).save("T_SuTas_N.png", optimize=True)
Image.fromarray(np.clip(renk[:1024, :1024], 0, 255).astype(np.uint8)).resize((512, 512)).save("T_SuTas_onizleme.jpg", quality=88)
print("blok", k, "tas ort", renk.reshape(-1, 3).mean(0).round(0), "islak %.0f%%" % ((islak > .5).mean() * 100))
