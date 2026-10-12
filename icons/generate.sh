#!/usr/bin/env bash
# Genera los PNG de los íconos a partir de los SVG vectoriales.
# Requiere: ImageMagick (`magick` / `convert`) o `rsvg-convert`.
set -euo pipefail
cd "$(dirname "$0")"

CONVERT=""
if command -v rsvg-convert >/dev/null 2>&1; then
    CONVERT="rsvg-convert -w SIZE -h SIZE -o OUT IN"
elif command -v magick >/dev/null 2>&1; then
    CONVERT="magick convert -background none -density 300 IN -resize SIZExSIZE OUT"
elif command -v convert >/dev/null 2>&1; then
    CONVERT="convert -background none -density 300 IN -resize SIZExSIZE OUT"
else
    echo "⚠️  Instala ImageMagick o rsvg-convert"
    exit 1
fi

gen() { # gen <in.svg> <out.png> <size>
  local out="${2%.png}-$3.png"
  local cmd="${CONVERT//SIZE/$3}"
  cmd="${cmd//OUT/$out}"
  cmd="${cmd//IN/$1}"
  eval "$cmd"
  echo "✓ $out"
}

gen icon.svg icon 192
gen icon.svg icon 512
gen icon-maskable.svg icon-maskable 512
echo "Listo."