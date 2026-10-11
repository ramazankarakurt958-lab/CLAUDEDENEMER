# Ates ve su tribunlerinin egik oturma yuzeylerine gercek 3D basamaklar (arena glTF eksenleri, Y yukari, metre)
import json,struct
import numpy as np,trimesh
from scipy import ndimage as nd
from scipy.interpolate import RegularGridInterpolator as RGI
from PIL import Image
m=trimesh.load('game.glb',force='mesh')
b=np.load('basamak.npz');xs,zs,w=b['xs'],b['zs'],b['w'];H=xs[1]-xs[0]
hm=np.load('hm.npz')['hm']
# yalniz basamak bolgesinden yumusak yukseklik (kuleler karismasin)
k=(w>.3)&np.isfinite(hm);h0=np.where(k,hm,-99)
hmax=nd.maximum_filter(h0,size=5)                                  # basamak yuzeyin altina gomulmesin: yerel en yuksek
hs=nd.gaussian_filter(np.where(k,hmax,0),1.5)/np.maximum(nd.gaussian_filter(k.astype(float),1.5),1e-3)
X_,Z_=np.meshgrid(xs,zs,indexing='ij');R_=np.hypot(X_,Z_)
lab,nl=nd.label(w>.5);hfit=np.zeros_like(hs);BOL=[]
for L in range(1,nl+1):
    q=(lab==L)&np.isfinite(hm)
    rr=R_[q];yy=hmax[q];kut=np.arange(rr.min(),rr.max()+.25,.25);prof=np.full(len(kut),np.nan)
    for t,k0 in enumerate(kut):
        s_=(rr>=k0-.4)&(rr<k0+.4)
        if s_.sum()>8: prof[t]=np.percentile(yy[s_],60)
    ok=np.isfinite(prof);prof=np.interp(kut,kut[ok],prof[ok])
    prof=np.maximum.accumulate(prof);prof=nd.gaussian_filter1d(prof,8,mode='nearest');prof=np.maximum.accumulate(prof)   # disa dogru inmesin (kademeler duz kalabilir)
    hfit[lab==L]=np.interp(R_[lab==L],kut,prof)+.03
    th_=np.arctan2(Z_[lab==L],X_[lab==L]);r_=R_[lab==L]
    BOL.append(dict(t0=np.percentile(th_,3),t1=np.percentile(th_,97),r0=np.percentile(r_,3),r1=np.percentile(r_,97),kut=kut,prof=prof))
    print('bolum',L,'r %.1f-%.1f'%(kut[0],kut[-1]),'h %.1f-%.1f'%(prof[0],prof[-1]))
hfit=np.where(lab>0,hfit,hs)
W=RGI((xs,zs),w,bounds_error=False,fill_value=0);HS=RGI((xs,zs),hfit,bounds_error=False,fill_value=0)
HM=RGI((xs,zs),np.nan_to_num(hm,nan=0),bounds_error=False,fill_value=0)
# ust gorunum renk haritasi (bolge rengi; bulanik)
X,Z=np.meshgrid(xs,zs,indexing='ij')
o=np.c_[X.ravel(),np.full(X.size,80.),Z.ravel()];d=np.tile([0,-1.,0],(X.size,1))
loc,ri,fi=m.ray.intersects_location(o,d,multiple_hits=False)
tex=np.array(Image.open('T_ArenaBolge.jpg').convert('RGB')).astype(np.float32)/255
bc=trimesh.triangles.points_to_barycentric(m.triangles[fi],loc)
uv=(m.visual.uv[m.faces[fi]]*bc[:,:,None]).sum(1)
T=tex.shape[0];px=np.clip((uv[:,0]*T).astype(int),0,T-1);py=np.clip(((1-uv[:,1])*T).astype(int),0,T-1)   # glTF uv: v asagi, goruntu satiri
col=np.zeros((X.size,3));col[ri]=tex[py,px];cm=np.zeros(X.size);cm[ri]=1
col=col.reshape(X.shape+(3,));cm=cm.reshape(X.shape)
wk=(w>.3)*cm
colb=np.stack([nd.gaussian_filter(col[...,c]*wk,6) for c in range(3)],-1)/np.maximum(nd.gaussian_filter(wk,6),1e-3)[...,None]
COL=RGI((xs,zs),colb,bounds_error=False,fill_value=.4)
D=0.75;R0=20.0;NRING=40;DT=0.30            # basamak derinligi, halka baslangici, cevre adimi (m)
ust=0.06
V=[];C=[];U=[];F=[]
def kare(p,c,u):
    b=len(V);V.extend(p);C.extend(c);U.extend(u);F.extend([[b,b+1,b+2],[b,b+2,b+3]])
