#!/usr/bin/env bash
# Lanza mGBA con el ROM+save de Moviplaya 2005 (el .sav se autocarga por tener el mismo nombre)
DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$DIR/squashfs-root/AppRun" "$DIR/pokemon-esmeralda/pokemon-esmeralda.gba" "$@"
