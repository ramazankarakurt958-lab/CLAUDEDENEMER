import numpy as np
exec(open('comps.py').read().split("cnt=np.bincount")[0].replace("fl=lab[PF[:,0]];np.save('flab.npy',fl)","fl=np.load('flab.npy')").replace("_,pid=np.unique","pass#").replace("e=np.vstack","#"))
UV,N=d['UV'],d['N']
def ray(sx,sy):
    x=(sx-512)/512/k;y=-(sy-512)/512/k;dv=f+x*rgt+y*up;return dv/np.linalg.norm(dv)
# blob centre(x,y), blob screen height, template comp, height of placement
jobs=[((163,454),56,3,30),((687,748),87,4,16),((982,800),58,2,2),((84,801),62,1,4),((17,814),57,2,6),((144,831),38,1,0),((1004,631),27,2,14),((949,700),39,1,8)]
rng=np.random.default_rng(3);NV=[V];NF=[F];NU=[UV];NN=[N];off=len(V)
for (sx,sy),h,tc,yh in jobs:
    fi=fl==tc;vid=np.unique(F[fi]);X=V[vid];ctr=(X.min(0)+X.max(0))/2
    dv=ray(sx,sy);t=(yh-c[1])/dv[1];P=c+t*dv
    a=rng.uniform(0,2*np.pi);R=np.array([[np.cos(a),0,np.sin(a)],[0,1,0],[-np.sin(a),0,np.cos(a)]])
    L=(X-ctr)@R.T
    def sh(s):p=proj(L*s+P);return p[:,1].max()-p[:,1].min()
    s=1.;
    for _ in range(4):s*=h/sh(s)
    Y=L*s+P;mp=-np.ones(len(V),np.int64);mp[vid]=np.arange(len(vid))+off
    NV.append(Y.astype(np.float32));NF.append(mp[F[fi]]);NU.append(UV[vid]);NN.append((N[vid]@R.T).astype(np.float32));off+=len(vid)
    print('added comp',tc,'at',P.round(1),'scale',round(s,2),'screen',proj(Y).mean(0).astype(int))
np.savez('clean2.npz',V=np.vstack(NV),UV=np.vstack(NU),N=np.vstack(NN),F=np.vstack(NF).astype(np.uint32))
