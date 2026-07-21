import { expect, test, type BrowserContext, type Page } from "@playwright/test";

const ACCESS_COOKIE = "elo_access";
const REFRESH_COOKIE = "elo_refresh";
const CSRF_COOKIE = "elo_csrf";

function requiredEnvironment(name: "E2E_USER_EMAIL" | "E2E_USER_PASSWORD"): string {
  const value = process.env[name];
  if (!value) throw new Error(`${name} deve ser configurada para os testes E2E.`);
  return value;
}

async function login(page: Page): Promise<Record<string, unknown>> {
  const email = requiredEnvironment("E2E_USER_EMAIL");
  const password = requiredEnvironment("E2E_USER_PASSWORD");

  const result = await page.evaluate(
    async (credentials) => {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        credentials: "include",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(credentials),
      });
      return {
        status: response.status,
        body: (await response.json()) as Record<string, unknown>,
      };
    },
    { email, password },
  );

  expect(result.status).toBe(200);
  return result.body;
}

async function cookieByName(context: BrowserContext, name: string) {
  const cookies = await context.cookies();
  return cookies.find((cookie) => cookie.name === name);
}

async function csrfFromDocument(page: Page): Promise<string> {
  const value = await page.evaluate((cookieName) => {
    const prefix = `${cookieName}=`;
    return (
      document.cookie
        .split(";")
        .map((part) => part.trim())
        .find((part) => part.startsWith(prefix))
        ?.slice(prefix.length) || ""
    );
  }, CSRF_COOKIE);
  expect(value).not.toBe("");
  return value;
}

async function sensitiveStorageKeys(page: Page) {
  return page.evaluate(() => {
    const sensitive = /(?:access|refresh|token|auth[_-]?role)/i;
    return {
      local: Object.keys(localStorage).filter((key) => sensitive.test(key)),
      session: Object.keys(sessionStorage).filter((key) => sensitive.test(key)),
    };
  });
}

test.beforeEach(async ({ page }) => {
  await page.goto("/login");
});

test("telas públicas não exibem detalhes técnicos e funcionam no mobile", async ({
  page,
}) => {
  await page.setViewportSize({ width: 375, height: 812 });

  for (const path of ["/login", "/register", "/forgot-password"]) {
    await page.goto(path);
    await expect(page.locator("body")).not.toContainText(
      /(?:EMAIL_BACKEND|DEFAULT_FROM_EMAIL|Traceback|Internal Server Error|Connection refused|ECONNREFUSED)/i,
    );
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - window.innerWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  }
});

