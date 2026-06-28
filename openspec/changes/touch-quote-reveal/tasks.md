## 1. Spike: confirm touch on a watchface (GATING)

- [ ] 1.1 Search the appstore / community (Discord, forum) for an existing **watchface** (not a watchapp) that uses `touch_service_subscribe` — the example touch apps (Mini Golf Touch, BreakerBrick, Calculator) are watchapps and do NOT answer whether touch works on a watchface window
- [ ] 1.2 If a touch watchface exists: install it on the PT2 (emery) and confirm a gentle screen tap registers — this directly proves watchfaces can use touch
- [ ] 1.3 If none exists (fallback): build a throwaway watchface that calls `touch_service_subscribe` and `vibes_short_pulse()` on `TouchEvent_Touchdown` (guarded by `PBL_TOUCH`), install on emery, and confirm a gentle tap fires the handler
- [ ] 1.4 Record the result and decide the path: touch fires on a watchface → do sections 2–4; touch does not fire → skip section 2 and ship auto-reveal (section 3) for all platforms

## 2. Touch reveal/dismiss (touch platforms)

- [ ] 2.1 Subscribe to `TouchService` in `init` and unsubscribe in `deinit`, guarded by `PBL_TOUCH`; remove `accel_tap_service_subscribe`/`unsubscribe`
- [ ] 2.2 Implement a touch handler that derives a "tap" from `TouchEvent_Touchdown` → `TouchEvent_Liftoff` within a short time and small movement tolerance
- [ ] 2.3 On tap in the sky (resting) state, reveal the current slot's quote
- [ ] 2.4 On tap while a quote is shown, dismiss back to the sky (cancel the auto-fade timer)
- [ ] 2.5 (Optional) Require a double-tap for dismiss if single-tap proves too easy to trigger by accident

## 3. Auto-reveal fallback (non-touch platforms)

- [ ] 3.1 In `tick_handler`, on a quarter-hour slot change while in the sky state, reveal the new slot's quote automatically (compile this path for non-`PBL_TOUCH` builds)
- [ ] 3.2 Confirm the existing ~20s auto-fade returns the watchface to the sky

## 4. Remove re-roll and old tap path

- [ ] 4.1 Remove the `s_variant` re-roll state and the re-tap re-roll branch in the old `tap_handler`
- [ ] 4.2 Remove `accel_tap_service` usage entirely; ensure quote selection uses the single deterministic option per slot

## 5. Verify

- [ ] 5.1 Build for all platforms (`pebble build`) and confirm no `PBL_TOUCH`/SDK 4.9 compile errors
- [ ] 5.2 On emery (PT2): gentle tap reveals; tap again dismisses; quote auto-fades after ~20s with no input
- [ ] 5.3 On a non-touch platform (e.g. basalt emulator): quote auto-reveals on quarter-hour change and auto-fades; no reliance on tap
- [ ] 5.4 `pebble screenshot --scale 6` to confirm the reveal/sky states render correctly