# cevre boyunca orneklenen aci kumesi (r~35 m'de DT aralik)
ths=np.arange(-np.pi,np.pi,DT/35.)
def profil(th):
    """halka i -> basamak ust yuksekligi; her bolum temiz bir halka dilimi (uclar radyal)"""
    pr={}
    for B in BOL:
        if not (B['t0']<=th<=B['t1']): continue
        for i in range(NRING):
            ra=R0+i*D;rb=ra+D
            if ra>=B['r0'] and rb<=B['r1']: pr[i]=float(np.interp(rb,B['kut'],B['prof']))+.03+ust
    return pr
P=[profil(t) for t in ths]
def nokta(r,th,y): return [r*np.cos(th),y,r*np.sin(th)]
for a in range(len(ths)):
    b_=(a+1)%len(ths);t0,t1=ths[a],ths[b_] if b_ else ths[0]+2*np.pi
    p0,p1=P[a],P[b_]
    for i in set(p0)&set(p1):
        ra,rb=R0+i*D,R0+(i+1)*D
        h0,h1=p0[i],p1[i];renk=COL([[ (ra+rb)/2*np.cos(t0),(ra+rb)/2*np.sin(t0)]])[0]
        s0,s1=t0*35,t1*35
        # basamak ustu (duz)
        kare([nokta(ra,t0,h0),nokta(ra,t1,h1),nokta(rb,t1,h1),nokta(rb,t0,h0)],[renk]*4,[[s0,ra],[s1,ra],[s1,rb],[s0,rb]])
        # on yuz (riser): onceki basamaktan bu basamaga ya da egimden
        alt0=p0.get(i-1,max(min(float(HM([[ra*np.cos(t0),ra*np.sin(t0)]])[0]),h0)-.1,h0-.9));alt1=p1.get(i-1,max(min(float(HM([[ra*np.cos(t1),ra*np.sin(t1)]])[0]),h1)-.1,h1-.9))
        kr=renk*.8
        kare([nokta(ra,t0,alt0),nokta(ra,t1,alt1),nokta(ra,t1,h1),nokta(ra,t0,h0)],[kr]*4,[[s0,alt0],[s1,alt1],[s1,h1],[s0,h0]])
        # arka: sonraki basamak yoksa egime/yuruyuse in
        if i+1 not in p0 or i+1 not in p1:
            g0=float(HM([[rb*np.cos(t0),rb*np.sin(t0)]])[0]);g1=float(HM([[rb*np.cos(t1),rb*np.sin(t1)]])[0])
            g0=max(min(g0,h0)-.05,h0-.9);g1=max(min(g1,h1)-.05,h1-.9)
            kare([nokta(rb,t0,h0),nokta(rb,t1,h1),nokta(rb,t1,g1),nokta(rb,t0,g0)],[kr]*4,[[s0,h0],[s1,h1],[s1,g1],[s0,g0]])
    # yan kapaklar: bu acida var, komsuda yok
    for (pa,pb,t) in ((p0,p1,t1),(p1,p0,t0)):
        for i in set(pa)-set(pb):
            pass
    for i in set(p0)-set(p1):          # t1 tarafinda biten basamaga yan kapak
        ra,rb=R0+i*D,R0+(i+1)*D;h=p0[i];g=max(min(float(HM([[ (ra+rb)/2*np.cos(t0),(ra+rb)/2*np.sin(t0)]])[0]),h)-.1,h-.9)
        renk=COL([[ (ra+rb)/2*np.cos(t0),(ra+rb)/2*np.sin(t0)]])[0]*.7
        kare([nokta(ra,t1,g),nokta(rb,t1,g),nokta(rb,t1,h),nokta(ra,t1,h)],[renk]*4,[[ra,g],[rb,g],[rb,h],[ra,h]])
    for i in set(p1)-set(p0):
        ra,rb=R0+i*D,R0+(i+1)*D;h=p1[i];g=max(min(float(HM([[ (ra+rb)/2*np.cos(t1),(ra+rb)/2*np.sin(t1)]])[0]),h)-.1,h-.9)
        renk=COL([[ (ra+rb)/2*np.cos(t1),(ra+rb)/2*np.sin(t1)]])[0]*.7
        kare([nokta(rb,t1,g),nokta(ra,t1,g),nokta(ra,t1,h),nokta(rb,t1,h)],[renk]*4,[[rb,g],[ra,g],[ra,h],[rb,h]])
