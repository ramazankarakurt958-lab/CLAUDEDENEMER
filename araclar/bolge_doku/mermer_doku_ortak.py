# Kaplama dokulari icin ortak: dikissiz gurultu ve kesme tas blok duzeni (kayan derzli siralar).
import numpy as np


def fbm(n, olc, okt=5, tohum=0):
    """dikissiz (periyodik) gurultu 0..1"""
    r = np.random.default_rng(tohum)
    o = np.zeros((n, n))
    a = 1
    fx = np.fft.fftfreq(n)[None, :]
    fy = np.fft.fftfreq(n)[:, None]
    f = np.hypot(fx, fy)
    for k in range(okt):
        w = np.exp(-(f * n / (olc * 2 ** k)) ** 2 / 2) - (np.exp(-(f * n / (olc * 2 ** (k - 1))) ** 2 / 2) if k else 0)
        o += a * np.real(np.fft.ifft2(np.fft.fft2(r.standard_normal((n, n))) * w))
        a *= .55
    return (o - o.min()) / (o.max() - o.min())


def blok_duzeni(S, M, sira, boylar, rng):
    """S px = M m kare; sira yuksekligi (m), blok boylari (m). Doner: etiket, derze uzaklik (m), blok ici u, v (m), blok sayisi."""
    px = S / M
    lab = np.zeros((S, S), np.int32)
    dmin = np.full((S, S), 9.0)
    bu = np.zeros((S, S))
    bv = np.zeros((S, S))
    yy, xx = np.mgrid[0:S, 0:S] / px
    k = 0
    for r_ in range(int(round(M / sira))):
        y0, y1 = r_ * sira, (r_ + 1) * sira
        seg, t = [], 0
        while t < M - 1e-6:
            b = rng.choice(boylar)
            if 1e-6 < M - t - b < min(boylar) * .9:
                b = M - t
            seg.append((t, min(b, M - t)))
            t += b
        off = rng.uniform(0, M)
        satir = (yy >= y0) & (yy < y1)
        for s0, b in seg:
            xr = (xx - (s0 + off) % M) % M
            icin = satir & (xr < b)
            lab[icin] = k
            d = np.minimum.reduce([xr, b - xr, yy - y0, y1 - yy])
            dmin[icin] = d[icin]
            bu[icin], bv[icin] = xr[icin], (yy - y0)[icin]
            k += 1
    return lab, dmin, bu, bv, k
