import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const featureBase = new URL(
  "./src/features/telemedicine/",
  import.meta.url,
);

async function read(relativePath) {
  return readFile(new URL(relativePath, featureBase), "utf8");
}

test("convite público é lido do fragmento e removido imediatamente", async () => {
  const source = await read("components/patient-telemedicine-flow.tsx");

  assert.match(source, /window\.location\.hash/);
  assert.match(source, /window\.history\.replaceState/);
  assert.match(source, /#token=/, "o fluxo não deve reconstruir o token na URL");
  assert.doesNotMatch(source, /searchParams\.get\(["']token["']\)/);
});

test("feature não persiste convite JWT ou chave E2EE no navegador", async () => {
  const files = [
    "services/telemedicine.service.ts",
    "components/patient-telemedicine-flow.tsx",
    "components/professional-telemedicine-flow.tsx",
    "components/telemedicine-session.tsx",
  ];
  const source = (await Promise.all(files.map(read))).join("\n");

  for (const forbidden of ["localStorage", "sessionStorage", "indexedDB"]) {
    assert.equal(source.includes(forbidden), false, forbidden);
  }
});

test("sala exige E2EE e não habilita gravação chat ou tela", async () => {
  const source = await read("components/telemedicine-session.tsx");

  assert.match(source, /ExternalE2EEKeyProvider/);
  assert.match(source, /livekit-client\/e2ee-worker/);
  assert.match(source, /setE2EEEnabled\(true\)/);
  assert.match(source, /screenShare: false/);
  assert.match(source, /chat: false/);
  assert.doesNotMatch(source, /MediaRecorder/);
  assert.doesNotMatch(source, /recording|egress/i);
});

test("cleanup interrompe tracks sala e worker", async () => {
  const source = await read("components/telemedicine-session.tsx");

  assert.match(source, /publication\.track\?\.stop\(\)/);
  assert.match(source, /nextRoom\.disconnect\(\)/);
  assert.match(source, /worker\.terminate\(\)/);
});

test("painel não recebe links persistidos do paciente ou profissional", async () => {
  const source = await readFile(
    new URL(
      "./src/features/agenda/components/telemedicine-panel.tsx",
      import.meta.url,
    ),
    "utf8",
  );

  assert.doesNotMatch(source, /patient_link/);
  assert.doesNotMatch(source, /professional_link/);
  assert.match(source, /createInvitation/);
  assert.match(source, /revokeInvitation/);
});

test("BFF libera somente operações públicas explícitas", async () => {
  const source = await readFile(
    new URL("./src/app/api/backend/[...path]/route.ts", import.meta.url),
    "utf8",
  );
  const allowed = ["exchange", "consent", "join", "leave"];

  for (const action of allowed) {
    assert.match(
      source,
      new RegExp(`scheduling/telemedicine/public/${action}`),
    );
  }
  assert.doesNotMatch(source, /scheduling\/telemedicine\/public\/\*+/);
  assert.match(source, /isTrustedRequestOrigin/);
});
