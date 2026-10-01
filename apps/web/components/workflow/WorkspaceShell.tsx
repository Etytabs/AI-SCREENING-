"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ROLE_LABELS } from "../../lib/labels";
import type { Role } from "../../lib/types";
import { SyntheticBadge } from "./ui";
import { useWorkspace, WorkspaceProvider } from "./WorkspaceContext";

export const NAV_ITEMS = {
  NCST_GRANT_PERSONNEL: [
    { href: "/dashboard", label: "Overview", icon: "⌂" },
    { href: "/dashboard/calls", label: "Grant Calls", icon: "□" },
    { href: "/dashboard/applications", label: "Applications", icon: "▤" },
    { href: "/dashboard/check", label: "Research Check", icon: "↥" },
    { href: "/dashboard/duplication", label: "Duplication", icon: "⧉" },
    { href: "/dashboard/screening", label: "Screening", icon: "◈" },
    { href: "/dashboard/review", label: "Human Review", icon: "✓" },
    { href: "/dashboard/publications", label: "Publications", icon: "◫" },
    { href: "/dashboard/sources", label: "Evidence Sources", icon: "◎" },
  ],
  GRANT_INSTITUTION: [
    { href: "/dashboard", label: "My Workspace", icon: "⌂" },
    { href: "/dashboard/calls", label: "Funding Calls", icon: "□" },
    { href: "/dashboard/applications", label: "My Submissions", icon: "▤" },
    { href: "/dashboard/check", label: "Submission Check", icon: "✓" },
    { href: "/dashboard/publications", label: "Research Outputs", icon: "◫" },
  ],
  RESEARCHER_APPLICANT: [
    { href: "/dashboard", label: "My Workspace", icon: "⌂" },
    { href: "/dashboard/calls", label: "Find Funding", icon: "□" },
    { href: "/dashboard/applications", label: "My Applications", icon: "▤" },
    { href: "/dashboard/check", label: "Research Check", icon: "✓" },
    { href: "/dashboard/publications", label: "My Publications", icon: "◫" },
  ],
  GRANT_ADMINISTRATOR: [
    { href: "/dashboard", label: "Overview", icon: "⌂" },
    { href: "/dashboard/calls", label: "Grant Calls", icon: "□" },
    { href: "/dashboard/applications", label: "Applications", icon: "▤" },
    { href: "/dashboard/check", label: "Research Check", icon: "↥" },
    { href: "/dashboard/duplication", label: "Duplication", icon: "⧉" },
    { href: "/dashboard/screening", label: "Screening", icon: "◈" },
    { href: "/dashboard/review", label: "Human Review", icon: "✓" },
  ],
  REVIEWER: [
    { href: "/dashboard", label: "Review Overview", icon: "⌂" },
    { href: "/dashboard/applications", label: "Applications", icon: "▤" },
    { href: "/dashboard/review", label: "Human Review", icon: "✓" },
  ],
  SYSTEM_ADMINISTRATOR: [
    { href: "/dashboard", label: "Overview", icon: "⌂" },
    { href: "/dashboard/sources", label: "Evidence Sources", icon: "◎" },
  ],
} as const;

const ROLE_PICKER_OPTIONS: Role[] = ["NCST_GRANT_PERSONNEL", "GRANT_INSTITUTION", "RESEARCHER_APPLICANT"];

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
        <label htmlFor="call-picker" className="sidebar-label">Selected call</label>
        <select id="call-picker" value={callId ?? ""} onChange={(e) => setCallId(e.target.value || null)} disabled={callsState !== "ready" || !calls.length}>
          {!calls.length && <option value="">{callsState === "loading" ? "Loading…" : "No calls yet"}</option>}
          {calls.map((c) => (
            <option key={c.id} value={c.id}>{c.name}{c.reference ? ` · ${c.reference}` : ""}</option>
          ))}
        </select>
        {call && <SyntheticBadge origin={call.data_origin} />}
      </div>
      <nav>
        {NAV_ITEMS[role].map((item) => (
          <Link key={item.href} href={item.href} className={isActive(pathname, item.href) ? "side-link active" : "side-link"} aria-current={isActive(pathname, item.href) ? "page" : undefined}>
            <span className="side-link-icon" aria-hidden="true">{item.icon}</span><span className="side-link-label">{item.label}</span>
          </Link>
        ))}
      </nav>
      <div className="sidebar-foot ws-identity">
        <label htmlFor="role-picker"><b>PRIMARY USER</b></label>
        <select id="role-picker" value={ROLE_PICKER_OPTIONS.includes(role) ? role : "NCST_GRANT_PERSONNEL"} onChange={(e) => setRole(e.target.value as Role)}>
          {ROLE_PICKER_OPTIONS.map((r) => <option key={r} value={r}>{ROLE_LABELS[r]}</option>)}
        </select>
        <small>Demo identity only. Selecting a user changes the workspace focus and navigation.</small>
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
