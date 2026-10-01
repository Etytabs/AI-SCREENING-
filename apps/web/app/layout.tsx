import "./globals.css";
import type { Metadata } from "next";
import Navbar from "../components/Navbar";

export const metadata: Metadata = {
  title: "shakaHive | Research Intelligence",
  description: "AI-assisted grant screening and publication reconciliation."
};

// Applies the stored theme before first paint so the page never flashes the wrong one.
const THEME_SCRIPT = `try{var t=localStorage.getItem("ai-screening-theme");if(t==="dark")document.documentElement.setAttribute("data-theme","dark")}catch(e){}`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head><script dangerouslySetInnerHTML={{ __html: THEME_SCRIPT }} /></head>
      <body><Navbar /><div className="page">{children}</div></body>
    </html>
  );
}
