# T_ArenaBolgeMaske: R=lav isimasi, G=parlaklik (buz/mermer), B=su isiltisi
import numpy as np
from PIL import Image
from scipy import ndimage as nd
S=4096;P=2048
pos=np.fromfile('dump/pos.f32',np.float32).reshape(P,P,4)
pc=pos[...,3]>0
idx=nd.distance_transform_edt(~pc,return_distances=False,return_indices=True);pos=pos[idx[0],idx[1]]
x,z=pos[...,0],pos[...,2]
K=4.0;sx=1/(1+np.exp(-x/K));sz=1/(1+np.exp(-z/K))
ates,su,toprak,hava=(1-sx)*(1-sz),sx*(1-sz),(1-sx)*sz,sx*sz
merkez=np.clip((np.hypot(x,z)-19)/4,0,1)
t=np.array(Image.open('T_ArenaBolge.jpg').convert('RGB').resize((P,P),Image.BILINEAR)).astype(np.float32)
r,g,b=t[...,0],t[...,1],t[...,2];mx=t.max(2);mn=t.min(2);sat=(mx-mn)/(mx+1)
lav=np.clip((r-80)/70,0,1)*np.clip((r-b-45)/50,0,1)*np.clip((sat-.4)/.25,0,1)
lav=np.clip(lav*np.clip(ates*3,0,1)*merkez,0,1)
lav=np.maximum(lav,nd.gaussian_filter(lav,3)*1.5).clip(0,1)   # biraz yayilsin (parilti hale)
mavi=np.clip((b-r-35)/50,0,1)*np.clip((mx-90)/80,0,1)
suy=np.clip(mavi*np.clip(su*3,0,1)*merkez,0,1)
lum=t.mean(2)
parlak=np.clip(su*.85+hava*.6,0,1)*merkez*np.clip((lum-40)/50,0,1)
parlak=np.maximum(parlak,suy)
m=np.dstack([lav,parlak,suy])
m=nd.gaussian_filter(m,(1,1,0))
Image.fromarray((m*255).clip(0,255).astype(np.uint8)).save('T_ArenaBolgeMaske.png',optimize=True)
print('lav %.2f%% parlak %.1f%% su %.2f%%'%((lav>.3).mean()*100,(parlak>.3).mean()*100,(suy>.3).mean()*100))
