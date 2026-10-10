# Basit GLB yazici: tek mesh, tek malzeme (doku yok). Girdi Z yukari, metre.
import json
import struct

import numpy as np


def yaz(yol, V, N, UV, F, ad="Mesh", renk=(0.5, 0.5, 0.5)):
    # Z yukari -> glTF Y yukari
    V = np.c_[V[:, 0], V[:, 2], -V[:, 1]].astype(np.float32)
    N = np.c_[N[:, 0], N[:, 2], -N[:, 1]].astype(np.float32)
    UV = np.c_[UV[:, 0], 1 - UV[:, 1]].astype(np.float32)
    F = np.asarray(F, np.uint32)
    bins, views, acc = [], [], []

    def ekle(arr, ct, tip, hedef, mm=False):
        b = arr.tobytes()
        views.append({"buffer": 0, "byteOffset": sum(map(len, bins)), "byteLength": len(b), "target": hedef})
        bins.append(b + b"\0" * ((4 - len(b) % 4) % 4))
        a = {"bufferView": len(views) - 1, "componentType": ct, "count": len(arr) if arr.ndim > 1 else arr.size, "type": tip}
        if mm:
            a["min"], a["max"] = arr.min(0).tolist(), arr.max(0).tolist()
        acc.append(a)
        return len(acc) - 1

    p = ekle(V, 5126, "VEC3", 34962, True)
    n = ekle(N, 5126, "VEC3", 34962)
    t = ekle(UV, 5126, "VEC2", 34962)
    i = ekle(F.ravel(), 5125, "SCALAR", 34963)
    j = {"asset": {"version": "2.0", "generator": "araclar/glb_yaz.py"}, "scene": 0, "scenes": [{"nodes": [0]}],
         "nodes": [{"mesh": 0, "name": ad}],
         "meshes": [{"name": ad, "primitives": [{"attributes": {"POSITION": p, "NORMAL": n, "TEXCOORD_0": t},
                                                  "indices": i, "material": 0}]}],
         "materials": [{"name": ad + "_Malzeme", "pbrMetallicRoughness": {"baseColorFactor": list(renk) + [1],
                                                                           "metallicFactor": 0, "roughnessFactor": .85}}],
         "accessors": acc, "bufferViews": views, "buffers": [{"byteLength": sum(map(len, bins))}]}
    js = json.dumps(j, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    bb = b"".join(bins)
    with open(yol, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, 28 + len(js) + len(bb)))
        f.write(struct.pack("<I4s", len(js), b"JSON") + js + struct.pack("<I4s", len(bb), b"BIN\0") + bb)
