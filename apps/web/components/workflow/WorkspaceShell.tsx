"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { ACTIVE_DEMO_ROLES, DEMO_ROLE_CONFIG, isActiveDemoRole, isDemoRouteAvailable } from "../../lib/demo-roles";
import { Notice, SyntheticBadge } from "./ui";
import { useWorkspace, WorkspaceProvider } from "./WorkspaceContext";

function isActive(rawPathname: string, href: string) {
  const pathname = rawPathname.replace(/\/+$/, "") || "/";
  return href === "/dashboard" ? pathname === "/dashboard" : pathname === href || pathname.startsWith(`${href}/`);
}

function Sidebar() {
  const pathname = usePathname() ?? "/dashboard";
  const { calls, callId, setCallId, call, role, setRole, callsState } = useWorkspace();
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
      <div className="sidebar-foot ws-identity">
        <label htmlFor="role-picker"><b>DEMO ROLE</b></label>
        <select
          id="role-picker"
          value={role}
          disabled={ACTIVE_DEMO_ROLES.length === 1}
          onChange={(event) => {
            const nextRole = event.currentTarget.value;
            if (isActiveDemoRole(nextRole)) setRole(nextRole);
          }}
        >
          {ACTIVE_DEMO_ROLES.map((demoRole) => <option key={demoRole} value={demoRole}>{DEMO_ROLE_CONFIG[demoRole].label}</option>)}
        </select>
        <small>Demo identity only. This role is sent as a header and is not authenticated. Only the implemented Grant Administrator workflow is available in this demo.</small>
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
