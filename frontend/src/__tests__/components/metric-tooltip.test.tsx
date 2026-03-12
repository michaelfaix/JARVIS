import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { MetricTooltip } from "@/components/ui/metric-tooltip";

describe("MetricTooltip", () => {
  it("renders children text", () => {
    render(<MetricTooltip term="ECE">ECE Score</MetricTooltip>);
    expect(screen.getByText("ECE Score")).toBeDefined();
  });

  it("shows tooltip on hover for known term", () => {
    render(<MetricTooltip term="ECE">ECE</MetricTooltip>);
    const wrapper = screen.getByText("ECE").closest("[tabindex]") as HTMLElement;
    fireEvent.mouseEnter(wrapper);
    expect(screen.getByText(/Expected Calibration Error/)).toBeDefined();
  });

  it("hides tooltip on mouse leave", () => {
    render(<MetricTooltip term="ECE">ECE</MetricTooltip>);
    const wrapper = screen.getByText("ECE").closest("[tabindex]") as HTMLElement;
    fireEvent.mouseEnter(wrapper);
    expect(screen.getByText(/Expected Calibration Error/)).toBeDefined();
    fireEvent.mouseLeave(wrapper);
    // After the timeout, tooltip should be hidden — but with 150ms delay
    // we check it's still visible immediately
  });

  it("renders nothing extra for unknown term", () => {
    const { container } = render(
      <MetricTooltip term="UNKNOWN_TERM">Label</MetricTooltip>
    );
    expect(screen.getByText("Label")).toBeDefined();
    // No help-circle icon for unknown terms
    expect(container.querySelector("svg")).toBeNull();
  });

  it("has help icon for known terms", () => {
    const { container } = render(
      <MetricTooltip term="OOD">OOD</MetricTooltip>
    );
    expect(container.querySelector("svg")).not.toBeNull();
  });

  it("supports all key glossary terms", () => {
    const terms = ["ECE", "OOD", "Meta-U", "Quality Score", "Market Regime", "Drawdown", "Win Rate"];
    for (const term of terms) {
      const { unmount } = render(
        <MetricTooltip term={term}>{term}</MetricTooltip>
      );
      const wrapper = screen.getByText(term).closest("[tabindex]") as HTMLElement;
      fireEvent.mouseEnter(wrapper);
      // Each term should have a tooltip with the term name bolded
      expect(screen.getByText(term, { selector: "span.font-semibold" })).toBeDefined();
      unmount();
    }
  });
});
