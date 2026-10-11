# Oturma basamaklari: ust gorunum yukseklik haritasinda merkezden disa duzenli yukselen bantlar
import numpy as np,trimesh
from scipy import ndimage as nd
from scipy.interpolate import RegularGridInterpolator as RGI
H=0.25
def harita(m):
    # yukaridan isinla gercek ust yuzey (kuleler/cikintilar dahil en ust)
    x0,x1,z0,z1=-50,50,-50,50
    xs=np.arange(x0,x1,H)+H/2;zs=np.arange(z0,z1,H)+H/2
    X,Z=np.meshgrid(xs,zs,indexing='ij')
    o=np.c_[X.ravel(),np.full(X.size,80.),Z.ravel()];d=np.tile([0,-1.,0],(X.size,1))
    loc,ri,fi=m.ray.intersects_location(o,d,multiple_hits=False)
    hm=np.full(X.size,np.nan);hm[ri]=loc[:,1];nrm=np.zeros((X.size,3));nrm[ri]=m.face_normals[fi]
    return xs,zs,hm.reshape(X.shape),nrm.reshape(X.shape+(3,))
def basamak_agirligi(xs,zs,hm,nrm):
    X,Z=np.meshgrid(xs,zs,indexing='ij');r=np.hypot(X,Z)
    dolu=np.isfinite(hm);h=np.where(dolu,hm,0)
    hs=nd.gaussian_filter(h,4)/np.maximum(nd.gaussian_filter(dolu.astype(float),4),1e-3)
    gx,gz=np.gradient(hs,H)
    egim=(gx*X+gz*Z)/np.maximum(r,1e-3)            # disa dogru yukselme (dy/dr)
    yan=np.abs(gx*Z-gz*X)/np.maximum(r,1e-3)        # cevre boyunca egim (az olmali)
    duz=nd.gaussian_filter(np.abs(h-hs),3)          # kucuk puruz (basamak boyasi kadar) - kule kenari gibi sicramalar buyuk
    w=np.clip((egim-.25)/.15,0,1)*np.clip((1.3-egim)/.3,0,1)*np.clip((.5-yan)/.25,0,1)*np.clip((2.5-duz)/1.0,0,1)
    w*=dolu*np.clip((r-24)/1.5,0,1)*np.clip((47-r)/2,0,1)*(hm>22.5 if True else 1)
    w=nd.binary_closing(nd.binary_opening(w>.5,iterations=2),iterations=3)*1.0
    w=nd.gaussian_filter(w,1.5)
    return w
if __name__=='__main__':
    m=trimesh.load('game.glb',force='mesh')
    xs,zs,hm,nrm=harita(m)
    w=basamak_agirligi(xs,zs,hm,nrm)
    np.savez('basamak.npz',xs=xs,zs=zs,w=w)
    print('basamak alani %.0f m2'%(w.sum()*H*H))
    from PIL import Image
    Image.fromarray((np.clip(w,0,1)[:,::-1].T*255).astype(np.uint8)).resize((800,800)).save('basamak_ust.png')
    # yuzlere: merkezi basamak bolgesinde olan ve yukari bakan yuzler
    c=m.triangles_center;n=m.face_normals
    f=RGI((xs,zs),w,bounds_error=False,fill_value=0)(c[:,[0,2]])
    sec=np.where((f>.5)&(n[:,1]>.2))[0]
    m.submesh([sec],append=True).export('dbg.glb');print('yuz',len(sec))
