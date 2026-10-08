"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Activity, ArrowUpRight, BrainCircuit, FilePlus2, FileText, LayoutDashboard, Menu, Moon, Sun, UsersRound, X } from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
  { label: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { label: "Applications", href: "/applications", icon: FileText },
  { label: "AI screening", href: "/screening", icon: Activity },
  { label: "Researcher registry", href: "/registry", icon: UsersRound },
];

export function ThemeToggle() {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem("novara-theme");
    const useDark = saved ? saved === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
    document.documentElement.classList.toggle("dark", useDark);
    setDark(useDark);
  }, []);

  const toggleTheme = () => {
    const nextDark = !dark;
    document.documentElement.classList.toggle("dark", nextDark);
    localStorage.setItem("novara-theme", nextDark ? "dark" : "light");
    setDark(nextDark);
  };

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={`Switch to ${dark ? "light" : "dark"} mode`}
      title={`Switch to ${dark ? "light" : "dark"} mode`}
      className="icon-button"
    >
      {dark ? <Sun size={18} /> : <Moon size={18} />}
    </button>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const isPublic = pathname === "/login" || pathname === "/register";
  const isWorkspace = pathname.startsWith("/dashboard") || pathname.startsWith("/applications") || pathname.startsWith("/screening") || pathname.startsWith("/registry");

  useEffect(() => {
    setMobileMenuOpen(false);
  }, [pathname]);

  if (isPublic || !isWorkspace) {
    return (
      <>
        <div className="fixed right-5 top-5 z-50"><ThemeToggle /></div>
        {children}
      </>
    );
  }

  return (
    <div className="workspace-shell">
      {mobileMenuOpen && (
        <button
          type="button"
          className="workspace-sidebar-backdrop lg:hidden"
          aria-label="Close navigation menu"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}
      <aside className={cn("workspace-sidebar", mobileMenuOpen && "workspace-sidebar-mobile-open")} id="workspace-navigation">
        <Link href="/dashboard" className="brand-lockup">
          <span className="brand-mark"><BrainCircuit size={21} /></span>
          <span><strong>SHAKAHIVE</strong><small>Research intelligence</small></span>
        </Link>
        <div className="sidebar-label">WORKSPACE</div>
        <nav className="sidebar-nav" aria-label="Main navigation">
          {navigation.map(({ label, href, icon: Icon }) => {
            const active = pathname === href || (href === "/applications" && pathname.startsWith("/applications"));
            return (
              <Link key={href} href={href} className={cn("sidebar-link", active && "sidebar-link-active")}>
                <Icon size={18} strokeWidth={1.8} />
                <span>{label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="sidebar-spacer" />
        <Link href="/applications/new" className="sidebar-create">
          <FilePlus2 size={17} />
          <span>New application</span>
          <ArrowUpRight size={15} className="ml-auto" />
        </Link>
        <div className="sidebar-tenant">
          <span className="tenant-dot" />
          <span><strong>NRIF workspace</strong><small>National Research &amp; Innovation Fund</small></span>
        </div>
      </aside>
      <div className="workspace-main">
        <header className="workspace-topbar">
          <button
            type="button"
            className="icon-button lg:hidden"
            aria-label={mobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
            aria-expanded={mobileMenuOpen}
            aria-controls="workspace-navigation"
            onClick={() => setMobileMenuOpen((open) => !open)}
          >
            {mobileMenuOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
          <div className="topbar-context">SHAKAHIVE <span>/</span> {navigation.find((item) => pathname.startsWith(item.href))?.label || "Workspace"}</div>
          <div className="topbar-actions">
            <span className="workspace-status"><span className="status-dot" /> Screening workspace</span>
            <ThemeToggle />
            <Link href="/login" className="avatar-link" aria-label="Account">S</Link>
          </div>
        </header>
        <main className="workspace-content">{children}</main>
      </div>
    </div>
  );
}