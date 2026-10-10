import numpy as np,json,struct,sys
def write(path,V,N,UV,F,tex):
    bins=[];views=[];acc=[]
    def add(arr,target=None):
        b=arr.tobytes();off=sum(len(x) for x in bins);bins.append(b+b'\0'*((4-len(b)%4)%4))
        v={'buffer':0,'byteOffset':off,'byteLength':len(b)}
        if target:v['target']=target
        views.append(v);return len(views)-1
    def A(arr,ct,typ,target,mm=False):
        a={'bufferView':add(arr,target),'componentType':ct,'count':len(arr),'type':typ}
        if mm:a['min']=arr.min(0).tolist();a['max']=arr.max(0).tolist()
        acc.append(a);return len(acc)-1
    p=A(V.astype(np.float32),5126,'VEC3',34962,True);n=A(N.astype(np.float32),5126,'VEC3',34962)
    UVg=UV.astype(np.float32).copy();UVg[:,1]=1-UVg[:,1];t=A(UVg,5126,'VEC2',34962);i=A(F.astype(np.uint32).ravel(),5125,'SCALAR',34963)
    imgs=[{'bufferView':add(np.frombuffer(open(f,'rb').read(),np.uint8)),'mimeType':'image/jpeg'} for f in tex]
    j={'asset':{'version':'2.0','generator':'arena-enhance'},'scene':0,'scenes':[{'nodes':[0]}],
     'nodes':[{'mesh':0,'name':'Arena'}],'meshes':[{'name':'Arena','primitives':[{'attributes':{'POSITION':p,'NORMAL':n,'TEXCOORD_0':t},'indices':i,'material':0}]}],
     'materials':[{'name':'ArenaStone','pbrMetallicRoughnessure':None}],
     'samplers':[{'magFilter':9729,'minFilter':9987,'wrapS':33071,'wrapT':33071}],
     'textures':[{'source':k,'sampler':0} for k in range(3)],'images':imgs,
     'accessors':acc,'bufferViews':views,'buffers':[{'byteLength':sum(len(x) for x in bins)}]}
    j['materials']=[{'name':'ArenaStone','pbrMetallicRoughness':{'baseColorTexture':{'index':0},'metallicRoughnessTexture':{'index':2},'metallicFactor':1.0,'roughnessFactor':1.0},
       'normalTexture':{'index':1},'occlusionTexture':{'index':2,'strength':0.0},'doubleSided':True}]
    js=json.dumps(j,separators=(',',':')).encode();js+=b' '*((4-len(js)%4)%4);bb=b''.join(bins)
    open(path,'wb').write(struct.pack('<III',0x46546C67,2,28+len(js)+len(bb))+struct.pack('<I4s',len(js),b'JSON')+js+struct.pack('<I4s',len(bb),b'BIN\0')+bb)
TEX=['t_basecolor.jpg','t_normal.jpg','t_orm.jpg']
if __name__=='__main__':
    d=np.load('clean.npz');write('arena_full.glb',d['V'],d['N'],d['UV'],d['F'],TEX)
    import pymeshlab
    ms=pymeshlab.MeshSet()
    m=pymeshlab.Mesh(vertex_matrix=d['V'].astype(np.float64),face_matrix=d['F'].astype(np.int32),v_tex_coords_matrix=d['UV'].astype(np.float64))
    ms.add_mesh(m);ms.compute_texcoord_transfer_vertex_to_wedge()
    ms.meshing_decimation_quadric_edge_collapse_with_texture(targetfacenum=600000,qualitythr=0.5,preserveboundary=True,preservenormal=True,planarquadric=True)
    ms.compute_texcoord_transfer_wedge_to_vertex() if False else None
    m=ms.current_mesh();V=m.vertex_matrix();Fc=m.face_matrix();W=m.wedge_tex_coord_matrix().reshape(-1,3,2)
    key=np.c_[Fc.reshape(-1),np.round(W.reshape(-1,2)*1e6)].astype(np.int64)
    _,first,inv=np.unique(key,axis=0,return_index=True,return_inverse=True)
    vi=Fc.reshape(-1)[first];NV=V[vi];UV=W.reshape(-1,2)[first];F2=inv.ravel().reshape(-1,3)
    # area-weighted normals on welded positions (smooth across UV seams)
    fn=np.cross(V[Fc[:,1]]-V[Fc[:,0]],V[Fc[:,2]]-V[Fc[:,0]]);vn=np.zeros_like(V)
    for k in range(3):np.add.at(vn,Fc[:,k],fn)
    vn/=np.linalg.norm(vn,axis=1,keepdims=True)+1e-12
    write('arena_game.glb',NV,vn[vi],UV,F2,TEX);print('game tris',len(F2),'verts',len(NV))
