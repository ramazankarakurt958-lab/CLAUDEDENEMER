import numpy as np
from PIL import Image,ImageFilter
P='fbx/floating_circular_arena_3d_model_';REF='/tmp/claude-0/-home-user-CLAUDEDENEMER/ed447e92-d2bc-5b0e-ac9a-394faff44f06/images/1.jpg'
S=4096
b=Image.open(P+'basecolor.JPEG').convert('RGB').resize((S,S),Image.LANCZOS)
a=np.array(b).astype(np.float32)
r=np.array(Image.open(REF).convert('RGB')).astype(np.float32);r=r[r.min(2)<225]
src=a.reshape(-1,3);v=src[src.sum(1)>15]
mx,mn=a.max(2),a.min(2);sat=(mx-mn)/(mx+1)
# water (cyan) and moss (green) keep their hue: weaker transfer there
cyan=(a[...,2]>a[...,0]+60)&(a[...,1]>a[...,0]+50)&(sat>.42)
moss=(a[...,1]>a[...,0]+8)&(a[...,1]>a[...,2]+8)
w=np.where(cyan|moss,.25,1.)[...,None]
w=np.array(Image.fromarray((w[...,0]*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6))).astype(np.float32)[...,None]/255
t=(a-v.mean(0))/v.std(0)*v.std(0).mean()*1.12+r.mean(0)
o=np.clip(a*(1-w)+t*w,0,255).astype(np.uint8)
bc=Image.fromarray(o).filter(ImageFilter.UnsharpMask(2,45,3))
bc.save('t_basecolor.jpg',quality=92)
n=Image.open(P+'normal.PNG').convert('RGB').resize((S,S),Image.LANCZOS)
na=np.array(n).astype(np.float32)/127.5-1;na[...,:2]*=1.1  # stronger surface relief
na/=np.linalg.norm(na,axis=2,keepdims=True)+1e-6
Image.fromarray(((na+1)*127.5).clip(0,255).astype(np.uint8)).save('t_normal.jpg',quality=95)
ro=np.array(Image.open(P+'roughness.JPEG').convert('L').resize((S,S),Image.LANCZOS)).astype(np.float32)/255
ro=.62+(ro-ro.min())/(ro.max()-ro.min())*.33          # stone 0.62..0.95
ro=np.where(cyan,.08,ro)                               # water stays glossy
ro=np.array(Image.fromarray((ro*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5)))
orm=np.dstack([np.full_like(ro,255),ro,np.zeros_like(ro)]).astype(np.uint8)
Image.fromarray(orm).save('t_orm.jpg',quality=92)
print('water px %',cyan.mean()*100,'moss %',moss.mean()*100,'new mean',o.reshape(-1,3)[o.sum(2).ravel()>15].mean(0))
