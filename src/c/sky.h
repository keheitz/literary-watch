#pragma once
#include <pebble.h>

// The six time-of-day scenes used for the ambient resting view.
typedef enum {
  BAND_NIGHT = 0,
  BAND_DAWN,
  BAND_MORNING,
  BAND_MIDDAY,
  BAND_AFTERNOON,
  BAND_DUSK,
  BAND_COUNT,
} SkyBand;

// Map an hour (0..23) to its time-of-day band.
SkyBand band_for_hour(int hour);

// Resource id for a band's sky bitmap (the build picks the color/bw variant).
uint32_t sky_resource_for_band(SkyBand band);
