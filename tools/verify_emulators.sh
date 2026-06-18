#!/usr/bin/env bash
#
# Verify the literary-watch watchface on one or more Pebble emulators.
#
# For each platform it: installs the app, screenshots the resting (sky) state,
# sends an accelerometer tap to reveal a quote, then screenshots again.
# Screenshots are written to build/screenshots/<platform>_{sky,quote}.png.
#
# Usage:
#   tools/verify_emulators.sh                 # default set of platforms
#   tools/verify_emulators.sh basalt diorite  # specific platforms
#   VNC=1 tools/verify_emulators.sh           # headless (adds --vnc)
#
# Run from the project root. Assumes `pebble build` has already succeeded.

set -euo pipefail

PLATFORMS=("${@:-basalt diorite chalk emery}")
# Re-split in case the default single arg carried multiple words.
read -r -a PLATFORMS <<< "${PLATFORMS[*]}"

VNC_FLAG=""
if [[ "${VNC:-0}" == "1" ]]; then
  VNC_FLAG="--vnc"
fi

OUT_DIR="build/screenshots"
mkdir -p "$OUT_DIR"

shot() {  # platform name
  pebble screenshot --emulator "$1" $VNC_FLAG --no-open "$OUT_DIR/$1_$2.png"
}

for p in "${PLATFORMS[@]}"; do
  echo "=== $p ==="
  pebble kill >/dev/null 2>&1 || true

  echo "  installing..."
  pebble install --emulator "$p" $VNC_FLAG >/dev/null

  echo "  resting (sky) screenshot..."
  shot "$p" sky

  echo "  tap -> reveal quote..."
  pebble emu-tap --emulator "$p" $VNC_FLAG --direction x+ >/dev/null
  sleep 1
  shot "$p" quote

  echo "  done: $OUT_DIR/${p}_sky.png, $OUT_DIR/${p}_quote.png"
done

echo "All requested platforms verified."
