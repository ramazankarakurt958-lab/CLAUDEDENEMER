# Hava tribunu mermer kaplamasi: dikissiz kesme mermer blok dokulari (4 m x 4 m, 2048 px = 5 mm/px).
# Siralar 50 cm, blok boylari 0.8-1.4 m (kayan derz), her blokta kendi yonunde ince damarlar, pahli derz.
# Cikti: T_Mermer_D.png (RGB renk, A = puruzluluk), T_Mermer_N.png (normal; x = +u, y = +satir yonu).
# Malzemede ucyonlu (triplanar) dunyaya hizali kullanilir: duvarda siralar yatay, zeminde levha.
import numpy as np
from PIL import Image
rng = np.random.default_rng(37)
S = 2048
M = 4.0
px = S / M


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


# --- blok duzeni ---
sira = 0.5
boylar = [.8, 1.0, 1.2, 1.4]
lab = np.zeros((S, S), np.int32)
dmin = np.full((S, S), 9.0)
bu = np.zeros((S, S))                          # blok ici yerel koordinat (m), dikis gecmez
bv = np.zeros((S, S))
yy, xx = np.mgrid[0:S, 0:S] / px
k = 0
for r_ in range(int(M / sira)):
    y0, y1 = r_ * sira, (r_ + 1) * sira
    seg, t = [], 0
    while t < M - 1e-6:
        b = rng.choice(boylar)
        if 1e-6 < M - t - b < .7:
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

# --- mermer: blok basina damar yonu, sikligi, ton ---
aci = rng.uniform(-0.6, 0.6, k) + rng.choice([0, np.pi / 2], k, p=[.7, .3])
sik = rng.uniform(2.5, 6.0, k)
faz = rng.uniform(0, 50, k)
ton = rng.choice(3, k, p=[.55, .3, .15])
tonlar = np.array([[234, 227, 213], [228, 225, 218], [238, 229, 210.]])     # krem, acik gri, sicak
parlak = rng.uniform(.95, 1.04, k)
turb = fbm(S, 3, 5, 3)                # buyuk olcekli bukulme: uzun, akan damarlar
turb2 = fbm(S, 9, 4, 4)
bulut = fbm(S, 5, 4, 5)
L = lab
yonlu = bu * np.cos(aci[L]) + bv * np.sin(aci[L])
dalga = np.sin(yonlu * sik[L] + faz[L] + turb * 4.0 + turb2 * 1.2)
damar = np.exp(-(dalga / 0.07) ** 2)                                 # ince ana damarlar
damar2 = np.exp(-(np.sin(yonlu * sik[L] * 2.7 + faz[L] * 1.7 + turb * 6 + turb2 * 2) / 0.05) ** 2) * .35
dm = np.clip(damar * (.25 + .75 * turb2) + damar2 * np.clip(bulut * 1.5 - .4, 0, 1), 0, 1)
renk = tonlar[ton][L] * parlak[L][..., None]
renk = renk * (.93 + .1 * bulut[..., None])                          # hafif bulutlanma
renk = renk - dm[..., None] * np.array([64, 62, 56.]) * .55               # damar: gri koyulasma

# --- derz ve pah ---
derz, pah = 0.004, 0.008
h = np.sqrt(np.clip((dmin - derz) / pah, 0, 1))
golge = 1 - .10 * np.clip((.025 - dmin) / .025, 0, 1)
renk = renk * golge[..., None]
harc = np.array([105, 100, 92.])
renk = renk * h[..., None] + harc * (1 - h[..., None])
rough = np.clip(.2 + .06 * (bulut - .5) + .12 * dm + .5 * (1 - h), 0, 1)
D = np.dstack([np.clip(renk, 0, 255), rough * 255]).astype(np.uint8)
Image.fromarray(D, "RGBA").save("T_Mermer_D.png", optimize=True)

H = h * (1 + rng.uniform(-.15, .15, k)[L] * .2) + bulut * .02 - dm * .01
gx = np.roll(H, -1, 1) - np.roll(H, 1, 1)
gy = np.roll(H, -1, 0) - np.roll(H, 1, 0)
n = np.dstack([-gx * 5, -gy * 5, np.ones_like(H)])
n /= np.linalg.norm(n, axis=2, keepdims=True)
Image.fromarray(((n * .5 + .5) * 255).astype(np.uint8)).save("T_Mermer_N.png", optimize=True)
Image.fromarray(np.clip(renk[:1024, :1024], 0, 255).astype(np.uint8)).resize((512, 512)).save("T_Mermer_onizleme.jpg", quality=88)
print("blok", k, "ortalama renk", renk.reshape(-1, 3).mean(0).round(0), "puruz", rough.mean().round(2))
