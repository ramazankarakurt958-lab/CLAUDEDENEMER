import json,struct,sys
src,img,dst=sys.argv[1:4]
f=open(src,'rb').read()
n=struct.unpack('<I',f[12:16])[0];j=json.loads(f[20:20+n]);bl=struct.unpack('<I',f[20+n:24+n])[0];binb=bytearray(f[28+n:28+n+bl])
new=open(img,'rb').read()
bv=j['bufferViews'][j['images'][0]['bufferView']]
# append new image at end, point bufferView there
off=len(binb);binb+=new;binb+=b'\0'*((4-len(binb)%4)%4)
bv['byteOffset']=off;bv['byteLength']=len(new);j['buffers'][0]['byteLength']=len(binb)
js=json.dumps(j).encode();js+=b' '*((4-len(js)%4)%4)
out=struct.pack('<III',0x46546C67,2,12+8+len(js)+8+len(binb))+struct.pack('<II',len(js),0x4E4F534A)+js+struct.pack('<II',len(binb),0x004E4942)+bytes(binb)
open(dst,'wb').write(out)
