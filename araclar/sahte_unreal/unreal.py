# Unreal Python API'sinin kaba bir taklidi: scriptlerdeki Python hatalarini (ad, arguman, akis) yakalamak icin.
import math, sys
from unittest.mock import MagicMock

class Vector:
    def __init__(self, x=0.0, y=0.0, z=0.0): self.x, self.y, self.z = float(x), float(y), float(z)
    def __repr__(self): return "V(%.0f,%.0f,%.0f)" % (self.x, self.y, self.z)
class LinearColor:
    def __init__(self, r=0, g=0, b=0, a=1): self.r, self.g, self.b, self.a = r, g, b, a
class Rotator:
    def __init__(self, roll=0, pitch=0, yaw=0): self.roll, self.pitch, self.yaw = roll, pitch, yaw

class _Meta(type):
    def __getattr__(cls, ad):
        if ad.startswith("__"): raise AttributeError(ad)
        m = MagicMock(name=cls.__name__ + "." + ad); setattr(cls, ad, m); return m
class _Taban(metaclass=_Meta):
    def __init__(self, *a, **k): pass
    def __getattr__(self, ad):
        if ad.startswith("__"): raise AttributeError(ad)
        m = MagicMock(name=type(self).__name__ + "." + ad); object.__setattr__(self, ad, m); return m

SAYAC = {"spawn": 0, "ifade": 0, "trace": 0}

def _yukseklik(x, y):
    r = math.hypot(x, y)
    if r < 2000: return 2300.0
    if r < 2500: return 2300.0 if (abs(x) < 180 or abs(y) < 180) else None
    if r < 5000:
        if abs(x) < 180 or abs(y) < 180: return 2300.0
        return 2300.0 + (r - 2500) * 0.5
    if r < 5400: return 3600.0
    return None

class _Hit:
    def __init__(self, z, x, y): self.z, self.x, self.y = z, x, y
    def to_tuple(self):
        p = Vector(self.x, self.y, self.z)
        return (True, False, 0.5, 100.0, p, p, Vector(0, 0, 1), Vector(0, 0, 1), None, None, None, "", "", 0, 0, 0, p, p)

class SystemLibrary(_Taban):
    @staticmethod
    def line_trace_single(w, a, b, *r):
        SAYAC["trace"] += 1
        z = _yukseklik(a.x, a.y)
        return _Hit(z, a.x, a.y) if z is not None and b.z <= z <= a.z else None

class Paths(_Taban):
    @staticmethod
    def project_content_dir(): return __import__("os").path.abspath(__import__("os").path.join(__import__("os").path.dirname(__file__), "..", "..", "Content")) + "/"
    @staticmethod
    def project_saved_dir(): return "/tmp/sahte_unreal_saved/"
    @staticmethod
    def convert_relative_path_to_full(p): return p

_mod = sys.modules[__name__]
_siniflar = {}
def __getattr__(ad):
    if ad.startswith("__"): raise AttributeError(ad)
    if ad[0].isupper():
        if ad not in _siniflar: _siniflar[ad] = _Meta(ad, (_Taban,), {})
        return _siniflar[ad]
    return MagicMock(name=ad)

def log_warning(m): print(m)
def log_error(m): print("ERR", m)
def log(m): print(m)

# --- varliklar ---
class EditorAssetLibrary(_Taban):
    @staticmethod
    def does_asset_exist(y): return True
    @staticmethod
    def does_directory_exist(y): return True
    @staticmethod
    def list_assets(k, recursive=True, include_folder=False):
        if "Isaret" in k: return [k + "/SM_EksenIsaret"]
        return [k + "/" + n for n in ("a_diff_2k", "a_nor_gl_2k", "a_rough_2k", "mesh1")]
    @staticmethod
    def load_asset(y):
        ad = y.split("/")[-1]
        if "mesh" in ad or "SM_" in ad or ad.startswith("Ada") or "Gotik" in y or "scfdy" in y: o = __getattr__("StaticMesh")()
        elif "texture" in ad or "diff" in ad or "nor" in ad or "rough" in ad or "color" in ad or "Noise" in ad or "Detay" in ad:
            o = __getattr__("Texture2D")()
        else: o = __getattr__("Object")()
        o.get_name = lambda: ad
        o.get_editor_property = lambda k: {"srgb": "diff" in ad or "texture_0" in ad}.get(k, MagicMock())
        if type(o).__name__ == "StaticMesh":
            o.get_bounding_box = lambda: _kutu(y)
            o.get_static_mesh_description = lambda lod: _MerdivenKose(y)
        return o
    @staticmethod
    def save_loaded_asset(a): return True

