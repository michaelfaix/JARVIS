import { render, screen } from "@testing-library/react";
import { HudTopbar } from "@/components/layout/hud-topbar";

// Mock dependencies
jest.mock("next/navigation", () => ({
  usePathname: () => "/",
}));

jest.mock("@/hooks/use-locale", () => ({
  useLocale: () => ({ locale: "en", setLocale: jest.fn(), t: (k: string) => k }),
}));

jest.mock("@/hooks/use-notifications", () => ({
  useNotifications: () => ({
    notifications: [],
    unreadCount: 0,
    markAllRead: jest.fn(),
    clearAll: jest.fn(),
    push: jest.fn(),
  }),
}));

describe("HudTopbar", () => {
  const defaultProps = {
    wsConnected: true,
    regime: "RISK_ON" as const,
    sentimentValue: 55,
    apiLatencyMs: 42,
  };

  it("renders JARVIS brand text", () => {
    render(<HudTopbar {...defaultProps} />);
    expect(screen.getByText("JARVIS")).toBeInTheDocument();
  });

  it("shows RISK ON badge for RISK_ON regime", () => {
    render(<HudTopbar {...defaultProps} regime="RISK_ON" />);
    expect(screen.getByText("RISK ON")).toBeInTheDocument();
  });

  it("shows RISK OFF badge for RISK_OFF regime", () => {
    render(<HudTopbar {...defaultProps} regime="RISK_OFF" />);
    expect(screen.getByText("RISK OFF")).toBeInTheDocument();
  });

  it("shows CRISIS badge for CRISIS regime", () => {
    render(<HudTopbar {...defaultProps} regime="CRISIS" />);
    expect(screen.getByText("CRISIS")).toBeInTheDocument();
  });

  it("shows LIVE when wsConnected is true", () => {
    render(<HudTopbar {...defaultProps} wsConnected={true} />);
    expect(screen.getByText("LIVE")).toBeInTheDocument();
  });

  it("shows OFF when wsConnected is false", () => {
    render(<HudTopbar {...defaultProps} wsConnected={false} />);
    expect(screen.getByText("OFF")).toBeInTheDocument();
  });

  it("shows EN and DE language buttons", () => {
    render(<HudTopbar {...defaultProps} />);
    expect(screen.getByText("EN")).toBeInTheDocument();
    expect(screen.getByText("DE")).toBeInTheDocument();
  });

  it("shows API latency when provided", () => {
    render(<HudTopbar {...defaultProps} apiLatencyMs={42} />);
    expect(screen.getByText("42ms")).toBeInTheDocument();
  });

  it("hides API latency when null", () => {
    render(<HudTopbar {...defaultProps} apiLatencyMs={null} />);
    expect(screen.queryByText(/ms$/)).not.toBeInTheDocument();
  });

  it("shows sentiment value", () => {
    render(<HudTopbar {...defaultProps} sentimentValue={65} />);
    expect(screen.getByText("65")).toBeInTheDocument();
  });

  it("renders notification bell", () => {
    const { container } = render(<HudTopbar {...defaultProps} />);
    // Bell icon renders as SVG
    const bellSvg = container.querySelector("svg");
    expect(bellSvg).toBeInTheDocument();
  });
});
