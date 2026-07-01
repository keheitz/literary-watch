# quote-data Specification

## Purpose
TBD - created by archiving change literary-quote-watchface. Update Purpose after archive.
## Requirements
### Requirement: SFW public-domain corpus

The watchface SHALL bundle a quote corpus derived from the public-domain literary-clock dataset, including only entries flagged safe-for-work (`sfw`). Each entry SHALL retain its quote text, book title, and author.

#### Scenario: Non-SFW entries excluded

- **WHEN** the corpus is built from the source dataset
- **THEN** every entry flagged non-SFW MUST be excluded
- **AND** only entries with title and author present are kept

### Requirement: Quarter-hour bucketing with full coverage

Each source quote's stated time SHALL be rounded to the nearest quarter-hour (`:00`, `:15`, `:30`, `:45`, wrapping across midnight) and assigned to that slot. The corpus SHALL provide at least one quote for all 96 quarter-hour slots.

#### Scenario: Time rounds to nearest quarter

- **WHEN** a source quote states the time `03:47`
- **THEN** it is assigned to the `03:45` slot

#### Scenario: Every slot is covered

- **WHEN** the corpus build completes
- **THEN** each of the 96 quarter-hour slots MUST contain at least one quote

### Requirement: Shortest-three selection per slot

For each slot the corpus SHALL keep at most the three shortest quotes (by rendered character length). Slots with fewer than three available quotes SHALL keep all of them.

#### Scenario: Slot with many candidates

- **WHEN** a slot has more than three candidate quotes
- **THEN** only the three with the shortest quote text are retained

#### Scenario: Slot with few candidates

- **WHEN** a slot has two candidate quotes
- **THEN** both are retained

### Requirement: Deterministic-by-date selection

When a slot holds more than one quote, the watchface SHALL select one deterministically from the current calendar date, so the choice is stable for the whole day and varies across days.

#### Scenario: Stable within a day

- **WHEN** the same slot is shown twice on the same date
- **THEN** the same quote is selected both times

#### Scenario: Varies across days

- **WHEN** the same multi-quote slot is shown on two different dates
- **THEN** the selection MAY differ, cycling through that slot's quotes over successive days

### Requirement: Packed on-watch storage format

The corpus SHALL be stored as a packed binary resource with an index allowing O(1) lookup of a slot's quotes without loading the entire corpus into memory. The packed text SHALL fit comfortably within platform resource limits (target ≤ ~70 KB).

#### Scenario: Single-slot lookup

- **WHEN** the watchface requests the quotes for a given slot
- **THEN** only that slot's entries are read from the resource into memory

### Requirement: Abbreviation-aware sentence boundaries

When mining a candidate quote from a source text, sentence-boundary
detection SHALL NOT treat the period following a common abbreviation
(including but not limited to "Mr.", "Mrs.", "Ms.", "Dr.", "St.", "Prof.",
"Rev.", "Jr.", "Sr.") as the end of the sentence. The mined quote SHALL
extend to the next true sentence-ending punctuation.

#### Scenario: Title abbreviation mid-sentence

- **WHEN** the source text contains `...and Mrs. Bridgenorth arrived at two o'clock.`
- **THEN** the mined quote extends through `arrived at two o'clock.`
- **AND** the quote does not end at `Mrs.`

#### Scenario: Abbreviation at a real sentence end

- **WHEN** the source text contains a time mention whose sentence
  genuinely ends right after an abbreviation-like token that is not in
  the known abbreviation list (e.g. ends in `etc.`)
- **THEN** the mined quote may end there, since only the listed
  abbreviations are excluded from boundary detection

### Requirement: No abbreviation-truncated quotes in shipped corpus

The corpus build SHALL flag any retained quote whose text ends
immediately after a known title abbreviation, as a regression guard
against truncated fragments reaching the shipped resource.

#### Scenario: Truncated fragment detected at build time

- **WHEN** a quote selected for packing ends with a known abbreviation
  token (e.g. `"...Mrs."`) followed by nothing else
- **THEN** the build SHALL report it so it can be excluded or repaired
  before shipping

