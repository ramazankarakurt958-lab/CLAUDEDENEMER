# Hacimli selaleler: Govde (yuvarlak kesitli su kutlesi), Serpinti (asagi indikce genisleyen kopuk kabugu), Sis (dipte bulut kumeleri).
# Arena glTF eksenlerinde (Y yukari, metre) tek GLB, 3 malzeme yuvasi.
import json,struct,sys
import numpy as np,trimesh
from kamera import *
m=trimesh.load('game.glb',force='mesh')
rng=np.random.default_rng(11)
def vur(o,d):
    h,_,fi=m.ray.intersects_location([o],[d],multiple_hits=False)
    return h[0] if len(h) else None
# ad: (ust x, ust y, genislik px, alt y) -- 2048'lik referans karesinde
SELALELER={'A':(1635,1035,50,1235),'B':(1688,1050,26,1185),'C':(1742,1050,45,1175),
 'D1':(1322,676,22,742),'D2':(1403,702,14,762),'D3':(1578,778,24,862),'D4':(1647,822,15,902),'E':(1802,1200,18,1300)}
NR,NV=16,56
def merkez_hatti(px,py,gpx,alt):
    for k in range(0,40,2):
        P=vur(*isin(px,py+k))
        if P is not None: break
    if P is None: return None
    mpp=2*np.linalg.norm(P-C)*tf/N;gen=gpx*mpp
    dis=(C-P)*np.array([1,0,1]);dis/=np.linalg.norm(dis)
    yan=np.cross([0,1,0],dis);yan/=np.linalg.norm(yan)
    t=0
    while izdus(P-[0,t,0])[1]<alt and t<60: t+=.1
    boy=t*1.35+1.5
    vs=np.linspace(0,1,NV);s=-.3;cs=[];ss=[]
    for v in vs:
        h=v*boy;Y=P[1]+.1-h;duv=-5
        for u in (-.5,-.25,0,.25,.5):            # genislik boyunca duvara en yakin nokta
            Q=P+yan*u*gen;o=np.array([Q[0],Y,Q[2]])+dis*3.5
            W=vur(o,-dis)
            if W is not None and np.linalg.norm(W-o)<6: duv=max(duv,3.5-np.linalg.norm(W-o))
        s=max(s,duv)
        ss.append(s)
    return P,gen,boy,dis,yan,vs,np.array(ss)
def tup(P,gen,boy,dis,yan,vs,ss,olcek,kalin,acilma,puruz):
    """Yuvarlak kesitli tup: on taraf bombeli, arka taraf duvara dogru basik."""
    V=[];U0=[];U1=[];a0=gen/2
    for j,v in enumerate(vs):
        h=v*boy
        a=a0*olcek*(1+acilma*v)                              # yari genislik (asagida acilir)
        bon=a*kalin;bark=a*kalin*.45                        # on/arka derinlik
        atis=.8*np.sqrt(min(h,4)/4)
        c=np.array([P[0],P[1]+.1-h,P[2]])+dis*(ss[j]+bark+.25+atis)
        for i in range(NR+1):
            th=2*np.pi*i/NR+np.pi                # dikis arkada kalsin
            x=np.sin(th)*a;z=np.cos(th)
            z=z*bon if z>0 else z*bark
            r=1+puruz*(rng.random()-.5)*(.3+v)
            V.append(c+yan*x*r+dis*z*r);U0.append([i/NR,v]);U1.append([i/NR*2*a*olcek*2,h])
    F=[]
    for j in range(NV-1):
        for i in range(NR):
            a_=j*(NR+1)+i;F+=[[a_,a_+NR+1,a_+1],[a_+1,a_+NR+1,a_+NR+2]]
    return np.array(V),np.array(U0),np.array(U1),np.array(F)
def puf(c,r):
    s=trimesh.creation.icosphere(2,1.0);v=s.vertices.copy()
    v*=1+.25*np.sin(v@rng.normal(size=(3,))*2.5)[:,None]           # yumru
    v*=np.array([1,.65,1]);v=v*r+c
    return v,np.tile([.5,.3],(len(v),1)),v[:,[0,1]]*.2,s.faces
