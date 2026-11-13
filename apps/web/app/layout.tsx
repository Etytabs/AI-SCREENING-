import "./globals.css";
import "./brand-global.css";
import type { Metadata } from "next";
import localFont from "next/font/local";
import Navbar from "../components/Navbar";

const fredoka = localFont({ src: "./fonts/Fredoka.ttf", variable: "--font-fredoka", weight: "300 700" });
const nunito = localFont({ src: "./fonts/Nunito.ttf", variable: "--font-nunito", weight: "200 1000" });

export const metadata: Metadata = {
  title: "ShakaHive | Research Intelligence",
  description: "Evidence-led, AI-assisted grant screening for human review."
};

// Applies the stored theme before first paint so the page never flashes the wrong one.
const THEME_SCRIPT = `try{var t=localStorage.getItem("ai-screening-theme");if(t==="dark")document.documentElement.setAttribute("data-theme","dark")}catch(e){}`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${fredoka.variable} ${nunito.variable}`} suppressHydrationWarning>
      <head><script dangerouslySetInnerHTML={{ __html: THEME_SCRIPT }} /></head>
      <body><Navbar /><div className="page">{children}</div></body>
    </html>
  );
}
