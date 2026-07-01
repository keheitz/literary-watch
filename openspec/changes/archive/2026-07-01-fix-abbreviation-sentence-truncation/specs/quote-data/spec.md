## ADDED Requirements

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
