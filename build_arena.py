import trimesh,numpy as np
from trimesh.creation import cylinder,box,cone,annulus,icosphere
rng=np.random.default_rng(7)
T=trimesh.transformations
parts={k:[] for k in ['stone','dark','floor','water','moss','rock','metal']}
def add(k,m):parts[k].append(m)
def at(m,x,y,z,ry=0):
    m.apply_transform(T.rotation_matrix(ry,[0,1,0]));m.apply_translation([x,y,z]);return m
def Y(m):m.apply_transform(T.rotation_matrix(-np.pi/2,[1,0,0]));return m  # z-up -> y-up
def cyl(r,h,s=64):return Y(cylinder(r,h,sections=s))
def ann(r0,r1,h,s=96):return Y(annulus(r0,r1,h,sections=s))
def arcseg(r0,r1,y0,y1,a0,a1,n=48):
    # solid annular sector
    a=np.linspace(a0,a1,n+1);V=[]
    for r,y in [(r0,y0),(r1,y0),(r1,y1),(r0,y1)]:V.append(np.c_[r*np.cos(a),np.full_like(a,y),r*np.sin(a)])
    V=np.vstack(V);F=[];N=n+1
    for i in range(n):
        for k in range(4):
            p,q=k*N,((k+1)%4)*N
            F+= [[p+i,q+i,q+i+1],[p+i,q+i+1,p+i+1]]
    F+=[[0,N,2*N],[0,2*N,3*N],[n,3*N+n,2*N+n],[n,2*N+n,N+n]]
    m=trimesh.Trimesh(V,F);m.fix_normals();return m
def spikes(cx,cz,r,y,n,L):
    for _ in range(n):
        a=rng.uniform(0,2*np.pi);d=r*np.sqrt(rng.uniform(0,1));l=L*rng.uniform(.4,1)
        c=cone(rng.uniform(.6,1.6)*L/6,l,sections=7);c.apply_transform(T.rotation_matrix(np.pi/2,[1,0,0]))
        add('rock',at(c,cx+d*np.cos(a),y,cz+d*np.sin(a)))
# --- central arena
R=15
add('dark',at(cyl(R,2.2,128),0,-1.1,0))
add('floor',at(cyl(R-.6,.25,128),0,.12,0))
for r in [4,7.5,11,14]:add('stone',at(ann(r-.25,r,.35,128),0,.2,0))
star=[];
for i in range(8):
    b=box([.35,.3,7]);add('stone',at(b,3.7*np.cos(i*np.pi/4),.2,3.7*np.sin(i*np.pi/4),-i*np.pi/4+np.pi/2))
for i in range(16):
    a=i*np.pi/8;add('stone',at(cyl(.45,2.4,12),(R-.3)*np.cos(a),-.2,(R-.3)*np.sin(a)))
    add('stone',at(Y(cone(.5,1.2,12)),(R-.3)*np.cos(a),1,(R-.3)*np.sin(a)))
add('dark',at(Y(cone(R*.9,10,64)),0,-1.2,0).apply_transform(T.rotation_matrix(np.pi,[1,0,0])))
spikes(0,0,R*.85,-2,60,9)
# --- bridges
gaps=[0,np.pi/2,np.pi,3*np.pi/2]
for g in gaps:
    L=19;b=box([L,.8,4]);m=at(b,(R+L/2-.5)*np.cos(g),-.2,(R+L/2-.5)*np.sin(g),-g);add('stone',m)
    for s in [-1,1]:
        for t in np.linspace(R+1,R+L-1,8):
            px=t*np.cos(g)-s*1.8*np.sin(g);pz=t*np.sin(g)+s*1.8*np.cos(g)
            add('stone',at(box([.3,1,.3]),px,.7,pz,-g))
        rail=box([L,.25,.3]);add('stone',at(rail,(R+L/2-.5)*np.cos(g)-s*1.8*np.sin(g),1.3,(R+L/2-.5)*np.sin(g)+s*1.8*np.cos(g),-g))
