## Why

The resting sky screen currently shows only the time-of-day scene and the book-page frame — it conveys no glanceable information until the wearer taps to reveal a quote. Surfacing the date and live health stats (steps, and heart rate where the hardware supports it) makes the resting screen useful at a glance, and presenting them in a book-cover layout reinforces the "a book that tells the time" concept.

## What Changes

- Add a glanceable information overlay to the resting (sky) state showing the **date**, **step count**, and **heart rate**.
- Lay the overlay out like a **book cover**: a title-style line, an author-style line, and supporting metadata arranged with book typography rather than a flat stats row.
- Render the overlay in a **book/serif-style font** consistent with the watchface's literary aesthetic.
- Show **heart rate only when available** — on devices without a heart-rate sensor (or before a reading exists), the overlay omits it gracefully without leaving a gap.
- Keep the overlay confined to the resting state; tapping to reveal a quote hides it, and fading back restores it.

## Capabilities

### New Capabilities
- `cover-overlay`: A book-cover-styled information overlay on the resting sky screen that displays the date, step count, and (when available) heart rate using book typography.

### Modified Capabilities
<!-- No existing requirements change. time-of-day-sky still governs which sky scene
     is shown and the book-page frame; this overlay is layered on top of it. -->

## Impact

- **Code**: `src/c/literary-watch.c` — the `STATE_SKY` rendering path (`bg_update_proc`) gains overlay drawing; new health data reads and a date string buffer; layout helpers for the cover regions.
- **Services**: Adds a dependency on the Pebble `HealthService` (steps via `health_service_sum_today`, heart rate via `health_service_peek_current_value`), guarded by `PBL_HEALTH` / heart-rate availability checks.
- **Config**: `package.json` may need the `health` capability declared so HealthService data is accessible.
- **Platforms**: Heart rate is only present on HRM-equipped models (e.g. diorite, emery); all targets must still render the overlay without it. Round (chalk) and black-and-white displays must lay the cover out within their existing frame insets.