parcalar={'Govde':[],'Serpinti':[],'Sis':[]};bilgi={}
for ad,(px,py,g,alt) in SELALELER.items():
    r=merkez_hatti(px,py,g,alt)
    if r is None: print(ad,'yok');continue
    P,gen,boy,dis,yan,vs,ss=r
    parcalar['Govde'].append(tup(P,gen,boy,dis,yan,vs,ss,1.0,.55,.3,.04))
    parcalar['Serpinti'].append(tup(P,gen,boy,dis,yan,vs,ss,1.18,.8,.9,.18))
    # dipte sis kumesi (selalenin gozden kayboldugu yerde) + tepede kucuk serpinti
    dip=np.array([P[0],P[1]+.1-boy*.7,P[2]])+dis*(ss[int(NV*.62)]+gen*.4+.8)
    for k in range(14 if gen>1.5 else 0):            # sadece buyuk selalelerin dibinde
        rr=gen*rng.uniform(.6,1.4)+.8
        o=dip+yan*rng.uniform(-1,1)*gen*.9+dis*rng.uniform(-.2,1)*gen*.5+np.array([0,rng.uniform(-1,1.5),0])
        parcalar['Sis'].append(puf(o,rr))
    bilgi[ad]=dict(tepe=P.round(2).tolist(),genislik=round(gen,2),boy=round(boy,2))
    print(ad,'genislik %.1f boy %.1f'%(gen,boy))
json.dump(bilgi,open('selale_bilgi.json','w'),indent=1)
bins,views,acc,prims,mats=[],[],[],[],[]
def ekle(arr,ct,tip,hedef,mm=False):
    b=arr.tobytes();views.append({"buffer":0,"byteOffset":sum(map(len,bins)),"byteLength":len(b),"target":hedef})
    bins.append(b+b"\0"*((4-len(b)%4)%4));a={"bufferView":len(views)-1,"componentType":ct,"count":len(arr) if arr.ndim>1 else arr.size,"type":tip}
    if mm:a["min"],a["max"]=arr.min(0).tolist(),arr.max(0).tolist()
    acc.append(a);return len(acc)-1
for k,(ad,lst) in enumerate(parcalar.items()):
    Vs,U0,U1,Fs=[],[],[],[];b=0
    for V,u0,u1,F in lst: Vs.append(V);U0.append(u0);U1.append(u1);Fs.append(F+b);b+=len(V)
    V=np.concatenate(Vs).astype(np.float32);F=np.concatenate(Fs).astype(np.uint32)
    tm=trimesh.Trimesh(V,F,process=False);Nn=tm.vertex_normals.astype(np.float32)
    p=ekle(V,5126,"VEC3",34962,True);n=ekle(Nn,5126,"VEC3",34962)
    t0=ekle(np.concatenate(U0).astype(np.float32),5126,"VEC2",34962);t1=ekle(np.concatenate(U1).astype(np.float32),5126,"VEC2",34962)
    i=ekle(F.ravel(),5125,"SCALAR",34963)
    prims.append({"attributes":{"POSITION":p,"NORMAL":n,"TEXCOORD_0":t0,"TEXCOORD_1":t1},"indices":i,"material":k})
    mats.append({"name":ad,"pbrMetallicRoughness":{"baseColorFactor":[.7,.9,1,1],"metallicFactor":0,"roughnessFactor":.1},"doubleSided":True})
    print(ad,len(V),'kose',len(F),'ucgen')
j={"asset":{"version":"2.0","generator":"araclar/bolge_doku/selale2.py"},"scene":0,"scenes":[{"nodes":[0]}],"nodes":[{"mesh":0,"name":"SM_Selale"}],
 "meshes":[{"name":"SM_Selale","primitives":prims}],"materials":mats,"accessors":acc,"bufferViews":views,"buffers":[{"byteLength":sum(map(len,bins))}]}
js=json.dumps(j,separators=(",",":")).encode();js+=b" "*((4-len(js)%4)%4);bb=b"".join(bins)
open('SM_Selale.glb','wb').write(struct.pack("<III",0x46546C67,2,28+len(js)+len(bb))+struct.pack("<I4s",len(js),b"JSON")+js+struct.pack("<I4s",len(bb),b"BIN\0")+bb)
