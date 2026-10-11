# Orman tribunu kaplamasi: asinmis gri kesme tas bloklar + yosun (4 m x 4 m dikissiz, 2048 px).
# Cikti: T_OrmanTas_D.png (RGB renk, A = puruzluluk), T_OrmanTas_N.png,
#        T_Yosun_D.png (RGB yosun rengi, A = buyume gurultusu: yosunun nerede tutunacagi).
import numpy as np
from PIL import Image
from scipy import ndimage as nd
from mermer_doku_ortak import fbm, blok_duzeni

rng = np.random.default_rng(53)
S, M = 2048, 4.0
lab, dmin, bu, bv, k = blok_duzeni(S, M, 0.5, [.6, .8, 1.0, 1.2], rng)
L = lab
# --- tas: koyu gri, blok basina ton, kenarlari yontulmus, kir akintisi ---
ton = rng.uniform(.85, 1.12, k)
sicak = rng.uniform(-6, 6, k)
taban = np.array([118, 116, 110.])
tane = fbm(S, 70, 5, 11)
leke = fbm(S, 6, 4, 12)
kirlik = fbm(S, 3, 3, 13)
renk = (taban + sicak[L][..., None] * np.array([1, .6, -.4])) * ton[L][..., None]
renk = renk * (.78 + .38 * tane[..., None]) * (.8 + .32 * leke[..., None])
akinti = np.clip((fbm(S, 25, 3, 14) - .45) * 3, 0, 1) * np.clip(bv / .5, 0, 1)      # bloklarin altina inen kir
renk = renk * (1 - .25 * akinti[..., None] * kirlik[..., None])
# yontulmus kenar: derz yaninda duzensiz pah
cent = fbm(S, 40, 3, 15)
pah = 0.012 + 0.03 * cent
derz = 0.006
h = np.clip((dmin - derz) / pah, 0, 1) ** .7
golge = 1 - .3 * np.clip((.05 - dmin) / .05, 0, 1)
renk = renk * golge[..., None]
harc = np.array([62, 62, 58.])
renk = renk * h[..., None] + harc * (1 - h[..., None])
rough = np.clip(.72 + .12 * (tane - .5) + .2 * (1 - h), 0, 1)
Image.fromarray(np.dstack([np.clip(renk, 0, 255), rough * 255]).astype(np.uint8), "RGBA").save("T_OrmanTas_D.png", optimize=True)
H = h * (1 + rng.uniform(-.2, .2, k)[L] * .25) + tane * .12 + leke * .05
gx = np.roll(H, -1, 1) - np.roll(H, 1, 1)
gy = np.roll(H, -1, 0) - np.roll(H, 1, 0)
n = np.dstack([-gx * 4, -gy * 4, np.ones_like(H)])
n /= np.linalg.norm(n, axis=2, keepdims=True)
Image.fromarray(((n * .5 + .5) * 255).astype(np.uint8)).save("T_OrmanTas_N.png", optimize=True)

# --- yosun: yesil tonlarda kumelenmis, ince taneli; A = buyume (buyuk lekeler + derzlerde fazla) ---
y1 = fbm(S, 120, 4, 21)
y2 = fbm(S, 30, 4, 22)
y3 = fbm(S, 8, 3, 23)
koyu = np.array([30, 46, 20.])
acik = np.array([86, 106, 42.])
sari = np.array([128, 132, 60.])
c = koyu + (acik - koyu) * y1[..., None] ** 1.3
c = c + (sari - c) * np.clip((y3 - .6) * 2.5, 0, 1)[..., None] * .5
c = c * (.6 + .55 * y2[..., None]) * (.8 + .3 * fbm(S, 12, 3, 24)[..., None])
buyume = np.clip(((y3 * .75 + y2 * .25) - .55) * 3.2 + .5 + .2 * np.clip((.05 - dmin) / .05, 0, 1), 0, 1)   # iri kumeler, derzde fazla
Image.fromarray(np.dstack([np.clip(c, 0, 255), buyume * 255]).astype(np.uint8), "RGBA").save("T_Yosun_D.png", optimize=True)
Image.fromarray(np.clip(renk[:1024, :1024], 0, 255).astype(np.uint8)).resize((512, 512)).save("T_OrmanTas_onizleme.jpg", quality=88)
print("blok", k, "tas ort", renk.reshape(-1, 3).mean(0).round(0), "yosun ort", c.reshape(-1, 3).mean(0).round(0))
