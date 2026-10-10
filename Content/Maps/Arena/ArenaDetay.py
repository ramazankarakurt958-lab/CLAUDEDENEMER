# Unreal Engine 5 - Arena malzemesine yakin plan taş detayi ekler (bulaniklik giderme).
# Ana dokunun ustune tekrar eden ince bir tas dokusu (renk + yuzey kabartmasi) bindirir.
# Ayar icin: Content/Maps/Arena/Varliklar/MI_ArenaTas  ->  DetayTekrar, DetayGucu
import os
import unreal

ICERIK = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir())
KAYNAK = os.path.join(ICERIK, "Maps", "Arena", "Kaynak")
VARLIK = "/Game/Maps/Arena/Varliklar"
DETAY = "/Game/Maps/Arena/Detay"

eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()


def log(msg):
    unreal.log_warning("[Arena] " + msg)


def hata(msg):
    unreal.log_error("[Arena] HATA: " + msg)
    raise RuntimeError(msg)


# 1) Detay dokularini ice aktar
log("1/4 Detay dokulari aktariliyor...")
gorevler = []
for ad in ("T_ArenaDetay_D.png", "T_ArenaDetay_N.png"):
    yol = os.path.join(KAYNAK, ad)
    if not os.path.isfile(yol):
        hata(ad + " bulunamadi: " + yol)
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", yol)
    t.set_editor_property("destination_path", DETAY)
    t.set_editor_property("automated", True)
    t.set_editor_property("replace_existing", True)
    t.set_editor_property("save", True)
    gorevler.append(t)
tools.import_asset_tasks(gorevler)

detay_d = eal.load_asset(DETAY + "/T_ArenaDetay_D")
detay_n = eal.load_asset(DETAY + "/T_ArenaDetay_N")
if not detay_d or not detay_n:
    hata("Detay dokulari yuklenemedi (" + DETAY + ").")
detay_d.set_editor_property("srgb", False)
detay_n.set_editor_property("srgb", False)
detay_n.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
for t in (detay_d, detay_n):
    eal.save_loaded_asset(t)

# 2) Arenanin kendi dokularini ve mesh'ini bul
log("2/4 Arena dokulari bulunuyor...")
renk = normal = orm = None
meshes = []
for yol in eal.list_assets(VARLIK, recursive=True, include_folder=False):
    a = eal.load_asset(yol)
    if isinstance(a, unreal.StaticMesh):
        meshes.append(a)
    elif isinstance(a, unreal.Texture2D):
        if a.get_editor_property("compression_settings") == unreal.TextureCompressionSettings.TC_NORMALMAP:
            normal = a
        elif a.get_editor_property("srgb"):
            renk = a
        else:
            orm = a
if not meshes or not renk:
    hata("Arena mesh'i veya renk dokusu bulunamadi. Once ArenaIceAktar.py calismis olmali.")
log("   renk=%s normal=%s orm=%s" % (renk.get_name(), normal.get_name() if normal else "-", orm.get_name() if orm else "-"))
for t in (renk, normal, orm):
    if t:  # tam cozunurlukte kalsin, dunya dokusu grubunda olsun
        t.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_WORLD)
        t.set_editor_property("max_texture_size", 0)
        eal.save_loaded_asset(t)

# 3) Malzemeyi olustur
log("3/4 Malzeme olusturuluyor: M_ArenaTas")
MAT_YOL = VARLIK + "/M_ArenaTas"
if eal.does_asset_exist(MAT_YOL):
    mat = eal.load_asset(MAT_YOL)
    mel.delete_all_material_expressions(mat)
else:
    mat = tools.create_asset("M_ArenaTas", VARLIK, unreal.Material, unreal.MaterialFactoryNew())


def ifade(sinif, x, y):
    return mel.create_material_expression(mat, sinif, x, y)


def doku(tex, tur, x, y):
    e = ifade(unreal.MaterialExpressionTextureSample, x, y)
    e.set_editor_property("texture", tex)
    e.set_editor_property("sampler_type", tur)
    return e


def param(ad, deger, x, y):
    e = ifade(unreal.MaterialExpressionScalarParameter, x, y)
    e.set_editor_property("parameter_name", ad)
    e.set_editor_property("default_value", deger)
    return e


bag = mel.connect_material_expressions
ST = unreal.MaterialSamplerType

