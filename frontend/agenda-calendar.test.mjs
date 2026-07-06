import test from "node:test";
import assert from "node:assert/strict";
import {
  addDays,
  buildMonthDays,
  endOfWeek,
  isSameDay,
  periodBounds,
  rangesOverlap,
  startOfDay,
  startOfWeek,
  toDateInput,
} from "./src/features/agenda/lib/calendar.mjs";
import { transactionSchema } from "./src/features/financeiro/schemas/transaction.schemas.ts";
import {
  APPOINTMENT_STATUS_LABELS,
  PATIENT_STATUS_LABELS,
  QUERY_KEYS,
  ROLE_LABELS,
  ROUTES,
  TRANSACTION_STATUS_LABELS,
} from "./src/constants/index.ts";
import {
  cn,
  extractApiError,
  formatCurrency,
  formatDate,
  formatTime,
  getInitials,
  truncate,
} from "./src/lib/utils.ts";


test("month grid has six complete weeks", () => {
  const days = buildMonthDays(new Date(2026, 5, 15));
  assert.equal(days.length, 42);
  assert.equal(days[0].getDay(), 0);
  assert.equal(days[41].getDay(), 6);
});


test("calendar helpers cover day, week and month bounds", () => {
  const value = new Date(2026, 5, 29, 14, 30);
  const dayStart = startOfDay(value);
  const weekStart = startOfWeek(value);
  const weekEnd = endOfWeek(value);

  assert.equal(dayStart.getHours(), 0);
  assert.equal(addDays(dayStart, 1).getDate(), 30);
  assert.ok(isSameDay(weekStart, new Date(2026, 5, 28)));
  assert.ok(isSameDay(weekEnd, new Date(2026, 6, 4)));
  assert.equal(isSameDay(value, addDays(value, 1)), false);
  assert.equal(toDateInput(value), "2026-06-29");

  assert.equal(periodBounds(value, "month").start.getDate(), 1);
  assert.ok(isSameDay(periodBounds(value, "week").end, new Date(2026, 6, 4)));
  assert.equal(periodBounds(value, "day").end.getHours(), 23);
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


test("shared helpers handle valid and invalid values", () => {
  assert.match(formatCurrency(1234.5), /1\.234,50/);
  assert.equal(formatCurrency("x"), "R$ 0,00");
  assert.notEqual(formatDate("2026-07-05T12:00:00Z"), "—");
  assert.equal(formatDate("x"), "—");
  assert.equal(formatTime("09:30:00"), "09:30");
  assert.equal(formatTime(""), "—");
  assert.equal(truncate("texto curto", 20), "texto curto");
  assert.equal(truncate("texto muito longo", 10), "texto muit…");
  assert.equal(getInitials("Flávio Marques"), "FM");
  assert.equal(getInitials("Elo"), "E");
  assert.equal(getInitials(""), "?");
  assert.equal(cn("px-2", "px-4"), "px-4");
});


test("API errors use the supported public envelopes", () => {
  assert.equal(extractApiError({ response: { data: "Mensagem" } }), "Mensagem");
  assert.equal(
    extractApiError({ response: { data: { detail: "Detalhe" } } }),
    "Detalhe",
  );
  assert.equal(
    extractApiError({ response: { data: { error: { message: "Envelope" } } } }),
    "Envelope",
  );
  assert.equal(
    extractApiError({ response: { data: { non_field_errors: ["Geral"] } } }),
    "Geral",
  );
  assert.equal(
    extractApiError({ response: { data: { amount: ["Inválido"] } } }),
    "amount: Inválido",
  );
  assert.match(extractApiError({}), /inesperado/);
});


test("global constants expose stable keys for all domains", () => {
  assert.deepEqual(QUERY_KEYS.patient(7), ["patients", 7]);
  assert.deepEqual(QUERY_KEYS.appointment(8), ["appointments", 8]);
  assert.deepEqual(QUERY_KEYS.record(9), ["records", 9]);
  assert.deepEqual(QUERY_KEYS.transaction(10), ["transactions", 10]);
  assert.deepEqual(QUERY_KEYS.documentTemplates, ["documents", "templates"]);
  assert.equal(PATIENT_STATUS_LABELS.active, "Ativo");
  assert.equal(APPOINTMENT_STATUS_LABELS.completed, "Realizado");
  assert.equal(TRANSACTION_STATUS_LABELS.overdue, "Vencido");
  assert.equal(ROLE_LABELS.therapist, "Terapeuta");
  assert.equal(ROUTES.documents, "/dashboard/documentos");
});


test("financial schema validates success and boundary cases", () => {
  const payload = {
    description: "Sessão fictícia",
    amount: "150,00",
    type: "income",
    category: "session",
    status: "pending",
    due_date: "2026-07-10",
    payment_method: "pix",
    notes: "",
  };

  assert.equal(transactionSchema.safeParse(payload).success, true);
  assert.equal(transactionSchema.safeParse({ ...payload, amount: "0" }).success, false);
  assert.equal(transactionSchema.safeParse({ ...payload, due_date: "x" }).success, false);
  assert.equal(transactionSchema.safeParse({ ...payload, description: "" }).success, false);
});
