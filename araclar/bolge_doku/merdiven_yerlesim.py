# Fab "Castle Stairs" modullerinin ates ve su tribunlerine dizilisi (arena glTF eksenleri: Y yukari, metre).
# Tribun bandi: 28 m yurume yolu -> rampa -> dik duvar -> ~34 m teras. Her oturma diliminde (ara bolme bloklari
# arasinda) iki sira modul: on sira yurume yolundan, arka sira onun ustunden terasa cikar. Moduller duvar egrisine
# diktir; bir sutundaki iki modul ayni normal cizgisini paylasir. Cikti: merdiven_yerlesim.json
#   on      : modulun on-alt-orta noktasi (en alt basamagin onu, taban yuksekliginde) [x, y, z]
#   yon     : yukselis yonu (yatay, duvara dogru) [x, 0, z]
#   derinlik, genislik, yukseklik: modulun kaplayacagi olculer (m) -> UE'de olcek = olcu / modulun kendi olcusu
# Girdi: game.glb (arena). Cikti FabMerdiven.py'nin sonundaki YERLESIM bloguna yazilir:
#   python3 merdiven_yerlesim.py game.glb ../../Content/Maps/Arena/FabMerdiven.py
import json
import sys
import numpy as np
import trimesh

DILIMLER = {            # arena merkezine gore aci araliklari (derece), ara bolmeler disarida
    "ates_1": (-155.5, -146.0), "ates_2": (-140.0, -124.0), "ates_3": (-117.5, -103.0),
    "su_1": (-79.5, -65.0), "su_2": (-59.0, -41.5), "su_3": (-36.0, -27.5),
}
TABAN = 28.0            # yurume yolu yuksekligi
GOMME = 0.03            # modul tabani yurume yolunun biraz altinda (aralik gorunmesin)
RAMPA_PAY = 0.15        # basamak cizgisi alttaki rampanin en az bu kadar ustunde (rampa basamaklardan tasmasin)
SIRA = 2                # radyal modul sirasi
DERIN_EN_COK = 6.4      # bant derinligi ust siniri (m)
KENAR_PAY = 0.5         # tarlaya bakan kenarda birakilan yurume yolu (m)
MODUL_GEN = 4.55        # modulun dogal genisligi (m) - sutun sayisi buna gore
ORTUSME = 1.03          # komsu moduller arasi bosluk kalmasin
EGIM_EN_COK = None      # None: terasa kadar cik; sayi (yukselme/derinlik): en fazla bu egim, ustte set duvari kalir


def duvar_olc(m, adim=0.5):
    rs = np.arange(24, 44, .1)
    out = []
    for t in np.arange(-160, -20, adim):
        th = np.radians(t)
        o = np.c_[rs * np.cos(th), np.full(len(rs), 90.), rs * np.sin(th)]
        loc, ri, _ = m.ray.intersects_location(o, np.tile([0, -1., 0], (len(rs), 1)), multiple_hits=False)
        h = np.full(len(rs), -99.)
        h[ri] = loc[:, 1]
        if not (h >= 27.5).any():
            out.append((t, np.nan, np.nan, np.nan)); continue
        i0 = int(np.argmax(h >= 27.5))
        j = next((i for i in range(i0 + 15, len(rs)) if h[i] >= 33.2 and h[i - 1] < 32.6), None)
        if j is None:
            out.append((t, rs[i0], np.nan, np.nan)); continue
        out.append((t, rs[i0], rs[j], np.median(h[j + 3:j + 20])))
    return np.array(out)


def puruzsuz(t, r, derece=2):
    """r(aci) icin aykirilara dayanikli 2. derece egri (duvar ustundeki kule, oluk gibi tekil sapmalar atilir)"""
    tut = np.ones(len(t), bool)
    for _ in range(4):
        c = np.polyfit(t[tut], r[tut], derece)
        e = np.abs(np.polyval(c, t) - r)
        tut = e < max(0.35, 2.5 * np.median(e[tut]))
    return c


