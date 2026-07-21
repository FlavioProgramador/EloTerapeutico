import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function source(path) {
  return readFile(path, "utf8");
}

test("landing mantém o laranja como ação principal", async () => {
  const landing = await source("./src/features/landing/styles/landing.css");
  const hero = await source("./src/features/landing/styles/hero-main.css");

  assert.match(landing, /--primary:\s*31 67% 50%/);
  assert.match(landing, /--ring:\s*31 67% 50%/);
  assert.match(hero, /background:\s*hsl\(var\(--primary\)\)/);
  assert.match(hero, /color:\s*hsl\(var\(--primary-foreground\)\)/);
  assert.doesNotMatch(hero, /color:\s*#fff/i);
});

test("navegação não utiliza pessoa fictícia como fallback", async () => {
  const sidebar = await source("./src/components/navigation/sidebar.tsx");

  assert.doesNotMatch(sidebar, /Juliana Martins/);
  assert.match(sidebar, /\|\| "Usuário"/);
  assert.doesNotMatch(sidebar, /text-\[(?:9|10|11)px\]/);
});

test("cadastro usa BFF e não persiste tokens no navegador", async () => {
  const register = await source("./src/app/register/page.tsx");
  const authService = await source(
    "./src/features/auth/services/auth.service.ts",
  );

  assert.match(register, /authService\.register/);
  assert.match(register, /safeInternalPath/);
  assert.doesNotMatch(register, /persistAuthTokens|persistAuthRole/);
  assert.doesNotMatch(register, /localStorage|sessionStorage/);
  assert.doesNotMatch(register, /response\.data\.tokens/);
  assert.match(authService, /"\/api\/auth\/register\/"/);
});

test("detalhes e listas de pacientes minimizam dados por padrão", async () => {
  const patient = await source("./src/app/dashboard/patients/[id]/page.tsx");
  const list = await source(
    "./src/features/patients/components/patient-list-panel.tsx",
  );
  const detailPanel = await source(
    "./src/features/patients/components/patient-detail-panel.tsx",
  );
  const sidePanel = await source(
    "./src/features/patients/components/patient-side-panel.tsx",
  );

  assert.match(patient, /patient\.masked_cpf \|\| maskCpf/);
  assert.match(patient, /maskEmail\(patient\.email\)/);
  assert.match(patient, /maskPhone\(patient\.phone\)/);
  assert.match(patient, /maskAddress\(address\)/);
  assert.match(patient, /maskDate\(patient\.birth_date\)/);
  assert.match(list, /maskEmail\(patient\.email\)/);
  assert.match(list, /maskPhone\(patient\.phone\)/);
  assert.match(detailPanel, /maskEmail\(patient\.email\)/);
  assert.match(detailPanel, /maskPhone\(patient\.phone\)/);
  assert.match(sidePanel, /maskEmail\(patient\.email\)/);
  assert.match(sidePanel, /maskPhone\(patient\.phone\)/);
  assert.doesNotMatch(detailPanel, /latest_evolution\.summary/);
  assert.doesNotMatch(detailPanel, /document\.name/);
  assert.doesNotMatch(patient, /value=\{patient\.phone\}/);
  assert.doesNotMatch(patient, /value=\{patient\.email\}/);
  for (const content of [patient, list, detailPanel, sidePanel]) {
    assert.doesNotMatch(content, /text-\[(?:9|10|11)px\]/);
  }
});

test("prontuário usa tokens semânticos e tipografia legível", async () => {
  const overview = await source(
    "./src/features/records/components/record-overview.tsx",
  );

  assert.doesNotMatch(overview, /text-\[(?:9|10|11)px\]/);
  assert.doesNotMatch(overview, /(?:emerald|sky|violet|cyan|lime|rose)-/);
  assert.doesNotMatch(overview, /bg-gradient/);
  assert.match(overview, /bg-primary-soft/);
  assert.match(overview, /bg-success-soft/);
});

test("canais e notificações não exibem conteúdo interno diretamente", async () => {
  const modal = await source(
    "./src/features/communications/channel-configuration-modal.tsx",
  );
  const page = await source(
    "./src/features/communications/communications-page.tsx",
  );
  const bell = await source(
    "./src/features/communications/notification-bell.tsx",
  );

  assert.match(modal, /getPublicErrorMessage/);
  assert.match(modal, /getPublicIntegrationError/);
  assert.match(page, /getPublicIntegrationError/);
  assert.match(page, /maskRecipient/);
  assert.doesNotMatch(modal, /last_error\.message/);
  assert.doesNotMatch(page, /last_error\.message/);
  assert.doesNotMatch(modal, /Object\.values\(response/);
  assert.doesNotMatch(modal, /backend está na versão/);
  assert.doesNotMatch(bell, /notification\.message/);
  assert.doesNotMatch(bell, /notification\.title/);
  for (const content of [modal, page, bell]) {
    assert.doesNotMatch(content, /text-\[(?:9|10|11)px\]/);
  }
});

test("providers não suprimem globalmente erros do console", async () => {
  const providers = await source("./src/providers/providers.tsx");

  assert.doesNotMatch(providers, /console\.error\s*=/);
  assert.match(providers, /process\.env\.NODE_ENV === "development"/);
});

test("erros de comunicação usam a política pública central", async () => {
  const utilities = await source(
    "./src/features/communications/communications.utils.ts",
  );
  const shared = await source("./src/lib/utils.ts");

  assert.match(utilities, /getPublicErrorMessage/);
  assert.doesNotMatch(utilities, /response\?\.data/);
  assert.doesNotMatch(utilities, /firstErrorMessage/);
  assert.match(shared, /getPublicErrorMessage/);
  assert.doesNotMatch(shared, /response\.data/);
});
