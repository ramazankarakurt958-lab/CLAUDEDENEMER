# Su tribunu kulelerinin sahadan gorunen yuzleri -> akinti_yuz.npy
import numpy as np,trimesh
m=trimesh.load('game.glb',force='mesh')
c=m.triangles_center;n=m.face_normals;a=m.area_faces
CX,CZ=-0.73,-0.36
dx,dz=c[:,0]-CX,c[:,2]-CZ;r=np.hypot(dx,dz);ang=np.degrees(np.arctan2(dz,dx))
nh=n[:,[0,2]];icer=-np.c_[dx,dz]/(r[:,None]+1e-6)
bakis=(nh*icer).sum(1)/(np.linalg.norm(nh,axis=1)+1e-6)
aday=(ang>-86)&(ang<30)&(r>20)&(np.abs(n[:,1])<.6)&(bakis>.1)&(c[:,1]>22)
idx=np.where(aday)[0];gor=np.zeros(len(idx),bool)
for px in (-8,0,8):
    for pz in (-8,0,8):
        for yy in (24.8,31.):
            g=np.array([CX+px,yy,CZ+pz]);d=c[idx]-g;d/=np.linalg.norm(d,axis=1)[:,None]
            _,ri,fi=m.ray.intersects_location(np.repeat(g[None],len(idx),0),d,multiple_hits=False)
            v=np.full(len(idx),-1);v[ri]=fi;gor|=(v==idx)
sec=idx[gor]
# bagli parcalar: dikey boyu kisa olanlar (basamak alinliklari, kucuk suslar) atilir
sub=m.submesh([sec],append=True,only_watertight=False)
cc=trimesh.graph.connected_components(sub.face_adjacency,nodes=np.arange(len(sub.faces)),min_len=1)
tut=np.zeros(len(sec),bool)
for comp in cc:
    ys=sub.vertices[sub.faces[comp]][...,1]
    if ys.max()-ys.min()>2.5 and a[sec[comp]].sum()>1.0: tut[comp]=True
sec=sec[tut]
print('secilen yuz',len(sec),'alan %.0f m2'%a[sec].sum(),'parca',sum(1 for comp in cc if tut[comp].all()))
np.save('akinti_yuz.npy',sec)
m.submesh([sec],append=True).export('dbg.glb')
