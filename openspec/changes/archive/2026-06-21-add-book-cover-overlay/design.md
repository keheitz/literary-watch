## Context

The watchface has two states (`literary-watch.c`): `STATE_SKY` (resting) and `STATE_QUOTE`. `bg_update_proc` on `s_bg_layer` draws the sky bitmap plus the book-page frame in the resting state, and a quote page in the quote state. The resting state draws no text today. This change adds a book-cover overlay (date, steps, heart rate) to the resting state only.

Health data comes from the Pebble `HealthService`. Steps are broadly available; heart rate exists only on HRM-equipped models (diorite, emery) and requires both the `PBL_HEALTH` build capability and a runtime availability check. Targets without health support must still build and render the overlay.

## Goals / Non-Goals

**Goals:**
- Show date, steps, and (when available) heart rate on the resting screen in a book-cover layout.
- Degrade gracefully when heart rate — or HealthService entirely — is unavailable.
- Keep the overlay confined to `STATE_SKY`; reuse the existing frame/inset helpers so round and B/W layouts stay correct.

**Non-Goals:**
- No new health screens, history, or goals UI.
- No change to quote selection, the sky scenes, or the tap-to-reveal flow.
- No always-on tap-to-cycle for stats; the overlay is passive.

## Decisions

- **Draw the overlay inside `bg_update_proc`, not as separate TextLayers.** The resting frame is already a custom-drawn layer; rendering the cover text with `graphics_draw_text` in the same update proc keeps state handling simple (no layers to show/hide) and guarantees it only appears in `STATE_SKY`. Alternative — dedicated `TextLayer`s toggled by state — adds lifecycle and hidden-flag bookkeeping for no visual gain.
- **Guard all health code behind `#if defined(PBL_HEALTH)`** and gate heart rate additionally on `health_service_metric_accessible(HealthMetricHeartRateBPM, ...)` / a non-zero `health_service_peek_current_value`. This satisfies "heart rate only when available" and keeps non-health targets compiling. Steps via `health_service_sum_today(HealthMetricStepCount)`.
- **Cache formatted strings (date, steps, HR) in static buffers, refreshed on `MINUTE_UNIT` tick and on health events.** Subscribe to `health_service_events_subscribe` for step/HR updates; reuse the existing `tick_handler` for the date. Avoids formatting on every redraw. Alternative — read live in the update proc — risks doing service calls during rendering.
- **Book-cover layout = title line + author line + footer.** Map the date to the title-style line (largest), steps/heart rate to an author-style / metadata line. Positioned within `page_frame`/`text_frame` insets so it tracks the existing round and B/W layouts.
- **Bundle IM Fell English (SIL OFL) as the serif resource** rather than a system font. It is a digitization of the 17th-century Fell types (Oxford University Press), giving the authentic antique-book-cover feel the system Gothic/serif fonts lack. Registered in `package.json` at two rasterized sizes — `FONT_IM_FELL_28` (date/title) and `FONT_IM_FELL_18` (metadata) — with a `characterRegex` of `[ -~—]` to subset to printable ASCII + em dash and keep flash usage small (notably for aplite's 128KB resource budget). License text lives at `resources/fonts/OFL.txt`.
- **Heart rate is numeric BPM only** — the value followed by a "BPM" label, no glyph — keeping the metadata line short and legible on small/round screens.
- **Declare the `health` capability in `package.json`** so HealthService returns data; without it steps/HR read as unavailable.

## Risks / Trade-offs

- **Text over the sky bitmap may have low contrast** → draw on a translucent/again-framed band or use a contrasting text color per `PBL_IF_COLOR_ELSE`, verified against each sky scene in the emulator.
- **Health permission denied or data sparse** → the availability checks already collapse the overlay to date + steps (or date only); ensure layout re-centers rather than leaving gaps.
- **HRM polling battery cost** → rely on cached/peeked values from health events rather than requesting continuous high-rate sampling.
- **Crowding on small/round screens** → keep to two short lines plus a footer; measure with `graphics_text_layout_get_content_size` and shrink the font tier if it overflows the frame.

## Open Questions

- ~~Bundle a dedicated serif font resource, or ship with a system font?~~ **Resolved:** bundle IM Fell English (OFL) at `FONT_IM_FELL_28` / `FONT_IM_FELL_18`.
- ~~Heart rate units/label: numeric BPM only, or with a small glyph?~~ **Resolved:** numeric BPM only.
- Are the two chosen point sizes (28 / 18) right for the cover proportions on emery and chalk, or does the title want to be larger? To confirm visually during apply.
