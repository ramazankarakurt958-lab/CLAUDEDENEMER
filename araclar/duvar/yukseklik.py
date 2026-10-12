# Arenanin ustten yukseklik haritasi: yuzeyden 8 milyon nokta ornekler, 20 cm hucrelerde en ust (H) ve en alt (B) y.
# Kullanim: python3 yukseklik.py arena_game.glb hmap.npz
import sys
import numpy as np
import trimesh

g = trimesh.load(sys.argv[1], force="mesh")
pts, _ = trimesh.sample.sample_surface(g, 8000000, seed=1)
G, O = 0.2, -56.0
S = int(112 / G)
i, j = ((pts[:, 0] - O) / G).astype(int), ((pts[:, 2] - O) / G).astype(int)
ok = (i >= 0) & (i < S) & (j >= 0) & (j < S)
H, B = np.full((S, S), -1e9), np.full((S, S), 1e9)
np.maximum.at(H, (j[ok], i[ok]), pts[ok, 1])
np.minimum.at(B, (j[ok], i[ok]), pts[ok, 1])
H[H < -1e8], B[B > 1e8] = np.nan, np.nan
np.savez(sys.argv[2] if len(sys.argv) > 2 else "hmap.npz", H=H, B=B, G=G, O=O)