# --- malzeme grafigi: dugumler, baglantilar ve UE kurallariyla bilesen sayisi (float1..4) denetimi ---
_GRAF = {}      # id(malzeme) -> {"ifadeler": [...], "cikis": {ozellik: (ifade, cikis_adi)}}
_DERLEME = {}   # id(malzeme) -> hata listesi (son recompile)

class _Ifade:
    def __init__(self, sinif):
        self.sinif, self.oz, self.giris = sinif, {}, {}
    def set_editor_property(self, k, v): self.oz[k] = v
    def get_editor_property(self, k): return self.oz.get(k, MagicMock())
    def __getattr__(self, ad):
        if ad.startswith("__"): raise AttributeError(ad)
        return MagicMock(name=self.sinif + "." + ad)

_TEK_GIRIS = {"Saturate", "Normalize", "Sine", "Cosine", "Frac", "Abs", "OneMinus", "ComponentMask", "Transform", "Floor"}
_SABIT = {"Constant": 1, "ScalarParameter": 1, "Time": 1, "Constant2Vector": 2, "Constant3Vector": 3,
          "Constant4Vector": 4, "VectorParameter": 4, "WorldPosition": 3, "VertexNormalWS": 3, "VertexColor": 3,
          "TextureCoordinate": 2, "CameraPositionWS": 3, "PixelNormalWS": 3, "ObjectPositionWS": 3, "Panner": 2}

def _cikis_boyu(e, cikis, hatalar, yol):
    t = e.sinif
    if t.startswith("TextureSample"):
        uv = e.giris.get("UVs")
        if uv is not None:
            n = _boy(uv, hatalar, yol)
            if n not in (1, 2): hatalar.append("(Node %s) UVs float%d olamaz" % (t, n))
        return {"": 3, "RGB": 3, "R": 1, "G": 1, "B": 1, "A": 1, "RGBA": 4}[cikis]
    if t == "Constant2Vector" and cikis in ("R", "G"): return 1
    if t in ("Constant3Vector", "VectorParameter", "VertexColor") and cikis in ("R", "G", "B", "A"): return 1
    if t == "VectorParameter" and cikis in ("", "RGB"): return 3
    if t in _SABIT:
        if cikis not in ("", "XYZ", "RGB"): hatalar.append("(Node %s) bilinmeyen cikis %r" % (t, cikis))
        return _SABIT[t]
    g = {k: _boy(v, hatalar, yol) for k, v in e.giris.items()}
    if t in ("Multiply", "Add", "Subtract", "Divide", "Max", "Min"):
        a, b = g.get("A", 1), g.get("B", 1)
        if a != b and 1 not in (a, b):
            hatalar.append("(Node %s) Arithmetic between types float%d and float%d are undefined" % (t, a, b))
        return max(a, b)
    if t == "LinearInterpolate":
        a, b, al = g.get("A", 1), g.get("B", 1), g.get("Alpha", 1)
        n = max(a, b)
        if (a != b and 1 not in (a, b)) or (al != 1 and al != n):
            hatalar.append("(Node Lerp) uyumsuz float%d/float%d/alfa float%d" % (a, b, al))
        return n
    if t == "DotProduct":
        a, b = g.get("A", 1), g.get("B", 1)
        if a != b: hatalar.append("(Node Dot) float%d . float%d" % (a, b))
        return 1
    if t == "AppendVector":
        n = g.get("A", 1) + g.get("B", 1)
        if n > 4: hatalar.append("(Node Append) float%d" % n)
        return n
    if t in _TEK_GIRIS:
        n = g.get("", 1)
        if t == "ComponentMask":
            k = [c for c in "rgba" if e.oz.get(c)]
            if not k: hatalar.append("(Node Mask) kanal secilmedi")
            if any("rgba".index(c) >= n for c in k): hatalar.append("(Node Mask) float%d icinde %s yok" % (n, k))
            return len(k) or 1
        if t == "Transform": return 3
        return n
    hatalar.append("(Node %s) denetleyici bu dugumu tanimiyor" % t)
    return 1

def _boy(bag_, hatalar, yol):
    e, cikis = bag_
    if id(e) in yol:
        hatalar.append("dongu: " + e.sinif); return 1
    return _cikis_boyu(e, cikis, hatalar, yol | {id(e)})

def _kutu(yol):
    """sahte mesh kutulari: eksen isareti glTF (x,y,z) -> UE (x, -z, y) * 100 gibi; Fab merdiveni 332x455x166"""
    b = MagicMock()
    if "EksenIsaret" in yol: b.min, b.max = Vector(0, -3000, 0), Vector(1000, 0, 2000)
    elif "scfdy" in yol or "Fab" in yol: b.min, b.max = Vector(-166, -227.5, 0), Vector(166, 227.5, 166)
    else: b.min, b.max = Vector(-100, -100, 0), Vector(100, 100, 200)
    return b

