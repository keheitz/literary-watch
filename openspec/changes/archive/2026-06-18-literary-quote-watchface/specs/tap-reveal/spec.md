## ADDED Requirements

### Requirement: Reveal quote on tap

The watchface SHALL listen for an accelerometer tap while in the resting (sky) state, and on tap SHALL transition to showing the literary quote for the current quarter-hour slot.

#### Scenario: Tap reveals quote

- **WHEN** the watchface is showing the sky and the user taps the wrist
- **THEN** the quote for the current slot is revealed

### Requirement: Auto-fade after 20 seconds

After a quote is revealed, the watchface SHALL automatically return to the sky resting state 20 seconds later if no further interaction occurs.

#### Scenario: Quote fades back to sky

- **WHEN** a quote has been displayed for 20 seconds with no further tap
- **THEN** the watchface returns to the sky resting state

### Requirement: Re-roll on re-tap

When the user taps again while a quote is already displayed, the watchface SHALL replace it with another quote from the same slot (if the slot holds more than one) and SHALL restart the 20-second fade timer.

#### Scenario: Re-tap shows another quote

- **WHEN** a quote is displayed and the slot holds more than one quote and the user taps again
- **THEN** a different quote from the same slot is shown
- **AND** the 20-second auto-fade timer restarts

#### Scenario: Re-tap with single-quote slot

- **WHEN** a quote is displayed, the slot holds only one quote, and the user taps again
- **THEN** the same quote remains shown
- **AND** the 20-second auto-fade timer restarts
