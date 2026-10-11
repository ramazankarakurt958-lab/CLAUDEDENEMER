# Ates tribunu kaplamasi: komurlesmis koyu kesme tas + lav catlaklari (4 m x 4 m dikissiz, 2048 px).
# Cikti: T_AtesTas_D.png (RGB renk, A = puruzluluk), T_AtesTas_N.png,
#        T_AtesCatlak.png (gri: lavin parladigi yer; derzlerin bir kismi + bloklari yaran catlaklar).
import numpy as np
from PIL import Image
from scipy import ndimage as nd
from mermer_doku_ortak import fbm, blok_duzeni

rng = np.random.default_rng(71)
S, M = 2048, 4.0
px = S / M
lab, dmin, bu, bv, k = blok_duzeni(S, M, 0.5, [.6, .8, 1.0, 1.2], rng)
L = lab
# --- tas: komur siyahi-koyu kahve, kenarlar yanik, yuzeyde kul ---
ton = rng.uniform(.75, 1.2, k)
tane = fbm(S, 80, 5, 31)
leke = fbm(S, 6, 4, 32)
kul = np.clip((fbm(S, 20, 4, 33) - .55) * 3, 0, 1)
taban = np.array([46, 38, 34.])
renk = taban * ton[L][..., None] * (.7 + .5 * tane[..., None]) * (.75 + .45 * leke[..., None])
renk = renk + (np.array([92, 86, 80.]) - renk) * kul[..., None] * .35          # kul lekeleri
pah = 0.01 + 0.03 * fbm(S, 40, 3, 34)
derz = 0.007
h = np.clip((dmin - derz) / pah, 0, 1) ** .7
yanik = np.clip((.06 - dmin) / .06, 0, 1)                                     # kenarlar daha cok yanmis
renk = renk * (1 - .45 * yanik[..., None])
renk = renk * h[..., None] + np.array([20, 14, 12.]) * (1 - h[..., None])

# --- catlaklar: blok icinde dallanan ince catlaklar (gurultunun es-yukselti cizgileri) ---
c1 = fbm(S, 5, 2, 35)                    # yumusak gurultunun es-yukselti cizgisi: uzun, kivrimli catlak
c1b = fbm(S, 40, 2, 39)                  # catlak kenarini hafif tirtikli yapar
c2 = fbm(S, 4, 2, 36)
cizgi = np.exp(-((c1 + (c1b - .5) * .03 - .5) / .006) ** 2) * np.clip((c2 - .52) * 4, 0, 1)   # yer yer kopuk
c3 = fbm(S, 7, 2, 37)
cizgi = np.maximum(cizgi, np.exp(-((c3 + (c1b - .5) * .03 - .5) / .004) ** 2) * .7 * np.clip((c2 - .65) * 5, 0, 1))
cizgi = cizgi * np.clip((dmin - .02) / .03, 0, 1)                               # derz kenarina yapismasin
# derzlerin bir kismi lavla dolu
derz_lav = (1 - h) * np.clip((fbm(S, 5, 3, 38) - .5) * 4, 0, 1)
catlak = np.clip(np.maximum(cizgi, derz_lav), 0, 1)
hale = nd.gaussian_filter(catlak, 3, mode="wrap")                             # catlak cevresi kizarir
renk = renk * (1 - .6 * catlak[..., None]) + np.array([90, 30, 10.]) * np.clip(hale * 1.5, 0, 1)[..., None] * .5
rough = np.clip(.8 + .1 * (tane - .5) - .25 * kul * 0 + .1 * (1 - h) - .3 * catlak, 0, 1)
Image.fromarray(np.dstack([np.clip(renk, 0, 255), rough * 255]).astype(np.uint8), "RGBA").save("T_AtesTas_D.png", optimize=True)
H = h * (1 + rng.uniform(-.2, .2, k)[L] * .25) + tane * .1 + leke * .05 - catlak * .25
gx = np.roll(H, -1, 1) - np.roll(H, 1, 1)
gy = np.roll(H, -1, 0) - np.roll(H, 1, 0)
n = np.dstack([-gx * 4, -gy * 4, np.ones_like(H)])
n /= np.linalg.norm(n, axis=2, keepdims=True)
Image.fromarray(((n * .5 + .5) * 255).astype(np.uint8)).save("T_AtesTas_N.png", optimize=True)
parilti = np.clip(catlak + hale * .35, 0, 1)
Image.fromarray((parilti * 255).astype(np.uint8)).save("T_AtesCatlak.png", optimize=True)
on = renk[:1024, :1024] + np.array([255, 110, 30.]) * parilti[:1024, :1024, None] * 1.2
Image.fromarray(np.clip(on, 0, 255).astype(np.uint8)).resize((512, 512)).save("T_AtesTas_onizleme.jpg", quality=88)
print("blok", k, "tas ort", renk.reshape(-1, 3).mean(0).round(0), "catlak %.1f%%" % ((catlak > .5).mean() * 100))
