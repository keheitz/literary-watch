## ADDED Requirements

### Requirement: Six time-of-day sky scenes

The resting state SHALL display one of six sky scenes — dawn, morning, midday, afternoon, dusk, night — chosen from the current time of day.

#### Scenario: Night scene at midnight

- **WHEN** the current time falls in the night band
- **THEN** the night sky scene is displayed

#### Scenario: Scene updates as time advances

- **WHEN** the current time crosses from one time-of-day band into the next
- **THEN** the displayed sky scene updates to match the new band

### Requirement: Art style selected by display capability

The watchface SHALL select art style from the display's actual capability rather than a hardcoded platform list: color-capable displays SHALL use the kids-illustration style; black-and-white displays SHALL use the woodcut/engraving style.

#### Scenario: Color display uses kids style

- **WHEN** the watchface runs on a color-capable display
- **THEN** the kids-illustration sky art is used

#### Scenario: Black-and-white display uses woodcut style

- **WHEN** the watchface runs on a 1-bit display
- **THEN** the woodcut/engraving sky art is used

### Requirement: Distinct round layout

On round displays the watchface SHALL use a layout designed for the circular screen rather than reusing the rectangular layout.

#### Scenario: Round display layout

- **WHEN** the watchface runs on a round display
- **THEN** the book-page frame and sky are laid out for the circular screen
