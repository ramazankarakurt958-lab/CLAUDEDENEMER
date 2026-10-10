import numpy as np,json,scipy.sparse as sp,scipy.sparse.csgraph as cg
d=np.load('clean.npz');V,F=d['V'],d['F'].astype(np.int64)
_,pid=np.unique(np.round(V/1e-4).astype(np.int64),axis=0,return_inverse=True);pid=pid.ravel();PF=pid[F];n=pid.max()+1
e=np.vstack([PF[:,[0,1]],PF[:,[1,2]]]);_,lab=cg.connected_components(sp.coo_matrix((np.ones(len(e)),(e[:,0],e[:,1])),shape=(n,n)),directed=False)
fl=lab[PF[:,0]];np.save('flab.npy',fl)
az,el,dd,fov,tx,ty,tz,roll=json.load(open('cam.json'))
def camera():
    t=np.array([tx,ty,tz]);c=t+dd*np.array([np.sin(az)*np.cos(el),np.sin(el),np.cos(az)*np.cos(el)])
    f=(t-c)/np.linalg.norm(t-c);rgt=np.cross(f,[0,1,0]);rgt/=np.linalg.norm(rgt);up=np.cross(rgt,f)
    cr,sr=np.cos(roll),np.sin(roll);rgt,up=cr*rgt+sr*up,-sr*rgt+cr*up
    return c,f,rgt,up
c,f,rgt,up=camera();k=1/np.tan(np.radians(fov)/2)
def proj(X):
    v=X-c;z=v@f;return np.c_[512+512*k*(v@rgt)/z,512-512*k*(v@up)/z]
cnt=np.bincount(fl)
for i in np.argsort(-cnt)[:60]:
    fi=fl==i;X=V[F[fi]].reshape(-1,3);mn,mx=X.min(0),X.max(0);s=proj(((mn+mx)/2)[None])[0]
    if cnt[i]<300000:print(i,cnt[i],'screen',s.astype(int),'size',(mx-mn).round(1),'ctr',((mn+mx)/2).round(1))
