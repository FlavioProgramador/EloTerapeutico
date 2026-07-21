const TECHNICAL_PATTERNS: readonly RegExp[] = [
  /\b(?:Internal Server Error|Traceback|KeyError|ValidationError|IntegrityError|OperationalError)\b/i,
  /\b(?:Connection refused|ECONNREFUSED|Redis|Celery|worker|container|migration|SQL)\b/i,
  /\b(?:EMAIL_BACKEND|DEFAULT_FROM_EMAIL|process\.env|DJANGO_SETTINGS_MODULE)\b/i,
  /\b(?:access[_ -]?token|refresh[_ -]?token|api[_ -]?key|app[_ -]?secret|auth[_ -]?token)\b/i,
  /(?:postgres|redis|backend|localhost|127\.0\.0\.1):\d+/i,
  /\/(?:api|backend|admin)\/[\w./-]+/i,
  /\b[A-Z][A-Z0-9]*_[A-Z0-9_]+\b/,
];

const PERSONAL_DATA_PATTERNS: readonly RegExp[] = [
  /\b\d{3}\.\d{3}\.\d{3}-\d{2}\b/,
  /\b\d{11}\b/,
  /\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b/,
  /\b(?:\+?55\s*)?(?:\(?\d{2}\)?\s*)?9?\d{4}[-\s]?\d{4}\b/,
];

export function isSafePublicMessage(value: unknown): value is string {
  if (typeof value !== "string") return false;
  const message = value.trim();
  if (!message || message.length > 240) return false;
  if (TECHNICAL_PATTERNS.some((pattern) => pattern.test(message))) return false;
  if (PERSONAL_DATA_PATTERNS.some((pattern) => pattern.test(message))) return false;
  return true;
}

export function sanitizePublicMessage(value: unknown): string | null {
  return isSafePublicMessage(value) ? value.trim() : null;
}
