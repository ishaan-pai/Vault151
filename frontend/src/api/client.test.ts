import { describe, expect, it } from "vitest";

import { buildQueryString } from "./client";

describe("buildQueryString", () => {
  it("returns an empty string when nothing is set", () => {
    expect(buildQueryString({})).toBe("");
  });

  it("drops undefined, null and empty values rather than sending them", () => {
    // The API would reject ?q= (min_length=1), and "undefined" would be a literal
    // search term.
    expect(buildQueryString({ q: undefined, rarity: null, variant: "" })).toBe("");
  });

  it("keeps the camelCase names the API expects", () => {
    expect(buildQueryString({ pageSize: 12, setId: 101 })).toBe("?pageSize=12&setId=101");
  });

  it("keeps false, which is a real filter value", () => {
    // graded=false means "raw cards only"; dropping it would mean "both".
    expect(buildQueryString({ graded: false })).toBe("?graded=false");
  });

  it("keeps a zero price floor", () => {
    expect(buildQueryString({ minPrice: 0 })).toBe("?minPrice=0");
  });

  it("escapes values that need it", () => {
    expect(buildQueryString({ q: "charizard ex" })).toBe("?q=charizard+ex");
  });
});
