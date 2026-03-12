import React from "react";
import { render, screen } from "@testing-library/react";
import { ApiOfflineBanner } from "@/components/ui/api-offline-banner";

describe("ApiOfflineBanner", () => {
  it("renders default message", () => {
    render(<ApiOfflineBanner />);
    expect(
      screen.getByText("JARVIS Backend offline — showing cached data")
    ).toBeDefined();
  });

  it("renders custom message", () => {
    render(<ApiOfflineBanner message="Custom error" />);
    expect(screen.getByText("Custom error")).toBeDefined();
  });

  it("has yellow styling classes", () => {
    const { container } = render(<ApiOfflineBanner />);
    const banner = container.firstChild as HTMLElement;
    expect(banner.className).toContain("bg-yellow-500/10");
    expect(banner.className).toContain("border-yellow-500/20");
    expect(banner.className).toContain("text-yellow-400");
  });
});
