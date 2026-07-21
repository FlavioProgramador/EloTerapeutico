function digits(value: string | null | undefined): string {
  return String(value ?? "").replace(/\D/g, "");
}

export function maskCpf(value: string | null | undefined): string {
  const normalized = digits(value);
  if (!normalized) return "Não informado";
  const suffix = normalized.slice(-2).padStart(2, "•");
  return `***.***.***-${suffix}`;
}

export function maskEmail(value: string | null | undefined): string {
  const normalized = String(value ?? "").trim();
  if (!normalized) return "Não informado";
  const separator = normalized.lastIndexOf("@");
  if (separator <= 0) return "E-mail protegido";
  const local = normalized.slice(0, separator);
  const domain = normalized.slice(separator + 1);
  const visible = local.slice(0, 1);
  return `${visible || "•"}***@${domain}`;
}

export function maskPhone(value: string | null | undefined): string {
  const normalized = digits(value);
  if (!normalized) return "Não informado";
  const local = normalized.length > 11 ? normalized.slice(-11) : normalized;
  const area = local.length >= 10 ? local.slice(0, 2) : "••";
  const suffix = local.slice(-4).padStart(4, "•");
  return `(${area}) *****-${suffix}`;
}

export function maskAddress(value: string | null | undefined): string {
  const normalized = String(value ?? "").trim();
  if (!normalized) return "Não informado";
  const parts = normalized
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
  if (parts.length >= 2) return `${parts[0]}, dados complementares protegidos`;
  return "Endereço cadastrado";
}

export function maskDate(value: string | null | undefined): string {
  const normalized = String(value ?? "").trim();
  if (!normalized) return "Não informado";
  const year = normalized.match(/\b(19|20)\d{2}\b/)?.[0];
  return year ? `••/••/${year}` : "Data protegida";
}

export function maskToken(value: string | null | undefined): string {
  return String(value ?? "").trim() ? "••••••••••••" : "Não configurado";
}

export function maskIdentifier(value: string | number | null | undefined): string {
  const normalized = String(value ?? "").trim();
  if (!normalized) return "Não informado";
  const suffix = normalized.slice(-4);
  return `••••${suffix}`;
}
