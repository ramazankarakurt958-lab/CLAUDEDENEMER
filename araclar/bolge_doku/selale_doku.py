# Dikissiz (tileable) selale dokulari: T_Selale_Akis (R=kopuk cizgileri, G=yogunluk, B=ince serpinti), T_Selale_N (dalga normali)
import numpy as np
from PIL import Image
S=512;rng=np.random.default_rng(7)
fx=np.fft.fftfreq(S)[None,:];fy=np.fft.fftfreq(S)[:,None]
def gurultu(sx,sy,us=2.0):
    # sx: yatay frekans olcegi, sy: dikey (kucuk sy -> dikeyde uzamis cizgiler)
    w=np.exp(-((fx/sx)**2+(fy/sy)**2))*(1/(np.hypot(fx,fy)+1e-3))**(us*0)
    n=np.real(np.fft.ifft2(np.fft.fft2(rng.standard_normal((S,S)))*w))
    return (n-n.min())/(n.max()-n.min())
cizgi=gurultu(.08,.006)*.55+gurultu(.2,.015)*.3+gurultu(.45,.05)*.15     # dikey akis cizgileri
yog=gurultu(.03,.01)
ince=gurultu(.35,.12)
def kontrast(a,k):return np.clip((a-.5)*k+.5,0,1)
R=kontrast(cizgi,1.8);G=kontrast(yog,1.4);B=kontrast(ince,2.0)
Image.fromarray((np.dstack([R,G,B])*255).astype(np.uint8)).save('T_Selale_Akis.png')
h=cizgi*1.0+ince*.25
dx=(np.roll(h,-1,1)-np.roll(h,1,1))*S*.02;dy=(np.roll(h,-1,0)-np.roll(h,1,0))*S*.02
n=np.dstack([-dx,-dy,np.ones_like(h)]);n/=np.linalg.norm(n,axis=2,keepdims=True)
Image.fromarray(((n*.5+.5)*255).astype(np.uint8)).save('T_Selale_N.png')
print('ok',R.mean(),G.mean())