# --- stands
R0,R1=31,48;gap=.11
for q in range(4):
    a0=gaps[q]+gap+np.pi/2*0;a1=gaps[q]+np.pi/2-gap
    add('dark',arcseg(R0,R1,-6,0,a0,a1,64))
    for k in range(10):  # tiers rising outward
        r=R0+3+k*1.2;add('stone',arcseg(r,R1-2,0,.7*(k+1),a0+.01,a1-.01,64))
    add('floor',arcseg(R0,R0+3,0,.3,a0,a1,64))
    add('stone',arcseg(R0-.6,R0,-1,1.4,a0,a1,64))        # inner parapet
    add('stone',arcseg(R1-2,R1,-6,10,a0,a1,64))          # outer wall
    add('stone',arcseg(R1-2.4,R1+.4,10,11,a0,a1,64))     # cornice
    # arches on outer & inner faces
    for a in np.linspace(a0+.03,a1-.03,14):
        for rr,yy,h in [(R1+.05,2,5),(R0-.65,-3.5,3.5)]:
            w=box([.25,h,1.6]);add('dark',at(w,rr*np.cos(a),yy,rr*np.sin(a),-a))
            c=cyl(.8,.25,16);c.apply_transform(T.rotation_matrix(np.pi/2,[0,0,1]));add('dark',at(c,rr*np.cos(a),yy+h/2,rr*np.sin(a),-a))
            p=box([.6,h+1.6,.5]);add('stone',at(p,(rr+.15)*np.cos(a+.035),yy+.2,(rr+.15)*np.sin(a+.035),-a))
    # stairs
    am=(a0+a1)/2
    for k in range(12):
        r=R0+3+k*1.05;add('floor',at(box([1.05,.55*(k+1),3]),r*np.cos(am),.275*(k+1),r*np.sin(am),-am))
    for a in np.linspace(a0+.08,a1-.08,7):
        add('moss',at(box([.2,4,1]),(R0-.75)*np.cos(a),-2.5,(R0-.75)*np.sin(a),-a))
    # towers with basins
    for i,a in enumerate(np.linspace(a0+.05,a1-.05,4)):
        r=R1+rng.uniform(-1,3);h=rng.uniform(13,22);x,z=r*np.cos(a),r*np.sin(a)
        add('stone',at(cyl(2.6,h,48),x,h/2-6,z))
        for yy in np.arange(-5,h-6,2.5):add('dark',at(ann(2.6,2.85,.3,48),x,yy,z))
        add('stone',at(cyl(4,.9,64),x,h-6,z));add('stone',at(ann(3.3,4.1,1.6,64),x,h-5.3,z))
        add('water',at(cyl(3.3,.2,64),x,h-5,z));add('metal',at(Y(cone(.35,2.5,16)),x,h-5,z))
        add('dark',at(Y(cone(2.6,6,24)).apply_transform(T.rotation_matrix(np.pi,[1,0,0])),x,-6,z))
        if q in (0,1): # spires on back stands
            add('dark',at(Y(cone(1.2,6,12)),x+2*np.cos(a+.3),h-6,z+2*np.sin(a+.3)))
    rc=(R0+R1)/2;spikes(rc*np.cos(am),rc*np.sin(am),11,-6,90,14)
# --- floating platforms & rocks
for i in range(12):
    a=(i//3)*np.pi/2+np.pi/4+rng.uniform(-.5,.5);r=rng.uniform(19,27);x,z=r*np.cos(a),r*np.sin(a);y=rng.uniform(2,8)
    add('stone',at(cyl(2.2,.6,40),x,y,z));add('water',at(cyl(1.7,.1,40),x,y+.32,z))
    add('dark',at(Y(cone(2,5,16)).apply_transform(T.rotation_matrix(np.pi,[1,0,0])),x,y-.3,z))
for i in range(28):
    a=rng.uniform(0,2*np.pi);r=rng.uniform(52,68);s=rng.uniform(1.5,4.5)
    m=icosphere(2,s);m.vertices*=1+.35*rng.standard_normal(m.vertices.shape)*.3
    m.vertices[:,1]*=np.where(m.vertices[:,1]<0,2.2,.6);add('rock',at(m,r*np.cos(a),rng.uniform(-15,8),r*np.sin(a)))
    add('moss',at(cyl(s*.9,.3,16),r*np.cos(a),m.bounds[1,1],r*np.sin(a)))
mats={'stone':[.55,.53,.49],'dark':[.32,.31,.30],'floor':[.62,.56,.46],'water':[.35,.75,.78],'moss':[.25,.42,.2],'rock':[.27,.28,.25],'metal':[.3,.55,.55]}
sc=trimesh.Scene()
for k,ms in parts.items():
    m=trimesh.util.concatenate(ms)
    # subtle per-vertex stone variation
    c=np.clip(np.array(mats[k])*(1+.08*rng.standard_normal((len(m.vertices),1))),0,1)
    m.visual=trimesh.visual.ColorVisuals(m,vertex_colors=(np.c_[c,np.ones(len(c))]*255).astype(np.uint8))
    m=trimesh.Trimesh(m.vertices,m.faces,vertex_colors=m.visual.vertex_colors,process=False)
    sc.add_geometry(m,node_name=k,geom_name=k)
sc.export('arena_v2.glb');print(sum(len(g.faces) for g in sc.geometry.values()),sc.bounds)
