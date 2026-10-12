# Arena duvarlarini gercek 3D taslarla kaplar (arena glTF eksenleri, Y yukari, metre).
# Girdi: kontur.py'nin konturlar.npy'si + arena_game.glb (eski yuzeyin disari tasan yerlerini olcmek icin).
# Her duvar kosusu icin:
#   - kesme tas bloklar (pahli on yuz, 2.5 cm derz, sira sira kaydirilmis), arkada koyu harc yuzeyi
#   - 3.5 m'den yuksek duvarlarda ~6 m arayla ayakli/baslikli plastirlar
#   - ustte profilli kornis; dis halka duvarlarinda mazgalli parapet (burc disleri)
#   - orman duvarlarinda kornisten sarkan sarmasiklar (yuva Orman_Sarmasik, T_Yaprak atlasi)
#   - kulelerde sadece govde: tac/havuz (genisleyen tepe) basladigi yerin altinda ince kusakla biter, tepeye dokunulmaz
# Eski erimis yuzey nerede disari tasiyorsa kaplama o kadar one alinir (en cok 1.2 m) ki hic gorunmesin.
# Cikti: SM_Duvar.glb -> 4 bolge x 3 yuva (Ates/Su/Orman/Hava _Blok, _Bezek, _Harc); kose rengi = blok tonu (orman: yosun,
# ates: is, su: buz, hava: damar); Harc'ta R = kor maskesi (ates derzlerinin seyrek parlayan yerleri). UV metre cinsinden (malzemede olceklenir).
# Kullanim: python3 duvar3d.py konturlar.npy arena_game.glb SM_Duvar.glb
import math
import sys
import numpy as np
import trimesh
from scipy import ndimage as nd

KONTUR, ARENA, CIKTI = (sys.argv[1:4] + ["konturlar.npy", "arena_game.glb", "SM_Duvar.glb"][len(sys.argv) - 1:])[:3]
MERKEZ = np.array([-0.886, -0.281])
DERZ, PAH = 0.025, 0.035
KORNIS_H, KORNIS_UST = 0.35, 0.45            # kornis yuksekligi; kornis tepesi = kademe + KORNIS_UST
rng = np.random.default_rng(7)
arena = trimesh.load(ARENA, force="mesh")
kosular = list(np.load(KONTUR, allow_pickle=True))


def bolge(xz):
    a = math.degrees(math.atan2(xz[1] - MERKEZ[1], xz[0] - MERKEZ[0]))
    return "Ates" if a < -90 else "Su" if a < 0 else "Hava" if a < 90 else "Orman"


class Yuva:
    def __init__(self):
        self.V, self.U, self.C, self.F = [], [], [], []

    def dortgen(self, p, uv, renk):
        """p: 4 kose (saat yonu tersi, disaridan bakinca), kendi koseleri (duz golgeleme)"""
        b = len(self.V)
        self.V += list(p)
        self.U += list(uv)
        self.C += [renk] * 4
        self.F += [[b, b + 1, b + 2], [b, b + 2, b + 3]]

    def ucgen(self, p, uv, renk):
        b = len(self.V)
        self.V += list(p)
        self.U += list(uv)
        self.C += [renk] * 3
        self.F += [[b, b + 1, b + 2]]


yuvalar = {}


def yuva(b, ad):
    return yuvalar.setdefault(b + "_" + ad, Yuva())


def tasma_olc(xz, n, alt, ust, hs=np.linspace(0.15, 0.9, 4), ham=False):
    """eski yuzeyin kontur cizgisinden ne kadar disari tastigi (yatay isinlarla, verilen bagil yuksekliklerde).
    ham=True: kirpilmamis (yukseklik x nokta) matris; eksi = yuzey konturun icinde"""
    O, D = [], []
    for h in hs:
        y = alt + (ust - alt) * h
        O.append(np.c_[xz[:, 0] + n[:, 0] * 2.5, y, xz[:, 1] + n[:, 1] * 2.5])
        D.append(np.c_[-n[:, 0], np.zeros(len(xz)), -n[:, 1]])
    O, D = np.concatenate(O), np.concatenate(D)
    t = np.full(len(O), 9.0)
    loc, ri, _ = arena.ray.intersects_location(O, D, multiple_hits=False)
    t[ri] = np.linalg.norm(loc - O[ri], axis=1)
    T = (2.5 - t).reshape(len(hs), -1)
    return T if ham else np.clip(T.max(0), 0, 1.2)


