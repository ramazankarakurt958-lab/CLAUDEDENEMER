# Duvar bloklarinin yuzey dokusu (derzsiz: derzler gercek 3D): dikissiz kesme tas yuzeyi, 2 m x 2 m, 1024 px.
# T_DuvarTas_D.png: RGB gri tas (bolge rengi malzemede), A = puruzluluk. T_DuvarTas_N.png: yuzey normali (keski izi, oyuk).
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as nd
sys.path.insert(0, "../bolge_doku")
from mermer_doku_ortak import fbm

S = 1024
h = .55 * fbm(S, 6, 5, 11) + .3 * fbm(S, 30, 3, 12) + .15 * fbm(S, 120, 2, 13)
# keski izleri: hafif egik ince oluklar
yy, xx = np.mgrid[0:S, 0:S] / S
iz = (np.sin((xx * .35 + yy) * 2 * np.pi * 46 + fbm(S, 8, 2, 14) * 6) * .5 + .5) ** 6 * (fbm(S, 5, 3, 15) > .5)
h -= iz * .05
# oyuklar
oy = (fbm(S, 90, 2, 16) > .8) * 1.0
h -= nd.gaussian_filter(oy, 1.2) * .12
renk = .5 + (h - h.mean()) * .9
renk *= .9 + .2 * fbm(S, 3, 3, 17)
renk = np.clip(renk, .15, .95)
puruz = np.clip(.78 + (fbm(S, 20, 3, 18) - .5) * .25 + nd.gaussian_filter(oy, 1.2) * .15, 0, 1)
Image.fromarray((np.dstack([renk, renk * .985, renk * .96, puruz]) * 255).astype(np.uint8), "RGBA").save("T_DuvarTas_D.png")
gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 18
gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 18
n = np.dstack([-gx, gy, np.ones_like(h)])
n /= np.linalg.norm(n, axis=2, keepdims=True)
Image.fromarray(((n * .5 + .5) * 255).astype(np.uint8)).save("T_DuvarTas_N.png")
print("T_DuvarTas_D.png T_DuvarTas_N.png")
