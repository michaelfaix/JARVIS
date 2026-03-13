import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { cn } from "@/lib/utils";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: {
    default: "JARVIS Trader — AI Trading Intelligence",
    template: "%s | JARVIS Trader",
  },
  description:
    "AI-powered trading intelligence with ML regime detection, real-time signals, paper trading, and risk management. Free to start.",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "JARVIS Trader",
  },
  openGraph: {
    type: "website",
    title: "JARVIS Trader — AI Trading Intelligence",
    description:
      "ML-powered market regime detection, trading signals, and automated risk management. Your AI co-pilot for crypto, forex, and stocks.",
    siteName: "JARVIS Trader",
  },
  twitter: {
    card: "summary_large_image",
    title: "JARVIS Trader — AI Trading Intelligence",
    description:
      "ML-powered market regime detection, trading signals, and automated risk management.",
  },
};

export const viewport: Viewport = {
  themeColor: "#2563eb",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={cn("min-h-screen bg-background antialiased", inter.variable, inter.className)}>
        {children}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              if ('serviceWorker' in navigator) {
                window.addEventListener('load', function() {
                  navigator.serviceWorker.register('/sw.js').catch(function() {});
                });
              }
            `,
          }}
        />
      </body>
    </html>
  );
}
