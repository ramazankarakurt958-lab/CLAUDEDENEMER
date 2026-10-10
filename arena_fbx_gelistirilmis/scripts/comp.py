import numpy as np
from PIL import Image,ImageFilter
from scipy import ndimage as nd
S=4096;b=np.fromfile('dump/bake.rgba',np.uint8).reshape(S,S,4)
proj=b[...,:3].astype(np.float32);a=b[...,3].astype(np.float32)/255;cov=b[...,3]>0;w=np.clip((a-.004)/.996,0,1)
print('covered %.1f%%  projected %.1f%%'%(cov.mean()*100,(w>.3).mean()*100))
# dilate projected colour/weight into the gutters around UV islands
idx=nd.distance_transform_edt(~cov,return_distances=False,return_indices=True)
d=nd.distance_transform_edt(~cov);fill=(~cov)&(d<10)
proj[fill]=proj[idx[0][fill],idx[1][fill]];w[fill]=w[idx[0][fill],idx[1][fill]]
w=nd.gaussian_filter(w,2.0)
base=np.array(Image.open('t_basecolor.jpg').convert('RGB')).astype(np.float32)
hf=base-nd.gaussian_filter(base,(6,6,0))                # fine detail from the model texture
out=base*(1-w[...,None]*.92)+(proj+hf*.85)*(w[...,None]*.92)
Image.fromarray(np.clip(out,0,255).astype(np.uint8)).save('t_basecolor_proj.jpg',quality=93)
Image.fromarray((w*255).astype(np.uint8)).resize((1024,1024)).save('w_preview.png')
