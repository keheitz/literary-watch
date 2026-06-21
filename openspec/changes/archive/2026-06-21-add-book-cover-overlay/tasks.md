## 1. Font resource

- [x] 1.1 Download IM Fell English (OFL) to `resources/fonts/IMFellEnglish-Regular.ttf` with `OFL.txt` license
- [x] 1.2 Register `FONT_IM_FELL_28` and `FONT_IM_FELL_18` in `package.json` with `characterRegex` subset; confirm `pebble build` rasterizes both on all platforms

## 2. Health data plumbing

- [x] 2.1 Declare the `health` capability in `package.json`
- [x] 2.2 Add static buffers for the formatted date, step count, and heart-rate strings
- [x] 2.3 Add a `refresh_cover_data()` helper that formats the date and, under `#if defined(PBL_HEALTH)`, reads steps via `health_service_sum_today(HealthMetricStepCount)`
- [x] 2.4 Read heart rate via `health_service_peek_current_value(HealthMetricHeartRateBPM)`, gated on `health_service_metric_accessible(...)` and a non-zero value; leave the HR string empty when unavailable
- [x] 2.5 Subscribe to `health_service_events_subscribe` to refresh steps/HR; call `refresh_cover_data()` and mark `s_bg_layer` dirty when in `STATE_SKY`
- [x] 2.6 Update `tick_handler` to refresh the date and trigger a redraw when the day changes in `STATE_SKY`

## 3. Book-cover rendering

- [x] 3.1 Add cover layout helpers that position the title line, author/metadata line, and footer within `page_frame`/`text_frame` (respecting round and B/W insets)
- [x] 3.2 In `bg_update_proc`'s `STATE_SKY` branch, draw the date as the title-style line using `graphics_draw_text` with `FONT_IM_FELL_28`
- [x] 3.3 Draw steps and heart rate as the author-style / metadata line in `FONT_IM_FELL_18`; render heart rate as numeric BPM only ("72 BPM"), omitting it cleanly and re-centering when absent
- [x] 3.4 Set contrasting text color per `PBL_IF_COLOR_ELSE` so the overlay reads against every sky scene
- [x] 3.5 Ensure the overlay is drawn only in `STATE_SKY` (not in the quote branch)

## 4. Verification

- [x] 4.1 Build for all target platforms with `pebble build`
- [x] 4.2 Install on the emery emulator and screenshot the resting screen; confirm date + steps + heart rate render in book-cover layout with IM Fell English
- [x] 4.3 Screenshot a non-HRM target (e.g. basalt) and confirm heart rate is omitted with the layout intact
- [x] 4.4 Screenshot the chalk (round) emulator and confirm the overlay fits the circular frame
- [x] 4.5 Tap to reveal a quote and confirm the overlay disappears, then fades back correctly
