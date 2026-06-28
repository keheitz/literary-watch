## Why

On the Pebble Time 2 (emery) the quote reveal is effectively unusable: the watchface listens for an **accelerometer** tap (`accel_tap_service`), whose firmware threshold is miscalibrated on PT2 hardware — neither a hard tap nor a wrist flick reliably fires it, only a forceful "slap." The device's actual gentle-touch capability is a *separate* capacitive touchscreen exposed via the SDK 4.9+ `TouchService` API, which this app does not use at all. Switching to the touch sensor gives the light-tap reveal users expect, with no battery cost (touch is event-driven, unlike continuous raw-accelerometer sampling).

## What Changes

- Replace the reveal trigger: drop `accel_tap_service`; use `TouchService` (`touch_service_subscribe`) on touch-capable platforms so a **gentle tap on the glass** reveals the quote.
- Add a **dismiss gesture**: a tap (or double-tap) while a quote is shown returns to the sky, instead of waiting for the auto-fade. The ~20s auto-fade is retained as a backstop.
- **BREAKING (behavior)**: Remove the **re-roll on re-tap** behavior (the `s_variant` re-roll). A second tap now dismisses rather than showing another quote from the slot.
- Platform guard with `PBL_TOUCH`: non-touch platforms (aplite, basalt, chalk, diorite, flint) fall back to **auto-reveal on the quarter-hour** — the quote surfaces on its own when the slot changes (the existing `tick_handler` already detects slot changes), then auto-fades.
- Remains a watchface (`"watchface": true` is a hard requirement); buttons are not an option (Up/Down are reserved for the timeline and watchfaces do not receive button events).

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `tap-reveal`: The reveal trigger changes from accelerometer tap to capacitive touch (touch platforms) or automatic reveal on quarter-hour change (non-touch platforms); a tap/double-tap dismiss gesture is added; the re-roll-on-re-tap requirement is removed.

## Impact

- **Code**: `src/c/literary-watch.c` — `tap_handler` (:261), the `accel_tap_service_subscribe`/`unsubscribe` calls (:349, :358), and the `s_variant` re-roll state. New touch handler + tap/double-tap derivation from raw `TouchEvent` (`Touchdown`/`Liftoff`/`PositionUpdate`); auto-reveal path wired into `tick_handler` (:271) for non-touch builds.
- **APIs**: New dependency on `TouchService` (SDK 4.9+, `PBL_TOUCH`). Removes dependency on `accel_tap_service`.
- **Risk (gating)**: The docs contradict each other on whether a **watchface** may use touch — the PT2 user help says watchfaces can; the developer guide says touch is "not supported in watchfaces." This must be confirmed by a throwaway spike before implementing the touch path; if touch does not fire on a watchface window, all platforms fall back to auto-reveal.
- **Platforms**: emery (PT2) gets touch; aplite/basalt/chalk/diorite/flint get auto-reveal. No change to quote selection, sky rendering, or cover overlay.
