# Pota Kaçtı – Arena Harita Oluşturucu (UE5)

`build_arena.py`, **Arena** haritasını referans görseldeki düzene göre kurar:

| Bölge | Konum | İçerik |
|---|---|---|
| Orta platform | Merkez | Altın halkalı / yıldız desenli yuvarlak zemin, 8 meşale, altında kaya gövdesi |
| Ateş | Kuzeybatı | Volkanik sivri kayalar, kale blokları, lav çatlakları ve lav şelaleleri |
| Buz / Su | Kuzeydoğu | Uzun buz kuleleri, fıskiyeli platformlar, şelaleler |
| Rüzgâr / Bulut | Güneydoğu | İnce kolonlu disk platformlar, rüzgâr girdapları, bulut öbekleri |
| Doğa | Güneybatı | Yosunlu kuleler, ağaçlar, sarmaşıklar |
| Ana kapı | Güney | Kuleler + kapı (**ortadaki alt köprü yok**) |
| Köprüler | Kuzey, doğu, batı | Merkezi halkaya bağlar |
| Çevre | — | Uçan kayalar, gökyüzü, güneş, sis ve bulutlar (haritada yoksa eklenir) |

## Kullanım

1. **Edit → Plugins**: *Python Editor Script Plugin* ve *Editor Scripting Utilities* açık olsun, sonra editörü yeniden başlat.
2. Önce Arena haritasının yedeğini al (Content Browser'da sağ tık → Duplicate).
3. **Arena** haritasını aç.
4. **Tools → Execute Python Script…** menüsünden `build_arena.py` dosyasını seç.
5. Her şey Outliner'daki **ArenaGen** klasörüne gelir. Materyaller `/Game/PotaKacti/ArenaGen/Materials` altına kaydedilir.

- Script yalnızca `PK_ArenaGen` etiketli (kendi oluşturduğu) aktörleri siler. Senin yaptığın parçalara dokunmaz. Kendi parçalarını kaldırmak ya da gizlemek istersen bunu elle yapmalısın.
- Tekrar çalıştırırsan önceki ArenaGen parçalarını silip yeniden kurar.
- Tüm işlem tek adımda **Ctrl+Z** ile geri alınabilir.

## Ayarlar (dosyanın başında)

- `ADD_SOUTH_BRIDGE = False`: ortadaki alt köprü kapalı.
- `ADD_SIDE_BRIDGES`, `ADD_SKY_AND_LIGHTS`, `ADD_FLOATING_ROCKS`: açıp kapatılabilir.
- `CENTER_R`, `RING_INNER_R`, `WALL_R`, `WALL_H`: arenanın boyutları (cm).
- `RANDOM_SEED`: kaya ve ağaçların yerleşimini değiştirmek için.

Parçalar Unreal'ın temel şekilleriyle (küp, silindir, koni, küre) yapılmış bir **blockout**. Yerleşim oturduktan sonra bunları kendi mesh'lerinle veya Megascans / Fab varlıklarıyla değiştirebilirsin.
