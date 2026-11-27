/**
 * Money arrives from the API as a decimal string ("663.00") and must never become a
 * float: 0.1 + 0.2 is famously not 0.3, and a storefront that adds up its own basket
 * wrongly is worse than one that cannot add up at all.
 *
 * Everything here works in integer cents and formats back to a string.
 */

export function toCents(amount: string): number {
  const [whole = "0", fraction = ""] = amount.trim().split(".");
  const cents = (fraction + "00").slice(0, 2);
  const sign = whole.startsWith("-") ? -1 : 1;
  return sign * (Math.abs(Number(whole)) * 100 + Number(cents));
}

export function fromCents(cents: number): string {
  const sign = cents < 0 ? "-" : "";
  const absolute = Math.abs(cents);
  return `${sign}${Math.floor(absolute / 100)}.${String(absolute % 100).padStart(2, "0")}`;
}

export function sumAmounts(amounts: string[]): string {
  return fromCents(amounts.reduce((total, amount) => total + toCents(amount), 0));
}

/** "663.00" + "CAD" -> "CAD $663.00". Never used for arithmetic. */
export function formatMoney(amount: string, currency: string): string {
  return `${currency} $${amount}`;
}
