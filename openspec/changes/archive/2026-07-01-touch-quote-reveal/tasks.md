## 1. Spike: confirm touch on a watchface (GATING)

- [x] 1.1 Search the appstore / community (Discord, forum) for an existing **watchface** (not a watchapp) that uses `touch_service_subscribe` — the example touch apps (Mini Golf Touch, BreakerBrick, Calculator) are watchapps and do NOT answer whether touch works on a watchface window. *No confirmed touch watchface found via web search.*
- [x] 1.2 (n/a — no existing touch watchface found; see 1.3)
- [x] 1.3 Docs review found the developer guide explicitly states touch is "intentionally restricted to watchapps" / "not supported in watchfaces," while a Core Devices blog post describes *planned future* "complications" support — a contradiction the spec called out. Per user decision, skipped the disposable throwaway-app spike and went straight to implementing the real touch reveal/dismiss code below; the user will tap-test it on their physical PT2.
- [x] 1.4 Decision: implemented sections 2–4 for real and confirmed on the physical PT2 (see 5.2 result) — **touch does not reach the watchface app**: a tap wakes the backlight (system-level gesture) but `touch_handler` never fires. Per user decision, the `PBL_TOUCH` code path was removed entirely and auto-reveal (section 3) now runs on all platforms including emery.

## 2. Touch reveal/dismiss (touch platforms) — ABANDONED

- [x] 2.1 Subscribed `TouchService` in `init`/`deinit` guarded by `PBL_TOUCH`; removed `accel_tap_service_subscribe`/`unsubscribe`. **Reverted**: confirmed on real PT2 hardware that touch never reaches the watchface app, so this whole section was removed after 5.2 testing.
- [x] 2.2 Implemented a touch handler deriving a tap from `TouchEvent_Touchdown` → `TouchEvent_Liftoff`. **Reverted** (see 2.1).
- [x] 2.3 Reveal-on-tap in sky state. **Reverted** (see 2.1).
- [x] 2.4 Dismiss-on-tap while a quote is shown. **Reverted** (see 2.1) — the ~20s auto-fade is now the only path back to the sky on every platform.
- [x] 2.5 N/A — no touch path remains to require double-tap tuning.

## 3. Auto-reveal fallback (now universal, all platforms)

- [x] 3.1 In `tick_handler`, on a quarter-hour slot change while in the sky state, reveal the new slot's quote automatically — now unconditional (no `PBL_TOUCH` guard), since touch never fires on any watchface
- [x] 3.2 Confirmed the existing ~20s auto-fade returns the watchface to the sky — verified on basalt emulator (state cycled sky → quote → fade → sky → next-slot quote) and structurally unchanged for emery

## 4. Remove re-roll and old tap path

- [x] 4.1 Remove the `s_variant` re-roll state and the re-tap re-roll branch in the old `tap_handler`
- [x] 4.2 Remove `accel_tap_service` usage entirely; ensure quote selection uses the single deterministic option per slot

## 5. Verify

- [x] 5.1 Build for all platforms (`pebble build`) and confirm no compile errors — clean build (including a forced `pebble clean` rebuild after an in-session SDK upgrade to 4.17), all 7 platforms
- [x] 5.2 On emery (PT2), tested on the physical device via `pebble install --phone`: a gentle tap only wakes the backlight — the quote never reveals. Confirms touch does not reach the watchface app; touch code removed (see section 2). Auto-reveal is now emery's behavior too.
- [x] 5.3 On a non-touch platform (basalt emulator): quote auto-reveals on quarter-hour change and auto-fades; no reliance on tap — verified
- [x] 5.4 `pebble screenshot` to confirm the reveal/sky states render correctly — verified on basalt and emery
