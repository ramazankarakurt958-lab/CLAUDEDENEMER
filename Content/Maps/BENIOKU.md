# Arena haritası (Unreal Engine 5)

1. Bu `Maps` klasörünü projenin `Content` klasörünün içine kopyala (`<Proje>/Content/Maps/...`).
2. Projeyi Unreal Editor'de aç.
3. **Tools → Execute Python Script...** ile `Content/Maps/Arena/ArenaIceAktar.py` dosyasını seç.
   - Menüde yoksa: **Edit → Plugins → "Python Editor Script Plugin"** etkinleştir, editörü yeniden başlat.
4. Script şunları yapar:
   - `Kaynak/arena_game.glb` dosyasını `/Game/Maps/Arena/Varliklar` içine aktarır (mesh, malzeme, dokular).
   - Çarpışmayı gerçek geometriye göre ayarlar (Complex as Simple) ve Nanite'ı açar.
   - `/Game/Maps/Arena_Map` haritasını oluşturur; arena, güneş, gökyüzü, sis, bulut ve orta platformun üstüne Player Start ekler.
5. **Content Browser → Maps → Arena_Map** haritasını aç ve Play'e bas.

Oyunun bu haritayla açılması için: **Edit → Project Settings → Maps & Modes → Editor Startup Map / Game Default Map = Arena_Map**.
