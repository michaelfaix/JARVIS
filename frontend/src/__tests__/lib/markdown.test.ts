import { simpleMarkdown } from "@/lib/markdown";

describe("simpleMarkdown", () => {
  it("escapes HTML entities to prevent XSS", () => {
    expect(simpleMarkdown("<script>alert('xss')</script>")).toContain("&lt;script&gt;");
    expect(simpleMarkdown("<script>alert('xss')</script>")).not.toContain("<script>");
  });

  it("escapes ampersands", () => {
    expect(simpleMarkdown("A & B")).toContain("&amp;");
  });

  it("converts ## to h2", () => {
    const result = simpleMarkdown("## Hello");
    expect(result).toContain("<h2");
    expect(result).toContain("Hello");
  });

  it("converts ### to h3", () => {
    const result = simpleMarkdown("### Title");
    expect(result).toContain("<h3");
    expect(result).toContain("Title");
  });

  it("converts # to h1", () => {
    const result = simpleMarkdown("# Big Title");
    expect(result).toContain("<h1");
  });

  it("converts **bold** to strong", () => {
    expect(simpleMarkdown("**bold text**")).toContain("<strong>bold text</strong>");
  });

  it("converts *italic* to em", () => {
    expect(simpleMarkdown("*italic*")).toContain("<em>italic</em>");
  });

  it("converts `code` to code element", () => {
    expect(simpleMarkdown("`const x = 1`")).toContain("<code");
    expect(simpleMarkdown("`const x = 1`")).toContain("const x = 1");
  });

  it("converts --- to hr", () => {
    expect(simpleMarkdown("---")).toContain("<hr");
  });

  it("converts - items to li", () => {
    expect(simpleMarkdown("- item one")).toContain("<li");
    expect(simpleMarkdown("- item one")).toContain("item one");
  });

  it("converts numbered lists to li", () => {
    expect(simpleMarkdown("1. first")).toContain("<li");
    expect(simpleMarkdown("1. first")).toContain("list-decimal");
  });

  it("converts newlines to br", () => {
    expect(simpleMarkdown("line1\nline2")).toContain("<br />");
  });

  it("handles table syntax", () => {
    const input = "|A|B|\n|---|---|\n|1|2|";
    const result = simpleMarkdown(input);
    expect(result).toContain("<table");
    expect(result).toContain("<td");
  });

  it("handles empty string", () => {
    expect(simpleMarkdown("")).toBe("");
  });

  it("handles plain text without markdown", () => {
    const result = simpleMarkdown("Hello world");
    expect(result).toBe("Hello world");
  });
});
