import test from "node:test";
import assert from "node:assert/strict";
import { canCancelCommunication, canRetryCommunication, communicationChannelLabel, communicationStatusLabel, isManualWhatsAppReady } from "./src/features/communications/communications.utils.ts";

test("rótulos de comunicação permanecem estáveis para a interface", () => { assert.equal(communicationStatusLabel.delivered, "Entregue"); assert.equal(communicationChannelLabel.whatsapp_manual, "WhatsApp manual"); });
test("somente falhas podem ser reenviadas", () => { assert.equal(canRetryCommunication("failed"), true); assert.equal(canRetryCommunication("sent"), false); });
test("cancelamento fica restrito aos estados não concluídos", () => { assert.equal(canCancelCommunication("scheduled"), true); assert.equal(canCancelCommunication("delivered"), false); });
test("WhatsApp manual só abre após o worker preparar a URL", () => { assert.equal(isManualWhatsAppReady("whatsapp_manual", "draft", "https://wa.me/55"), true); assert.equal(isManualWhatsAppReady("whatsapp_manual", "draft"), false); });
