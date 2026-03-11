import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { cn } from "@/lib/utils";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: "JARVIS Trader — Decision Quality Platform",
  description:
    "Multi-Asset Strategy Platform with ML-powered regime detection, uncertainty quantification, and decision quality scoring.",
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
      </body>
    </html>
  );
}