def dilim(d, a, b):
    s = (d[:, 0] >= a) & (d[:, 0] <= b) & np.isfinite(d[:, 2]) & (d[:, 3] > 33) & (d[:, 3] < 35)
    t, ri, rw, ht = np.radians(d[s, 0]), d[s, 1], d[s, 2], d[s, 3]
    T = np.radians(np.arange(a, b + 1e-6, 0.25))
    RW = np.polyval(puruzsuz(t, rw, 2 if b - a > 12 else 1), T)   # kisa dilimde az ornek: dogru
    RI = np.polyval(puruzsuz(t, ri, 1), T)
    W = np.c_[RW * np.cos(T), RW * np.sin(T)]                # duvar egrisi (x, z)
    I = np.c_[RI * np.cos(T), RI * np.sin(T)]
    return W, I, float(np.median(ht))


def normaller(W):
    tg = np.gradient(W, axis=0)
    tg /= np.linalg.norm(tg, axis=1, keepdims=True)
    n = np.c_[tg[:, 1], -tg[:, 0]]                              # tegete dik
    merkez = np.array([-0.73, -0.36])
    if np.mean(np.sum(n * (W - merkez), 1)) < 0:                # disa (duvara) baksin
        n = -n
    return n


def rampa_yuksekligi(m, sutunlar, nokta, norm):
    """Sutunlarin on-alt kosesinden arka-ust kosesine cizgi, alttaki arena rampasini asmali: gereken toplam yukselme."""
    if m is None:
        return 0.0
    gerek = 0.0
    for i0, i1, derin in sutunlar:
        for f in np.linspace(i0 + 0.2 * (i1 - i0), i1 - 0.2 * (i1 - i0), 4):   # uclar ara bolmeye degiyor
            P, nn = nokta(f), norm(f)
            t = np.arange(1.0, derin + 1e-6, 0.1)                 # ondan duvara (on kenardaki kucuk cikintilar haric)
            Q = P[None, :] - nn[None, :] * (derin - t)[:, None]
            o = np.c_[Q[:, 0], np.full(len(t), 90.), Q[:, 1]]
            loc, ri, _ = m.ray.intersects_location(o, np.tile([0, -1., 0], (len(t), 1)), multiple_hits=False)
            h = np.full(len(t), TABAN)
            h[ri] = loc[:, 1]
            h = np.where(h > TABAN + 4.5, TABAN, h)                # duvar ustu / kule: rampa degil
            gerek = max(gerek, float(np.max((h + RAMPA_PAY - TABAN) * derin / t)))
    return gerek


