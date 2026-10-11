# Su tribunundeki kuleleri bulur: tribun seviyesinden belirgin yukselen yapilar (yukseklik haritasi).
import numpy as np,trimesh
from scipy import ndimage as nd
CX,CZ=-0.73,-0.36;H=0.5
def kule_haritasi(m):
    V=m.vertices;x0,z0=V[:,0].min(),V[:,2].min()
    ix=((V[:,0]-x0)/H).astype(int);iz=((V[:,2]-z0)/H).astype(int)
    hm=np.full((ix.max()+1,iz.max()+1),-np.inf);np.maximum.at(hm,(ix,iz),V[:,1])
    dolu=np.isfinite(hm);hf=np.where(dolu,hm,0)
    taban=nd.percentile_filter(np.where(dolu,hm,-50),25,size=17)     # ~8 m pencerede tribun seviyesi
    gx,gz=np.meshgrid(np.arange(hm.shape[0])*H+x0+H/2,np.arange(hm.shape[1])*H+z0+H/2,indexing='ij')
    ang=np.degrees(np.arctan2(gz-CZ,gx-CX));r=np.hypot(gx-CX,gz-CZ)
    kule=dolu&(hf-taban>2.5)&(hf>33)&(ang>-86)&(ang<30)&(r>22)
    kule=nd.binary_dilation(nd.binary_opening(kule,iterations=1),iterations=2)
    lab,n=nd.label(kule)
    def sor(p):
        i=int((p[0]-x0)/H);k=int((p[2]-z0)/H)
        if 0<=i<lab.shape[0] and 0<=k<lab.shape[1]: return lab[i,k]
        return 0
    return lab,n,sor
if __name__=='__main__':
    m=trimesh.load('game.glb',force='mesh');lab,n,sor=kule_haritasi(m)
    print('kule sayisi',n,[int((lab==i).sum()*H*H) for i in range(1,n+1)])
    c=m.triangles_center;fl=np.array([sor(p) for p in c])
    sec=np.load('akinti_yuz.npy')
    t=sec[(fl[sec]>0)&(c[sec,1]>24)]
    np.save('kule_yuz.npy',t);print('kule yuzu',len(t),'alan %.0f'%m.area_faces[t].sum())
    m.submesh([t],append=True).export('dbg.glb')
