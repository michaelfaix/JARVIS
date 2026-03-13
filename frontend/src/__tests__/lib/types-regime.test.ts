// =============================================================================
// Tests: lib/types.ts — Regime types, colors, labels, and inferRegime
// =============================================================================

import {
  REGIME_COLORS,
  REGIME_LABELS,
  MODUS_COLORS,
  inferRegime,
  type RegimeState,
} from "@/lib/types";

describe("REGIME_COLORS", () => {
  const regimes: RegimeState[] = ["RISK_ON", "RISK_OFF", "CRISIS", "TRANSITION", "UNKNOWN"];

  it("has a color for every regime state", () => {
    for (const regime of regimes) {
      expect(REGIME_COLORS[regime]).toBeDefined();
      expect(typeof REGIME_COLORS[regime]).toBe("string");
    }
  });

  it("RISK_ON is green", () => {
    expect(REGIME_COLORS.RISK_ON).toMatch(/#22c55e/i);
  });

  it("CRISIS is red", () => {
    expect(REGIME_COLORS.CRISIS).toMatch(/#ef4444/i);
  });
});

describe("REGIME_LABELS", () => {
  it("has a label for every regime state", () => {
    const regimes: RegimeState[] = ["RISK_ON", "RISK_OFF", "CRISIS", "TRANSITION", "UNKNOWN"];
    for (const regime of regimes) {
      expect(REGIME_LABELS[regime]).toBeDefined();
      expect(typeof REGIME_LABELS[regime]).toBe("string");
      expect(REGIME_LABELS[regime].length).toBeGreaterThan(0);
    }
  });

  it("returns human-readable labels", () => {
    expect(REGIME_LABELS.RISK_ON).toBe("Risk On");
    expect(REGIME_LABELS.RISK_OFF).toBe("Risk Off");
    expect(REGIME_LABELS.CRISIS).toBe("Crisis");
    expect(REGIME_LABELS.TRANSITION).toBe("Transition");
    expect(REGIME_LABELS.UNKNOWN).toBe("Unknown");
  });
});

describe("MODUS_COLORS", () => {
  it("has colors for core system modi", () => {
    const modi = [
      "NORMAL",
      "ERHOEHTE_VORSICHT",
      "REDUZIERTES_VERTRAUEN",
      "MINIMALE_EXPOSITION",
      "NUR_MONITORING",
      "NOTFALL_MODUS",
      "DATEN_QUARANTAENE",
      "MODELL_ROLLBACK",
      "KONFIDENZ_KOLLAPS",
    ];
    for (const modus of modi) {
      expect(MODUS_COLORS[modus]).toBeDefined();
      expect(typeof MODUS_COLORS[modus]).toBe("string");
    }
  });
});

describe("inferRegime", () => {
  it("maps NORMAL to RISK_ON", () => {
    expect(inferRegime("NORMAL")).toBe("RISK_ON");
  });

  it("maps ERHOEHTE_VORSICHT to RISK_OFF", () => {
    expect(inferRegime("ERHOEHTE_VORSICHT")).toBe("RISK_OFF");
  });

  it("maps REDUZIERTES_VERTRAUEN to RISK_OFF", () => {
    expect(inferRegime("REDUZIERTES_VERTRAUEN")).toBe("RISK_OFF");
  });

  it("maps NOTFALL_MODUS to CRISIS", () => {
    expect(inferRegime("NOTFALL_MODUS")).toBe("CRISIS");
  });

  it("maps KONFIDENZ_KOLLAPS to CRISIS", () => {
    expect(inferRegime("KONFIDENZ_KOLLAPS")).toBe("CRISIS");
  });

  it("maps MINIMALE_EXPOSITION to TRANSITION", () => {
    expect(inferRegime("MINIMALE_EXPOSITION")).toBe("TRANSITION");
  });

  it("maps NUR_MONITORING to TRANSITION", () => {
    expect(inferRegime("NUR_MONITORING")).toBe("TRANSITION");
  });

  it("defaults unknown modus to RISK_ON", () => {
    expect(inferRegime("SOME_UNKNOWN_MODE")).toBe("RISK_ON");
    expect(inferRegime("")).toBe("RISK_ON");
  });
});
