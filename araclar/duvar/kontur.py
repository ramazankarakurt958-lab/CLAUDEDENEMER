# Arena duvarlarinin temiz konturlari: ust yukseklik haritasi (H) 0.5 m kademelerle kesilir, her kademenin sinir cizgisi
# yumusatilir; sinirin disinda en az DUSUS metre asagi inen yerler "duvar" sayilir (sadece o duvarin en ust kademesinde).
# Kuleler kaplanmaz: herhangi bir kademede kapali, yuvarlak ve cevresi < 70 m olan kontur "kule" sayilir, cevresindeki duvar
# noktalari atilir. Selalelerin (SM_Selale.glb) aktigi yuzeyler de kaplanmaz.
# Girdi: hmap.npz (H: ust, B: alt yukseklik, G hucre, O koken; arena glTF x-z duzlemi, metre), istege bagli SM_Selale.glb.
# Cikti: konturlar.npy
# Kullanim: python3 kontur.py hmap.npz [SM_Selale.glb]
import sys
import numpy as np
import cv2
from scipy import ndimage as nd

d = np.load(sys.argv[1] if len(sys.argv) > 1 else "hmap.npz")
H, B, G, O = d["H"], d["B"], float(d["G"]), float(d["O"])
S = H.shape[0]
MERKEZ = np.array([-0.886, -0.281])
KOPRULER = {0: (22.45, 1.65), 180: (31.4, 1.72), 270: (24.45, 1.52)}   # aci: (r son, yari genislik)
DUSUS = 1.6

# kucuk bosluklari doldur, ince sivri pikleri yumusat
dolu = ~np.isnan(H)
Hf = np.where(dolu, H, -50.0)
Hf = nd.median_filter(Hf, 3)
Bf = nd.median_filter(np.where(dolu, B, 99.0), 3)


def ornek(A, x, z, bos):
    i = ((x - O) / G - .5).round().astype(int)
    j = ((z - O) / G - .5).round().astype(int)
    ok = (i >= 0) & (i < S) & (j >= 0) & (j < S)
    v = np.full(x.shape, bos, float)
    v[ok] = A[j[ok], i[ok]]
    return v


def disarida(x, z):
    """orta platform, kopruler ve uzak adalar kaplanmaz"""
    dx, dz = x - MERKEZ[0], z - MERKEZ[1]
    r = np.hypot(dx, dz)
    h = (r < 16.6) | (r > 53.5)
    for aci, (r1, yg) in KOPRULER.items():
        t = np.radians(aci)
        boy = dx * np.cos(t) + dz * np.sin(t)
        yan = np.abs(-dx * np.sin(t) + dz * np.cos(t))
        h |= (boy > 14) & (boy < r1 + .6) & (yan < yg + .7)
    return h


cek = np.ones((3, 3), np.uint8)
seviyeler = np.arange(20.5, 51.5, 0.5)

# kuleler: kapali, yuvarlak, kucuk konturlar (merkez, yaricap)
kuleler = []
for L in seviyeler:
    m = cv2.morphologyEx((Hf >= L).astype(np.uint8), cv2.MORPH_OPEN, cek)
    for k in cv2.findContours(m, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)[0]:
        cevre, alan = cv2.arcLength(k, True) * G, cv2.contourArea(k) * G * G
        if 6 < cevre < 70 and alan > 0 and 4 * np.pi * alan / cevre ** 2 > .72:
            (cx, cz), rad = cv2.minEnclosingCircle(k)
            kuleler.append((O + G * (cx + .5), O + G * (cz + .5), rad * G))
kuleler = np.array(kuleler) if kuleler else np.zeros((0, 3))
print("kule konturu", len(kuleler))

selale = None
if len(sys.argv) > 2:
    import trimesh
    from scipy.spatial import cKDTree
    sv = trimesh.load(sys.argv[2], force="mesh").vertices
    selale = (cKDTree(sv[:, [0, 2]]), sv[:, 1])


def kule_ya_da_selale(x, z, alt, ust):
    h = np.zeros(len(x), bool)
    for cx, cz, rad in kuleler:
        h |= np.hypot(x - cx, z - cz) < rad + .9
    if selale is not None:
        agac, sy = selale
        for i, yakin in enumerate(agac.query_ball_point(np.c_[x, z], 1.6)):
            if yakin and np.any((sy[yakin] > alt[i] - 1) & (sy[yakin] < ust + 1)):
                h[i] = True
    return h


