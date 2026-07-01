## Context

The watchface reveals a literary quote on a wrist tap via `accel_tap_service` (`src/c/literary-watch.c:349`, handler at `:261`). On the Pebble Time 2 (emery) this is effectively unusable: the accelerometer tap threshold is miscalibrated for the hardware, so only a forceful slap registers — a gentle tap or wrist flick does nothing. Exploration established the root cause: the app is listening to the wrong sensor. The PT2's gentle "Touch" feature (Settings → Display → Touch) is a *capacitive touchscreen* exposed via the SDK 4.9+ `TouchService`, a completely separate API the app does not use.

Constraints:
- Must remain a watchface (`"watchface": true` is a hard requirement). This rules out buttons entirely — Up/Down are reserved for the timeline and watchfaces do not receive button events.
- Battery matters: continuous raw `accel_data_service` sampling was considered and rejected for power cost. `TouchService` is event-driven and cheap.
- Multi-platform: only emery (PT2) has a touchscreen among the supported targets (aplite, basalt, chalk, diorite, emery, flint).

## Goals / Non-Goals

**Goals:**
- A gentle tap on the screen reveals the quote on touch-capable hardware.
- A tap (or double-tap) dismisses the quote early, with the ~20s auto-fade kept as a backstop.
- Non-touch platforms still surface quotes (auto-reveal on quarter-hour) so behavior degrades gracefully.
- No battery regression vs. the current tap-service approach.

**Non-Goals:**
- No change to quote selection, sky rendering, cover overlay, or the auto-fade duration.
- No swipe/scroll/positional touch UI — only tap/double-tap gestures.
- Not converting the app to a watchapp, and not using buttons.
- Not keeping the re-roll feature.

## Decisions

**Decision: Use `TouchService` instead of `accel_tap_service` for the reveal.**
Touch is the sensor the user is actually trying to use, it responds to a light tap, and it is event-driven (no battery cost). Alternatives considered: (a) custom raw-accel threshold via `accel_data_service` — rejected for battery drain and because it works around, rather than uses, the intended sensor; (b) buttons — impossible on a watchface; (c) keeping `accel_tap_service` — this is the broken status quo.

**Decision: Derive tap/double-tap from low-level touch events.**
`TouchService` reports primitives only — `TouchEvent_Touchdown`, `TouchEvent_PositionUpdate`, `TouchEvent_Liftoff` (each with x/y) — not gestures. A "tap" is a touchdown→liftoff with little movement within a short time; a "double-tap" is two taps within a timing window. The reveal/dismiss model only needs a single tap, so initial implementation can treat any quick touchdown→liftoff as a tap. Double-tap is optional polish if single-tap dismiss proves too easy to trigger accidentally.

**Decision: `PBL_TOUCH` compile-time guard with an auto-reveal fallback.**
Touch code compiles only where the touchscreen exists. Non-touch platforms reuse the existing `tick_handler` (`:271`), which already detects slot changes, to auto-reveal the quote when the quarter-hour turns, then auto-fade. This keeps a single binary behaving sensibly everywhere.

**Decision: Remove the `s_variant` re-roll state.**
Per the user, re-roll is not worth keeping. A second tap now dismisses. Quote selection collapses to the first deterministic option for the slot.

## Risks / Trade-offs

- **Docs contradict on watchface touch support** → The PT2 user help says watchfaces can use the touchscreen; the developer guide says touch is "not supported in watchfaces." Mitigation: a throwaway spike (task #1) — a minimal watchface that subscribes to `touch_service` and vibrates on `TouchEvent_Touchdown` — gates all touch work. If touch does not fire on a watchface window, every platform falls back to auto-reveal and the touch path is abandoned.
- **Accidental dismiss / reveal from incidental touches** → Tap detection uses a short touchdown→liftoff window with a small movement tolerance; double-tap can be required for dismiss if single-tap is too sensitive in practice.
- **Auto-reveal feels intrusive on non-touch platforms** → It reuses the existing 20s auto-fade, so a quote appears briefly each quarter-hour and clears itself; acceptable for an ambient quote face.
- **SDK 4.9+ requirement** → `touch_service_is_enabled()` and `PBL_TOUCH` guard against building/running where unsupported.

## Migration Plan

1. Spike: confirm touch fires on a watchface window (gates the rest).
2. If confirmed: implement `TouchService` reveal/dismiss under `PBL_TOUCH`; wire auto-reveal fallback for non-touch builds; remove `accel_tap_service` and `s_variant`.
3. If not confirmed: ship auto-reveal for all platforms; remove `accel_tap_service` and `s_variant`.

Rollback: revert to the `accel_tap_service` reveal (current `main`); no persisted state or resource changes are involved.

## Open Questions

- Does touch fire on a watchface window on PT2? (Resolved by the spike.)
- Single-tap dismiss vs. required double-tap — decide after feeling it on-device.
