# cover-overlay Specification

## Purpose
Display an at-rest information overlay — date, step count, and heart rate — laid out and typeset like a book cover, drawn over the sky scene within the book-page frame, degrading gracefully when health data is unavailable.
## Requirements
### Requirement: Cover overlay on the resting screen

The resting (sky) state SHALL display an information overlay showing the current date, today's step count, and the wearer's heart rate, drawn on top of the sky scene within the book-page frame.

#### Scenario: Overlay visible at rest

- **WHEN** the watchface is in the resting sky state
- **THEN** the date and step count are displayed over the sky scene within the book-page frame

#### Scenario: Overlay hidden while a quote is shown

- **WHEN** a quote is revealed
- **THEN** the cover overlay is not displayed

#### Scenario: Overlay restored on fade back

- **WHEN** the quote view fades back to the sky
- **THEN** the cover overlay is displayed again with current values

### Requirement: Heart rate shown only when available

The overlay SHALL display heart rate only when the device exposes a valid heart-rate reading. On devices without a heart-rate sensor, or before a reading is available, the overlay SHALL omit the heart rate without leaving an empty placeholder or misaligned layout.

#### Scenario: Heart rate available

- **WHEN** the device reports a valid current heart-rate value
- **THEN** the heart rate is displayed in the overlay

#### Scenario: No heart-rate sensor

- **WHEN** the device has no heart-rate sensor
- **THEN** the overlay omits heart rate and the remaining elements stay correctly laid out

#### Scenario: Sensor present but no reading yet

- **WHEN** the device has a heart-rate sensor but no valid reading is available
- **THEN** the overlay omits heart rate until a reading becomes available

### Requirement: Book-cover layout and typography

The overlay elements SHALL be arranged as a book cover — a prominent title-style line and a supporting author-style line — rather than a flat row of statistics, and SHALL be rendered in a book/serif-style font consistent with the watchface aesthetic. The layout SHALL fit within the existing book-page frame insets on rectangular, round, and black-and-white displays.

#### Scenario: Book-cover arrangement

- **WHEN** the overlay is displayed
- **THEN** its elements are arranged in a book-cover layout using book typography, not a flat stats row

#### Scenario: Round display layout

- **WHEN** the watchface runs on a round display
- **THEN** the overlay is laid out within the circular book-page frame without clipping

### Requirement: Overlay reflects current values

The overlay SHALL keep its date, step count, and heart rate current as the underlying values change while the resting screen is shown.

#### Scenario: Date advances at midnight

- **WHEN** the date changes while the resting screen is displayed
- **THEN** the overlay updates to show the new date

#### Scenario: Steps accumulate during the day

- **WHEN** the step count increases while the resting screen is displayed
- **THEN** the overlay reflects the updated step count on the next refresh