class VertexID:
    def __init__(self, i=0): self.i = i

class _MerdivenKose:
    """-x yonunde yukselen 8 basamakli sahte merdiven yuzeyi"""
    def __init__(self, yol): self.p = [(x, y, 166.0 * (int((166 - x) / 332 * 8) + 1) / 8) for x in range(-160, 166, 10) for y in range(-220, 228, 40)]
    def get_vertex_count(self): return len(self.p)
    def get_vertex_position(self, v): return Vector(*self.p[v.i])

class MaterialEditingLibrary(_Taban):
    @staticmethod
    def create_material_expression(m, sinif, x, y):
        SAYAC["ifade"] += 1
        if not isinstance(sinif, type): raise TypeError("ifade sinifi degil: %r" % sinif)
        e = _Ifade(sinif.__name__.replace("MaterialExpression", ""))
        _GRAF.setdefault(id(m), {"ifadeler": [], "cikis": {}})["ifadeler"].append(e)
        return e
    @staticmethod
    def delete_all_material_expressions(m):
        _GRAF[id(m)] = {"ifadeler": [], "cikis": {}}
    @staticmethod
    def connect_material_expressions(a, cikis, b, giris):
        if not isinstance(a, _Ifade) or not isinstance(b, _Ifade): raise TypeError("ifade degil: %r -> %r" % (a, b))
        b.giris[giris] = (a, cikis)
        return True
    @staticmethod
    def connect_material_property(a, cikis, ozellik):
        if not isinstance(a, _Ifade): raise TypeError("ifade degil: %r" % (a,))
        for g in _GRAF.values():
            if any(e is a for e in g["ifadeler"]): g["cikis"][str(ozellik)] = (a, cikis)
        return True
    @staticmethod
    def recompile_material(m):
        g = _GRAF.get(id(m), {"cikis": {}})
        hatalar = []
        for oz, bg in g["cikis"].items():
            n = _boy(bg, hatalar, frozenset())
            beklenen = 1 if ("ROUGHNESS" in oz or "OPACITY" in oz or "METALLIC" in oz) else 3
            if n not in (1, beklenen): hatalar.append("%s float%d alamaz" % (oz, n))
        _DERLEME[id(m)] = hatalar
        for h in hatalar: print("DERLEME HATASI", h)
    @staticmethod
    def get_statistics(m):
        hata_var = bool(_DERLEME.get(id(m)))
        ist = MagicMock()
        ist.get_editor_property = lambda k: 0 if hata_var else 123
        return ist

class _Aktor(_Taban):
    def __init__(self, etiket, konum, donus=None):
        self._e, self._k, self._d, self._s = etiket, konum, donus or Rotator(), Vector(1, 1, 1)
    def get_actor_rotation(self): return self._d
    def set_actor_scale3d(self, s): self._s = s
    def get_actor_label(self): return self._e
    def set_actor_label(self, e): self._e = e
    def get_actor_location(self): return self._k
    def get_actor_scale3d(self): return self._s

class _EAS(_Taban):
    def __init__(self):
        self.aktorler = []
        arena = __getattr__("StaticMeshActor")()
        arena.get_actor_label = lambda: "Arena"
        arena.get_actor_location = lambda: Vector(0, 0, 0)
        arena.get_actor_scale3d = lambda: Vector(1, 1, 1)
        arena.get_actor_rotation = lambda: Rotator()
        sm = MagicMock(); sm.get_name.return_value = "arena_game"
        arena.static_mesh_component.get_editor_property.return_value = sm
        arena.static_mesh_component.get_num_materials.return_value = 1
        self.aktorler.append(arena)
        for ad, (x, y) in {"Toprak": (1200, 800), "Hava": (1200, -800), "Su": (-1200, -800), "Ates": (-1200, 800)}.items():
            self.aktorler.append(_Aktor("ES_Kure_" + ad, Vector(x, y, 3060)))
    def get_all_level_actors(self): return list(self.aktorler)
    secili = []
    def get_selected_level_actors(self): return [a for a in self.secili if a in self.aktorler]
    def destroy_actor(self, a): self.aktorler.remove(a)
    def spawn_actor_from_object(self, o, konum, donus=None):
        if not isinstance(konum, Vector): raise TypeError("konum Vector degil")
        SAYAC["spawn"] += 1
        a = _Aktor("yeni", konum, donus); self.aktorler.append(a); return a
    def spawn_actor_from_class(self, c, konum, donus=None):
        return self.spawn_actor_from_object(c, konum, donus)

_eas = _EAS()
def get_editor_subsystem(c):
    return _eas if c.__name__ == "EditorActorSubsystem" else c()
