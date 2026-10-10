#!/bin/sh
# Unreal scriptlerini sahte Unreal API'siyle calistirip Python hatalarini yakalar (gorsel sonucu test etmez).
# Kullanim: sh araclar/dene.sh BolgeSahasi
cd "$(dirname "$0")/.." && PYTHONPATH=araclar/sahte_unreal python3 -c "
import unreal
exec(open('Content/Maps/Arena/$1.py', encoding='utf-8').read())
print('sayac:', unreal.SAYAC)"
