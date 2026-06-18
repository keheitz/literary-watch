## Why

The current project is an empty scaffold. We want to turn it into a watchface with a point of view: a "book that tells the time." Inspired by Christian Marclay's *The Clock*, it tells time through public-domain literary quotes that name the current hour — an ambient, glanceable experience by default, with the literary payoff revealed on demand.

## What Changes

- Convert the empty scaffold into a working watchface (stays a watchface — `"watchface": true` — so it can be the user's default clock; the accelerometer, not buttons, drives interaction).
- **Resting state**: render a book-page frame containing a time-of-day **sky illustration** (6 scenes: dawn, morning, midday, afternoon, dusk, night) selected by the current time.
- **On tap**: a wrist tap reveals a literary quote whose stated time matches the current **quarter-hour** (rounded, "close enough"), with author and book attribution, then **auto-fades back to the sky after 20 seconds**. Tapping again while a quote is shown re-rolls to another option for that slot.
- **Data**: bundle an on-watch corpus derived from the public-domain literary-clock dataset — **SFW-only**, bucketed into the 96 quarter-hour slots, keeping the **3 shortest** quotes per slot (~67 KB). Coverage is 96/96. The selected quote for a slot is chosen **deterministically by date** (random-per-day) so it is stable all day but varies across days.
- **Display fit**: prefer the shortest fitting quote; if even the shortest overflows the screen, **slowly auto-scroll** it.
- **Art direction by platform capability** (not a hardcoded platform list): color-capable displays get a **kids-illustration** style; black-and-white displays get a **woodcut/engraving** style; round displays (chalk) get a distinct circular layout.
- Phone-side (PebbleKit JS) delivery is explicitly **out of scope** but the data layer is designed so it can later scale to all 1440 minutes without redesign.

## Capabilities

### New Capabilities
- `quote-data`: The bundled quote corpus — sourcing from the public-domain dataset, SFW filtering, quarter-hour bucketing, shortest-3-per-slot selection, deterministic-by-date pick, and the packed on-watch storage format + index.
- `quote-display`: Rendering the current quote with attribution inside the book-page frame, including the prefer-shortest fit rule and slow auto-scroll fallback for overflow.
- `time-of-day-sky`: The ambient resting view — mapping current time to one of 6 sky scenes, and selecting art style (kids-color vs woodcut-b&w) and layout (rectangular vs round) by display capability.
- `tap-reveal`: The accelerometer tap interaction — reveal quote on tap, auto-fade back to sky after 20 s, re-roll on re-tap.

### Modified Capabilities
<!-- None: this is a greenfield watchface; there are no existing specs to modify. -->

## Impact

- **App type**: remains a watchface (`package.json` `"watchface": true`).
- **Source**: new C in `src/c/` (state machine, rendering, quote lookup, accel handling).
- **Resources**: new packed quote data blob + index (~67 KB text, 1–2 resource IDs); ~6 sky illustration resource IDs using per-platform file variants. Well under the 256-resource limit.
- **Build tooling**: a build-time script to fetch/filter/bucket/pack the dataset into the resource blob.
- **Platforms**: aplite, basalt, chalk, diorite, emery, flint — style/layout selected via `PBL_COLOR`/`PBL_IF_COLOR_ELSE` and `PBL_ROUND` rather than per-platform conditionals, so flint resolves correctly regardless of its (undocumented) display capability.
- **Dependencies**: none beyond the Pebble SDK; dataset is public domain.
