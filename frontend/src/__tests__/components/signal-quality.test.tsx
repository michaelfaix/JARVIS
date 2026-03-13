import { render, screen } from "@testing-library/react";
import { SignalQuality } from "@/components/dashboard/signal-quality";
import type { Signal } from "@/lib/types";

function makeSignal(overrides: Partial<Signal> = {}): Signal {
  return {
    id: "sig-1",
    asset: "BTC",
    direction: "LONG",
    entry: 65000,
    stopLoss: 63000,
    takeProfit: 70000,
    confidence: 0.8,
    qualityScore: 0.7,
    regime: "RISK_ON",
    isOod: false,
    oodScore: 0.1,
    uncertainty: null,
    deepPathUsed: false,
    timestamp: new Date(),
    ...overrides,
  };
}

describe("SignalQuality", () => {
  it("shows 'No signals available' when no signals", () => {
    render(<SignalQuality signals={[]} metrics={null} accuracyByAsset={[]} backendOnline={false} />);
    expect(screen.getByText("No signals available")).toBeInTheDocument();
  });

  it("shows average confidence percentage", () => {
    const signals = [makeSignal({ confidence: 0.6 }), makeSignal({ id: "2", confidence: 0.8 })];
    render(<SignalQuality signals={signals} metrics={null} accuracyByAsset={[]} backendOnline={true} />);
    // avg = 0.7 → "70%". Use getAllByText since confidence may appear multiple times
    const matches = screen.getAllByText("70%");
    expect(matches.length).toBeGreaterThanOrEqual(1);
  });

  it("shows OOD count warning", () => {
    const signals = [
      makeSignal({ isOod: true, oodScore: 0.9 }),
      makeSignal({ id: "2", isOod: false, oodScore: 0.1 }),
    ];
    render(<SignalQuality signals={signals} metrics={null} accuracyByAsset={[]} backendOnline={true} />);
    expect(screen.getByText(/1\/2 OOD/)).toBeInTheDocument();
  });

  it("shows deep path count", () => {
    const signals = [makeSignal({ deepPathUsed: true })];
    render(<SignalQuality signals={signals} metrics={null} accuracyByAsset={[]} backendOnline={true} />);
    expect(screen.getByText(/1 Deep Path/)).toBeInTheDocument();
  });

  it("shows uncertainty bars when data available", () => {
    const signals = [
      makeSignal({
        uncertainty: { aleatoric: 0.1, epistemic_model: 0.2, epistemic_data: 0.15, total: 0.45 },
      }),
    ];
    render(<SignalQuality signals={signals} metrics={null} accuracyByAsset={[]} backendOnline={true} />);
    expect(screen.getByText("Aleatoric")).toBeInTheDocument();
    expect(screen.getByText("Epistemic")).toBeInTheDocument();
  });

  it("shows calibration metrics when available", () => {
    const metrics = {
      quality_score: 0.8,
      calibration_component: 0.85,
      confidence_component: 0.7,
      stability_component: 0.9,
      data_quality_component: 0.75,
      regime_component: 0.8,
    };
    const signals = [makeSignal()];
    render(<SignalQuality signals={signals} metrics={metrics} accuracyByAsset={[]} backendOnline={true} />);
    expect(screen.getByText("Cal.")).toBeInTheDocument();
    expect(screen.getByText("Stab.")).toBeInTheDocument();
  });

  it("shows per-asset accuracy when available", () => {
    const signals = [makeSignal({ confidence: 0.85, qualityScore: 0.9 })];
    const accuracy = [{ asset: "BTC", totalTrades: 10, wins: 7, losses: 3, winRate: 70, avgPnlPercent: 5.2 }];
    render(<SignalQuality signals={signals} metrics={null} accuracyByAsset={accuracy} backendOnline={true} />);
    // BTC appears in signal card and accuracy section
    const btcElements = screen.getAllByText("BTC");
    expect(btcElements.length).toBeGreaterThanOrEqual(1);
    // 70% appears in accuracy section
    const pctElements = screen.getAllByText("70%");
    expect(pctElements.length).toBeGreaterThanOrEqual(1);
  });
});