V=np.array(V,np.float32);C=np.clip(np.array(C,np.float32),0,1);U=(np.array(U,np.float32)/4.0);F=np.array(F,np.uint32)
# alani sifir (yuksekligi esit basamak yuzu) kareleri at - sifir normal isikta bozulma yapar
A=np.linalg.norm(np.cross(V[F[:,1]]-V[F[:,0]],V[F[:,2]]-V[F[:,0]]),axis=1).reshape(-1,2).min(1)
tut=np.repeat(A>1e-4,2);F=F[tut]
kul=np.unique(F);yeni=np.full(len(V),-1);yeni[kul]=np.arange(len(kul))
V,C,U=V[kul],C[kul],U[kul];F=yeni[F].astype(np.uint32)
print('atilan kare',(~(A>1e-4)).sum())
tm=trimesh.Trimesh(V,F,process=False);Nn=tm.face_normals[np.repeat(np.arange(len(F)//2)*2,4)] if False else None
# duz yuzlu (sert kenar) normaller: her kare kendi normali
Nn=np.zeros_like(V)
q0=F[0::2];cr=np.cross(V[q0[:,1]]-V[q0[:,0]],V[q0[:,2]]-V[q0[:,0]])+np.cross(V[F[1::2][:,2]]-V[q0[:,0]],V[q0[:,2]]-V[q0[:,0]])*0
ln=np.linalg.norm(cr,axis=1,keepdims=True);fn=np.where(ln>1e-9,cr/np.maximum(ln,1e-9),[0,1,0])
for k in range(3): Nn[q0[:,k]]=fn
Nn[F[1::2][:,2]]=fn
print('kose',len(V),'ucgen',len(F),'bolge alani %.0f m2'%tm.area)
# srgb -> lineer vertex rengi
Cl=np.where(C<=.04045,C/12.92,((C+.055)/1.055)**2.4).astype(np.float32);Cl=np.c_[Cl,np.ones(len(Cl),np.float32)]
bins,views,acc=[],[],[]
def ekle(arr,ct,tip,hedef,mm=False):
    bb=arr.tobytes();views.append({"buffer":0,"byteOffset":sum(map(len,bins)),"byteLength":len(bb),"target":hedef})
    bins.append(bb+b"\0"*((4-len(bb)%4)%4));a={"bufferView":len(views)-1,"componentType":ct,"count":len(arr) if arr.ndim>1 else arr.size,"type":tip}
    if mm:a["min"],a["max"]=arr.min(0).tolist(),arr.max(0).tolist()
    acc.append(a);return len(acc)-1
p=ekle(V,5126,"VEC3",34962,True);n=ekle(Nn.astype(np.float32),5126,"VEC3",34962);t=ekle(U,5126,"VEC2",34962);c=ekle(Cl,5126,"VEC4",34962);i=ekle(F.ravel(),5125,"SCALAR",34963)
j={"asset":{"version":"2.0","generator":"araclar/bolge_doku/basamak3d.py"},"scene":0,"scenes":[{"nodes":[0]}],"nodes":[{"mesh":0,"name":"SM_Basamak"}],
 "meshes":[{"name":"SM_Basamak","primitives":[{"attributes":{"POSITION":p,"NORMAL":n,"TEXCOORD_0":t,"COLOR_0":c},"indices":i,"material":0}]}],
 "materials":[{"name":"Basamak","pbrMetallicRoughness":{"baseColorFactor":[1,1,1,1],"metallicFactor":0,"roughnessFactor":.8}}],
 "accessors":acc,"bufferViews":views,"buffers":[{"byteLength":sum(map(len,bins))}]}
js=json.dumps(j,separators=(",",":")).encode();js+=b" "*((4-len(js)%4)%4);bb=b"".join(bins)
open('SM_Basamak.glb','wb').write(struct.pack("<III",0x46546C67,2,28+len(js)+len(bb))+struct.pack("<I4s",len(js),b"JSON")+js+struct.pack("<I4s",len(bb),b"BIN\0")+bb)
