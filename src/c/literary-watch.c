#include <pebble.h>
#include "quotes.h"
#include "sky.h"

// "A book that tells the time."
//   SKY state   - ambient book page showing the time-of-day sky.
//   QUOTE state - a literary quote naming the current quarter-hour, revealed
//                 on a wrist tap, auto-fading back to the sky after 20s.

#define FADE_TIMEOUT_MS 20000
#define AUTOSCROLL_INTERVAL_MS 110
#define AUTOSCROLL_START_DELAY_MS 1200

typedef enum { STATE_SKY, STATE_QUOTE } AppState;

static Window *s_window;
static Layer *s_bg_layer;          // draws sky or page background + book frame
static ScrollLayer *s_scroll;      // holds the quote text in QUOTE state
static TextLayer *s_quote_layer;
static GBitmap *s_sky_bitmap;

static GFont s_cover_title_font;   // IM Fell English 28 — book "title" line
static GFont s_cover_body_font;    // IM Fell English 18 — date + stats
static char s_cover_title[16];     // weekday, e.g. "Friday"
static char s_cover_date[24];      // e.g. "June 20"
static char s_cover_stats[48];     // e.g. "8432 steps — 72 BPM"

static AppState s_state = STATE_SKY;
static SkyBand s_band;
static int s_slot;
static int s_day;
static int s_variant;              // advances on re-tap to re-roll the quote

static AppTimer *s_fade_timer;
static AppTimer *s_scroll_timer;
static int s_content_h;            // rendered height of current quote text
static int s_page_h;               // visible height of the page area

static Quote s_quote;
static char s_display[QUOTE_TEXT_MAX + QUOTE_TITLE_MAX + QUOTE_AUTHOR_MAX + 16];

// --- layout helpers --------------------------------------------------------

static GRect page_frame(GRect bounds) {
  int inset = PBL_IF_ROUND_ELSE(22, 8);
  return grect_inset(bounds, GEdgeInsets(inset));
}

static GRect text_frame(GRect bounds) {
  return grect_inset(page_frame(bounds), GEdgeInsets(PBL_IF_ROUND_ELSE(10, 6)));
}

// --- rendering -------------------------------------------------------------

static void load_sky_bitmap(void) {
  if (s_sky_bitmap) {
    gbitmap_destroy(s_sky_bitmap);
  }
  s_sky_bitmap = gbitmap_create_with_resource(sky_resource_for_band(s_band));
}

// Draw one centered cover line with a 1px contrasting halo so the text stays
// legible against any sky scene (including the dark night scene).
static void draw_cover_line(GContext *ctx, const char *text, GFont font,
                            GRect box, GColor main, GColor halo) {
  if (!text || !text[0]) {
    return;
  }
  static const GPoint offsets[] = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};
  graphics_context_set_text_color(ctx, halo);
  for (unsigned i = 0; i < ARRAY_LENGTH(offsets); i++) {
    graphics_draw_text(ctx, text, font,
                       GRect(box.origin.x + offsets[i].x,
                             box.origin.y + offsets[i].y, box.size.w, box.size.h),
                       GTextOverflowModeFill, GTextAlignmentCenter, NULL);
  }
  graphics_context_set_text_color(ctx, main);
  graphics_draw_text(ctx, text, font, box, GTextOverflowModeFill,
                     GTextAlignmentCenter, NULL);
}

static void draw_cover_overlay(GContext *ctx, GRect bounds) {
  GRect tf = text_frame(bounds);
  GColor main = PBL_IF_COLOR_ELSE(GColorWhite, GColorBlack);
  GColor halo = PBL_IF_COLOR_ELSE(GColorBlack, GColorWhite);
  int x = tf.origin.x;
  int w = tf.size.w;

  // Book-cover arrangement: big title (weekday), subtitle (date), footer (stats).
  draw_cover_line(ctx, s_cover_title, s_cover_title_font,
                  GRect(x, tf.origin.y + 6, w, 34), main, halo);
  draw_cover_line(ctx, s_cover_date, s_cover_body_font,
                  GRect(x, tf.origin.y + 42, w, 24), main, halo);
  draw_cover_line(ctx, s_cover_stats, s_cover_body_font,
                  GRect(x, tf.origin.y + tf.size.h - 28, w, 24), main, halo);
}

