# Unreal Engine 5 - Hizli gorunum duzeltmesi: hicbir seyi yeniden ice aktarmaz, sadece mevcut malzeme orneklerinin
# ayarlarini degistirir (saniyeler surer, tekrar calistirmak zararsiz).
#   - Ates duvari: derzlerdeki kor seritleri kapanir (KorGucu 0), tas tonu acilir (bloklar secilir); arenadaki sahte
#     turuncu catlak izgarasi soner (AtesLavGucu, AtesKor)
#   - Selaleler: kopuk/sis/serpinti daha seffaf ve daha az parlak; kopuk rengi beyaz yerine buz mavisi
#   - Lav akintisi: parlaklik dengelenir
# Calistirma: exec(open(unreal.Paths.project_content_dir() + "Maps/Arena/Gorunum.py", encoding="utf-8").read())
import unreal

eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary

AYAR = {
    "/Game/Maps/Arena/Duvar/MI_Duvar_Ates_Harc": ({"KorGucu": 0.0}, {"HarcRenk": (0.03, 0.025, 0.02)}),
    "/Game/Maps/Arena/Duvar/MI_Duvar_Ates_Blok": ({"Parlaklik": 1.0}, {"Ton": (0.8, 0.7, 0.64)}),
    "/Game/Maps/Arena/Duvar/MI_Duvar_Ates_Bezek": ({"Parlaklik": 1.0}, {"Ton": (0.9, 0.79, 0.72)}),
    "/Game/Maps/Arena/Duvar/MI_Lav": ({"LavGucu": 12.0}, {}),
    "/Game/Maps/Arena/Bolge/MI_ArenaBolge": ({"AtesLavGucu": 0.9, "AtesKor": 0.02, "AtesParlaklik": 1.3}, {}),
    "/Game/Maps/Arena/Selale/MI_Selale_Govde": ({"Parlaklik": 0.08, "KopukEsik": 0.7, "Opaklik": 0.85},
                                                {"RenkSu": (0.04, 0.2, 0.5), "RenkKopuk": (0.62, 0.75, 0.85)}),
    "/Game/Maps/Arena/Selale/MI_Selale_Serpinti": ({"Parlaklik": 0.1, "Opaklik": 0.15}, {"RenkKopuk": (0.62, 0.75, 0.85)}),
    "/Game/Maps/Arena/Selale/MI_Selale_Sis": ({"Parlaklik": 0.1, "Opaklik": 0.07}, {"RenkKopuk": (0.7, 0.8, 0.88)}),
    "/Game/Maps/Arena/Selale/MI_Selale_Akinti": ({"Parlaklik": 0.05, "Opaklik": 0.25}, {"RenkKopuk": (0.62, 0.75, 0.85)}),
}

n = 0
for yol, (skaler, vektor) in AYAR.items():
    if not eal.does_asset_exist(yol):
        unreal.log_warning("[Gorunum]    yok, atlandi: " + yol)
        continue
    mi = eal.load_asset(yol)
    for k, v in skaler.items():
        mel.set_material_instance_scalar_parameter_value(mi, k, v)
    for k, v in vektor.items():
        mel.set_material_instance_vector_parameter_value(mi, k, unreal.LinearColor(v[0], v[1], v[2], 1.0))
    eal.save_loaded_asset(mi)
    n += 1
unreal.log_warning("[Gorunum] TAMAM - %d malzeme ornegi guncellendi." % n)
