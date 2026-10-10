import numpy as np
from PIL import Image
from scipy import ndimage as nd
S=4096;P=2048
b=np.fromfile('dump/proj.rgba',np.uint8).reshape(S,S,4)
proj=b[...,:3].astype(np.float32);cov=b[...,3]>0
w=np.clip((b[...,3].astype(np.float32)/255-.004)/.996,0,1)
pos=np.fromfile('dump/pos.f32',np.float32).reshape(P,P,4)
# world pos to 4096 (nearest), fill gutters
pc=pos[...,3]>0
idx=nd.distance_transform_edt(~pc,return_distances=False,return_indices=True)
pos=pos[idx[0],idx[1]]
pos=np.repeat(np.repeat(pos,2,0),2,1)
x,y,z=pos[...,0],pos[...,1],pos[...,2]
# gutter fill for the projection
idx=nd.distance_transform_edt(~cov,return_distances=False,return_indices=True)
d=nd.distance_transform_edt(~cov);fill=(~cov)&(d<12)
proj[fill]=proj[idx[0][fill],idx[1][fill]];w[fill]=w[idx[0][fill],idx[1][fill]]
w=nd.gaussian_filter(w,1.5)
base=np.array(Image.open('base.jpg').convert('RGB')).astype(np.float32)
# region weights: quadrants by sign of x,z (soft), centre platform neutral
K=4.0
sx=1/(1+np.exp(-x/K));sz=1/(1+np.exp(-z/K))
reg={'ates':(1-sx)*(1-sz),'su':sx*(1-sz),'toprak':(1-sx)*sz,'hava':sx*sz}
r=np.hypot(x,z);merkez=np.clip((r-19)/4,0,1)   # 0 inside central platform
out=base.copy();tot=np.zeros_like(w)
for k,rw in reg.items():
    sel=(rw>.8)&cov&(merkez>.99)
    pm=sel&(w>.6)
    pv=proj[pm];bv=base[sel&(base.sum(2)>20)]
    print(k,pm.sum(),pv.mean(0).round(1),pv.std(0).round(1),'| base',bv.mean(0).round(1),bv.std(0).round(1))
    g=(base-bv.mean(0))/bv.std(0).mean()*pv.std(0).mean()*.9+pv.mean(0)
    a=(rw*merkez)[...,None]*.85
    out=out*(1-a)+g*a
# normals for moss (up-facing) and noise for variation
nr=np.fromfile('dump/nrm.f32',np.float32).reshape(P,P,4)
nr=nr[idx2[0],idx2[1]] if False else nr
nr=np.repeat(np.repeat(nr,2,0),2,1)
lum=base.mean(2)
rng=np.random.default_rng(3)
def noise(sc):
    n=rng.random((S//sc,S//sc)).astype(np.float32);n=nd.gaussian_filter(n,2);n=(n-n.min())/(n.max()-n.min())
    return np.array(Image.fromarray((n*255).astype(np.uint8)).resize((S,S),Image.BICUBIC)).astype(np.float32)/255
nz=noise(32)*.6+noise(8)*.4
yuk=np.clip((nr[...,1]-.35)/.4,0,1)
lum3=(lum/110)[...,None]
# earth: moss on up-facing stone
yosun=np.clip(yuk*.8+(nz-.45)*1.6,0,1)*reg['toprak']*merkez*(1-w*.7)
out=out*(1-yosun[...,None]*.75)+(np.array([62,92,34])*lum3*1.1)*yosun[...,None]*.75
# fire: charred dark with glowing cracks in crevices
kav=np.clip((nd.gaussian_filter(lum,6)-lum-12)/14,0,1)*np.clip((nz-.5)*3,0,1)*.8
fa=reg['ates']*merkez*(1-w*.8)
gri=out.mean(2,keepdims=True);out=out*(1-(fa*.6)[...,None])+(gri*np.array([.62,.5,.46]))*(fa*.6)[...,None]
lav=(kav*fa)[...,None]
out=out*(1-lav)+np.array([255,96,20])*lav
# water: cold glossy blue tint; air: brighten towards white marble
sa=(reg['su']*merkez*(1-w*.8))[...,None]
out=out*(1-sa*.3)+(out*np.array([.8,1.0,1.25]))*sa*.3
ha=(reg['hava']*merkez*(1-w*.8))[...,None]
out=out*(1-ha*.35)+(out*.6+np.array([235,238,245])*.4)*ha*.35
hf=base-nd.gaussian_filter(base,(5,5,0))
wp=(w*.95)[...,None]
out=out*(1-wp)+(proj+hf*.6)*wp
out=np.clip(out,0,255).astype(np.uint8)
Image.fromarray(out).save('T_ArenaBolge.jpg',quality=93)
Image.fromarray(out).resize((1024,1024)).save('comp_prev.jpg')