# Detay UV = TexCoord * DetayTekrar
uv = ifade(unreal.MaterialExpressionTextureCoordinate, -1400, 300)
tekrar = param("DetayTekrar", 150.0, -1400, 450)
duv = ifade(unreal.MaterialExpressionMultiply, -1200, 350)
bag(uv, "", duv, "A")
bag(tekrar, "", duv, "B")
guc = param("DetayGucu", 1.0, -1000, 650)

# Renk: ana renk * lerp(1, detay*2, DetayGucu*0.7)
t_renk = doku(renk, ST.SAMPLERTYPE_COLOR, -900, -400)
t_dd = doku(detay_d, ST.SAMPLERTYPE_LINEAR_COLOR, -1000, 100)
bag(duv, "", t_dd, "UVs")
dd2 = ifade(unreal.MaterialExpressionMultiply, -750, 100)
dd2.set_editor_property("const_b", 2.0)
bag(t_dd, "R", dd2, "A")
alfa = ifade(unreal.MaterialExpressionMultiply, -750, 250)
alfa.set_editor_property("const_b", 0.7)
bag(guc, "", alfa, "A")
lr = ifade(unreal.MaterialExpressionLinearInterpolate, -550, 100)
lr.set_editor_property("const_a", 1.0)
bag(dd2, "", lr, "B")
bag(alfa, "", lr, "Alpha")
son_renk = ifade(unreal.MaterialExpressionMultiply, -300, -300)
bag(t_renk, "RGB", son_renk, "A")
bag(lr, "", son_renk, "B")
mel.connect_material_property(son_renk, "", unreal.MaterialProperty.MP_BASE_COLOR)

# Puruzluluk: ORM'nin yesil kanali (yoksa sabit 0.85)
if orm:
    t_orm = doku(orm, ST.SAMPLERTYPE_LINEAR_COLOR, -900, -100)
    mel.connect_material_property(t_orm, "G", unreal.MaterialProperty.MP_ROUGHNESS)
else:
    rc = ifade(unreal.MaterialExpressionConstant, -300, -100)
    rc.set_editor_property("r", 0.85)
    mel.connect_material_property(rc, "", unreal.MaterialProperty.MP_ROUGHNESS)

# Normal: normalize(ana + detay * (DetayGucu, DetayGucu, 0))
t_dn = doku(detay_n, ST.SAMPLERTYPE_NORMAL, -1000, 400)
bag(duv, "", t_dn, "UVs")
maske = ifade(unreal.MaterialExpressionConstant3Vector, -1000, 800)
maske.set_editor_property("constant", unreal.LinearColor(1.0, 1.0, 0.0, 0.0))
olcek = ifade(unreal.MaterialExpressionMultiply, -750, 700)
bag(maske, "", olcek, "A")
bag(guc, "", olcek, "B")
dn = ifade(unreal.MaterialExpressionMultiply, -550, 450)
bag(t_dn, "RGB", dn, "A")
bag(olcek, "", dn, "B")
if normal:
    t_n = doku(normal, ST.SAMPLERTYPE_NORMAL, -900, 300)
    top = ifade(unreal.MaterialExpressionAdd, -350, 350)
    bag(t_n, "RGB", top, "A")
    bag(dn, "", top, "B")
else:
    top = ifade(unreal.MaterialExpressionAdd, -350, 350)
    top.set_editor_property("const_a", 0.0)
    bag(dn, "", top, "B")
nrm = ifade(unreal.MaterialExpressionNormalize, -150, 350)
bag(top, "", nrm, "")
mel.connect_material_property(nrm, "", unreal.MaterialProperty.MP_NORMAL)

mel.layout_material_expressions(mat)
mel.recompile_material(mat)
eal.save_loaded_asset(mat)

# Ayarlanabilir malzeme ornegi
MI_YOL = VARLIK + "/MI_ArenaTas"
mi = eal.load_asset(MI_YOL) if eal.does_asset_exist(MI_YOL) else \
    tools.create_asset("MI_ArenaTas", VARLIK, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
mel.set_material_instance_parent(mi, mat)
eal.save_loaded_asset(mi)

# 4) Mesh'e ata
log("4/4 Malzeme arenaya ataniyor...")
for m in meshes:
    for i in range(len(m.get_editor_property("static_materials"))):
        m.set_material(i, mi)
    eal.save_loaded_asset(m)

log("TAMAM - Detay eklendi. Ayar: " + MI_YOL + " (DetayTekrar, DetayGucu)")
