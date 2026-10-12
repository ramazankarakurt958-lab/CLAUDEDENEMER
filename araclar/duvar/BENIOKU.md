# Duvar kaplama (SM_Duvar.glb) nasil uretildi

1. `yukseklik.py arena_game.glb hmap.npz`: ustten yukseklik haritasi (20 cm).
2. `kontur.py hmap.npz SM_Selale.glb`: 0.5 m kademelerin yumusatilmis sinir cizgileri; en az 1.6 m dik dusen ust kenarlar duvar
   sayilir. Kuleler (kapali, yuvarlak, cevresi < 70 m konturlar) isaretlenir: duvar3d sadece govdelerini kaplar, tac/havuz
   (genisleyen tepe) basladigi yerde ince kusakla biter. Selalelerin aktigi yuzeyler, orta platform ve kopruler atlanir.
3. `duvar_doku.py`: derzsiz tas yuzeyi T_DuvarTas_D/N (derzler 3D geometride).
4. `duvar3d.py konturlar.npy arena_game.glb SM_Duvar.glb`: kesme tas bloklar, harc yuzeyi, plastirlar, kornis, dis halka
   duvarlarinda mazgalli parapet. Eski yuzeyin tastigi yerlerde kaplama one alinir (yatay isinlarla olculur).
5. Sancaklar yeni duvar yuzune asilsin diye: `../bolge_doku/susleme3d.py arena_game.glb SM_Duvar.glb`.
Unreal: `Content/Maps/Arena/DuvarKaplama.py` (tek basina) ya da `ArenaHepsi.py` (butun katmanlar).
