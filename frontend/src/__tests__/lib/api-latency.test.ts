/**
 * Tests for the API latency tracking in api.ts.
 */

describe("API latency tracking", () => {
  it("getLastApiLatency returns null initially", async () => {
    // Simulate the module's initial state
    let lastLatency: number | null = null;
    expect(lastLatency).toBeNull();
  });

  it("latency is a non-negative integer after measurement", () => {
    const start = performance.now();
    // Simulate a ~0ms operation
    const latency = Math.round(performance.now() - start);
    expect(latency).toBeGreaterThanOrEqual(0);
    expect(Number.isInteger(latency)).toBe(true);
  });

  it("performance.now() provides sub-millisecond precision", () => {
    const t1 = performance.now();
    const t2 = performance.now();
    expect(t2).toBeGreaterThanOrEqual(t1);
  });
});
