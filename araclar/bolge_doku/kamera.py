import numpy as np, trimesh
az,el,dd,fov,tx,ty,tz,roll=[-0.02125,0.42704,215,28,-3.6486,34.9766,-0.8509,0.03068]
T=np.array([tx,ty,tz]);C=T+dd*np.array([np.sin(az)*np.cos(el),np.sin(el),np.cos(az)*np.cos(el)])
f=(C-T)/np.linalg.norm(C-T)            # camera +z (backwards)
x=np.cross([0,1,0],f);x/=np.linalg.norm(x);y=np.cross(f,x)
Rl=np.c_[x,y,f]
cr,sr=np.cos(roll),np.sin(roll);Rz=np.array([[cr,-sr,0],[sr,cr,0],[0,0,1]])
R=Rl@Rz;tf=np.tan(np.radians(fov)/2);N=2048
def isin(px,py):
    nx=px/N*2-1;ny=1-py/N*2
    d=R@np.array([nx*tf,ny*tf,-1.]);return C,d/np.linalg.norm(d)
def izdus(P):
    q=R.T@(np.asarray(P)-C);return np.array([(q[0]/-q[2]/tf+1)/2*N,(1-q[1]/-q[2]/tf)/2*N])
