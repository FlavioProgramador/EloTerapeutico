import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  AUTH_ACCESS_COOKIE,
  AUTH_CSRF_COOKIE,
  AUTH_REFRESH_COOKIE,
  isBlockedAuthProxyPath,
  isUnsafeHttpMethod,
} from "./src/lib/auth-constants.ts";

test("cookies de autenticação usam nomes separados do legado", () => {
  assert.equal(AUTH_ACCESS_COOKIE, "elo_access");
  assert.equal(AUTH_REFRESH_COOKIE, "elo_refresh");
  assert.equal(AUTH_CSRF_COOKIE, "elo_csrf");
  assert.notEqual(AUTH_ACCESS_COOKIE, "auth_token");
  assert.notEqual(AUTH_REFRESH_COOKIE, "auth_refresh_token");
});

test("métodos mutáveis exigem proteção CSRF", () => {
  for (const method of ["POST", "PUT", "PATCH", "DELETE"]) {
    assert.equal(isUnsafeHttpMethod(method), true);
  }
  assert.equal(isUnsafeHttpMethod("GET"), false);
  assert.equal(isUnsafeHttpMethod("HEAD"), false);
});

test("proxy genérico bloqueia endpoints que retornam ou revogam tokens", () => {
  assert.equal(isBlockedAuthProxyPath("auth/login"), true);
  assert.equal(isBlockedAuthProxyPath("/auth/logout/"), true);
  assert.equal(isBlockedAuthProxyPath("auth/logout-all"), true);
  assert.equal(isBlockedAuthProxyPath("auth/token/refresh"), true);
  assert.equal(isBlockedAuthProxyPath("auth/me"), false);
  assert.equal(isBlockedAuthProxyPath("patients"), false);
});

test("cliente não lê access ou refresh token", async () => {
  const apiSource = await readFile("./src/lib/api.ts", "utf8");
  const sessionSource = await readFile("./src/lib/auth-session.ts", "utf8");

  assert.equal(apiSource.includes("getAccessToken"), false);
  assert.equal(apiSource.includes("getRefreshToken"), false);
  assert.equal(apiSource.includes("Bearer ${token}"), false);
  assert.equal(sessionSource.includes("getCookie(AUTH_ACCESS_COOKIE"), false);
  assert.equal(sessionSource.includes("getCookie(AUTH_REFRESH_COOKIE"), false);
  assert.equal(sessionSource.includes("setCookie(AUTH_ACCESS_COOKIE"), false);
  assert.equal(sessionSource.includes("setCookie(AUTH_REFRESH_COOKIE"), false);
});

test("BFF não encaminha headers hop-by-hop", async () => {
  const source = await readFile("./src/lib/server/auth-bff.ts", "utf8");

  assert.equal(source.includes('headers.set("connection"'), false);
  assert.equal(source.includes('"connection",'), false);
  assert.equal(source.includes('"keep-alive",'), false);
  assert.equal(source.includes('"transfer-encoding",'), false);
});

test("proxy não usa papel controlado pelo navegador", async () => {
  const source = await readFile("./src/proxy.ts", "utf8");
  assert.equal(source.includes("auth_role"), false);
  assert.equal(source.includes("role ==="), false);
  assert.equal(source.includes("AUTH_ACCESS_COOKIE"), true);
  assert.equal(source.includes("AUTH_REFRESH_COOKIE"), true);
});
