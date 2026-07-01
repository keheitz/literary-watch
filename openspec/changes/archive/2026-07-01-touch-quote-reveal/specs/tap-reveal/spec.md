## MODIFIED Requirements

### Requirement: Reveal quote on tap

The watchface SHALL automatically reveal the current slot's quote when the quarter-hour slot changes while in the resting (sky) state, without requiring any user input. The watchface SHALL NOT depend on the accelerometer tap service or the touch service for the reveal.

**Note**: A spike on physical Pebble Time 2 (emery) hardware confirmed `TouchService` does not deliver touch events to a watchface window — a tap wakes the backlight (a system-level gesture) but the app's `touch_service_subscribe` handler never fires. This matches the developer docs' statement that touch is "intentionally restricted to watchapps." All platforms, including emery, therefore use the auto-reveal-on-quarter-hour behavior; there is no touch-capable code path.

#### Scenario: Auto-reveal on quarter-hour (all platforms)

- **WHEN** the watchface is showing the sky and the quarter-hour slot changes
- **THEN** the quote for the new slot is revealed automatically without user input

## REMOVED Requirements

### Requirement: Re-roll on re-tap

**Reason**: The re-roll feature is being dropped at the user's request; the reveal is no longer gesture-driven at all (see above), so there is no re-tap to re-roll on.

**Migration**: None. The `s_variant` re-roll state is removed; quote selection for a slot is deterministic for the first option only.
