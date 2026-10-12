# Duvar bloklarinin yuzey dokusu (derzsiz: derzler gercek 3D): dikissiz kesme tas yuzeyi, 2 m x 2 m, 1024 px.
# T_DuvarTas_D.png: RGB gri tas (bolge rengi malzemede), A = puruzluluk. T_DuvarTas_N.png: yuzey normali (keski izi, oyuk).
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as nd
sys.path.insert(0, __file__.rsplit("/", 2)[0] + "/bolge_doku")
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

# T_Yaprak.png: 2x2 sarmasik yapragi atlasi (RGB renk, A = maske), 512 px
Y = 512
yap = np.zeros((Y, Y, 4))
rr = np.random.default_rng(9)
for hy in range(2):
    for hx in range(2):
        for _ in range(7):                                          # hucre basina yaprak kumesi
            cx, cy = rr.uniform(.25, .75) * 256 + hx * 256, rr.uniform(.25, .75) * 256 + hy * 256
            a = rr.uniform(0, np.pi)
            ry, rx = rr.uniform(35, 60), rr.uniform(18, 30)
            yy, xx = np.mgrid[0:Y, 0:Y]
            u = ((xx - cx) * np.cos(a) + (yy - cy) * np.sin(a)) / ry
            v = (-(xx - cx) * np.sin(a) + (yy - cy) * np.cos(a)) / rx
            ic = (u ** 2 + v ** 2 * (1 + .6 * u)) < 1
            ic &= (xx // 256 == hx) & (yy // 256 == hy)
            ton = rr.uniform(.7, 1.1)
            damar = np.exp(-(v * 8) ** 2) * .25
            c = np.dstack([.16 * ton + damar * .1, .38 * ton + damar * .2, .1 * ton + damar * .05])
            yap[ic, :3] = c[ic] * (.8 + .3 * (1 - np.abs(u[ic])))[:, None]
            yap[ic, 3] = 1
Image.fromarray((np.clip(yap, 0, 1) * 255).astype(np.uint8), "RGBA").save("T_Yaprak.png")
print("T_Yaprak.png")
