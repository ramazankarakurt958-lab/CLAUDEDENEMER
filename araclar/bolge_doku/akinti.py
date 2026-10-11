# Su tribunu kulelerinin sahadan gorunen yuzlerinde 3D akis:
#  - Akinti: duvari kaplayan dalgali ince su tabakasi (kenarlarda incelir)
#  - dereler: kule tepelerinden baslayip duvari takip eden, cikintidan dokulen, asagida carpip devam eden yuvarlak kesitli akintilar
#  - carptigi yerlerde kucuk sis/sicrama
import numpy as np,trimesh
from scipy.sparse.csgraph import dijkstra
from scipy.sparse import coo_matrix
CX,CZ=-0.73,-0.36
rng=np.random.default_rng(5)

def gurultu3(p,olc):
    """Basit 3B deger gurultusu (0..1), olc: eksen olcekleri."""
    q=p*np.asarray(olc);i=np.floor(q).astype(np.int64);f=q-i;f=f*f*(3-2*f)
    def h(ix,iy,iz):
        v=(ix*73856093)^(iy*19349663)^(iz*83492791);v=(v*2654435761)&0xffffffff
        return (v%10007)/10007.0
    o=0
    for dx in (0,1):
        for dy in (0,1):
            for dz in (0,1):
                w=(f[:,0] if dx else 1-f[:,0])*(f[:,1] if dy else 1-f[:,1])*(f[:,2] if dz else 1-f[:,2])
                o=o+w*h(i[:,0]+dx,i[:,1]+dy,i[:,2]+dz)
    return o

def disari(p):
    v=np.array([CX-p[0],0,CZ-p[2]]);return v/(np.linalg.norm(v)+1e-9)

def tabaka(m,sec):
    s=m.submesh([sec],append=True);s.merge_vertices();V=s.vertices.copy();F=s.faces;Nv=s.vertex_normals
    # sinira uzaklik (kenarlarda su incelsin)
    e=s.edges_unique;L=s.edges_unique_length
    G=coo_matrix((np.r_[L,L],(np.r_[e[:,0],e[:,1]],np.r_[e[:,1],e[:,0]])),shape=(len(V),len(V))).tocsr()
    sinir=np.unique(trimesh.grouping.group_rows(s.edges_sorted,require_count=1))
    sv=np.unique(s.edges_sorted[sinir].ravel())
    d=dijkstra(G,indices=sv,min_only=True,limit=2.0);d=np.where(np.isinf(d),2.0,d)
    k=np.clip(d/0.7,0,1)
    g=gurultu3(V,(1.2,.25,1.2))*.7+gurultu3(V,(3,.8,3))*.3
    off=(.03+.13*g)*k+.02
    V2=V+Nv*off[:,None]
    up=np.array([0,1,0.]);t=np.cross(up,Nv);tn=np.linalg.norm(t,axis=1);t=np.where(tn[:,None]>1e-3,t/np.maximum(tn,1e-6)[:,None],[1,0,0])
    U1=np.c_[(V*t).sum(1),-V[:,1]]
    U0=np.c_[np.full(len(V),.5),1-.45*k]
    print('tabaka',len(V),'kose',len(F),'ucgen')
    return V2,U0,U1,F

def yol_izle(m,p,n,kulede=lambda p:True):
    """Bir derenin yolunu yercekimiyle izler. Donus: noktalar, durumlar ('d' duvar,'c' cikinti,'u' dusus), dis yonler, carpma noktalari"""
    def vur(o,dr,mx):
        h,_,fi=m.ray.intersects_location([o],[dr],multiple_hits=False)
        if len(h) and np.linalg.norm(h[0]-o)<=mx: return h[0],m.face_normals[fi[0]]
        return None,None
    P=[p.copy()];D=['d'];NN=[n.copy()];carp=[];durum='d';adim=.3;toplam=0;cik=0
    while toplam<45 and p[1]>14:
        if np.hypot(p[0]-CX,p[2]-CZ)<21: break          # sahaya/koprulere tasma
        if cik>10: break                                   # duz zeminde birikti (havuz)
        if durum=='d':
            q=p+[0,-adim,0];o=q+n*.6
            h,fn=vur(o,-n,1.3)
            if h is None: durum='u';continue
            if fn[1]>.65: durum='c'
            elif abs(fn[1])<.8:
                nh=np.array([fn[0],0,fn[2]]);
                if np.linalg.norm(nh)>.2: n=nh/np.linalg.norm(nh)
            p=h
        elif durum=='c':
            cik+=1
            n=disari(p) if np.dot(disari(p),n)<.2 else n
            q=p+n*adim
            h,fn=vur(q+[0,.4,0],np.array([0,-1.,0]),.9)
            if h is None: durum='u';p=q;continue
            p=h
            if fn[1]<.5: durum='d';cik=0
        else:
            o=p+n*.15;h,fn=vur(o,np.array([0,-1.,0]),30)
            son=h[1] if h is not None else p[1]-6
            for yy in np.arange(p[1]-adim,son,-adim*2):
                P.append(np.array([o[0],yy,o[2]]));D.append('u');NN.append(n.copy());toplam+=adim*2
            if h is None: break
            if p[1]-h[1]>1.5: carp.append(h.copy())
            if not kulede(h): P.append(h.copy());D.append('u');NN.append(n.copy());break   # tribune dustu: burada biter
            p=h;durum='c' if fn[1]>.65 else 'd'
            if durum=='d' and abs(fn[1])<.8:
                nh=np.array([fn[0],0,fn[2]])
                if np.linalg.norm(nh)>.2:n=nh/np.linalg.norm(nh)
        if durum!='u' and not kulede(p): break                # kulenin disina cikti
        P.append(p.copy());D.append(durum);NN.append(n.copy());toplam+=adim
    return np.array(P),D,np.array(NN),carp

