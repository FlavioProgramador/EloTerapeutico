import test from "node:test";
import assert from "node:assert/strict";
import {
  canActivateCommunicationChannel,
  canCancelCommunication,
  canRetryCommunication,
  communicationChannelLabel,
  communicationConnectionStatusLabel,
  communicationStatusLabel,
  getCommunicationApiErrorMessage,
  isManualWhatsAppReady,
} from "./src/features/communications/communications.utils.ts";

test("rótulos de comunicação permanecem estáveis para a interface", () => {
  assert.equal(communicationStatusLabel.delivered, "Entregue");
  assert.equal(communicationChannelLabel.whatsapp_manual, "WhatsApp manual");
});

test("somente falhas podem ser reenviadas", () => {
  assert.equal(canRetryCommunication("failed"), true);
  assert.equal(canRetryCommunication("sent"), false);
});

test("cancelamento fica restrito aos estados não concluídos", () => {
  assert.equal(canCancelCommunication("scheduled"), true);
  assert.equal(canCancelCommunication("delivered"), false);
});

test("WhatsApp manual só abre após o worker preparar a URL", () => {
  assert.equal(
    isManualWhatsAppReady("whatsapp_manual", "draft", "https://wa.me/55"),
    true,
  );
  assert.equal(isManualWhatsAppReady("whatsapp_manual", "draft"), false);
});

test("canais só podem ser ativados após validação", () => {
  assert.equal(canActivateCommunicationChannel("configured"), true);
  assert.equal(canActivateCommunicationChannel("incomplete"), false);
  assert.equal(communicationConnectionStatusLabel.validating, "Validando");
});

test("erro padronizado da API é exibido ao usuário", () => {
  const error = {
    response: {
      data: {
        error: {
          code: "BAD_REQUEST",
          message: "patient_id: Selecione um paciente para este canal.",
          details: { patient_id: ["Selecione um paciente para este canal."] },
        },
      },
    },
  };

  assert.equal(
    getCommunicationApiErrorMessage(error),
    "Paciente: Selecione um paciente para este canal.",
  );
});

test("erro de campo sem envelope também é tratado", () => {
  const error = { response: { data: { body: ["Informe o conteúdo."] } } };
  assert.equal(
    getCommunicationApiErrorMessage(error),
    "Mensagem: Informe o conteúdo.",
  );
});