kosular = []
for L in seviyeler:
    m = (Hf >= L).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cek)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cek)
    kn, _ = cv2.findContours(m, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    for k in kn:
        if len(k) < 20:
            continue
        p = k[:, 0, :].astype(float)
        p = nd.gaussian_filter1d(p, 4.0, axis=0, mode="wrap")
        seg = np.linalg.norm(np.diff(np.r_[p, p[:1]], axis=0), axis=1)
        s = np.r_[0, np.cumsum(seg)]
        n = max(int(s[-1] * G / 0.5), 6)                        # 0.5 m aralik
        t = np.linspace(0, s[-1], n, endpoint=False)
        q = np.c_[np.interp(t, s, np.r_[p[:, 0], p[:1, 0]]), np.interp(t, s, np.r_[p[:, 1], p[:1, 1]])]
        xz = O + G * (q + .5)
        tan = np.roll(xz, -1, 0) - np.roll(xz, 1, 0)
        tan /= np.maximum(np.linalg.norm(tan, axis=1, keepdims=True), 1e-6)
        nrm = np.c_[tan[:, 1], -tan[:, 0]]
        # normal disari (H < L tarafi) baksin
        dis = ornek(Hf, xz[:, 0] + nrm[:, 0] * .5, xz[:, 1] + nrm[:, 1] * .5, -50)
        ic = ornek(Hf, xz[:, 0] - nrm[:, 0] * .5, xz[:, 1] - nrm[:, 1] * .5, -50)
        if np.mean(dis < ic) < .5:
            nrm = -nrm
            dis, ic = ic, dis
        # ust kenar mi (icerisi bu kademeden 0.5 m'den fazla yuksek degil)
        ic = ornek(Hf, xz[:, 0] - nrm[:, 0] * .45, xz[:, 1] - nrm[:, 1] * .45, -50)
        ust = (ic >= L - .3) & (ic < L + .6)
        ayak = np.full(len(xz), np.inf)
        for kk in (.4, .7, 1.0, 1.4, 1.8):
            ayak = np.minimum(ayak, ornek(Hf, xz[:, 0] + nrm[:, 0] * kk, xz[:, 1] + nrm[:, 1] * kk, -50))
        yakin = np.full(len(xz), np.inf)                         # dik mi: 0.7 m icinde en az 1.2 m dusus (oturma basamaklari degil)
        for kk in (.35, .55, .75):
            yakin = np.minimum(yakin, ornek(Hf, xz[:, 0] + nrm[:, 0] * kk, xz[:, 1] + nrm[:, 1] * kk, -50))
        bosluk = ayak < -40
        alt = ornek(Bf, xz[:, 0] - nrm[:, 0] * .3, xz[:, 1] - nrm[:, 1] * .3, 99)
        ayak = np.where(bosluk, np.clip(alt, L - 14, L - 2), ayak)
        duvar = ust & (L - ayak >= DUSUS) & (L - yakin >= 1.2) & ~disarida(xz[:, 0], xz[:, 1])
        if duvar.any():
            duvar &= ~kule_ya_da_selale(xz[:, 0], xz[:, 1], ayak, L)
        # kucuk bosluklari kapat, kisa parcalari at
        duvar = nd.binary_closing(np.r_[duvar, duvar, duvar], np.ones(3))[len(duvar):2 * len(duvar)]
        if not duvar.any():
            continue
        if duvar.all():
            parcalar = [np.arange(len(xz))]
            kapali = True
        else:
            bas = np.argmin(duvar)                               # bir duvar olmayan noktadan baslayip dola
            sira = np.roll(np.arange(len(xz)), -bas)
            dv = duvar[sira]
            etiket, say = nd.label(dv)
            parcalar = [sira[etiket == e] for e in range(1, say + 1)]
            kapali = False
        for pr in parcalar:
            if len(pr) < 5:
                continue
            kosular.append(dict(L=float(L), xz=xz[pr], n=nrm[pr], ayak=ayak[pr], bosluk=bosluk[pr],
                                kapali=kapali and len(pr) == len(xz)))
print("duvar kosusu", len(kosular), "toplam uzunluk %.0f m" % sum(len(k["xz"]) * .5 for k in kosular),
      "alan %.0f m2" % sum(((k["L"] - k["ayak"]) * .5).sum() for k in kosular))
np.save("konturlar.npy", np.array(kosular, dtype=object), allow_pickle=True)