def tup_yol(P,D,NN,gen,NR=8):
    # yumusat
    if len(P)<6: return None
    K=np.ones(5)/5;Ps=np.c_[[np.convolve(np.pad(P[:,i],2,mode='edge'),K,'valid') for i in range(3)]].T
    Ns=np.c_[[np.convolve(np.pad(NN[:,i],2,mode='edge'),K,'valid') for i in range(3)]].T;Ns/=np.linalg.norm(Ns,axis=1)[:,None]+1e-9
    s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(Ps,axis=0),axis=1))];Ltop=s[-1]
    V=[];U0=[];U1=[];kab=[]
    for j in range(len(Ps)):
        T=Ps[min(j+1,len(Ps)-1)]-Ps[max(j-1,0)];T/=np.linalg.norm(T)+1e-9
        nd=Ns[j]-T*np.dot(Ns[j],T);nd/=np.linalg.norm(nd)+1e-9;yan=np.cross(T,nd)
        dus=D[j]=='u'
        w=gen*(1+.25*np.sin(s[j]*1.7+gen*9))*(1.25 if dus else 1)/2
        on=w*(.75 if dus else .35);ark=w*(.75 if dus else .12)
        c=Ps[j]+nd*((0 if dus else ark+.06))
        v=s[j]/Ltop*.55 if s[j]<Ltop-2 else .55+.45*(s[j]-(Ltop-2))/2
        for i in range(NR+1):
            th=2*np.pi*i/NR+np.pi;x=np.sin(th)*w;z=np.cos(th);z=z*on if z>0 else z*ark
            V.append(c+yan*x+nd*z);U0.append([i/NR,v]);U1.append([i/NR*2*w*2,s[j]])
        kab.append(dus)
    F=[]
    for j in range(len(Ps)-1):
        for i in range(NR):
            a=j*(NR+1)+i;F+=[[a,a+NR+1,a+1],[a+1,a+NR+1,a+NR+2]]
    return np.array(V),np.array(U0),np.array(U1),np.array(F),Ps,np.array(kab)

def ekle(parcalar,m,puf):
    import kule
    _,_,sor=kule.kule_haritasi(m);kulede=lambda p:sor(p)>0
    sec=np.load('kule_yuz.npy')
    parcalar.setdefault('Akinti',[]).append(tabaka(m,sec))
    # baslangiclar: her parcanin tepe kenarindan
    s=m.submesh([sec],append=True);s.merge_vertices()
    cc=trimesh.graph.connected_components(s.face_adjacency,nodes=np.arange(len(s.faces)),min_len=1)
    bas=[]
    for comp in cc:
        vi=np.unique(s.faces[comp]);vv=s.vertices[vi];nv=s.vertex_normals[vi]
        ust=vv[:,1]>vv[:,1].max()-.6;cand=np.where(ust)[0];rng.shuffle(cand)
        alinan=[]
        for c in cand:
            if all(np.linalg.norm(vv[c]-a)>1.4 for a in alinan): alinan.append(vv[c]);bas.append((vv[c],nv[c]))
    print('dere baslangici',len(bas))
    nd=0;nc=0
    for p,n in bas:
        nh=np.array([n[0],0,n[2]])
        if np.linalg.norm(nh)<.3: nh=disari(p)
        nh/=np.linalg.norm(nh)
        P,D,NN,carp=yol_izle(m,p+nh*.05,nh,kulede)
        gen=rng.uniform(.25,.8)
        r=tup_yol(P,D,NN,gen)
        if r is None: continue
        V,U0,U1,F,Ps,kab=r;parcalar['Govde'].append((V,U0,U1,F));nd+=1
        if kab.sum()>6:   # dusen kisimlara serpinti kabugu
            r2=tup_yol(P,D,NN,gen*1.5);parcalar['Serpinti'].append(r2[:4])
        for h in carp[:3]:
            parcalar['Sis'].append(puf(h+[0,.3,0]+disari(h)*.4,gen*.9+.3));nc+=1
    print('dere',nd,'carpma sisi',nc)
