/**
 * Tests for the price history ring buffer logic in usePrices.
 */

describe("Price history ring buffer", () => {
  const HISTORY_SIZE = 60;

  function pushToRingBuffer(
    history: Record<string, number[]>,
    prices: Record<string, number>
  ): Record<string, number[]> {
    const next = { ...history };
    for (const [symbol, price] of Object.entries(prices)) {
      const arr = next[symbol] ? [...next[symbol]] : [];
      arr.push(price);
      if (arr.length > HISTORY_SIZE) arr.shift();
      next[symbol] = arr;
    }
    return next;
  }

  it("adds prices to empty history", () => {
    const result = pushToRingBuffer({}, { BTC: 65000, ETH: 3200 });
    expect(result.BTC).toEqual([65000]);
    expect(result.ETH).toEqual([3200]);
  });

  it("appends to existing history", () => {
    const prev = { BTC: [64000, 64500] };
    const result = pushToRingBuffer(prev, { BTC: 65000 });
    expect(result.BTC).toEqual([64000, 64500, 65000]);
  });

  it("caps at HISTORY_SIZE entries", () => {
    const prev = { BTC: Array.from({ length: 60 }, (_, i) => 60000 + i * 100) };
    expect(prev.BTC).toHaveLength(60);
    const result = pushToRingBuffer(prev, { BTC: 66100 });
    expect(result.BTC).toHaveLength(60);
    expect(result.BTC[0]).toBe(60100); // first element shifted
    expect(result.BTC[59]).toBe(66100); // new element at end
  });

  it("handles multiple assets independently", () => {
    const prev = { BTC: [64000], ETH: [3100] };
    const result = pushToRingBuffer(prev, { BTC: 65000, ETH: 3200, SOL: 145 });
    expect(result.BTC).toHaveLength(2);
    expect(result.ETH).toHaveLength(2);
    expect(result.SOL).toEqual([145]);
  });
});
