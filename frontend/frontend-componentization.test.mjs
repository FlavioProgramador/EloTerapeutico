import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function source(path) {
  return readFile(path, "utf8");
}

function lineCount(content) {
  return content.trimEnd().split("\n").length;
}

test("componentes principais atuam como composição", async () => {
  const appointment = await source(
    "./src/features/agenda/components/appointment-modal.tsx",
  );
  const evolution = await source(
    "./src/features/records/components/evolution-editor-modal.tsx",
  );
  const checkout = await source("./src/features/billing/checkout-wizard.tsx");

  assert.ok(lineCount(appointment) < 130);
  assert.ok(lineCount(evolution) < 140);
  assert.ok(lineCount(checkout) < 190);

  assert.match(appointment, /useAppointmentForm/);
  assert.match(evolution, /useEvolutionEditorController/);
  assert.match(checkout, /useCheckoutWizard/);

  assert.doesNotMatch(appointment, /useQuery|api\./);
  assert.doesNotMatch(evolution, /evolutionModalService|useQuery/);
  assert.doesNotMatch(checkout, /createCheckout|previewCheckout|listPlans/);
});

test("regras sensíveis permanecem nos controllers", async () => {
  const appointment = await source(
    "./src/features/agenda/hooks/use-appointment-form.ts",
  );
  const evolution = await source(
    "./src/features/records/hooks/use-evolution-editor-controller.ts",
  );
  const checkout = await source(
    "./src/features/billing/hooks/use-checkout-wizard.ts",
  );

  assert.match(appointment, /buildAppointmentPayload/);
  assert.match(appointment, /useAvailableSlots/);

  assert.match(evolution, /is_confidential/);
  assert.match(evolution, /uploadAttachment/);
  assert.match(evolution, /invalidateQueries/);
  assert.doesNotMatch(evolution, /eslint-disable/);

  assert.match(checkout, /idempotencyKeyRef/);
  assert.match(checkout, /previewCheckout/);
  assert.match(checkout, /createCheckout/);
});

test("seções extraídas preservam responsabilidades locais", async () => {
  const agendaSection = await source(
    "./src/features/agenda/components/appointment-form/appointment-who-when-section.tsx",
  );
  const recordSection = await source(
    "./src/features/records/components/evolution-editor/evolution-security-section.tsx",
  );
  const checkoutStep = await source(
    "./src/features/billing/checkout/checkout-customer-step.tsx",
  );

  assert.match(agendaSection, /Horários livres sugeridos/);
  assert.match(recordSection, /Marcar como confidencial/);
  assert.match(recordSection, /EvolutionAttachmentDropzone/);
  assert.match(checkoutStep, /CheckoutPlanOptions/);
  assert.match(checkoutStep, /CheckoutCustomerFields/);
  assert.match(checkoutStep, /CheckoutPaymentMethods/);
});
