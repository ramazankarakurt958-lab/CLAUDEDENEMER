import numpy as np
from PIL import Image
S=2048;rng=np.random.default_rng(11)
def fnoise(beta,lo=1):
    # periodic (tileable) fractal noise via spectral synthesis
    f=np.fft.fftfreq(S)*S;fx,fy=np.meshgrid(f,f);r=np.hypot(fx,fy);r[0,0]=1
    amp=r**(-beta);amp[r<lo]=0;ph=np.exp(2j*np.pi*rng.random((S,S)))
    n=np.real(np.fft.ifft2(amp*ph));return (n-n.mean())/n.std()
def cracks(n):
    # tileable voronoi edges (distance F2-F1), points wrapped over the tile
    p=rng.random((n,2))*S;P=np.vstack([p+[dx,dy] for dx in(-S,0,S) for dy in(-S,0,S)])
    from scipy.spatial import cKDTree
    y,x=np.mgrid[0:S,0:S];q=np.c_[x.ravel(),y.ravel()]+.5
    d,_=cKDTree(P).query(q,k=2);e=(d[:,1]-d[:,0]).reshape(S,S);return e
grain=fnoise(1.2,lo=8)*.55+fnoise(2.0,lo=2)*.6
e=cracks(90)+fnoise(1.6,lo=4)*2.5;crk=np.clip(1-e/3.5,0,1)**2*np.clip(fnoise(1.8,lo=3)*.8+.2,0,1)
H=grain*.6-crk*1.2
H=(H-H.min())/(H.max()-H.min())
gx=np.roll(H,-1,1)-np.roll(H,1,1);gy=np.roll(H,-1,0)-np.roll(H,1,0);k=6
n=np.dstack([-gx*k,gy*k,np.ones_like(H)]);n/=np.linalg.norm(n,axis=2,keepdims=True)
Image.fromarray(((n+1)*127.5).astype(np.uint8)).save('T_ArenaDetay_N.png')
alb=np.clip(.5+ (H-.5)*.55 - crk*.10,0,1)      # grey ~0.5 => neutral when used as overlay
Image.fromarray((alb*255).astype(np.uint8)).save('T_ArenaDetay_D.png')
print('ok',alb.mean())
