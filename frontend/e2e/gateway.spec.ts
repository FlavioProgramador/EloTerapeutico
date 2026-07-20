import { expect, test } from "@playwright/test";

test("gateway indisponível retorna somente contrato público seguro", async ({
  page,
}) => {
  await page.goto("/login");

  const result = await page.evaluate(async () => {
    const syntheticPassword = crypto.randomUUID();
    const response = await fetch("/api/auth/login", {
      method: "POST",
      credentials: "include",
      headers: {
        "content-type": "application/json",
        "x-request-id": "e2e-gateway-001",
      },
      body: JSON.stringify({
        email: "usuario-sintetico@example.test",
        password: syntheticPassword,
      }),
    });
    return {
      status: response.status,
      requestId: response.headers.get("x-request-id"),
      body: (await response.json()) as Record<string, unknown>,
      syntheticPassword,
    };
  });

  expect(result.status).toBe(502);
  expect(result.requestId).toBe("e2e-gateway-001");
  expect(result.body).toEqual({
    error: {
      code: "AUTH_GATEWAY_UNAVAILABLE",
      message: "O serviço de autenticação está temporariamente indisponível.",
    },
    request_id: "e2e-gateway-001",
  });

  const serialized = JSON.stringify(result.body);
  for (const forbidden of [
    "details",
    "stack",
    "cause",
    "statusText",
    "BACKEND_API_URL",
    "127.0.0.1:9",
    "ECONNREFUSED",
    result.syntheticPassword,
  ]) {
    expect(serialized).not.toContain(forbidden);
  }
});