static void bg_update_proc(Layer *layer, GContext *ctx) {
  GRect bounds = layer_get_bounds(layer);
  GRect page = page_frame(bounds);
  int radius = PBL_IF_ROUND_ELSE(0, 6);

  if (s_state == STATE_SKY) {
    // Fill the screen with the sky, then frame it like a book page.
    graphics_context_set_fill_color(ctx, GColorBlack);
    graphics_fill_rect(ctx, bounds, 0, GCornerNone);
    if (s_sky_bitmap) {
      graphics_draw_bitmap_in_rect(ctx, s_sky_bitmap, bounds);
    }
    draw_cover_overlay(ctx, bounds);
  } else {
    // Opaque page so the sky doesn't bleed behind the quote text.
    GColor page_color = PBL_IF_COLOR_ELSE(GColorPastelYellow, GColorWhite);
    graphics_context_set_fill_color(ctx, GColorBlack);
    graphics_fill_rect(ctx, bounds, 0, GCornerNone);
    graphics_context_set_fill_color(ctx, page_color);
    graphics_fill_rect(ctx, page, radius, GCornersAll);
  }

  // Book-page border in both states.
  graphics_context_set_stroke_color(ctx, PBL_IF_COLOR_ELSE(GColorWindsorTan, GColorBlack));
  graphics_context_set_stroke_width(ctx, 2);
  graphics_draw_round_rect(ctx, page, radius);
}

// --- auto-scroll for overflowing quotes ------------------------------------

static void stop_autoscroll(void) {
  if (s_scroll_timer) {
    app_timer_cancel(s_scroll_timer);
    s_scroll_timer = NULL;
  }
}

static void autoscroll_tick(void *data) {
  s_scroll_timer = NULL;
  int min_y = -(s_content_h - s_page_h);
  GPoint off = scroll_layer_get_content_offset(s_scroll);
  if (off.y <= min_y) {
    return;  // reached the end; rest here until fade
  }
  off.y -= 1;
  scroll_layer_set_content_offset(s_scroll, off, false);
  s_scroll_timer = app_timer_register(AUTOSCROLL_INTERVAL_MS, autoscroll_tick, NULL);
}

// --- state transitions -----------------------------------------------------

static void refresh_time_context(void) {
  time_t now = time(NULL);
  struct tm *t = localtime(&now);
  s_slot = slot_for_time(t->tm_hour, t->tm_min);
  s_day = t->tm_yday;
  SkyBand band = band_for_hour(t->tm_hour);
  if (band != s_band || !s_sky_bitmap) {
    s_band = band;
    load_sky_bitmap();
  }
}

// Refresh the cover overlay strings: date always, steps + heart rate when the
// HealthService exposes them. Heart rate is shown as numeric BPM only.
static void refresh_cover_data(void) {
  time_t now = time(NULL);
  struct tm *t = localtime(&now);
  strftime(s_cover_title, sizeof(s_cover_title), "%A", t);
  strftime(s_cover_date, sizeof(s_cover_date), "%B %e", t);

  char steps_str[24] = "";
  char hr_str[16] = "";
#if defined(PBL_HEALTH)
  HealthServiceAccessibilityMask steps_ok =
      health_service_metric_accessible(HealthMetricStepCount,
                                       time_start_of_today(), now);
  if (steps_ok & HealthServiceAccessibilityMaskAvailable) {
    int steps = (int)health_service_sum_today(HealthMetricStepCount);
    snprintf(steps_str, sizeof(steps_str), "%d steps", steps);
  }
  HealthValue bpm = health_service_peek_current_value(HealthMetricHeartRateBPM);
  if (bpm > 0) {
    snprintf(hr_str, sizeof(hr_str), "%d BPM", (int)bpm);
  }
#endif

  // Compose the footer, omitting any missing metric so the line stays centered.
  if (steps_str[0] && hr_str[0]) {
    snprintf(s_cover_stats, sizeof(s_cover_stats), "%s — %s", steps_str, hr_str);
  } else if (steps_str[0]) {
    snprintf(s_cover_stats, sizeof(s_cover_stats), "%s", steps_str);
  } else if (hr_str[0]) {
    snprintf(s_cover_stats, sizeof(s_cover_stats), "%s", hr_str);
  } else {
    s_cover_stats[0] = '\0';
  }
}

static void go_to_sky(void) {
  stop_autoscroll();
  refresh_cover_data();  // show current values when fading back to the sky
  scroll_layer_set_content_offset(s_scroll, GPointZero, false);
  layer_set_hidden(scroll_layer_get_layer(s_scroll), true);
  s_state = STATE_SKY;
  layer_mark_dirty(s_bg_layer);
}

static void fade_timer_cb(void *data) {
  s_fade_timer = NULL;
  go_to_sky();
}

static void restart_fade_timer(void) {
  if (s_fade_timer) {
    app_timer_cancel(s_fade_timer);
  }
  s_fade_timer = app_timer_register(FADE_TIMEOUT_MS, fade_timer_cb, NULL);
}

