#!/usr/bin/env bash
#
# verify-screenshot.sh — reproducible single-flow Pebble emulator verification.
#
# Boots a clean emulator for one platform, installs the freshly-built app, and
# captures a screenshot. Handles the two flaky failure modes seen on this SDK:
#   1. Boot hangs at "Waiting for the firmware to boot." -> corrupted SPI flash;
#      fixed by deleting qemu_spi_flash.bin so it re-extracts from the SDK.
#   2. Screenshot TimeoutError -> only screenshot AFTER a genuine
#      "App install succeeded"; gate on that line and retry with bounds.
#
# Usage:
#   scripts/verify-screenshot.sh <platform> [--tap] [--out FILE]
#
#   <platform>   emery | basalt | chalk | diorite | aplite | flint | gabbro
#   --tap        accelerometer-tap before the shot (reveals the quote screen)
#   --out FILE   output png (default: ./verify-<platform>.png)
#
# Exit code 0 on a saved screenshot, non-zero otherwise. Every step prints
# progress, so a hang is always visible at the step it occurs.

set -uo pipefail

SDK_VER="4.9.169"
PLATFORM="${1:-emery}"
shift || true

TAP=0
OUT=""
while [ $# -gt 0 ]; do
  case "$1" in
    --tap) TAP=1 ;;
    --out) shift; OUT="${1:-}" ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
  shift || true
done
OUT="${OUT:-$(pwd)/verify-${PLATFORM}.png}"

STATE_DIR="$HOME/Library/Application Support/Pebble SDK/${SDK_VER}/${PLATFORM}"
INSTALL_LOG="/tmp/verify_install_${PLATFORM}.log"
SHOT_LOG="/tmp/verify_shot_${PLATFORM}.log"

log() { printf '%s %s\n' "$(date +%H:%M:%S)" "$*"; }

teardown() {
  pebble kill                       >/dev/null 2>&1
  pkill -9 -f qemu-pebble           >/dev/null 2>&1
  pkill -9 -f pypkjs                >/dev/null 2>&1
  pkill -9 -f "pebble install"      >/dev/null 2>&1
  pkill -9 -f "pebble screenshot"   >/dev/null 2>&1
  pkill -9 -f "pebble emu-tap"      >/dev/null 2>&1
  sleep 2
}

reset_flash() {
  # The boot-hang fix: drop the persisted (possibly corrupted) flash + caches.
  # They are re-created fresh from the SDK's qemu_spi_flash.bin.bz2 on next boot.
  rm -f  "${STATE_DIR}/qemu_spi_flash.bin" "${STATE_DIR}/timeline.db"
  rm -rf "${STATE_DIR}/app_cache"
}

# Run an install in the background, polling its log for a genuine result.
# Returns: 0 succeeded | 2 TimeoutError | 3 boot hang | 4 overall timeout
do_install() {
  rm -f "$INSTALL_LOG"
  # -vv is essential: plain `pebble install` buffers stdout when not on a TTY,
  # so a boot hang produces an EMPTY log and is indistinguishable from progress.
  # -vv streams the emulator/pypkjs markers we poll on.
  nohup pebble install --emulator "$PLATFORM" -vv > "$INSTALL_LOG" 2>&1 &
  local e=0 limit=150
  while [ $e -lt $limit ]; do
    if grep -qi "App install succeeded" "$INSTALL_LOG" 2>/dev/null; then return 0; fi
    if grep -qi "TimeoutError"          "$INSTALL_LOG" 2>/dev/null; then return 2; fi
    # Boot hang: firmware-wait was printed but the app never became Ready ~40s in.
    # Catch it early so we reset the flash and retry instead of blocking 150s.
    if [ $e -ge 40 ] \
       && grep -qi "Waiting for the firmware to boot" "$INSTALL_LOG" 2>/dev/null \
       && ! grep -qi "Ready. Loaded apps" "$INSTALL_LOG" 2>/dev/null; then
      return 3
    fi
    sleep 3; e=$((e+3))
  done
  return 4
}

# Send an accelerometer tap, bounded. The tap event fires over the connection
# shortly after connecting; the client itself can hang on a post-tap confirm
# (like `install` does), so we cap it and then force-kill it. Crucially the
# emu-tap client must be dead before we screenshot, or its lingering connection
# wedges the single qemu control channel (every shot then TimeoutErrors).
do_tap() {
  rm -f "/tmp/verify_tap_${PLATFORM}.log"
  nohup pebble emu-tap --emulator "$PLATFORM" --direction x+ \
        > "/tmp/verify_tap_${PLATFORM}.log" 2>&1 &
  local tpid=$! e=0
  while [ $e -lt 12 ]; do
    kill -0 "$tpid" 2>/dev/null || break
    sleep 1; e=$((e+1))
  done
  kill -9 "$tpid"               >/dev/null 2>&1
  pkill -9 -f "pebble emu-tap"  >/dev/null 2>&1
  sleep 2
}

# Take a screenshot with a bounded wait, retrying a few times.
screenshot() {
  local out="$1" tries=0
  while [ $tries -lt 4 ]; do
    tries=$((tries+1))
    pkill -9 -f "pebble screenshot" >/dev/null 2>&1; sleep 1
    rm -f "$out" "$SHOT_LOG"
    nohup pebble screenshot --emulator "$PLATFORM" --no-open "$out" > "$SHOT_LOG" 2>&1 &
    local spid=$! e=0
    while [ $e -lt 30 ]; do
      if [ -f "$out" ] && grep -qi "Saved screenshot" "$SHOT_LOG" 2>/dev/null; then
        return 0
      fi
      kill -0 "$spid" 2>/dev/null || break   # client exited (likely TimeoutError)
      sleep 1; e=$((e+1))
    done
    kill -9 "$spid" >/dev/null 2>&1
    log "    screenshot attempt ${tries} did not return; retrying…"
  done
  return 1
}

# ---- flow ------------------------------------------------------------------

log "[1/4] Teardown of any running emulator/clients…"
teardown

log "[2/4] Install on ${PLATFORM} (boots emulator)…"
do_install; rc=$?
if [ $rc -eq 3 ]; then
  log "    boot hung at firmware -> resetting SPI flash and retrying…"
  teardown; reset_flash; do_install; rc=$?
elif [ $rc -ne 0 ]; then
  log "    install stalled (rc=${rc}) -> teardown + flash reset + retry…"
  teardown; reset_flash; do_install; rc=$?
fi
if [ $rc -ne 0 ]; then
  log "FAIL: install did not reach 'App install succeeded' (rc=${rc})"
  grep -iv "gevent\|geventwebsocket\|^DEBUG" "$INSTALL_LOG" 2>/dev/null | tail -8
  exit 1
fi
log "    App install succeeded."
sleep 3   # let the install client exit and the connection settle

if [ $TAP -eq 1 ]; then
  log "[3/4] Accelerometer tap (reveal quote)…"
  do_tap
else
  log "[3/4] (no tap — resting screen)"
fi

log "[4/4] Screenshot -> ${OUT}"
if screenshot "$OUT"; then
  log "OK: saved ${OUT} ($(stat -f%z "$OUT" 2>/dev/null) bytes)"
  exit 0
fi
log "FAIL: screenshot did not complete after retries"
grep -iv "gevent\|^DEBUG\|File \"\|~~~\|\^\^" "$SHOT_LOG" 2>/dev/null | tail -6
exit 1