def yerlesim(d, m=None):
    moduller = []
    for ad, (a, b) in DILIMLER.items():
        W, I, ht = dilim(d, a, b)
        n = normaller(W)
        bant = np.sum((W - I) * n, 1)                          # duvardan ic kenara derinlik
        dh = (ht - TABAN) / SIRA
        derinlikler = []
        # duvar boyunca yay uzunlugu ile esit sutunlar
        s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(W, axis=0), axis=1))]
        ns = max(1, int(round(s[-1] / MODUL_GEN)))           # genislik olcegi 1e en yakin
        sinir = np.linspace(0, s[-1], ns + 1)
        idx = np.arange(len(W))

        def nokta(f):
            return np.array([np.interp(f, idx, W[:, c]) for c in (0, 1)])

        def norm(f):
            v = np.array([np.interp(f, idx, n[:, c]) for c in (0, 1)])
            return v / np.linalg.norm(v)
        sutunlar = []
        for k in range(ns):
            i0, i1 = np.interp([sinir[k], sinir[k + 1]], s, idx)
            # sutunun derinligi: sutun icinde en dar yerde kenar payi kalsin
            derin = min(DERIN_EN_COK, float(bant[int(np.floor(i0)):int(np.ceil(i1)) + 1].min()) - KENAR_PAY)
            sutunlar.append((i0, i1, derin))
        derinlikler = [c[2] for c in sutunlar]
        # dilimde tum sutunlarin siralari ayni yukseklikte (komsu basamaklar hizali)
        if EGIM_EN_COK is not None:
            dh = min(dh, max(EGIM_EN_COK * min(derinlikler) / SIRA, rampa_yuksekligi(m, sutunlar, nokta, norm) / SIRA))
        for k, (i0, i1, derin) in enumerate(sutunlar):
            A, B = nokta(i0), nokta(i1)
            na, nb = norm(i0), norm(i1)
            nm = norm((i0 + i1) / 2)
            L = derin / SIRA
            for j in range(SIRA):                            # j=0 on (alt) sira
                geri = (SIRA - j) * L                           # sira onunun duvardan uzakligi
                arka = geri - L
                # sutun sinir cizgileri boyunca on ve arka kenar noktalari
                Fa, Fb = A - na * geri, B - nb * geri
                Ba, Bb = A - na * arka, B - nb * arka
                gen = max(np.linalg.norm(Fb - Fa), np.linalg.norm(Bb - Ba)) * ORTUSME
                on = (Fa + Fb) / 2
                moduller.append(dict(dilim=ad, sira=j, sutun=k,
                                     on=[round(float(on[0]), 3), round(TABAN - GOMME + j * dh, 3), round(float(on[1]), 3)],
                                     yon=[round(float(nm[0]), 4), 0.0, round(float(nm[1]), 4)],
                                     derinlik=round(L, 3), genislik=round(float(gen), 3), yukseklik=round(dh + (GOMME if j == 0 else 0), 3)))
        print("%-7s aci %6.1f..%6.1f  sutun %d  derinlik %s  yukselme %.2f (sira %.2f)  teras %.2f  duvar boyu %.1f m"
              % (ad, a, b, ns, " ".join("%.2f" % x for x in derinlikler), SIRA * dh, dh, ht, s[-1]))
    return moduller


ALANLAR = ("dilim", "sira", "sutun", "on", "yon", "derinlik", "genislik", "yukseklik")


def betige_yaz(sonuc, betik):
    """Yerlesimi Unreal scriptinin YERLESIM bloguna Python sabiti olarak yazar."""
    satir = ["ALANLAR = %r" % (ALANLAR,), "YERLESIM = {"]
    for ad, mod in sonuc.items():
        satir.append("    %r: [" % ad)
        for o in mod:
            satir.append("        (%s)," % ", ".join(json.dumps(o[k]) for k in ALANLAR))
        satir.append("    ],")
    satir.append("}")
    s = open(betik, encoding="utf-8").read()
    bas, son = "# --- YERLESIM BASI", "# --- YERLESIM SONU ---"
    i = s.index("\n", s.index(bas)) + 1
    j = s.index(son)
    open(betik, "w", encoding="utf-8").write(s[:i] + "\n".join(satir) + "\n" + s[j:])
    print("yazildi:", betik)


if __name__ == "__main__":
    # iki dizilis: "dogal" (modulun kendi egimine yakin, ustte set duvari kalir), "dik" (terasa kadar cikar)
    oyun = sys.argv[1] if len(sys.argv) > 1 else "game.glb"
    m = trimesh.load(oyun, force="mesh")
    d = duvar_olc(m)
    sonuc = {}
    for ad, egim in (("dogal", 0.6), ("dik", None)):
        EGIM_EN_COK = egim
        print("--", ad)
        sonuc[ad] = yerlesim(d, m)
    json.dump(sonuc, open("merdiven_yerlesim.json", "w"), separators=(",", ":"))
    print("modul:", {k: len(v) for k, v in sonuc.items()})
    if len(sys.argv) > 2:
        betige_yaz(sonuc, sys.argv[2])