static void reveal_quote(void) {
  refresh_time_context();

  int count = quote_for_slot(s_slot, s_day, s_variant, &s_quote);
  if (count == 0) {
    return;  // nothing to show; stay in current state
  }

  snprintf(s_display, sizeof(s_display), "%s\n\n— %s, %s",
           s_quote.text, s_quote.author, s_quote.title);

  GRect tf = text_frame(layer_get_bounds(s_bg_layer));
  GFont font = fonts_get_system_font(FONT_KEY_GOTHIC_18);
  GTextAlignment align = PBL_IF_ROUND_ELSE(GTextAlignmentCenter, GTextAlignmentLeft);

  // Measure, then size the text layer to its content for scrolling.
  GSize content = graphics_text_layout_get_content_size(
      s_display, font, GRect(0, 0, tf.size.w, 2000),
      GTextOverflowModeWordWrap, align);
  s_content_h = content.h;
  s_page_h = tf.size.h;

  text_layer_set_text(s_quote_layer, s_display);
  text_layer_set_font(s_quote_layer, font);
  text_layer_set_text_alignment(s_quote_layer, align);
  layer_set_frame(text_layer_get_layer(s_quote_layer), GRect(0, 0, tf.size.w, s_content_h));
  scroll_layer_set_content_size(s_scroll, GSize(tf.size.w, s_content_h));
  scroll_layer_set_content_offset(s_scroll, GPointZero, false);

  s_state = STATE_QUOTE;
  layer_set_hidden(scroll_layer_get_layer(s_scroll), false);
  layer_mark_dirty(s_bg_layer);

  stop_autoscroll();
  if (s_content_h > s_page_h) {
    s_scroll_timer = app_timer_register(AUTOSCROLL_START_DELAY_MS, autoscroll_tick, NULL);
  }

  restart_fade_timer();
}

// --- input & ticks ---------------------------------------------------------

static void tap_handler(AccelAxisType axis, int32_t direction) {
  if (s_state == STATE_SKY) {
    s_variant = 0;
    reveal_quote();
  } else {
    s_variant++;       // re-roll another quote for the same slot
    reveal_quote();    // also restarts the fade timer
  }
}

static void tick_handler(struct tm *tick_time, TimeUnits units_changed) {
  SkyBand band = band_for_hour(tick_time->tm_hour);
  if (band != s_band) {
    s_band = band;
    load_sky_bitmap();
  }
  refresh_cover_data();  // keep the date (and steps) current each minute
  if (s_state == STATE_SKY) {
    layer_mark_dirty(s_bg_layer);
  }
}

#if defined(PBL_HEALTH)
static void health_handler(HealthEventType event, void *context) {
  if (event == HealthEventSignificantUpdate ||
      event == HealthEventMovementUpdate ||
      event == HealthEventHeartRateUpdate) {
    refresh_cover_data();
    if (s_state == STATE_SKY) {
      layer_mark_dirty(s_bg_layer);
    }
  }
}
#endif

// --- window lifecycle ------------------------------------------------------

static void window_load(Window *window) {
  Layer *root = window_get_root_layer(window);
  GRect bounds = layer_get_bounds(root);

  s_bg_layer = layer_create(bounds);
  layer_set_update_proc(s_bg_layer, bg_update_proc);
  layer_add_child(root, s_bg_layer);

  GRect tf = text_frame(bounds);
  s_scroll = scroll_layer_create(tf);
  scroll_layer_set_shadow_hidden(s_scroll, true);
  s_quote_layer = text_layer_create(GRect(0, 0, tf.size.w, tf.size.h));
  text_layer_set_background_color(s_quote_layer, GColorClear);
  text_layer_set_text_color(s_quote_layer, PBL_IF_COLOR_ELSE(GColorDarkGray, GColorBlack));
  scroll_layer_add_child(s_scroll, text_layer_get_layer(s_quote_layer));
  layer_add_child(root, scroll_layer_get_layer(s_scroll));
  layer_set_hidden(scroll_layer_get_layer(s_scroll), true);

  s_cover_title_font = fonts_load_custom_font(resource_get_handle(RESOURCE_ID_FONT_IM_FELL_28));
  s_cover_body_font = fonts_load_custom_font(resource_get_handle(RESOURCE_ID_FONT_IM_FELL_18));

  refresh_time_context();
  refresh_cover_data();
}

static void window_unload(Window *window) {
  stop_autoscroll();
  if (s_fade_timer) {
    app_timer_cancel(s_fade_timer);
  }
  if (s_sky_bitmap) {
    gbitmap_destroy(s_sky_bitmap);
  }
  fonts_unload_custom_font(s_cover_title_font);
  fonts_unload_custom_font(s_cover_body_font);
  text_layer_destroy(s_quote_layer);
  scroll_layer_destroy(s_scroll);
  layer_destroy(s_bg_layer);
}

static void init(void) {
  if (!quotes_init()) {
    APP_LOG(APP_LOG_LEVEL_ERROR, "quote resource failed to load");
  }
  s_window = window_create();
  window_set_window_handlers(s_window, (WindowHandlers) {
    .load = window_load,
    .unload = window_unload,
  });
  window_stack_push(s_window, true);

  accel_tap_service_subscribe(tap_handler);
  tick_timer_service_subscribe(MINUTE_UNIT, tick_handler);
#if defined(PBL_HEALTH)
  health_service_events_subscribe(health_handler, NULL);
#endif
}

static void deinit(void) {
  tick_timer_service_unsubscribe();
  accel_tap_service_unsubscribe();
  window_destroy(s_window);
}

int main(void) {
  init();
  app_event_loop();
  deinit();
}
