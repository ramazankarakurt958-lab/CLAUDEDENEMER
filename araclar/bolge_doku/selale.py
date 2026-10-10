# Referanstaki selaleleri arena modelinin uzerinde 3D perde olarak uretir (arena glTF koordinatlarinda, Y yukari, metre).
import json,struct,sys
import numpy as np,trimesh
from kamera import *
m=trimesh.load('game.glb',force='mesh')
def vur(o,d):
    h,_,fi=m.ray.intersects_location([o],[d],multiple_hits=False)
    return (h[0],m.face_normals[fi[0]]) if len(h) else (None,None)
# ad: (ust x, ust y, genislik px, alt y)  -- 2048'lik referans karesinde
SELALELER={'A':(1635,1035,50,1235),'B':(1688,1050,26,1185),'C':(1742,1050,45,1175),
 'D1':(1322,676,22,742),'D2':(1403,702,14,762),'D3':(1578,778,24,862),'D4':(1647,822,15,902),'E':(1802,1200,18,1300)}
def selale(px,py,gpx,alt):
    # tepe noktasi: bulunamazsa biraz asagida ara
    for k in range(0,40,2):
        P,n=vur(*isin(px,py+k))
        if P is not None: break
    if P is None: return None
    dist=np.linalg.norm(P-C);mpp=2*dist*tf/N
    gen=gpx*mpp
    dis=(C-P)*np.array([1,0,1]);dis/=np.linalg.norm(dis)          # disari = kameraya bakan yatay yon
    yan=np.cross([0,1,0],dis);yan/=np.linalg.norm(yan)
    # dusme boyu: P'den asagi inen dogrunun goruntude 'alt' y'sine ulastigi yer
    t=0
    while izdus(P-[0,t,0])[1]<alt and t<60: t+=.1
    boy=t*1.35+1.5                                                # alt kisim bulutlara/sise karisarak kaybolur
    nu,nv=9,48
    us=np.linspace(-.5,.5,nu);vs=np.linspace(0,1,nv)
    V=np.zeros((nu,nv,3))
    for i,u in enumerate(us):
        s=-.25; prev=-1e9
        for j,v in enumerate(vs):
            h=v*boy
            Y=P[1]+.15-h
            # duvari disaridan tara
            Q=P+yan*u*gen; o=np.array([Q[0],Y,Q[2]])+dis*3.5
            W,_=vur(o,-dis)                                # sadece 3.5 m'lik pencerede duvar ara (ondeki baska yapilari sayma)
            duvar=(3.5-np.linalg.norm(W-o)) if W is not None and np.linalg.norm(W-o)<6 else -5
            s=max(s,duvar+.35, prev)                     # suyun disari dogru akisi: duvardan uzak, geri cekilmez
            atis=.9*np.sqrt(min(h,4)/4)                    # ilk 4 m'de kenardan disari firlama
            sw=1+.25*v                                     # asagida biraz genisler
            V[i,j]=np.array([Q[0],Y,Q[2]])+yan*u*gen*(sw-1)+dis*(s+atis)
            prev=s
    # kenarda hafif kavis (perde disa bombeli)
    V+=dis*(0.12*gen*(1-(2*us[:,None])**2))[...,None]
    uv0=np.stack(np.meshgrid(us+.5,vs,indexing='ij'),-1)
    uv1=np.stack(np.meshgrid((us+.5)*gen,vs*boy,indexing='ij'),-1)
    return V.reshape(-1,3),uv0.reshape(-1,2),uv1.reshape(-1,2),nu,nv,gen,boy,P
Vs=[];U0=[];U1=[];F=[];bilgi={}
for ad,(px,py,g,alt) in SELALELER.items():
    r=selale(px,py,g,alt)
    if r is None: print(ad,'bulunamadi');continue
    V,u0,u1,nu,nv,gen,boy,P=r;b=sum(len(v) for v in Vs)
    for i in range(nu-1):
        for j in range(nv-1):
            a=b+i*nv+j;F+=[[a,a+1,a+nv],[a+1,a+nv+1,a+nv]]
    Vs.append(V);U0.append(u0);U1.append(u1);bilgi[ad]=dict(tepe=P.round(2).tolist(),genislik=round(gen,2),boy=round(boy,2))
    print(ad,'tepe',P.round(1),'genislik %.1f m boy %.1f m'%(gen,boy))
V=np.concatenate(Vs).astype(np.float32);UV0=np.concatenate(U0).astype(np.float32);UV1=np.concatenate(U1).astype(np.float32);F=np.array(F,np.uint32)
tm=trimesh.Trimesh(V,F,process=False);N_=tm.vertex_normals.astype(np.float32)
json.dump(bilgi,open('selale_bilgi.json','w'),indent=1)
# GLB (arena ile ayni eksenler: Y yukari, metre)
bins,views,acc=[],[],[]
def ekle(arr,ct,tip,hedef,mm=False):
    b=arr.tobytes();views.append({"buffer":0,"byteOffset":sum(map(len,bins)),"byteLength":len(b),"target":hedef})
    bins.append(b+b"\0"*((4-len(b)%4)%4));a={"bufferView":len(views)-1,"componentType":ct,"count":len(arr) if arr.ndim>1 else arr.size,"type":tip}
    if mm:a["min"],a["max"]=arr.min(0).tolist(),arr.max(0).tolist()
    acc.append(a);return len(acc)-1
p=ekle(V,5126,"VEC3",34962,True);n=ekle(N_,5126,"VEC3",34962);t0=ekle(UV0,5126,"VEC2",34962);t1=ekle(UV1,5126,"VEC2",34962);i=ekle(F.ravel(),5125,"SCALAR",34963)
j={"asset":{"version":"2.0","generator":"araclar/bolge_doku/selale.py"},"scene":0,"scenes":[{"nodes":[0]}],"nodes":[{"mesh":0,"name":"SM_Selale"}],
 "meshes":[{"name":"SM_Selale","primitives":[{"attributes":{"POSITION":p,"NORMAL":n,"TEXCOORD_0":t0,"TEXCOORD_1":t1},"indices":i,"material":0}]}],
 "materials":[{"name":"Selale","pbrMetallicRoughness":{"baseColorFactor":[.7,.9,1,1],"metallicFactor":0,"roughnessFactor":.1},"doubleSided":True}],
 "accessors":acc,"bufferViews":views,"buffers":[{"byteLength":sum(map(len,bins))}]}
js=json.dumps(j,separators=(",",":")).encode();js+=b" "*((4-len(js)%4)%4);bb=b"".join(bins)
open(sys.argv[1] if len(sys.argv)>1 else 'SM_Selale.glb','wb').write(struct.pack("<III",0x46546C67,2,28+len(js)+len(bb))+struct.pack("<I4s",len(js),b"JSON")+js+struct.pack("<I4s",len(bb),b"BIN\0")+bb)
print(len(V),'kose',len(F),'ucgen')
