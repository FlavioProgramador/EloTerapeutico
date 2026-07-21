import {
  DEFAULT_PUBLIC_ERROR,
  HTTP_PUBLIC_MESSAGES,
  PUBLIC_ERROR_MESSAGES,
} from "./error-codes";
import { PUBLIC_FIELD_LABELS } from "./field-labels";
import { sanitizePublicMessage } from "./sanitize-error";

type UnknownRecord = Record<string, unknown>;

function asRecord(value: unknown): UnknownRecord | null {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as UnknownRecord)
    : null;
}

function responseStatus(error: unknown): number | undefined {
  const record = asRecord(error);
  const response = asRecord(record?.response);
  return typeof response?.status === "number" ? response.status : undefined;
}

function responseData(error: unknown): unknown {
  const record = asRecord(error);
  const response = asRecord(record?.response);
  return response?.data;
}

function publicCodeMessage(data: unknown): string | null {
  const payload = asRecord(data);
  const envelope = asRecord(payload?.error);
  const code = envelope?.code ?? payload?.code;
  return typeof code === "string" ? PUBLIC_ERROR_MESSAGES[code] ?? null : null;
}

function firstSafeFieldMessage(value: unknown): string | null {
  if (Array.isArray(value)) {
    for (const item of value) {
      const message = firstSafeFieldMessage(item);
      if (message) return message;
    }
    return null;
  }
  return sanitizePublicMessage(value);
}

function publicFieldMessage(data: unknown): string | null {
  const payload = asRecord(data);
  if (!payload) return null;

  const envelope = asRecord(payload.error);
  const details = asRecord(envelope?.details) ?? payload;

  for (const [field, label] of Object.entries(PUBLIC_FIELD_LABELS)) {
    if (!(field in details)) continue;
    const message = firstSafeFieldMessage(details[field]);
    if (message) return `${label}: ${message}`;
  }

  return null;
}

export function getPublicErrorMessage(
  error: unknown,
  fallback = DEFAULT_PUBLIC_ERROR,
): string {
  const data = responseData(error);
  const codeMessage = publicCodeMessage(data);
  if (codeMessage) return codeMessage;

  const fieldMessage = publicFieldMessage(data);
  if (fieldMessage) return fieldMessage;

  const status = responseStatus(error);
  if (status && status >= 500) return PUBLIC_ERROR_MESSAGES.SERVICE_UNAVAILABLE;
  if (status && HTTP_PUBLIC_MESSAGES[status]) return HTTP_PUBLIC_MESSAGES[status];

  return fallback;
}

export function getPublicIntegrationError(
  value: unknown,
  fallback = PUBLIC_ERROR_MESSAGES.CHANNEL_NOT_AVAILABLE,
): string {
  const record = asRecord(value);
  const code = record?.code;
  if (typeof code === "string" && PUBLIC_ERROR_MESSAGES[code]) {
    return PUBLIC_ERROR_MESSAGES[code];
  }
  return fallback;
}
