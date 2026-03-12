import React from "react";
import { render } from "@testing-library/react";
import { Skeleton } from "@/components/ui/skeleton";

describe("Skeleton", () => {
  it("renders with animate-pulse class", () => {
    const { container } = render(<Skeleton />);
    const el = container.firstChild as HTMLElement;
    expect(el.className).toContain("animate-pulse");
  });

  it("accepts custom className", () => {
    const { container } = render(<Skeleton className="h-8 w-32" />);
    const el = container.firstChild as HTMLElement;
    expect(el.className).toContain("h-8");
    expect(el.className).toContain("w-32");
    expect(el.className).toContain("animate-pulse");
  });

  it("renders as a div", () => {
    const { container } = render(<Skeleton />);
    expect(container.firstChild?.nodeName).toBe("DIV");
  });
});
