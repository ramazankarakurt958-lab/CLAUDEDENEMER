# Su tribunu zemini: dikissiz tas levha dokulari (4 m x 4 m) + birikinti maskesi + dalga normali
import numpy as np
from PIL import Image
from scipy import ndimage as nd
rng=np.random.default_rng(21)
S=2048;M=4.0;px=S/M                       # piksel / metre
def fbm(n,olc,okt=5,tohum=0):
    r=np.random.default_rng(tohum);o=np.zeros((n,n));a=1;t=0
    fx=np.fft.fftfreq(n)[None,:];fy=np.fft.fftfreq(n)[:,None];f=np.hypot(fx,fy)
    for k in range(okt):
        w=np.exp(-(f*n/(olc*2**k))**2/2)-np.exp(-(f*n/(olc*2**(k-1)))**2/2) if k else np.exp(-(f*n/olc)**2/2)
        o+=a*np.real(np.fft.ifft2(np.fft.fft2(r.standard_normal((n,n)))*w));t+=a;a*=.55
    o=(o-o.min())/(o.max()-o.min());return o
# --- levha duzeni (yatay siralar, kayan derzler) ---
sira=0.5;nsira=int(M/sira);boylar=[.6,.8,1.0,1.2]
lab=np.zeros((S,S),np.int32);kenar=np.full((S,S),9.0)
yy,xx=np.mgrid[0:S,0:S]/px
k=0;dmin=np.full((S,S),9.0)
for r_ in range(nsira):
    y0=r_*sira;y1=y0+sira
    seg=[];t=0
    while t<M-1e-6:
        b=rng.choice(boylar)
        if M-t-b<.55 and M-t-b>1e-6: b=M-t
        seg.append((t,min(b,M-t)));t+=b
    off=rng.uniform(0,M)
    satir=(yy>=y0)&(yy<y1)
    for (s0,b) in seg:
        x0=(s0+off)%M
        xr=(xx-x0)%M
        icin=satir&(xr<b)
        lab[icin]=k
        d=np.minimum.reduce([xr,b-xr,yy-y0,y1-yy])
        dmin[icin]=d[icin];k+=1
derz=0.006;pah=0.025
h=np.clip((dmin-derz)/pah,0,1);h=np.sqrt(h)                    # pahli kenar
v_=rng.uniform(-1,1,k);renk_s=v_[:,None]*np.array([7,7,7])+np.array([108,111,116])   # notr gri, az fark
yuk_s=rng.uniform(-.25,.25,k)                                  # levhalar hafif farkli yukseklikte
tane=fbm(S,60,5,1);ince=fbm(S,300,3,2);leke=fbm(S,8,4,3)
renk=renk_s[lab]*(.72+.5*tane[...,None])*(.82+.3*leke[...,None])
kir_ao=1-.22*np.clip((.05-dmin)/.05,0,1)               # derz yaninda kir/golge
renk=renk*kir_ao[...,None]
derzrenk=np.array([48,52,58.])
renk=renk*h[...,None]+derzrenk*(1-h[...,None])
# kenarlarda buz/kirag i
kir=np.clip((pah*2-dmin)/(pah*2),0,1)*np.clip((ince-.5)*3,0,1)*.6     # kenarlarda hafif asinma/kirag
renk=renk*(1-kir[...,None]*.35)+np.array([150,160,172])*kir[...,None]*.35
Image.fromarray(np.clip(renk,0,255).astype(np.uint8)).save('T_SuZemin_D.png')
H=h*(1+yuk_s[lab]*.3)+tane*.08+ince*.03
gx=(np.roll(H,-1,1)-np.roll(H,1,1));gy=(np.roll(H,-1,0)-np.roll(H,1,0))
n=np.dstack([-gx*6,-gy*6,np.ones_like(H)]);n/=np.linalg.norm(n,axis=2,keepdims=True)
Image.fromarray(((n*.5+.5)*255).astype(np.uint8)).save('T_SuZemin_N.png')
rough=np.clip(.62+.15*(tane-.5)+.25*(1-h)-.25*kir,0,1)
Image.fromarray((rough*255).astype(np.uint8)).save('T_SuZemin_R.png')
# --- birikinti maskesi (20 m'lik dikissiz) ---
b=fbm(1024,3,2,7);b=nd.gaussian_filter(b,6,mode='wrap');b=(b-b.min())/(b.max()-b.min())
Image.fromarray((b*255).astype(np.uint8)).save('T_SuZemin_Birikinti.png')
# --- dalga normali (yumusak halkasi/kipirtilar) ---
w=fbm(512,24,3,9)
gx=(np.roll(w,-1,1)-np.roll(w,1,1));gy=(np.roll(w,-1,0)-np.roll(w,1,0))
n=np.dstack([-gx*25,-gy*25,np.ones_like(w)]);n/=np.linalg.norm(n,axis=2,keepdims=True)
Image.fromarray(((n*.5+.5)*255).astype(np.uint8)).save('T_SuZemin_Dalga.png')
print('levha',k)
