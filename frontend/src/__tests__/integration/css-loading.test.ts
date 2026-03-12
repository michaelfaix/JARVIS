// =============================================================================
// Integration Tests: CSS is correctly configured and not empty
// =============================================================================

import * as fs from "fs";
import * as path from "path";

describe("CSS Configuration", () => {
  const rootDir = path.resolve(__dirname, "../../..");

  it("globals.css exists and is not empty", () => {
    const cssPath = path.join(rootDir, "src/app/globals.css");
    expect(fs.existsSync(cssPath)).toBe(true);

    const content = fs.readFileSync(cssPath, "utf-8");
    expect(content.length).toBeGreaterThan(0);
  });

  it("globals.css contains Tailwind directives", () => {
    const cssPath = path.join(rootDir, "src/app/globals.css");
    const content = fs.readFileSync(cssPath, "utf-8");

    expect(content).toContain("@tailwind base");
    expect(content).toContain("@tailwind components");
    expect(content).toContain("@tailwind utilities");
  });

  it("globals.css defines CSS custom properties for dark theme", () => {
    const cssPath = path.join(rootDir, "src/app/globals.css");
    const content = fs.readFileSync(cssPath, "utf-8");

    expect(content).toContain(".dark");
    expect(content).toContain("--background");
    expect(content).toContain("--foreground");
    expect(content).toContain("--card");
    expect(content).toContain("--border");
    expect(content).toContain("--primary");
  });

  it("root layout imports globals.css", () => {
    const layoutPath = path.join(rootDir, "src/app/layout.tsx");
    expect(fs.existsSync(layoutPath)).toBe(true);

    const content = fs.readFileSync(layoutPath, "utf-8");
    expect(content).toContain("./globals.css");
  });

  it("root layout applies dark class to html element", () => {
    const layoutPath = path.join(rootDir, "src/app/layout.tsx");
    const content = fs.readFileSync(layoutPath, "utf-8");

    expect(content).toMatch(/class.*dark/);
  });

  it("tailwind.config.js exists and has correct content paths", () => {
    const configPath = path.join(rootDir, "tailwind.config.js");
    expect(fs.existsSync(configPath)).toBe(true);

    const content = fs.readFileSync(configPath, "utf-8");
    expect(content).toContain("./src/**/*.{js,ts,jsx,tsx,mdx}");
    expect(content).toContain('darkMode: "class"');
  });

  it("postcss.config.js exists", () => {
    const configPath = path.join(rootDir, "postcss.config.js");
    expect(fs.existsSync(configPath)).toBe(true);
  });

  it("globals.css applies base styles to body", () => {
    const cssPath = path.join(rootDir, "src/app/globals.css");
    const content = fs.readFileSync(cssPath, "utf-8");

    expect(content).toContain("bg-background");
    expect(content).toContain("text-foreground");
  });

  it("dark theme defines all required CSS variables", () => {
    const cssPath = path.join(rootDir, "src/app/globals.css");
    const content = fs.readFileSync(cssPath, "utf-8");

    const requiredVars = [
      "--background",
      "--foreground",
      "--card",
      "--card-foreground",
      "--popover",
      "--popover-foreground",
      "--primary",
      "--primary-foreground",
      "--secondary",
      "--secondary-foreground",
      "--muted",
      "--muted-foreground",
      "--accent",
      "--accent-foreground",
      "--destructive",
      "--destructive-foreground",
      "--border",
      "--input",
      "--ring",
    ];

    for (const varName of requiredVars) {
      expect(content).toContain(varName);
    }
  });
});
