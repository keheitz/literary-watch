## MODIFIED Requirements

### Requirement: Reveal quote on tap

On platforms with a touchscreen (`PBL_TOUCH`), the watchface SHALL subscribe to the touch service and, while in the resting (sky) state, on a tap of the screen SHALL transition to showing the literary quote for the current quarter-hour slot. On platforms without a touchscreen, the watchface SHALL automatically reveal the current slot's quote when the quarter-hour slot changes, without requiring any user input. The watchface SHALL NOT depend on the accelerometer tap service for the reveal.

#### Scenario: Touch reveals quote (touch platform)

- **WHEN** the watchface is showing the sky on a touch-capable platform and the user taps the screen
- **THEN** the quote for the current slot is revealed

#### Scenario: Auto-reveal on quarter-hour (non-touch platform)

- **WHEN** the watchface is showing the sky on a platform without a touchscreen and the quarter-hour slot changes
- **THEN** the quote for the new slot is revealed automatically without user input

## ADDED Requirements

### Requirement: Dismiss quote on tap

On touch-capable platforms, while a quote is displayed, a tap on the screen SHALL dismiss the quote and return the watchface to the sky resting state before the auto-fade timer elapses.

#### Scenario: Tap dismisses quote

- **WHEN** a quote is displayed on a touch-capable platform and the user taps the screen
- **THEN** the watchface returns to the sky resting state

## REMOVED Requirements

### Requirement: Re-roll on re-tap

**Reason**: The re-roll feature is being dropped at the user's request; a second tap now dismisses the quote instead of showing another quote from the same slot.

**Migration**: None. The `s_variant` re-roll state is removed; quote selection for a slot is deterministic for the first option only.
