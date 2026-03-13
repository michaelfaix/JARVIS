/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
    "!./src/__tests__/**",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border) / <alpha-value>)",
        input: "hsl(var(--input) / <alpha-value>)",
        ring: "hsl(var(--ring) / <alpha-value>)",
        background: "hsl(var(--background) / <alpha-value>)",
        foreground: "hsl(var(--foreground) / <alpha-value>)",
        primary: {
          DEFAULT: "hsl(var(--primary) / <alpha-value>)",
          foreground: "hsl(var(--primary-foreground) / <alpha-value>)",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary) / <alpha-value>)",
          foreground: "hsl(var(--secondary-foreground) / <alpha-value>)",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive) / <alpha-value>)",
          foreground: "hsl(var(--destructive-foreground) / <alpha-value>)",
        },
        muted: {
          DEFAULT: "hsl(var(--muted) / <alpha-value>)",
          foreground: "hsl(var(--muted-foreground) / <alpha-value>)",
        },
        accent: {
          DEFAULT: "hsl(var(--accent) / <alpha-value>)",
          foreground: "hsl(var(--accent-foreground) / <alpha-value>)",
        },
        popover: {
          DEFAULT: "hsl(var(--popover) / <alpha-value>)",
          foreground: "hsl(var(--popover-foreground) / <alpha-value>)",
        },
        card: {
          DEFAULT: "hsl(var(--card) / <alpha-value>)",
          foreground: "hsl(var(--card-foreground) / <alpha-value>)",
        },
        hud: {
          bg: "#05080f",
          panel: "#060c18",
          border: "#0a1f35",
          cyan: "#4db8ff",
          "cyan-dim": "#2a6b99",
          green: "#00e5a0",
          "green-dim": "#007a55",
          red: "#ff4466",
          "red-dim": "#992233",
          amber: "#ffaa00",
          "amber-dim": "#996600",
        },
      },
      fontFamily: {
        mono: ['"Courier New"', "Courier", "monospace"],
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        scanLine: {
          "0%": { top: "0%" },
          "100%": { top: "100%" },
        },
        pulseLive: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.4" },
        },
        cornerFade: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.5" },
        },
      },
      animation: {
        "scan-line": "scanLine 3s linear infinite",
        "pulse-live": "pulseLive 2s ease-in-out infinite",
        "corner-fade": "cornerFade 1.5s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
