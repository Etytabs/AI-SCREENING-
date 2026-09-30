"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ROLE_LABELS } from "../../lib/labels";
import type { Role } from "../../lib/types";
import { SyntheticBadge } from "./ui";
import { useWorkspace, WorkspaceProvider } from "./WorkspaceContext";

export const NAV_ITEMS = [
  { href: "/dashboard", label: "Overview" },
  { href: "/dashboard/check", label: "Research Check" },
  { href: "/dashboard/calls", label: "Grant Calls" },
  { href: "/dashboard/applications", label: "Applications" },
  { href: "/dashboard/screening", label: "Screening" },
  { href: "/dashboard/review", label: "Review" },
  { href: "/dashboard/publications", label: "Publications" },
  { href: "/dashboard/sources", label: "Sources" },
];

function isActive(rawPathname: string, href: string) {
  const pathname = rawPathname.replace(/\/+$/, "") || "/";
  return href === "/dashboard" ? pathname === "/dashboard" || pathname === "/dashboard/report" : pathname.startsWith(href);
}

function Sidebar() {
  const pathname = usePathname() ?? "/dashboard";
  const { calls, callId, setCallId, call, role, setRole, callsState } = useWorkspace();
  return (
    <aside className="sidebar ws-sidebar" aria-label="Workspace navigation">
      <div className="ws-call-picker">
        <label htmlFor="call-picker" className="sidebar-label">GRANT CALL</label>
        <select id="call-picker" value={callId ?? ""} onChange={(e) => setCallId(e.target.value || null)} disabled={callsState !== "ready" || !calls.length}>
          {!calls.length && <option value="">{callsState === "loading" ? "Loading…" : "No calls yet"}</option>}
          {calls.map((c) => (
            <option key={c.id} value={c.id}>{c.reference ? `${c.reference} · ` : ""}{c.name}</option>
          ))}
        </select>
        {call && <SyntheticBadge origin={call.data_origin} />}
      </div>
      <nav>
        {NAV_ITEMS.map((item) => (
          <Link key={item.href} href={item.href} className={isActive(pathname, item.href) ? "side-link active" : "side-link"} aria-current={isActive(pathname, item.href) ? "page" : undefined}>
            <span>{item.label}</span>
          </Link>
        ))}
      </nav>
      <div className="sidebar-foot ws-identity">
        <label htmlFor="role-picker"><b>ACTING AS</b></label>
        <select id="role-picker" value={role} onChange={(e) => setRole(e.target.value as Role)}>
          {(Object.keys(ROLE_LABELS) as Role[]).map((r) => <option key={r} value={r}>{ROLE_LABELS[r]}</option>)}
        </select>
        <small>Demo identity only. The role is sent as a header and is not authenticated.</small>
      </div>
    </aside>
  );
}

export default function WorkspaceShell({ children }: { children: React.ReactNode }) {
  return (
    <WorkspaceProvider>
      <main className="shell">
        <Sidebar />
        <section className="workspace ws-main">{children}</section>
      </main>
    </WorkspaceProvider>
  );
}
