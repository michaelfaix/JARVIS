// =============================================================================
// Tests: lib/types.ts — inferRegime helper
// =============================================================================

import { inferRegime } from "@/lib/types";

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
    expect(inferRegime("UNKNOWN_VALUE")).toBe("RISK_ON");
    expect(inferRegime("")).toBe("RISK_ON");
  });
});
