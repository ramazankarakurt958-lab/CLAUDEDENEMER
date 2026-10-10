# Ucan ada modelleri uretir -> Content/Maps/Arena/Kaynak/SM_UcanAda_1..3.glb
# Ust yuzey hafif kubbeli ve duzensiz kenarli; alt taraf sarkitli, sivri bir kaya konisi.
# Olcu: ust yaricap ~1 m (Unreal'da olceklenir), taban Z=0'da, sivri uc asagida.
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from glb_yaz import yaz  # noqa: E402

KAYNAK = os.path.join(os.path.dirname(__file__), "..", "Content", "Maps", "Arena", "Kaynak")
NA, NU, NT = 72, 10, 28  # aci, ust halka, alt kademe sayisi


def dalga(rng, n):
    """Aciya bagli puruzsuz rastgele fonksiyon: sum a*sin(k*th + faz)."""
    ks = rng.integers(2, 14, n)
    a = rng.uniform(0.3, 1.0, n) / ks
    f = rng.uniform(0, 2 * math.pi, n)
    return lambda th: sum(ai * np.sin(k * th + fi) for ai, k, fi in zip(a, ks, f)) / a.sum()


def ada(tohum, derinlik, sivrilik, sarkit):
    rng = np.random.default_rng(tohum)
    th = np.linspace(0, 2 * math.pi, NA, endpoint=False)
    kenar = 1 + 0.16 * dalga(rng, 6)(th)
    ust_dalga = dalga(rng, 5)
    sirt = dalga(rng, 10)
    puruz = dalga(rng, 12)
    V, UV = [], []
    # ust kapak: merkezden kenara halkalar
    V.append((0, 0, 0.10))
    UV.append((0.5, 0.5))
    for j in range(1, NU + 1):
        r = j / NU
        for i, a in enumerate(th):
            rr = r * kenar[i]
            z = 0.10 * (1 - r * r) + 0.025 * ust_dalga(a + 3 * r) * r
            V.append((rr * math.cos(a), rr * math.sin(a), z))
            UV.append((0.5 + 0.5 * rr * math.cos(a), 0.5 + 0.5 * rr * math.sin(a)))
    # alt koni: kenardan sivri uca, sirtli ve sarkitli
    uc = (rng.uniform(-.15, .15), rng.uniform(-.15, .15))
    sarkitlar = [(rng.uniform(0, 2 * math.pi), rng.uniform(.12, .3)) for _ in range(sarkit)]
    for k in range(1, NT + 1):
        t = k / NT
        for i, a in enumerate(th):
            ki = (1 - t) ** sivrilik
            rr = kenar[i] * ki * (1 + (0.22 * sirt(a + 2.0 * t) + 0.07 * puruz(3 * a + 9 * t)) * min(1, 4 * t) * (1 - t) ** 0.5)
            z = -derinlik * t ** 1.05
            # sarkit: belirli acilarda koni asagi uzar
            for sa, sg in sarkitlar:
                d = math.atan2(math.sin(a - sa), math.cos(a - sa))
                z -= derinlik * sg * math.exp(-(d / 0.4) ** 2) * t * t
            x = rr * math.cos(a) + uc[0] * t
            y = rr * math.sin(a) + uc[1] * t
            V.append((x, y, z))
            UV.append((i / NA * 4, 1 + t * 3))
    V.append((uc[0], uc[1], -derinlik * 1.08))
    UV.append((0, 4))
    V = np.array(V, float)
    F = []
    for i in range(NA):  # merkez yelpazesi
        F.append((0, 1 + i, 1 + (i + 1) % NA))
    halkalar = NU + NT
    for j in range(halkalar - 1):
        b0, b1 = 1 + j * NA, 1 + (j + 1) * NA
        for i in range(NA):
            i2 = (i + 1) % NA
            F += [(b0 + i, b1 + i, b1 + i2), (b0 + i, b1 + i2, b0 + i2)]
    son, tep = 1 + (halkalar - 1) * NA, len(V) - 1
    for i in range(NA):
        F.append((son + i, tep, son + (i + 1) % NA))
    F = np.array(F)
    # disa bakan sarim + puruzsuz normaller
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    merkez = V.mean(0)
    ters = (fn * (V[F].mean(1) - merkez)).sum(1) < 0
    ters[:NA] = fn[:NA, 2] < 0  # ust kapak yukari baksin
    F[ters] = F[ters][:, ::-1]
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    N = np.zeros_like(V)
    for k in range(3):
        np.add.at(N, F[:, k], fn)
    N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
    return V, N, np.array(UV, float), F


for no, (tohum, derinlik, sivrilik, sarkit) in enumerate([(11, 1.7, 0.75, 3), (23, 2.4, 0.95, 4), (37, 1.2, 0.6, 2)], 1):
    V, N, UV, F = ada(tohum, derinlik, sivrilik, sarkit)
    yol = os.path.join(KAYNAK, "SM_UcanAda_%d.glb" % no)
    yaz(yol, V, N, UV, F, "SM_UcanAda_%d" % no, (0.35, 0.33, 0.3))
    print(yol, "ucgen:", len(F))
