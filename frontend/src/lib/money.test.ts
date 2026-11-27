import { describe, expect, it } from "vitest";

import { formatMoney, fromCents, sumAmounts, toCents } from "./money";

describe("money", () => {
  it("reads a decimal string as cents", () => {
    expect(toCents("663.00")).toBe(66300);
    expect(toCents("0.05")).toBe(5);
    expect(toCents("12")).toBe(1200);
  });

  it("round-trips without drifting", () => {
    expect(fromCents(toCents("1038.00"))).toBe("1038.00");
    expect(fromCents(5)).toBe("0.05");
  });

  it("adds prices exactly, where floats would not", () => {
    // 0.1 + 0.2 === 0.30000000000000004 as floats.
    expect(sumAmounts(["0.10", "0.20"])).toBe("0.30");
    expect(sumAmounts(["663.00", "375.00"])).toBe("1038.00");
  });

  it("sums an empty basket to zero", () => {
    expect(sumAmounts([])).toBe("0.00");
  });

  it("formats with the currency the API supplied", () => {
    expect(formatMoney("663.00", "CAD")).toBe("CAD $663.00");
  });
});
