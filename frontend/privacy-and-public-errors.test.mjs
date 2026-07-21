import test from "node:test";
import assert from "node:assert/strict";

import {
  getPublicErrorMessage,
  getPublicIntegrationError,
} from "./src/lib/errors/public-error.ts";
import {
  isSafePublicMessage,
  sanitizePublicMessage,
} from "./src/lib/errors/sanitize-error.ts";
import {
  maskAddress,
  maskCpf,
  maskDate,
  maskEmail,
  maskIdentifier,
  maskPhone,
  maskToken,
} from "./src/lib/privacy/masks.ts";

test("máscaras minimizam dados pessoais sem persistir o valor completo", () => {
  assert.equal(maskCpf("123.456.789-09"), "***.***.***-09");
  assert.equal(maskEmail("flavio@example.com"), "f***@example.com");
  assert.equal(maskPhone("+55 (21) 99999-1234"), "(21) *****-1234");
  assert.equal(
    maskAddress("Rua das Flores, 100, Centro, Niterói"),
    "Rua das Flores, dados complementares protegidos",
  );
  assert.equal(maskDate("2004-07-21"), "••/••/2004");
  assert.equal(maskToken("segredo"), "••••••••••••");
  assert.equal(maskIdentifier("AC12345678"), "••••5678");
});

test("máscaras tratam valores ausentes e incompletos", () => {
  assert.equal(maskCpf(null), "Não informado");
  assert.equal(maskEmail("invalido"), "E-mail protegido");
  assert.equal(maskPhone("123"), "(••) *****-•123");
  assert.equal(maskAddress("Rua cadastrada"), "Endereço cadastrado");
  assert.equal(maskDate("sem-data"), "Data protegida");
  assert.equal(maskToken(""), "Não configurado");
});

test("códigos públicos conhecidos são traduzidos sem usar mensagem bruta", () => {
  const error = {
    response: {
      status: 403,
      data: {
        error: {
          code: "PERMISSION_DENIED",
          message: "Internal Server Error: access_token=abc",
        },
      },
    },
  };

  assert.equal(
    getPublicErrorMessage(error),
    "Você não tem permissão para realizar esta ação.",
  );
});

test("validações de campos conhecidos podem ser exibidas quando seguras", () => {
  const error = {
    response: {
      status: 400,
      data: {
        error: {
          code: "BAD_REQUEST",
          details: {
            patient_id: ["Selecione um paciente para este canal."],
          },
        },
      },
    },
  };

  assert.equal(
    getPublicErrorMessage(error),
    "Paciente: Selecione um paciente para este canal.",
  );
});

test("mensagens técnicas, credenciais e dados pessoais são bloqueados", () => {
  const blocked = [
    "Internal Server Error",
    "Connection refused on redis:6379",
    "Configure EMAIL_BACKEND e DEFAULT_FROM_EMAIL",
    "access_token=abc123",
    "Traceback: OperationalError",
    "Contato: usuario@example.com",
    "CPF 123.456.789-09 inválido",
  ];

  for (const message of blocked) {
    assert.equal(isSafePublicMessage(message), false, message);
    assert.equal(sanitizePublicMessage(message), null, message);
  }
});

test("erros desconhecidos usam fallback neutro por status", () => {
  assert.equal(
    getPublicErrorMessage({
      response: { status: 500, data: { detail: "KeyError: SECRET_KEY" } },
    }),
    "O serviço está temporariamente indisponível. Tente novamente mais tarde.",
  );
  assert.equal(
    getPublicErrorMessage({ response: { status: 429, data: {} } }),
    "Muitas tentativas foram realizadas. Aguarde e tente novamente.",
  );
});

test("falhas de integração não renderizam a mensagem armazenada", () => {
  assert.equal(
    getPublicIntegrationError({
      code: "CHANNEL_NOT_AVAILABLE",
      message: "ECONNREFUSED redis:6379",
    }),
    "Este canal está temporariamente indisponível.",
  );
  assert.equal(
    getPublicIntegrationError({
      code: "ProviderError",
      message: "Connection refused",
    }),
    "Este canal está temporariamente indisponível.",
  );
});
