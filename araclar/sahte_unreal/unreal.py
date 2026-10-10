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
        return [k + "/" + n for n in ("a_diff_2k", "a_nor_gl_2k", "a_rough_2k", "mesh1")]
    @staticmethod
    def load_asset(y):
        ad = y.split("/")[-1]
        if "mesh" in ad or "SM_" in ad or ad.startswith("Ada") or "Gotik" in y: o = __getattr__("StaticMesh")()
        elif "texture" in ad or "diff" in ad or "nor" in ad or "rough" in ad or "color" in ad or "Noise" in ad or "Detay" in ad:
            o = __getattr__("Texture2D")()
        else: o = __getattr__("Object")()
        o.get_name = lambda: ad
        o.get_editor_property = lambda k: {"srgb": "diff" in ad or "texture_0" in ad}.get(k, MagicMock())
        return o
    @staticmethod
    def save_loaded_asset(a): return True

class MaterialEditingLibrary(_Taban):
    @staticmethod
    def create_material_expression(m, sinif, x, y):
        SAYAC["ifade"] += 1
        if not isinstance(sinif, type): raise TypeError("ifade sinifi degil: %r" % sinif)
        return sinif()

class _Aktor(_Taban):
    def __init__(self, etiket, konum):
        self._e, self._k = etiket, konum
    def get_actor_label(self): return self._e
    def set_actor_label(self, e): self._e = e
    def get_actor_location(self): return self._k
    def get_actor_scale3d(self): return Vector(1, 1, 1)

class _EAS(_Taban):
    def __init__(self):
        self.aktorler = []
        arena = __getattr__("StaticMeshActor")()
        arena.get_actor_label = lambda: "Arena"
        arena.get_actor_location = lambda: Vector(0, 0, 0)
        arena.get_actor_scale3d = lambda: Vector(1, 1, 1)
        sm = MagicMock(); sm.get_name.return_value = "arena_game"
        arena.static_mesh_component.get_editor_property.return_value = sm
        arena.static_mesh_component.get_num_materials.return_value = 1
        self.aktorler.append(arena)
        for ad, (x, y) in {"Toprak": (1200, 800), "Hava": (1200, -800), "Su": (-1200, -800), "Ates": (-1200, 800)}.items():
            self.aktorler.append(_Aktor("ES_Kure_" + ad, Vector(x, y, 3060)))
    def get_all_level_actors(self): return list(self.aktorler)
    def destroy_actor(self, a): self.aktorler.remove(a)
    def spawn_actor_from_object(self, o, konum, donus=None):
        if not isinstance(konum, Vector): raise TypeError("konum Vector degil")
        SAYAC["spawn"] += 1
        a = _Aktor("yeni", konum); self.aktorler.append(a); return a
    def spawn_actor_from_class(self, c, konum, donus=None):
        return self.spawn_actor_from_object(c, konum, donus)

_eas = _EAS()
def get_editor_subsystem(c):
    return _eas if c.__name__ == "EditorActorSubsystem" else c()