class Kosu:
    """duvar cizgisi: yay uzunlugu s'den konum/normal; d = disari derinlik"""

    def __init__(self, k):
        self.L = k["L"]
        self.kapali = bool(k["kapali"])
        xz, n = k["xz"].astype(float), k["n"].astype(float)
        mod = "wrap" if self.kapali else "nearest"
        self.ayak = nd.gaussian_filter1d(nd.minimum_filter1d(k["ayak"], 5, mode=mod), 1.5, mode=mod)
        self.bosluk = float(np.mean(k["bosluk"]))
        self.kule = bool(k.get("kule", False))
        self.gecersiz = False
        if self.kule:
            # kule: gövde profilini olc, tac/havuz (genisleyen tepe) basladigi yerin altinda bit; tepeye dokunma
            hs = np.linspace(0.05, 0.97, 14)
            T = tasma_olc(xz, n, self.ayak, self.L, hs, ham=True)
            T = np.where(T < -6, np.nan, T)
            with np.errstate(all="ignore"):
                import warnings
                warnings.simplefilter("ignore")
                prof = np.nanmedian(T, axis=1)
                govde = np.nanmedian(prof[:7])
            i = len(hs) - 1
            while i > 0 and prof[i] > govde + .3:
                i -= 1
            yuk = np.min(self.ayak) + (self.L - np.min(self.ayak)) * hs
            self.ust = min(yuk[min(i + 1, len(hs) - 1)] - .2 if i < len(hs) - 1 else self.L, self.L - .6)
            alt_ = self.ayak[None, :] + (self.L - self.ayak[None, :]) * hs[:, None]
            T = np.where(alt_ < self.ust - .1, T, np.nan)
            with np.errstate(all="ignore"):
                tas = np.nanmax(np.r_[T, np.full((1, T.shape[1]), np.nan)], axis=0)
            tas = np.clip(np.where(np.isnan(tas), np.nanmedian(tas) if np.isfinite(tas).any() else 0.0, tas), -3, 1.2)
            if self.ust - np.min(self.ayak) < 1.5 or not np.isfinite(govde):
                self.gecersiz = True
        else:
            self.ust = self.L + KORNIS_UST - KORNIS_H
            tas = tasma_olc(xz, n, self.ayak, self.L)
        tas = nd.gaussian_filter1d(nd.maximum_filter1d(tas, 7, mode=mod), 2.0, mode=mod) + 0.06
        self.P = xz + n * tas[:, None]
        tg = np.gradient(self.P, axis=0)                          # yon: teget x yukari = disari olsun (on yuz disa baksin)
        if np.mean(-tg[:, 1] * n[:, 0] + tg[:, 0] * n[:, 1]) < 0:
            self.P, n, self.ayak = self.P[::-1].copy(), n[::-1].copy(), self.ayak[::-1].copy()
        if self.kapali:
            self.P = np.r_[self.P, self.P[:1]]
            n = np.r_[n, n[:1]]
            self.ayak = np.r_[self.ayak, self.ayak[:1]]
        self.N = n / np.linalg.norm(n, axis=1, keepdims=True)
        self.s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(self.P, axis=0), axis=1))]
        self.boy = self.s[-1]
        self.bolge = bolge(xz.mean(0))
        # egrilik yaricapi (kisa bloklar dar kivrimlarda)
        don = np.abs(np.diff(np.unwrap(np.arctan2(self.N[:, 1], self.N[:, 0]))))
        self.yaricap = 0.5 / max(np.percentile(don, 80), 1e-3)

    def nokta(self, s, y, d):
        s = np.clip(s, 0, self.boy)
        p = np.array([np.interp(s, self.s, self.P[:, 0]), np.interp(s, self.s, self.P[:, 1])])
        n = np.array([np.interp(s, self.s, self.N[:, 0]), np.interp(s, self.s, self.N[:, 1])])
        n /= np.linalg.norm(n)
        return [p[0] + n[0] * d, y, p[1] + n[1] * d]

    def taban(self, s):
        return float(np.interp(np.clip(s, 0, self.boy), self.s, self.ayak))