test("cadastro usa BFF, cookies HttpOnly e não persiste tokens", async ({
  page,
  context,
}) => {
  await page.goto("/register");
  const uniqueEmail = `register-e2e-${Date.now()}@example.test`;

  await page.getByLabel("Nome completo").fill("Usuário Cadastro E2E");
  await page.getByLabel("E-mail").fill(uniqueEmail);
  await page.getByLabel("Telefone").fill("21999991234");
  await page.getByLabel("Senha", { exact: true }).fill("SenhaE2E123!");
  await page.getByLabel("Confirmar senha").fill("SenhaE2E123!");

  const checkboxes = page.locator('input[type="checkbox"]');
  await checkboxes.nth(0).check();
  await checkboxes.nth(1).check();

  const responsePromise = page.waitForResponse(
    (response) =>
      response.url().includes("/api/auth/register/") &&
      response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Criar conta" }).click();
  const response = await responsePromise;

  expect(response.status()).toBeGreaterThanOrEqual(200);
  expect(response.status()).toBeLessThan(300);
  const body = (await response.json()) as Record<string, unknown>;
  expect(body).not.toHaveProperty("access");
  expect(body).not.toHaveProperty("refresh");
  expect(body).not.toHaveProperty("tokens");

  const access = await cookieByName(context, ACCESS_COOKIE);
  const refresh = await cookieByName(context, REFRESH_COOKIE);
  expect(access?.httpOnly).toBe(true);
  expect(refresh?.httpOnly).toBe(true);

  const storage = await sensitiveStorageKeys(page);
  expect(storage.local).toEqual([]);
  expect(storage.session).toEqual([]);
});

test("login mantém JWTs somente em cookies HttpOnly", async ({
  page,
  context,
}) => {
  const body = await login(page);

  expect(body).not.toHaveProperty("access");
  expect(body).not.toHaveProperty("refresh");
  expect(body).not.toHaveProperty("tokens");

  const access = await cookieByName(context, ACCESS_COOKIE);
  const refresh = await cookieByName(context, REFRESH_COOKIE);
  const csrf = await cookieByName(context, CSRF_COOKIE);

  expect(access).toBeDefined();
  expect(access?.httpOnly).toBe(true);
  expect(access?.sameSite).toBe("Lax");
  expect(refresh).toBeDefined();
  expect(refresh?.httpOnly).toBe(true);
  expect(refresh?.sameSite).toBe("Lax");
  expect(csrf).toBeDefined();
  expect(csrf?.httpOnly).toBe(false);
  expect(csrf?.sameSite).toBe("Lax");

  const browserState = await page.evaluate(
    ({ accessName, refreshName, csrfName }) => ({
      documentCookie: document.cookie,
      localAccess: localStorage.getItem(accessName),
      localRefresh: localStorage.getItem(refreshName),
      sessionAccess: sessionStorage.getItem(accessName),
      sessionRefresh: sessionStorage.getItem(refreshName),
      csrfVisible: document.cookie.includes(`${csrfName}=`),
    }),
    {
      accessName: ACCESS_COOKIE,
      refreshName: REFRESH_COOKIE,
      csrfName: CSRF_COOKIE,
    },
  );

  expect(browserState.documentCookie).not.toContain(`${ACCESS_COOKIE}=`);
  expect(browserState.documentCookie).not.toContain(`${REFRESH_COOKIE}=`);
  expect(browserState.csrfVisible).toBe(true);
  expect(browserState.localAccess).toBeNull();
  expect(browserState.localRefresh).toBeNull();
  expect(browserState.sessionAccess).toBeNull();
  expect(browserState.sessionRefresh).toBeNull();
});

test("refresh exige double-submit CSRF e rotaciona a sessão", async ({
  page,
  context,
}) => {
  await login(page);
  const csrf = await csrfFromDocument(page);
  const accessBefore = await cookieByName(context, ACCESS_COOKIE);
  const refreshBefore = await cookieByName(context, REFRESH_COOKIE);
  expect(accessBefore).toBeDefined();
  expect(refreshBefore).toBeDefined();

  const missing = await context.request.post("/api/auth/refresh");
  expect(missing.status()).toBe(403);

  const divergent = await context.request.post("/api/auth/refresh", {
    headers: { "x-csrf-token": "csrf-divergente" },
  });
  expect(divergent.status()).toBe(403);

  const externalOrigin = await context.request.post("/api/auth/refresh", {
    headers: {
      origin: "https://externo.example",
      "x-csrf-token": csrf,
    },
  });
  expect(externalOrigin.status()).toBe(403);

  const valid = await context.request.post("/api/auth/refresh", {
    headers: { "x-csrf-token": csrf },
  });
  expect(valid.status()).toBe(200);
  expect(await valid.json()).toEqual({ refreshed: true });

  const accessAfter = await cookieByName(context, ACCESS_COOKIE);
  const refreshAfter = await cookieByName(context, REFRESH_COOKIE);
  expect(accessAfter).toBeDefined();
  expect(refreshAfter).toBeDefined();
  expect(accessAfter?.value).not.toBe(accessBefore?.value);
  expect(refreshAfter?.value).not.toBe(refreshBefore?.value);
});

test("logout limpa cookies, revoga refresh e permanece controlado", async ({
  page,
  context,
}) => {
  await login(page);
  const csrf = await csrfFromDocument(page);
  const refreshBefore = await cookieByName(context, REFRESH_COOKIE);
  expect(refreshBefore).toBeDefined();

  const logout = await context.request.post("/api/auth/logout", {
    headers: { "x-csrf-token": csrf },
  });
  expect(logout.status()).toBeGreaterThanOrEqual(200);
  expect(logout.status()).toBeLessThan(300);

  expect(await cookieByName(context, ACCESS_COOKIE)).toBeUndefined();
  expect(await cookieByName(context, REFRESH_COOKIE)).toBeUndefined();
  expect(await cookieByName(context, CSRF_COOKIE)).toBeUndefined();

  const protectedResponse = await context.request.get("/api/backend/auth/me/");
  expect(protectedResponse.status()).toBe(401);

  const origin = new URL(page.url()).origin;
  await context.addCookies([
    {
      name: REFRESH_COOKIE,
      value: refreshBefore?.value || "",
      url: origin,
      httpOnly: true,
      sameSite: "Lax",
    },
    {
      name: CSRF_COOKIE,
      value: csrf,
      url: origin,
      httpOnly: false,
      sameSite: "Lax",
    },
  ]);

  const revokedRefresh = await context.request.post("/api/auth/refresh", {
    headers: { "x-csrf-token": csrf },
  });
  expect(revokedRefresh.status()).toBe(401);

  await context.addCookies([
    {
      name: CSRF_COOKIE,
      value: csrf,
      url: origin,
      httpOnly: false,
      sameSite: "Lax",
    },
  ]);
  const repeatedLogout = await context.request.post("/api/auth/logout", {
    headers: { "x-csrf-token": csrf },
  });
  expect(repeatedLogout.status()).toBe(200);
});
