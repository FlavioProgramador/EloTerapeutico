import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  AUTH_GATEWAY_PUBLIC_ERROR,
  csrfTokensMatch,
  gatewayUnavailableLog,
  gatewayUnavailablePayload,
  isTrustedOriginValue,
  sanitizeRequestId,
  shouldUseSecureCookies,
} from "./src/lib/server/auth-bff-policy.ts";

test("cookies de autenticação usam Secure em produção real", () => {
  assert.equal(shouldUseSecureCookies("production", "false", "false"), true);
  assert.equal(shouldUseSecureCookies("production", "true", "false"), true);
  assert.equal(shouldUseSecureCookies("production", "false", "true"), true);
  assert.equal(shouldUseSecureCookies("development", "false", "false"), false);
  assert.equal(shouldUseSecureCookies("test", "false", "false"), false);
});

test("cookies inseguros só podem ser habilitados no E2E do CI", () => {
  assert.equal(shouldUseSecureCookies("production", "true", "true"), false);
  assert.equal(shouldUseSecureCookies("production", "false", "true"), true);
  assert.equal(shouldUseSecureCookies("production", "true", "false"), true);
});

test("request id aceita somente formato seguro e limitado", () => {
  assert.equal(sanitizeRequestId(" request-123 "), "request-123");
  assert.equal(sanitizeRequestId("../../segredo"), null);
  assert.equal(sanitizeRequestId("id com espaço"), null);
  assert.equal(sanitizeRequestId("x".repeat(129)), null);
  assert.equal(sanitizeRequestId(null), null);
});

test("origem explícita deve coincidir com a origem da aplicação", () => {
  assert.equal(
    isTrustedOriginValue(
      "https://app.eloterapeutico.com.br",
      "https://app.eloterapeutico.com.br",
      "cross-site",
    ),
    true,
  );
  assert.equal(
    isTrustedOriginValue(
      "https://externo.example",
      "https://app.eloterapeutico.com.br",
      "same-site",
    ),
    false,
  );
  assert.equal(
    isTrustedOriginValue("origem-inválida", "https://app.example", null),
    false,
  );
});

test("sec-fetch-site permite apenas contextos confiáveis sem Origin", () => {
  assert.equal(isTrustedOriginValue(null, "https://app.example", null), true);
  assert.equal(
    isTrustedOriginValue(null, "https://app.example", "same-origin"),
    true,
  );
  assert.equal(
    isTrustedOriginValue(null, "https://app.example", "same-site"),
    true,
  );
  assert.equal(
    isTrustedOriginValue(null, "https://app.example", "cross-site"),
    false,
  );
});

test("CSRF exige cookie e header presentes e idênticos", () => {
  assert.equal(csrfTokensMatch("token-123", "token-123"), true);
  assert.equal(csrfTokensMatch("token-123", "token-456"), false);
  assert.equal(csrfTokensMatch("curto", "token-mais-longo"), false);
  assert.equal(csrfTokensMatch("", ""), false);
  assert.equal(csrfTokensMatch(null, "token"), false);
  assert.equal(csrfTokensMatch("token", undefined), false);
});

test("payload público do gateway não expõe detalhes internos", () => {
  const payload = gatewayUnavailablePayload("req-123");
  assert.deepEqual(payload, {
    error: AUTH_GATEWAY_PUBLIC_ERROR,
    request_id: "req-123",
  });

  const serialized = JSON.stringify(payload);
  for (const forbidden of [
    "details",
    "stack",
    "cause",
    "BACKEND_API_URL",
    "backend:8000",
    "ECONNREFUSED",
  ]) {
    assert.equal(serialized.includes(forbidden), false);
  }
});

test("log seguro registra somente tipo do erro", () => {
  const original = new Error("postgresql://usuario:senha@db-interno:5432/base");
  original.name = "UpstreamConnectionError";
  const entry = gatewayUnavailableLog("req-456", original);

  assert.deepEqual(entry, {
    event: "auth_gateway_unavailable",
    request_id: "req-456",
    error_type: "UpstreamConnectionError",
  });
  assert.equal(JSON.stringify(entry).includes(original.message), false);
});

test("rotas de login não contêm respostas DEBUG nem detalhes do upstream", async () => {
  const source = await readFile(
    new URL("./src/app/api/auth/login/route.ts", import.meta.url),
    "utf8",
  );

  for (const forbidden of [
    "DEBUG_FETCH_FAILED",
    "DEBUG_PAYLOAD_NULL",
    "err?.message",
    "err?.cause",
    "err?.stack",
    "statusText",
    "BACKEND_API_URL",
  ]) {
    assert.equal(source.includes(forbidden), false, forbidden);
  }
});

test("JWTs não são persistidos pelo JavaScript do navegador", async () => {
  const source = await readFile(
    new URL("./src/lib/auth-session.ts", import.meta.url),
    "utf8",
  );

  for (const forbidden of ["localStorage", "sessionStorage", "indexedDB"]) {
    assert.equal(source.includes(forbidden), false, forbidden);
  }
  assert.match(source, /persistAuthTokens[\s\S]*Intencionalmente vazio/);
});

test("BFF mantém access e refresh HttpOnly e CSRF acessível ao double-submit", async () => {
  const source = await readFile(
    new URL("./src/lib/server/auth-bff.ts", import.meta.url),
    "utf8",
  );

  assert.match(source, /AUTH_ACCESS_COOKIE[\s\S]*httpOnly: true/);
  assert.match(source, /AUTH_REFRESH_COOKIE[\s\S]*httpOnly: true/);
  assert.match(source, /AUTH_CSRF_COOKIE[\s\S]*httpOnly: false/);
  assert.match(source, /maxAge: 0[\s\S]*expires: new Date\(0\)/);
});