def renk_blok(b, rr):
    t = rr.uniform(.8, 1.12)
    if b == "Orman" and rr.random() < .35:                       # yosun lekesi
        m = rr.uniform(.3, .8)
        return [t * (1 - m) + .45 * m, t * (1 - m) + .62 * m, t * (1 - m) + .3 * m, 1]
    if b == "Ates" and rr.random() < .3:                         # is / yanik
        k = rr.uniform(.45, .75)
        return [t * k, t * k * .95, t * k * .9, 1]
    if b == "Su" and rr.random() < .25:                          # buz
        return [t * .9, t * 1.0, t * 1.12, 1]
    if b == "Hava" and rr.random() < .2:                         # sicak damar
        return [t * 1.04, t, t * .94, 1]
    return [t, t, t, 1]


def blok(k, y_, s0, s1, y0, y1, dp, renk, uofs):
    """pahli on yuzlu tas blok (arka yuz yok: harc yuzeyine oturur)"""
    a, b = s0 + DERZ, s1 - DERZ
    c, e = y0 + DERZ, y1 - DERZ
    if b - a < .12 or e - c < .1:
        return
    pf = min(PAH, (b - a) / 3, (e - c) / 3)
    d1, d2 = dp - pf, dp
    q = lambda s, y, d: k.nokta(s, y, d)
    du, dv = uofs
    U = lambda s, y: [s + du, y + dv]
    # on yuz
    y_.dortgen([q(a + pf, c + pf, d2), q(b - pf, c + pf, d2), q(b - pf, e - pf, d2), q(a + pf, e - pf, d2)],
               [U(a, c), U(b, c), U(b, e), U(a, e)], renk)
    # pahlar
    y_.dortgen([q(a, c, d1), q(b, c, d1), q(b - pf, c + pf, d2), q(a + pf, c + pf, d2)], [U(a, c - .05), U(b, c - .05), U(b, c), U(a, c)], renk)
    y_.dortgen([q(a + pf, e - pf, d2), q(b - pf, e - pf, d2), q(b, e, d1), q(a, e, d1)], [U(a, e), U(b, e), U(b, e + .05), U(a, e + .05)], renk)
    y_.dortgen([q(a, e, d1), q(a, c, d1), q(a + pf, c + pf, d2), q(a + pf, e - pf, d2)], [U(a - .05, e), U(a - .05, c), U(a, c), U(a, e)], renk)
    y_.dortgen([q(b - pf, e - pf, d2), q(b - pf, c + pf, d2), q(b, c, d1), q(b, e, d1)], [U(b, e), U(b, c), U(b + .05, c), U(b + .05, e)], renk)



def kutu(k, y_, s0, s1, y0, y1, d0, d1, renk, ust=True, arka=False):
    """duz kutu: on (d1), yanlar, ust; istenirse arka (d0)"""
    q = lambda s, y, d: k.nokta(s, y, d)
    w, h, t = s1 - s0, y1 - y0, d1 - d0
    y_.dortgen([q(s0, y0, d1), q(s1, y0, d1), q(s1, y1, d1), q(s0, y1, d1)], [[s0, y0], [s1, y0], [s1, y1], [s0, y1]], renk)
    y_.dortgen([q(s0, y1, d0), q(s0, y0, d0), q(s0, y0, d1), q(s0, y1, d1)], [[0, y1], [0, y0], [t, y0], [t, y1]], renk)
    y_.dortgen([q(s1, y1, d1), q(s1, y0, d1), q(s1, y0, d0), q(s1, y1, d0)], [[0, y1], [0, y0], [t, y0], [t, y1]], renk)
    if ust:
        y_.dortgen([q(s0, y1, d1), q(s1, y1, d1), q(s1, y1, d0), q(s0, y1, d0)], [[s0, 0], [s1, 0], [s1, t], [s0, t]], renk)
    if arka:
        y_.dortgen([q(s1, y0, d0), q(s0, y0, d0), q(s0, y1, d0), q(s1, y1, d0)], [[s1, y0], [s0, y0], [s0, y1], [s1, y1]], renk)


# kornis profili (d, y): duvar yuzunden one tasan, ustu iceri uzanan pervaz
KORNIS = [(0.0, 0.0), (0.10, 0.0), (0.10, 0.07), (0.17, 0.10), (0.24, 0.20), (0.27, 0.30), (0.27, KORNIS_H), (-0.7, KORNIS_H)]


# kule kusagi: tepenin altinda ince silme; ustu duvara geri doner (tepeye uzanmaz)
KUSAK = [(0.0, 0.0), (0.09, 0.0), (0.09, 0.16), (0.0, 0.24)]


