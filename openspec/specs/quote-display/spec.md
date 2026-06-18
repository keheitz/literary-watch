# quote-display Specification

## Purpose
TBD - created by archiving change literary-quote-watchface. Update Purpose after archive.
## Requirements
### Requirement: Quote rendered with attribution

When a quote is shown, the watchface SHALL render the quote text together with its book title and author, framed as a book page consistent with the active platform style.

#### Scenario: Quote and attribution visible

- **WHEN** a quote is revealed for the current slot
- **THEN** the quote text, book title, and author are all displayed within the book-page frame

### Requirement: Prefer shortest fitting quote

The watchface SHALL display the shortest available quote for the current slot. Selection order SHALL favor quotes whose rendered length fits the screen before longer ones.

#### Scenario: A short quote fits

- **WHEN** the current slot's selected quote fits within the visible page area
- **THEN** it is displayed in full without scrolling

### Requirement: Slow auto-scroll on overflow

When the selected quote is the shortest available yet still exceeds the visible page area, the watchface SHALL slowly auto-scroll the text so the whole quote can be read.

#### Scenario: Overflowing quote scrolls

- **WHEN** the selected quote does not fit the visible page area
- **THEN** the text scrolls slowly and automatically through its full length

#### Scenario: Scroll stops on fade

- **WHEN** the quote view fades back to the sky
- **THEN** any in-progress auto-scroll stops and resets

