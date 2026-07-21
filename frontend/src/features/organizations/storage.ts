const ACTIVE_ORGANIZATION_KEY = "elo.active-organization";

export function getStoredOrganizationId(): string | null {
  if (typeof window === "undefined") return null;
  const value = window.localStorage.getItem(ACTIVE_ORGANIZATION_KEY);
  return value && /^[0-9a-f-]{36}$/i.test(value) ? value : null;
}

export function storeOrganizationId(value: string | null): void {
  if (typeof window === "undefined") return;
  if (value) {
    window.localStorage.setItem(ACTIVE_ORGANIZATION_KEY, value);
  } else {
    window.localStorage.removeItem(ACTIVE_ORGANIZATION_KEY);
  }
}
