import test from "node:test";
import assert from "node:assert/strict";
import {
  buildMonthDays,
  isSameDay,
  periodBounds,
  rangesOverlap,
  startOfWeek,
} from "./src/features/agenda/lib/calendar.mjs";

test("month grid has six complete weeks", () => {
  const days = buildMonthDays(new Date(2026, 5, 15));
  assert.equal(days.length, 42);
  assert.equal(days[0].getDay(), 0);
  assert.equal(days[41].getDay(), 6);
});

test("week bounds cover Sunday through Saturday", () => {
  const start = startOfWeek(new Date(2026, 5, 29));
  const bounds = periodBounds(new Date(2026, 5, 29), "week");
  assert.ok(isSameDay(start, new Date(2026, 5, 28)));
  assert.ok(isSameDay(bounds.end, new Date(2026, 6, 4)));
});

test("overlap checks interval intersection", () => {
  assert.equal(
    rangesOverlap(
      "2026-06-29T09:00:00",
      "2026-06-29T09:50:00",
      "2026-06-29T09:30:00",
      "2026-06-29T10:00:00",
    ),
    true,
  );
  assert.equal(
    rangesOverlap(
      "2026-06-29T09:00:00",
      "2026-06-29T09:50:00",
      "2026-06-29T09:50:00",
      "2026-06-29T10:30:00",
    ),
    false,
  );
});
