# Bolge dokusu (T_ArenaBolge.jpg) nasil uretildi

1. `images/6.jpg` (referans), arenanin uretildigi ilk resme SIFT + homografi ile hizalanir -> `ref6.jpg`, `mask6.png` (2048).
2. `bake.html` (three.js, onceden bulunan kamera ile) resmi arena UV'lerine yansitir; ayrica her texel'in dunya konumu/normali alinir.
3. `comp.py`: gorunmeyen yuzler bolgesine gore (x,z isaretine gore ceyrek) referansin renk dagilimina cekilir,
   toprakta yosun, ateste kömür + lav catlagi, suda buz, havada mermer tonu eklenir; ustune yansitilan resim bindirilir.
4. `swap.py` onizleme icin glb'nin renk dokusunu degistirir.
5. `maske.py`: T_ArenaBolgeMaske.png (R=lav isigi, G=parlaklik buz/mermer, B=su isiltisi).
6. `selale.py` (+`kamera.py`): referanstaki selale noktalarini kameradan arenaya isinlayip duvari takip eden su perdeleri uretir -> SM_Selale.glb.
7. `selale2.py` + `selale_doku.py`: hacimli surum (govde/serpinti/sis) ve dikissiz akis + dalga normali dokulari.
8. `kule.py` + `yuzey.py` + `akinti.py`: su tribunu kulelerinin sahadan gorunen yuzleri, kulelerden akan 3D dereler ve ince su tabakasi (selale2.py bunlari SM_Selale.glb'ye ekler).
