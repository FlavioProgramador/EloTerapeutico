import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

test("tipo de documento inclui estados do scanner e URL opcional", async () => {
  const source = await readFile("./src/features/records/types.ts", "utf8");
  assert.equal(source.includes('"pending"'), true);
  assert.equal(source.includes('"scanning"'), true);
  assert.equal(source.includes('"infected"'), true);
  assert.equal(source.includes('"failed"'), true);
  assert.equal(source.includes("download_url: string | null"), true);
});

test("serviço impede download antes do status clean", async () => {
  const source = await readFile(
    "./src/features/records/services/record-workspace.service.ts",
    "utf8",
  );
  assert.equal(source.includes('document.scan_status !== "clean"'), true);
  assert.equal(source.includes("!document.download_url"), true);
  assert.equal(
    source.includes("O arquivo ainda não está disponível para download."),
    true,
  );
});
