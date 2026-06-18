#include "sky.h"

SkyBand band_for_hour(int hour) {
  if (hour >= 5 && hour <= 6)   return BAND_DAWN;
  if (hour >= 7 && hour <= 10)  return BAND_MORNING;
  if (hour >= 11 && hour <= 13) return BAND_MIDDAY;
  if (hour >= 14 && hour <= 17) return BAND_AFTERNOON;
  if (hour >= 18 && hour <= 20) return BAND_DUSK;
  return BAND_NIGHT;  // 21:00 - 04:59
}

uint32_t sky_resource_for_band(SkyBand band) {
  switch (band) {
    case BAND_DAWN:      return RESOURCE_ID_SKY_DAWN;
    case BAND_MORNING:   return RESOURCE_ID_SKY_MORNING;
    case BAND_MIDDAY:    return RESOURCE_ID_SKY_MIDDAY;
    case BAND_AFTERNOON: return RESOURCE_ID_SKY_AFTERNOON;
    case BAND_DUSK:      return RESOURCE_ID_SKY_DUSK;
    case BAND_NIGHT:
    default:             return RESOURCE_ID_SKY_NIGHT;
  }
}
