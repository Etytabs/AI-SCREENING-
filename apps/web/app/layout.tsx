import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI-SCREENING | Research Intelligence",
  description: "AI-assisted grant screening and publication reconciliation."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>{children}</body></html>;
}