import assert from "node:assert/strict";
import test from "node:test";

import {
  createSingleFlight,
  extractApiErrorMessage,
  prepareRetryRequest,
  resolvePostLoginDestination,
  safeInternalPath,
} from "./src/lib/auth-flow.ts";

test("safeInternalPath rejeita redirecionamentos externos", () => {
  assert.equal(safeInternalPath("https://example.com"), "/dashboard");
  assert.equal(safeInternalPath("//example.com"), "/dashboard");
  assert.equal(safeInternalPath("/checkout?plan=pro"), "/checkout?plan=pro");
});

test("usuário com entitlement acessa o destino interno solicitado", () => {
  assert.equal(
    resolvePostLoginDestination({
      requested: "/dashboard/patients",
      entitlementAllowed: true,
      subscriptionStatus: "ACTIVE",
    }),
    "/dashboard/patients",
  );
});

test("trial válido segue para o dashboard solicitado", () => {
  assert.equal(
    resolvePostLoginDestination({
      requested: "/dashboard",
      entitlementAllowed: true,
      subscriptionStatus: "TRIALING",
    }),
    "/dashboard",
  );
});

test("usuário sem assinatura é direcionado para planos", () => {
  assert.equal(
    resolvePostLoginDestination({
      requested: "/dashboard",
      entitlementAllowed: false,
      subscriptionStatus: null,
      entitlementRedirect: "/planos",
    }),
    "/planos",
  );
});

test("pagamento pendente direciona para billing", () => {
  assert.equal(
    resolvePostLoginDestination({
      requested: "/dashboard",
      entitlementAllowed: false,
      subscriptionStatus: "PENDING",
    }),
    "/billing",
  );
});

test("checkout permanece acessível para regularização", () => {
  assert.equal(
    resolvePostLoginDestination({
      requested: "/checkout?plan=profissional",
      entitlementAllowed: false,
      subscriptionStatus: null,
    }),
    "/checkout?plan=profissional",
  );
});

test("mensagem estável do envelope de erro tem precedência", () => {
  assert.equal(
    extractApiErrorMessage(
      {
        error: {
          code: "ASAAS_CONFIGURATION_ERROR",
          message: "A integração de pagamentos não está configurada.",
          details: {},
        },
      },
      "fallback",
    ),
    "A integração de pagamentos não está configurada.",
  );
});

test("detalhe de campo é usado quando não há mensagem principal", () => {
  assert.equal(
    extractApiErrorMessage(
      {
        error: {
          details: {
            cpfCnpj: ["CPF ou CNPJ inválido."],
          },
        },
      },
      "fallback",
    ),
    "CPF ou CNPJ inválido.",
  );
});

test("single-flight executa apenas um refresh para chamadas concorrentes", async () => {
  const run = createSingleFlight();
  let calls = 0;
  let release;
  const gate = new Promise((resolve) => {
    release = resolve;
  });
  const factory = async () => {
    calls += 1;
    await gate;
    return "new-access-token";
  };

  const first = run(factory);
  const second = run(factory);
  release();

  assert.equal(await first, "new-access-token");
  assert.equal(await second, "new-access-token");
  assert.equal(calls, 1);
});

test("retry atualiza Authorization sem alterar body ou Idempotency-Key", () => {
  const body = { idempotency_key: "checkout-key-001", plan_price_id: 7 };
  const request = {
    headers: {
      "Idempotency-Key": "checkout-key-001",
      "Content-Type": "application/json",
    },
    data: body,
  };

  const retried = prepareRetryRequest(request, "new-access-token");

  assert.equal(retried, request);
  assert.equal(retried.data, body);
  assert.equal(retried.headers["Idempotency-Key"], "checkout-key-001");
  assert.equal(retried.headers.Authorization, "Bearer new-access-token");
});
