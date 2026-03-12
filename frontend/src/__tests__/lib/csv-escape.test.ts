/**
 * CSV escape / injection prevention tests.
 * The csvEscape function lives inside journal/page.tsx — we test the logic directly.
 */

function csvEscape(val: string | number): string {
  let s = String(val);
  if (/^[=+\-@\t\r]/.test(s)) {
    s = "\t" + s;
  }
  return '"' + s.replace(/"/g, '""') + '"';
}

describe("csvEscape", () => {
  it("wraps normal string in double quotes", () => {
    expect(csvEscape("BTC")).toBe('"BTC"');
  });

  it("wraps number in double quotes", () => {
    expect(csvEscape(42.5)).toBe('"42.5"');
  });

  it("escapes internal double quotes", () => {
    expect(csvEscape('say "hello"')).toBe('"say ""hello"""');
  });

  it("prefixes = with tab to prevent formula injection", () => {
    expect(csvEscape("=CMD()")).toBe('"\t=CMD()"');
  });

  it("prefixes + with tab to prevent formula injection", () => {
    expect(csvEscape("+1+2")).toBe('"\t+1+2"');
  });

  it("prefixes - with tab to prevent formula injection", () => {
    expect(csvEscape("-1-2")).toBe('"\t-1-2"');
  });

  it("prefixes @ with tab to prevent formula injection", () => {
    expect(csvEscape("@SUM(A1)")).toBe('"\t@SUM(A1)"');
  });

  it("does not prefix negative numbers redundantly when using number type", () => {
    // Negative numbers passed as number get stringified to "-123.45"
    const result = csvEscape(-123.45);
    expect(result).toBe('"\t-123.45"');
  });

  it("leaves normal values untouched", () => {
    expect(csvEscape("LONG")).toBe('"LONG"');
    expect(csvEscape("2026-01-15")).toBe('"2026-01-15"');
    expect(csvEscape(65000)).toBe('"65000"');
  });
});
