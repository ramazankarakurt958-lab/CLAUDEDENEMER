# Orta platform altin kakma yollari (platform merkezine gore metre; x, y = glTF x, z).
# Doku (merkez_doku.py) ve zemine gomulu duz altin seritler (merkez_run3d.py) ayni yollari kullanir.
# Duz zemin diski 15.05 m'ye kadar: en dis halka 14.92 m.
import math
import numpy as np


def daire(r, n=None):
    n = n or max(48, int(2 * math.pi * r / 0.08))
    return [(r * math.cos(t), r * math.sin(t)) for t in np.linspace(0, 2 * math.pi, n + 1)]


def altin_yollari():
    """[(nokta listesi, genislik m)]; tek noktali yol = nokta (dairesel civi)."""
    rng = np.random.default_rng(91)
    yollar = []
    for r in (2.2, 5.0, 8.0, 11.5, 14.92):
        yollar.append((daire(r), .06))
    yollar.append((daire(11.75), .035))
    for ofs in (0, math.pi / 4):                                   # 8 koseli yildiz (r = 5)
        yollar.append(([(5.0 * math.cos(ofs + j * math.pi / 2), 5.0 * math.sin(ofs + j * math.pi / 2)) for j in range(5)], .05))
    for ofs in (math.pi / 8, math.pi / 8 + math.pi / 4):          # ic yildiz (r = 2.2)
        yollar.append(([(2.2 * math.cos(ofs + j * math.pi / 2), 2.2 * math.sin(ofs + j * math.pi / 2)) for j in range(5)], .045))
    yollar.append((daire(0.6, 48), .05))
    yollar.append((daire(0.25, 32), .05))
    for j in range(16):                                            # isinlar
        a = j * math.pi / 8
        r0 = 5.0 if j % 2 == 0 else 8.0
        yollar.append(([(r0 * math.cos(a), r0 * math.sin(a)), (11.5 * math.cos(a), 11.5 * math.sin(a))], .045))
    rr = 14.1                                                      # run halkasi
    nrun = int(2 * math.pi * rr / 0.95)
    izgara = [(gx, gy) for gx in (-.22, 0, .22) for gy in (-.35, 0, .35)]
    for j in range(nrun):
        a = j / nrun * 2 * math.pi
        cx, cy = rr * math.cos(a), rr * math.sin(a)
        tx, ty, nx, ny = -math.sin(a), math.cos(a), math.cos(a), math.sin(a)
        for _ in range(rng.integers(3, 6)):
            p1, p2 = rng.choice(len(izgara), 2, replace=False)
            (x1, y1), (x2, y2) = izgara[p1], izgara[p2]
            yollar.append(([(cx + tx * x1 + nx * y1, cy + ty * x1 + ny * y1), (cx + tx * x2 + nx * y2, cy + ty * x2 + ny * y2)], .045))
        if j % 2 == 0:
            a2 = (j + .5) / nrun * 2 * math.pi
            yollar.append(([(rr * math.cos(a2), rr * math.sin(a2))], .1))
    return yollar
