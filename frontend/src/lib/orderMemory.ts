/**
 * Remembers which email placed which order, on this device only.
 *
 * Guest orders are looked up with the reference plus the email, and nothing is
 * logged in. Without this, a buyer returning to their own confirmation page would
 * have to retype their email every time. It is a convenience, not security: the API
 * still demands the email on every request.
 */

const STORAGE_KEY = "vault151.orders";

type OrderEmails = Record<string, string>;

function read(): OrderEmails {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    const parsed: unknown = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") return {};
    return parsed as OrderEmails;
  } catch {
    return {};
  }
}

export function rememberOrderEmail(publicRef: string, email: string): void {
  try {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ ...read(), [publicRef]: email }),
    );
  } catch {
    // Not being able to remember is survivable: the lookup form asks instead.
  }
}

export function recallOrderEmail(publicRef: string): string | null {
  return read()[publicRef] ?? null;
}
