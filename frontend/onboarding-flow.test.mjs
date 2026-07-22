import assert from "node:assert/strict";
import test from "node:test";

import {
  buildOnboardingStepPayload,
  getOnboardingStepFields,
  normalizeOnboardingStep,
  onboardingPayloadToForm,
  organizationOnboardingDefaults,
} from "./src/features/organizations/onboarding-flow.ts";
import { mergeActivatedOrganizationContext } from "./src/features/organizations/context-state.ts";

function organization(overrides = {}) {
  return {
    id: "11111111-1111-4111-8111-111111111111",
    name: "Consultório Teste",
    slug: "consultorio-teste",
    legal_name: "",
    organization_type: "individual",
    document: "",
    email: "teste@example.test",
    phone: "21986532547",
    timezone: "America/Sao_Paulo",
    status: "active",
    onboarding_status: "in_progress",
    onboarding_step: 2,
    onboarding_completed_at: null,
    created_at: "2026-07-21T12:00:00Z",
    updated_at: "2026-07-21T12:00:00Z",
    ...overrides,
  };
}

function membership(overrides = {}) {
  return {
    id: "10",
    organization: "11111111-1111-4111-8111-111111111111",
    user_id: 1,
    user_name: "Usuário Teste",
    user_email: "teste@example.test",
    role: "owner",
    status: "active",
    is_default: true,
    joined_at: "2026-07-21T12:00:00Z",
    ...overrides,
  };
}

test("etapa de organização não valida campos das etapas futuras", () => {
  const fields = getOnboardingStepFields(1);

  assert.deepEqual(fields, [
    "name",
    "organization_type",
    "legal_name",
    "document",
    "email",
    "phone",
    "timezone",
  ]);
  assert.equal(fields.includes("display_name"), false);
  assert.equal(fields.includes("default_appointment_duration"), false);
});

test("payload da primeira etapa avança para a etapa dois sem perder dados", () => {
  const form = {
    ...organizationOnboardingDefaults,
    name: "Consultório Teste",
    email: "teste@example.test",
    phone: "21986532547",
  };

  const payload = buildOnboardingStepPayload(1, form);

  assert.equal(payload.step, 2);
  assert.deepEqual(payload.organization, {
    name: "Consultório Teste",
    organization_type: "individual",
    legal_name: "",
    document: "",
    email: "teste@example.test",
    phone: "21986532547",
    timezone: "America/Sao_Paulo",
  });
  assert.equal("professional_profile" in payload, false);
  assert.equal(form.name, "Consultório Teste");
});

test("especialidades são normalizadas no payload do perfil", () => {
  const form = {
    ...organizationOnboardingDefaults,
    display_name: "Profissional Teste",
    specialties_text: " Ansiedade, Terapia de casal, , Ansiedade ",
  };

  const payload = buildOnboardingStepPayload(2, form);

  assert.equal(payload.step, 3);
  assert.deepEqual(payload.professional_profile.specialties, [
    "Ansiedade",
    "Terapia de casal",
    "Ansiedade",
  ]);
});

test("resposta persistida hidrata o formulário e preserva os dados salvos", () => {
  const payload = {
    organization: organization(),
    membership: membership(),
    settings: {
      reminder_hours_before: 48,
      business_name_on_documents: "Consultório Teste",
    },
    professional_profile: {
      display_name: "Profissional Teste",
      specialties: ["Ansiedade", "Terapia de casal"],
      default_session_value: "150.50",
    },
    status: "in_progress",
    step: 2,
    completed_at: null,
  };

  const form = onboardingPayloadToForm(payload, {
    full_name: "Nome da Conta",
    email: "conta@example.test",
  });

  assert.equal(form.name, "Consultório Teste");
  assert.equal(form.email, "teste@example.test");
  assert.equal(form.phone, "21986532547");
  assert.equal(form.display_name, "Profissional Teste");
  assert.equal(form.specialties_text, "Ansiedade, Terapia de casal");
  assert.equal(form.default_session_value, 150.5);
  assert.equal(form.reminder_hours_before, 48);
});

test("etapa recebida do servidor é limitada ao intervalo do onboarding", () => {
  assert.equal(normalizeOnboardingStep(-10), 1);
  assert.equal(normalizeOnboardingStep(4.8), 4);
  assert.equal(normalizeOnboardingStep(99), 6);
  assert.equal(normalizeOnboardingStep("inválido"), 1);
});

test("organização recém-criada é ativada mesmo ausente na lista antiga", () => {
  const oldOrganization = organization({
    id: "22222222-2222-4222-8222-222222222222",
    name: "Organização anterior",
  });
  const newOrganization = organization();
  const newMembership = membership();

  const merged = mergeActivatedOrganizationContext(
    {
      active_organization: oldOrganization,
      active_membership: membership({
        organization: oldOrganization.id,
        is_default: false,
      }),
      organizations: [oldOrganization],
    },
    {
      organization: newOrganization,
      membership: newMembership,
    },
  );

  assert.equal(merged.active_organization?.id, newOrganization.id);
  assert.equal(merged.active_membership?.organization, newOrganization.id);
  assert.deepEqual(
    merged.organizations.map((item) => item.id),
    [newOrganization.id, oldOrganization.id],
  );
});
