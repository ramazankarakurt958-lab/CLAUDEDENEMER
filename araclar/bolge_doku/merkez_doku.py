# Orta platform deseni: halkalarda dilimlenmis tas doseme + altin kakma (halkalar, 8 koseli yildiz, isinlar, run halkasi).
# Platform: arena glTF'te merkez (-0.886, -0.281), yaricap 15.70 m, ust yuzey y = 22.95. Doku platformun cevresindeki
# kareyi kaplar (4096 px = 2R): malzemede dunyaya yukaridan, platform merkezine gore yansitilir. Kopruler kaplanmaz.
# Cikti: T_Merkez_D.jpg (renk, altin cizgiler boyali), T_Merkez_N.png (derz normali). Altin seritler: merkez_run3d.py.
import math
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd
from mermer_doku_ortak import fbm

R = 15.70
S = 4096
px = S / (2 * R)                        # piksel / metre
rng = np.random.default_rng(91)
yy, xx = (np.mgrid[0:S, 0:S] + .5) / px - R
r = np.hypot(xx, yy)
th = np.arctan2(yy, xx)

# --- halka halka dilimlenmis levhalar ---
halkalar = [0, 2.2, 3.4, 5.0, 6.3, 8.0, 9.4, 11.5, 13.2, 15.0, R]
lab = np.full((S, S), -1, np.int32)
dmin = np.full((S, S), 9.0)
k = 0
for i in range(len(halkalar) - 1):
    r0, r1 = halkalar[i], halkalar[i + 1]
    halka = (r >= r0) & (r < r1)
    dr = np.minimum(r - r0, r1 - r)
    if r0 == 0:
        lab[halka] = k
        dmin[halka] = dr[halka]
        k += 1
        continue
    n = max(8, int(round(2 * math.pi * (r0 + r1) / 2 / 1.8 / 8)) * 8)      # 8'in kati: yildiza hizali
    kay = (i % 2) * .5
    a = (th / (2 * math.pi) * n + kay) % n
    seg = np.floor(a)
    da = np.minimum(a - seg, seg + 1 - a) * 2 * math.pi / n * r          # dilim sinirina uzaklik (m)
    lab[halka] = (k + seg[halka]).astype(np.int32)
    dmin[halka] = np.minimum(dr, da)[halka]
    k += n
ton = rng.uniform(.88, 1.1, k)
sicak = rng.uniform(-8, 8, k)
tane = fbm(S, 120, 5, 41)
leke = fbm(S, 8, 4, 42)
L = np.clip(lab, 0, k - 1)
renk = (np.array([152, 138, 118.]) + sicak[L][..., None] * np.array([1, .5, -.3])) * ton[L][..., None]
renk = renk * (.78 + .35 * tane[..., None]) * (.82 + .3 * leke[..., None])
derz, pah = 0.006, 0.015
h = np.clip((dmin - derz) / pah, 0, 1) ** .7
renk = renk * (1 - .15 * np.clip((.04 - dmin) / .04, 0, 1))[..., None]
renk = renk * h[..., None] + np.array([60, 54, 46.]) * (1 - h[..., None])

# --- altin kakma: merkez_desen.altin_yollari (3D seritler de ayni yollardan uretilir) ---
from merkez_desen import altin_yollari
alt = Image.new("L", (S, S), 0)
d = ImageDraw.Draw(alt)
c = S / 2
for yol, gen in altin_yollari():
    pts = [(c + x * px, c + y * px) for x, y in yol]
    if len(pts) == 1:
        q = pts[0]
        d.ellipse([q[0] - gen / 2 * px, q[1] - gen / 2 * px, q[0] + gen / 2 * px, q[1] + gen / 2 * px], fill=255)
    else:
        d.line(pts, fill=255, width=max(1, int(gen * px)), joint="curve")
g = np.array(alt, np.float32) / 255
g = nd.gaussian_filter(g, .8)
g[r > R] = 0
altin = np.array([235, 178, 92.]) * (.85 + .25 * fbm(S, 60, 3, 43)[..., None])
renk = renk * (1 - g[..., None]) + altin * g[..., None]
# platform disi: tasin ortalamasi (malzemede zaten maskelenir, kenar kanamasin)
renk[r > R] = renk[r <= R].mean(0)
Image.fromarray(np.clip(renk, 0, 255).astype(np.uint8)).save("T_Merkez_D.jpg", quality=92)   # altin ayri mesh: alfa gerekmez
H = nd.zoom(h * (1 + rng.uniform(-.2, .2, k)[L] * .2), .5, order=1)       # sadece derz ve levha farki, 2048 px (kucuk dosya)
gx = np.roll(H, -1, 1) - np.roll(H, 1, 1)
gy = np.roll(H, -1, 0) - np.roll(H, 1, 0)
n = np.dstack([-gx * 3, -gy * 3, np.ones_like(H)])
n /= np.linalg.norm(n, axis=2, keepdims=True)
Image.fromarray(((n * .5 + .5) * 255).astype(np.uint8)).save("T_Merkez_N.png", optimize=True)
Image.fromarray(np.clip(renk, 0, 255).astype(np.uint8)).resize((1024, 1024)).save("T_Merkez_onizleme.jpg", quality=88)
print("levha", k, "altin %.2f%%" % ((g > .5).mean() * 100))
