export function startOfDay(value: Date | string): Date;
export function addDays(value: Date | string, amount: number): Date;
export function startOfWeek(value: Date | string): Date;
export function endOfWeek(value: Date | string): Date;
export function buildMonthDays(value: Date | string): Date[];
export function isSameDay(left: Date | string, right: Date | string): boolean;
export function rangesOverlap(
  startA: Date | string,
  endA: Date | string,
  startB: Date | string,
  endB: Date | string,
): boolean;
export function toDateInput(value: Date | string): string;
export function periodBounds(
  value: Date | string,
  view: "day" | "week" | "month",
): { start: Date; end: Date };