def kornis(k, y_, yt, renk, KORNIS=KORNIS):
    ns = max(2, int(math.ceil(k.boy / 0.5)))
    ss = np.linspace(0, k.boy, ns + 1)
    v = np.r_[0, np.cumsum([math.hypot(KORNIS[i + 1][0] - KORNIS[i][0], KORNIS[i + 1][1] - KORNIS[i][1]) for i in range(len(KORNIS) - 1)])]
    for i in range(ns):
        for j in range(len(KORNIS) - 1):
            (da, ya), (db, yb) = KORNIS[j], KORNIS[j + 1]
            p = [k.nokta(ss[i], yt + ya, da), k.nokta(ss[i + 1], yt + ya, da), k.nokta(ss[i + 1], yt + yb, db), k.nokta(ss[i], yt + yb, db)]
            y_.dortgen(p, [[ss[i], v[j]], [ss[i + 1], v[j]], [ss[i + 1], v[j + 1]], [ss[i], v[j + 1]]], renk)
    if not k.kapali:                                              # uc kapaklari
        for s_, yon in ((0, -1), (k.boy, 1)):
            m = [k.nokta(s_, yt + y, d) for d, y in KORNIS]
            for j in range(1, len(m) - 1):
                tri = [m[0], m[j], m[j + 1]] if yon > 0 else [m[0], m[j + 1], m[j]]
                y_.ucgen(tri, [[0, 0], [KORNIS[j][0], KORNIS[j][1]], [KORNIS[j + 1][0], KORNIS[j + 1][1]]], renk)


