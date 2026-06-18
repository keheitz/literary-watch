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

static void go_to_sky(void) {
  stop_autoscroll();
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
    if (s_state == STATE_SKY) {
      layer_mark_dirty(s_bg_layer);
    }
  }
}

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

  refresh_time_context();
}

static void window_unload(Window *window) {
  stop_autoscroll();
  if (s_fade_timer) {
    app_timer_cancel(s_fade_timer);
  }
  if (s_sky_bitmap) {
    gbitmap_destroy(s_sky_bitmap);
  }
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
