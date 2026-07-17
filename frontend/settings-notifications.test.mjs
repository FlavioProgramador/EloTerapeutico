import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function source(path) {
  return readFile(path, "utf8");
}

test("configurações usam services e BFF sem Web Storage", async () => {
  const page = await source("./src/features/settings/settings-page.tsx");
  const service = await source("./src/features/settings/settings.service.ts");

  assert.match(page, /usePracticeSettings/);
  assert.match(page, /useNotificationPreferences/);
  assert.doesNotMatch(page, /api\.|axios|fetch\(/);
  assert.doesNotMatch(page + service, /localStorage|sessionStorage/);
  assert.match(service, /auth\/settings\//);
  assert.match(service, /auth\/working-hours\//);
  assert.match(service, /auth\/sessions\//);
});

test("central de notificações mantém ações e filtros no service", async () => {
  const page = await source("./src/features/communications/notifications-page.tsx");
  const service = await source("./src/features/communications/communications.service.ts");
  const bell = await source("./src/features/communications/notification-bell.tsx");

  assert.match(page, /Não lidas/);
  assert.match(page, /Arquivadas/);
  assert.match(page, /useArchiveNotification/);
  assert.match(service, /unread-count/);
  assert.match(service, /archive-read/);
  assert.match(service, /notifications\/preferences/);
  assert.match(bell, /99\+/);
  assert.doesNotMatch(page + bell, /dangerouslySetInnerHTML/);
});
