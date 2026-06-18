## Context

`literary-watch` is an empty Pebble SDK scaffold targeting six platforms (aplite, basalt, chalk, diorite, emery, flint). We are building a "book that tells the time" watchface: an ambient time-of-day sky by default, with a public-domain literary quote revealed on a wrist tap.

Key platform constraints that shape the design:
- **Watchfaces cannot capture buttons.** Buttons are reserved by the system; only the accelerometer (tap/shake) and sensors are available. This is why the reveal trigger is a tap, not a button — and why the project stays `"watchface": true`.
- **Tight memory on small platforms.** aplite/diorite have very little RAM; resources live in flash and must be loaded one at a time.
- **256-resource limit**, and per-platform resource file variants share a single resource ID.
- Displays vary in **color depth** (1-bit vs 64-color) and **shape** (chalk is round). Flint's display capability is undocumented.

Coverage and sizing were validated against the real dataset during exploration: SFW-only, quarter-hour bucketed, 96/96 slots covered; keeping the 3 shortest quotes per slot ≈ 67 KB of packed text.

## Goals / Non-Goals

**Goals:**
- A glanceable watchface with a sky resting state and tap-to-reveal literary quote.
- Quarter-hour ("close enough") time mapping with guaranteed full coverage.
- Fully bundled/offline; no phone dependency.
- One art system that adapts to color depth and screen shape across all six platforms.
- A reproducible build step that turns the public-domain dataset into the packed resource.

**Non-Goals:**
- Minute-level precision (deferred; quarter-hour only).
- Phone-side (PebbleKit JS) quote delivery — explicitly out of scope, but the data layer stays swappable so it can be added later to reach all 1440 minutes.
- Configurable settings UI, multiple themes, or quote favoriting.

## Decisions

### State machine: two states driven by tap + timer
`SKY` (resting) ⇄ `QUOTE` (revealed). Tap in `SKY` → `QUOTE`. Tap in `QUOTE` → re-roll + restart timer. 20 s timer in `QUOTE` with no tap → `SKY`. A minute tick keeps the sky scene and current slot current.
- *Alternative considered*: continuous auto-show of quotes (no tap). Rejected — loses the deliberate "turn the page" gesture and drains attention/battery.

### Trigger: accelerometer tap service
Use `accel_tap_service_subscribe`. It is low-power, event-driven, and one of the few input channels available to a watchface.
- *Alternative*: shake/flick via raw accel sampling. Rejected — higher power and more false positives than the tap service.

### Time mapping: round-to-nearest-quarter → slot index 0..95
`slot = round((h*60+m)/15) mod 96`. Sky band derived from the hour (6 bands). "Close enough" is a deliberate product stance, and rounding is what guarantees 96/96 coverage (each slot absorbs ±7 min of source quotes).

### Data pipeline: build-time packing, runtime indexed read
A build-time script (`tools/build_quotes.py`) fetches the public-domain dataset, filters to SFW, buckets to quarter-hours, keeps the 3 shortest per slot, and emits:
- a **packed blob** resource: concatenated `quote\0title\0author\0` records, and
- an **index** (96 entries → offset + count) at the head of the blob.
At runtime the watchface reads only the requested slot's records from flash into a small buffer — never the whole corpus.
- *Alternative*: one resource file per quote. Rejected — burns the 256-resource budget and is slower to manage.
- *Alternative*: phone-delivered quotes. Deferred (Non-Goal) but the lookup is abstracted behind a `quote_for_slot(slot, date)` function so the source can change without touching rendering.

### Per-day selection: deterministic hash of date
`pick = (day_of_year + slot) mod count`. Stable for the whole day, rotates across days, no RNG state to persist.

### Rendering & fit: prefer shortest, scroll on overflow
Records are pre-sorted shortest-first at build time, so the runtime simply takes the date-selected record and measures it. If it fits the page area, draw statically; if not, drive a slow vertical auto-scroll via `ScrollLayer` or an animated `text_layer` offset. Scroll stops/resets on fade.

### Art selection: capability-driven, not platform-driven
Use `PBL_IF_COLOR_ELSE`/`PBL_COLOR` to choose kids-color vs woodcut assets, and `PBL_ROUND`/`PBL_IF_ROUND_ELSE` for layout. ~6 sky scenes × style variants are provided as **per-platform resource files under shared resource IDs**, so the build picks the right file. **This resolves the flint unknown**: whatever flint's real display is, it gets the correct style automatically.
- *Alternative*: `#if defined(PBL_PLATFORM_*)` per platform. Rejected — brittle, and would force a guess about flint.

## Risks / Trade-offs

- **Quote length vs. small screens** → Build step keeps only the 3 shortest per slot and sorts shortest-first; runtime falls back to auto-scroll so even a long survivor is readable.
- **Flint display capability unknown** → Capability-driven asset selection means no code path depends on knowing it; verify visually on the flint emulator during implementation.
- **1-bit sky art is hard** → The woodcut/engraving style is chosen specifically because dithered line-art reads well on 1-bit and suits the "old book" theme.
- **Dataset licensing/availability at build time** → Quotes are public domain; the fetched dataset (and its SFW flags) is checked into the repo so builds are reproducible offline and don't depend on a live URL.
- **Resource/RAM pressure on aplite/diorite** → Text is read one slot at a time; only one sky bitmap is loaded at a time; total text ≈ 67 KB lives in flash, not RAM.
- **Tap false positives / battery** → Use the built-in tap service (debounced, low-power) rather than raw sampling; the 20 s timer bounds active-render time.

## Migration Plan

Greenfield — no existing behavior to migrate. Rollout is simply building and installing the watchface. Rollback is removing it; there is no persisted state or external system. Future enhancement (phone-side full-1440 corpus) slots in behind the existing `quote_for_slot` abstraction without changing the rendering or state machine.

## Open Questions

- Final visual treatment of the six sky scenes (palette, sun/moon/star motifs) for both styles — to be settled with screenshots during implementation.
- Exact round-display book-frame composition for chalk.
- Whether to gently animate the sky→quote transition (cross-fade) or hard-cut, within the 20 s reveal window.
