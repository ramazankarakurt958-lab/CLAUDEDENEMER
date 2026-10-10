import numpy as np,scipy.sparse as sp,scipy.sparse.csgraph as cg
P=np.fromfile('dump/position',np.float32).reshape(-1,3);N=np.fromfile('dump/normal',np.float32).reshape(-1,3);U=np.fromfile('dump/uv',np.float32).reshape(-1,2)
key=np.c_[np.round(P/2e-6),np.round(U/1e-5),np.round(N*500)].astype(np.int64)
_,first,inv=np.unique(key,axis=0,return_index=True,return_inverse=True);inv=inv.ravel()
V,UV,NN=P[first],U[first],N[first];F=inv.reshape(-1,3)
_,pid=np.unique(np.round(V/2e-6).astype(np.int64),axis=0,return_inverse=True);pid=pid.ravel();PF=pid[F]
ok=(PF[:,0]!=PF[:,1])&(PF[:,1]!=PF[:,2])&(PF[:,0]!=PF[:,2])
ar=np.linalg.norm(np.cross(V[F[:,1]]-V[F[:,0]],V[F[:,2]]-V[F[:,0]]),axis=1);ok&=ar>1e-14
_,ui=np.unique(np.sort(PF,1),axis=0,return_index=True);u=np.zeros(len(F),bool);u[ui]=True;ok&=u
print('degenerate/duplicate removed',(~ok).sum())
F,PF=F[ok],PF[ok];n=pid.max()+1;e=np.vstack([PF[:,[0,1]],PF[:,[1,2]]])
_,lab=cg.connected_components(sp.coo_matrix((np.ones(len(e)),(e[:,0],e[:,1])),shape=(n,n)),directed=False)
fl=lab[PF[:,0]];cnt=np.bincount(fl);c=V[F].mean(1)
mn=np.full((len(cnt),3),9.);mx=np.full((len(cnt),3),-9.);np.minimum.at(mn,fl,c);np.maximum.at(mx,fl,c);ext=np.linalg.norm(mx-mn,axis=1)
bad=(cnt<20)|(ext<0.002);keep=~bad[fl];print('debris pieces',bad.sum(),'faces',(~keep).sum())
F=F[keep];used=np.unique(F);rm=-np.ones(len(V),np.int64);rm[used]=np.arange(len(used))
V,UV,NN,F=V[used],UV[used],NN[used],rm[F]
# scale: ~100 m wide, centred, base on y=0
V=V-[(V[:,0].max()+V[:,0].min())/2,V[:,1].min(),(V[:,2].max()+V[:,2].min())/2];s=100/(V[:,[0,2]].max()-V[:,[0,2]].min());V*=s
np.savez('clean.npz',V=V.astype(np.float32),UV=UV,N=NN,F=F.astype(np.uint32))
print('verts',len(V),'tris',len(F),'size',V.max(0)-V.min(0))