def parapet(k, y_, yt):
    """mazgalli parapet: alcak duvar + burc disleri (kornisin ustunde, duvar yuzune hizali)"""
    taban = yt + KORNIS_H
    d0, d1 = -0.38, 0.0
    renk = [.95, .95, .95, 1]
    ns = max(1, int(round(k.boy / 1.0)))
    for i in range(ns):
        kutu(k, y_, k.boy * i / ns, k.boy * (i + 1) / ns, taban, taban + .5, d0, d1, renk, ust=True, arka=True)
    adim = 1.0
    n = max(2, int(k.boy // adim))
    bas = (k.boy - n * adim) / 2 + .2
    for i in range(n if k.kapali else n):
        s0 = bas + i * adim
        if s0 + .55 > k.boy:
            break
        kutu(k, y_, s0, s0 + .55, taban + .5, taban + 1.15, d0, d1, renk, ust=True, arka=True)


def plastir(k, y_, sm, alt, yt, renk):
    kutu(k, y_, sm - .5, sm + .5, alt, alt + .55, 0, .42, renk)                 # ayak
    kutu(k, y_, sm - .38, sm + .38, alt + .55, yt - .4, 0, .3, renk, ust=False)  # govde
    kutu(k, y_, sm - .5, sm + .5, yt - .4, yt, 0, .42, renk)                     # baslik


def sarmasik(k, y_, ust, rr):
    """kornisten sarkan sarmasik: yaprak kartlari zinciri (UV: T_Yaprak 2x2 atlasindan rastgele hucre, iki yuzlu malzeme)"""
    for s0 in np.arange(rr.uniform(.2, .6), k.boy - .3, .8):
        if rr.random() > .7:
            continue
        boy = rr.uniform(1.2, max(1.3, min(5.5, ust - k.taban(s0) - .3)))
        faz, y = rr.uniform(0, 6.3), ust + .15
        while y > ust - boy:
            sx = s0 + .14 * math.sin(y * 2.3 + faz)
            d = .14 + rr.uniform(0, .06)
            w = rr.uniform(.32, .48) * (.6 + .4 * (y - (ust - boy)) / boy)
            hx, hy = (rr.integers(0, 2) * .5, rr.integers(0, 2) * .5)
            renk = [rr.uniform(.75, 1.1)] * 3 + [1]
            ac = rr.uniform(-.5, .5)
            ds = w * math.cos(ac) / 2
            dd = w * math.sin(ac) / 2
            y_.dortgen([k.nokta(sx - ds, y - w, d - dd), k.nokta(sx + ds, y - w, d + dd), k.nokta(sx + ds, y, d + dd + .05),
                        k.nokta(sx - ds, y, d - dd + .05)], [[hx, hy + .5], [hx + .5, hy + .5], [hx + .5, hy], [hx, hy]], renk)
            y -= w * rr.uniform(.45, .7)


toplam_blok = 0
for kd in kosular:
    k = Kosu(kd)
    if k.gecersiz or k.boy < 3.0 or (k.kapali and k.boy < 6):
        continue
    b = k.bolge
    rr = np.random.default_rng(int(k.L * 100) + len(k.P))
    yt = k.ust - (KUSAK[-1][1] if k.kule else 0)
    yuk = k.L - float(np.min(k.ayak))
    # plastir yerleri
    plastirlar = []
    if yuk >= 3.5 and k.boy >= 7 and k.yaricap > 4 and not k.kule:
        n = max(1, int(round(k.boy / 6.0)))
        plastirlar = [k.boy * (i + .5) / n for i in range(n)]
    # harc (koyu arka yuzey)
    ns = max(1, int(math.ceil(k.boy / 0.5)))
    ss = np.linspace(0, k.boy, ns + 1)
    hy = yuva(b, "Harc")
    for i in range(ns):
        a0, a1 = k.taban(ss[i]), k.taban(ss[i + 1])
        hy.dortgen([k.nokta(ss[i], a0, 0), k.nokta(ss[i + 1], a1, 0), k.nokta(ss[i + 1], yt, 0), k.nokta(ss[i], yt, 0)],
                   [[ss[i], a0], [ss[i + 1], a1], [ss[i + 1], yt], [ss[i], yt]], [float(rr.random() < .18) * rr.uniform(.4, 1), 0, 0, 1])
    # bloklar: ustten asagi siralar
    by = yuva(b, "Blok")
    bmax = float(np.clip(k.yaricap * .4, .5, 1.9))
    y1 = yt
    alt_min = float(np.min(k.ayak))
    sira = 0
    while y1 > alt_min + .1:
        y0 = y1 - rr.uniform(.5, .72)
        s = -rr.uniform(0, bmax) if not k.kapali else 0.0
        if k.kapali:                                              # kapali halkada bloklar tam sigsin
            nb = max(3, int(round(k.boy / (bmax * .85))))
            kesit = list(np.linspace(0, k.boy, nb + 1) + (sira % 2) * k.boy / nb / 2)
            araliklar = [(kesit[i], kesit[i + 1]) for i in range(nb)]
        else:
            araliklar = []
            while s < k.boy:
                L_ = rr.uniform(bmax * .55, bmax)
                araliklar.append((max(s, 0), min(s + L_, k.boy)))
                s += L_
        for s0, s1 in araliklar:
            if s1 - s0 < .2:
                continue
            sm = (s0 + s1) / 2
            taban = max(k.taban(s0), k.taban(sm), k.taban(min(s1, k.boy)))
            if y1 - max(y0, taban) < .15:
                continue
            blok(k, by, s0, s1, max(y0, taban), y1, rr.uniform(.05, .1), renk_blok(b, rr), (rr.uniform(0, 8), rr.uniform(0, 8)))
            toplam_blok += 1
        y1 = y0
        sira += 1
    bz = yuva(b, "Bezek")
    kornis(k, bz, yt, [1, 1, 1, 1], KUSAK if k.kule else KORNIS)
    for p in plastirlar:
        plastir(k, bz, p, k.taban(p), yt, [1, 1, 1, 1])
    if b == "Orman" and not k.kule:
        sarmasik(k, yuva(b, "Sarmasik"), yt + KORNIS_H, rr)
    if k.bosluk > .6 and yuk >= 3 and not k.kule:                               # sadece dis halka duvarlari (kuleler kaplanmaz)
        parapet(k, bz, yt)

sahne = trimesh.Scene()
tri = 0
for ad, y_ in sorted(yuvalar.items()):
    if not y_.F:
        continue
    V = np.array(y_.V, float)
    m = trimesh.Trimesh(V, np.array(y_.F), process=False)
    m.visual = trimesh.visual.TextureVisuals(uv=np.array(y_.U, float), material=trimesh.visual.material.PBRMaterial(name=ad))
    m.visual.vertex_attributes["color"] = (np.clip(np.array(y_.C, float), 0, 1) * 255).astype(np.uint8)
    _ = m.vertex_normals
    sahne.add_geometry(m, geom_name=ad)
    tri += len(y_.F)
    print("%-12s %7d ucgen" % (ad, len(y_.F)))
sahne.export(CIKTI)
print("blok", toplam_blok, "toplam ucgen", tri, "->", CIKTI)
