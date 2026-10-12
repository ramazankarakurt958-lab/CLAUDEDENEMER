# Unreal Engine 5 - "Aydinlatmanin yeniden insa edilmesi gerek" uyarisini kalici olarak kaldirir: haritayi tamamen dinamik
# isiga (Lumen) gecirir, isik pisirme (Build Lighting) gerekmez.
#   - World Settings: Force No Precomputed Lighting = acik (pisirilmis isik haritasi kullanilmaz)
#   - Sahnedeki butun isiklar (gunes, gok isigi, mesale isiklari, nokta/spot isiklar) Movable
#   - Gok isigi gercek zamanli yakalama (gokyuzu degisince isik da degisir)
# Hicbir seyi silmez/ice aktarmaz; saniyeler surer, tekrar calistirmak zararsiz.
# Calistirma: exec(open(unreal.Paths.project_content_dir() + "Maps/Arena/Aydinlatma.py", encoding="utf-8").read())
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)


def log(msg):
    unreal.log_warning("[Isik] " + msg)


dunya = ues.get_editor_world()
ws = dunya.get_world_settings()
try:
    ws.set_editor_property("force_no_precomputed_lighting", True)
    log("   World Settings: Force No Precomputed Lighting acik")
except Exception as e:
    log("   World Settings ayarlanamadi (%s) - elle: World Settings > Lightmass > Force No Precomputed Lighting" % e)

n = 0
for a in eas.get_all_level_actors():
    for c in a.get_components_by_class(unreal.LightComponentBase):
        try:
            c.set_mobility(unreal.ComponentMobility.MOVABLE)
            n += 1
        except Exception as e:
            log("   %s hareketli yapilamadi: %s" % (a.get_actor_label(), e))
        if isinstance(c, unreal.SkyLightComponent):
            try:
                c.set_editor_property("real_time_capture", True)
            except Exception:
                pass
            c.recapture_sky()
les.save_current_level()
log("TAMAM - %d isik dinamik (Movable), pisirilmis isik kapali. 'Aydinlatma yeniden insa' uyarisi gitmeli." % n)
