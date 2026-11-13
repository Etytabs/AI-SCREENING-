"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import ThemeToggle from "./ThemeToggle";
import logo from "../public/brand/logo-on-dark.png";

const links = [
  { href: "/", label: "Home" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/login", label: "Sign in" },
];

export default function Navbar() {
  const pathname = usePathname();
  const isActive = (href: string) => (href === "/" ? pathname === "/" : pathname.startsWith(href));
  if (pathname === "/") return null;
  return (
    <>
      <header className="navbar">
        <Link href="/" className="nav-brand" aria-label="ShakaHive home"><Image src={logo} alt="ShakaHive" priority className="brand-logo" /><small>Research Intelligence</small></Link>
        <nav className="nav-links" aria-label="Main navigation">
          {links.map(l => <Link key={l.href} href={l.href} className={isActive(l.href) ? "active" : ""}>{l.label}</Link>)}
          <ThemeToggle />
        </nav>
      </header>
      <div className="nav-spacer" />
    </>
  );
}
