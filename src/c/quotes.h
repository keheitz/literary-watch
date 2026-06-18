#pragma once
#include <pebble.h>

// One literary quote with its attribution, copied out of the packed resource.
// Field sizes are generous over the largest record in the bundled corpus
// (max single record ~281 bytes; see tools/build_quotes.py output).
#define QUOTE_TEXT_MAX 320
#define QUOTE_TITLE_MAX 128
#define QUOTE_AUTHOR_MAX 96

typedef struct {
  char text[QUOTE_TEXT_MAX];
  char title[QUOTE_TITLE_MAX];
  char author[QUOTE_AUTHOR_MAX];
} Quote;

// Open the packed quote resource. Call once at startup. Returns false if the
// resource is missing or malformed.
bool quotes_init(void);

// Round a wall-clock time to the nearest quarter-hour slot (0..95), wrapping
// across midnight.
int slot_for_time(int hour, int min);

// Fill `out` with a quote for `slot`. The option is chosen deterministically
// from `day_of_year` (stable for a whole day, rotating across days), with
// `variant` advancing to another option for the same slot (used by re-tap).
// Returns the number of options available for the slot (>= 1), or 0 on failure.
int quote_for_slot(int slot, int day_of_year, int variant, Quote *out);
