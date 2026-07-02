export function startOfDay(value) {
  const date = new Date(value);
  date.setHours(0, 0, 0, 0);
  return date;
}

export function addDays(value, amount) {
  const date = new Date(value);
  date.setDate(date.getDate() + amount);
  return date;
}

export function startOfWeek(value) {
  const date = startOfDay(value);
  date.setDate(date.getDate() - date.getDay());
  return date;
}

export function endOfWeek(value) {
  return addDays(startOfWeek(value), 6);
}

export function buildMonthDays(value) {
  const current = new Date(value);
  const first = new Date(current.getFullYear(), current.getMonth(), 1);
  const gridStart = addDays(first, -first.getDay());
  return Array.from({ length: 42 }, (_, index) => addDays(gridStart, index));
}

export function isSameDay(left, right) {
  const a = new Date(left);
  const b = new Date(right);
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

export function rangesOverlap(startA, endA, startB, endB) {
  return new Date(startA) < new Date(endB) && new Date(endA) > new Date(startB);
}

export function toDateInput(value) {
  const date = new Date(value);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function periodBounds(value, view) {
  const date = new Date(value);
  if (view === "month") {
    return {
      start: new Date(date.getFullYear(), date.getMonth(), 1),
      end: new Date(
        date.getFullYear(),
        date.getMonth() + 1,
        0,
        23,
        59,
        59,
        999,
      ),
    };
  }
  if (view === "week") {
    const start = startOfWeek(date);
    const end = endOfWeek(date);
    end.setHours(23, 59, 59, 999);
    return { start, end };
  }
  const start = startOfDay(date);
  const end = new Date(start);
  end.setHours(23, 59, 59, 999);
  return { start, end };
}
