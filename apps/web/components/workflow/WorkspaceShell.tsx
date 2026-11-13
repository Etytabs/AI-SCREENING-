"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { DEMO_ROLE_CONFIG, isDemoRouteAvailable } from "../../lib/demo-roles";
import { Notice, SyntheticBadge } from "./ui";
import { useWorkspace, WorkspaceProvider } from "./WorkspaceContext";

function isActive(rawPathname: string, href: string) {
  const pathname = rawPathname.replace(/\/+$/, "") || "/";
  return href === "/dashboard" ? pathname === "/dashboard" : pathname === href || pathname.startsWith(`${href}/`);
}

function Sidebar() {
  const pathname = usePathname() ?? "/dashboard";
  const { calls, callId, setCallId, call, role, callsState } = useWorkspace();
  const roleDefinition = DEMO_ROLE_CONFIG[role];
  return (
    <aside className="sidebar ws-sidebar" aria-label="Workspace navigation">
      <div className="ws-call-picker">
        <p className="workspace-caption">RESEARCH INTELLIGENCE<br /><strong>Grant screening</strong></p>
        <label htmlFor="call-picker" className="sidebar-label">GRANT CALL</label>
        <select id="call-picker" value={callId ?? ""} onChange={(e) => setCallId(e.target.value || null)} disabled={callsState !== "ready" || !calls.length}>
          {!calls.length && <option value="">{callsState === "loading" ? "Loading…" : "No calls yet"}</option>}
          {calls.map((c) => (
            <option key={c.id} value={c.id}>{c.reference ? `${c.reference} · ` : ""}{c.name}</option>
          ))}
        </select>
        {call && <SyntheticBadge origin={call.data_origin} />}
      </div>
      <nav aria-label="Grant screening">
        {roleDefinition.navigation.map((item) => (
          <Link key={item.href} href={item.href} className={isActive(pathname, item.href) ? "side-link active" : "side-link"} aria-current={isActive(pathname, item.href) ? "page" : undefined}>
            <span className="side-link-label">{item.label}</span>
          </Link>
        ))}
      </nav>
      <div className="sidebar-foot ws-identity" role="group" aria-labelledby="demo-role-heading">
        <span id="demo-role-heading" className="sidebar-label">ACTIVE DEMO ROLE · READ-ONLY</span>
        <strong className="ws-identity-role">{roleDefinition.label}</strong>
        <small>Only implemented demo workflow.</small>
        <small>Demo identity only. The role is sent as a header and is not authenticated.</small>
      </div>
    </aside>
  );
}

function WorkspaceAccessBoundary({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() ?? "/dashboard";
  const router = useRouter();
  const { role } = useWorkspace();
  const roleDefinition = DEMO_ROLE_CONFIG[role];
  const available = isDemoRouteAvailable(role, pathname);

  useEffect(() => {
    if (!available) router.replace(roleDefinition.landingPath);
  }, [available, roleDefinition.landingPath, router]);

  if (!available) {
    return (
      <section className="workspace ws-main" aria-live="polite">
        <div className="ws-role-current" aria-label={`Current demo role: ${roleDefinition.label}`}>
          <span>DEMO WORKSPACE</span>
          <strong>{roleDefinition.label}</strong>
        </div>
        <Notice kind="info" title="Screen unavailable for this demo role">
          Returning to the {roleDefinition.label} workspace.
        </Notice>
      </section>
    );
  }
  return (
    <section className="workspace ws-main">
      <div className="ws-role-current" aria-label={`Current demo role: ${roleDefinition.label}`}>
        <span>DEMO WORKSPACE</span>
        <strong>{roleDefinition.label}</strong>
      </div>
      {children}
    </section>
  );
}

export default function WorkspaceShell({ children }: { children: React.ReactNode }) {
  return (
    <WorkspaceProvider>
      <main className="shell dashboard-shell-flow">
        <Sidebar />
        <WorkspaceAccessBoundary>
          {children}
        </WorkspaceAccessBoundary>
      </main>
    </WorkspaceProvider>
  );
}
