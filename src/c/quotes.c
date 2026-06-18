#include "quotes.h"

// Packed resource layout (little-endian; built by tools/build_quotes.py):
//   [ 96 x index entry ]  then  [ records section ]
//   index entry = u16 offset (relative to records section) + u8 count
//   record      = quote '\0' title '\0' author '\0'
#define NUM_SLOTS 96
#define INDEX_ENTRY_BYTES 3
#define INDEX_BYTES (NUM_SLOTS * INDEX_ENTRY_BYTES)

// Largest slot in the bundled corpus is ~727 bytes; keep headroom for rebuilds.
#define SLOT_BUF_SIZE 1280

static ResHandle s_handle;
static size_t s_records_total;  // bytes in the records section

bool quotes_init(void) {
  s_handle = resource_get_handle(RESOURCE_ID_QUOTES_DATA);
  size_t size = resource_size(s_handle);
  if (size <= INDEX_BYTES) {
    return false;
  }
  s_records_total = size - INDEX_BYTES;
  return true;
}

int slot_for_time(int hour, int min) {
  int total = hour * 60 + min;
  // round-to-nearest-quarter via integer math, then wrap into 0..95
  return (((total + 7) / 15) % NUM_SLOTS + NUM_SLOTS) % NUM_SLOTS;
}

// Read one little-endian index entry (offset, count) for `slot`.
static void read_index(int slot, uint16_t *offset, uint8_t *count) {
  uint8_t entry[INDEX_ENTRY_BYTES];
  resource_load_byte_range(s_handle, slot * INDEX_ENTRY_BYTES, entry, sizeof(entry));
  *offset = (uint16_t)(entry[0] | (entry[1] << 8));
  *count = entry[2];
}

// Copy the NUL-terminated string at *cursor into dst (bounded), then advance
// *cursor past the NUL. Returns false if no terminator is found in range.
static bool copy_field(const uint8_t *buf, size_t len, size_t *cursor,
                       char *dst, size_t dst_size) {
  size_t i = 0;
  while (*cursor < len && buf[*cursor] != '\0') {
    if (i + 1 < dst_size) {
      dst[i++] = (char)buf[*cursor];
    }
    (*cursor)++;
  }
  if (*cursor >= len) {
    return false;  // ran off the end without a terminator
  }
  dst[i] = '\0';
  (*cursor)++;  // skip the NUL
  return true;
}

int quote_for_slot(int slot, int day_of_year, int variant, Quote *out) {
  if (slot < 0 || slot >= NUM_SLOTS || !s_handle) {
    return 0;
  }

  uint16_t offset;
  uint8_t count;
  read_index(slot, &offset, &count);
  if (count == 0) {
    return 0;
  }

  // The slot's records run from this offset to the next slot's offset
  // (or the end of the records section for the last slot).
  size_t end;
  if (slot + 1 < NUM_SLOTS) {
    uint16_t next_offset;
    uint8_t next_count;
    read_index(slot + 1, &next_offset, &next_count);
    end = next_offset;
  } else {
    end = s_records_total;
  }

  size_t seg_len = end - offset;
  if (seg_len == 0 || seg_len > SLOT_BUF_SIZE) {
    return 0;
  }

  // Static (not on the stack): Pebble's app stack is ~2 KB, far too small
  // for this buffer.
  static uint8_t buf[SLOT_BUF_SIZE];
  resource_load_byte_range(s_handle, INDEX_BYTES + offset, buf, seg_len);

  // Deterministic per-day pick, advanced by `variant` for re-roll.
  int pick = ((day_of_year + slot + variant) % count + count) % count;

  // Walk records to the picked one (3 fields each).
  size_t cursor = 0;
  for (int r = 0; r < count; r++) {
    if (r == pick) {
      if (!copy_field(buf, seg_len, &cursor, out->text, QUOTE_TEXT_MAX) ||
          !copy_field(buf, seg_len, &cursor, out->title, QUOTE_TITLE_MAX) ||
          !copy_field(buf, seg_len, &cursor, out->author, QUOTE_AUTHOR_MAX)) {
        return 0;
      }
      return count;
    }
    // Skip this record's three fields.
    for (int f = 0; f < 3; f++) {
      while (cursor < seg_len && buf[cursor] != '\0') {
        cursor++;
      }
      if (cursor >= seg_len) {
        return 0;
      }
      cursor++;
    }
  }
  return 0;
}
