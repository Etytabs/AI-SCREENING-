import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AppShell } from "@/components/app-shell";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "ShakaHive - AI-Powered Grant Screening",
  description: "ShakaHive automates eligibility, plagiarism, duplication, and novelty checks for grant applications",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}><AppShell>{children}</AppShell></body>
    </html>
  );
}
