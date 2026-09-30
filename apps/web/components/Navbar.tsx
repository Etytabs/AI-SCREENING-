"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Home" },
  { href: "/dashboard", label: "Dashboard" },
];

export default function Navbar() {
  const pathname = usePathname();
  const isActive = (href: string) => (href === "/" ? pathname === "/" : pathname.startsWith(href));
  if (pathname === "/") return null;
  return (
    <>
      <header className="navbar">
        <Link href="/" className="nav-brand"><span>AI</span><div><b>AI-SCREENING</b><small>Research Intelligence</small></div></Link>
        <nav className="nav-links">
          {links.map(l => <Link key={l.href} href={l.href} className={isActive(l.href) ? "active" : ""}>{l.label}</Link>)}
        </nav>
      </header>
      <div className="nav-spacer" />
    </>
  );
}
