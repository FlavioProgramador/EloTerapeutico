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

test("detalhes do paciente minimizam dados por padrão", async () => {
  const patient = await source("./src/app/dashboard/patients/[id]/page.tsx");

  assert.match(patient, /patient\.masked_cpf \|\| maskCpf/);
  assert.match(patient, /maskEmail\(patient\.email\)/);
  assert.match(patient, /maskPhone\(patient\.phone\)/);
  assert.match(patient, /maskAddress\(address\)/);
  assert.match(patient, /maskDate\(patient\.birth_date\)/);
  assert.doesNotMatch(patient, /value=\{patient\.phone\}/);
  assert.doesNotMatch(patient, /value=\{patient\.email\}/);
  assert.doesNotMatch(patient, /text-\[(?:9|10|11)px\]/);
});

test("modal de canais não exibe erros internos diretamente", async () => {
  const modal = await source(
    "./src/features/communications/channel-configuration-modal.tsx",
  );

  assert.match(modal, /getPublicErrorMessage/);
  assert.match(modal, /getPublicIntegrationError/);
  assert.doesNotMatch(modal, /last_error\.message/);
  assert.doesNotMatch(modal, /Object\.values\(response/);
  assert.doesNotMatch(modal, /backend está na versão/);
  assert.doesNotMatch(modal, /text-\[(?:9|10|11)px\]/);
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

  assert.match(utilities, /getPublicErrorMessage/);
  assert.doesNotMatch(utilities, /response\?\.data/);
  assert.doesNotMatch(utilities, /firstErrorMessage/);
});
