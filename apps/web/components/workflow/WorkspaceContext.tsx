"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { ApiError, createClient, type ApiClient } from "../../lib/api";
import { ACTIVE_DEMO_ROLES, isActiveDemoRole, normalizeDemoRole } from "../../lib/demo-roles";
import type { GrantCall, Role } from "../../lib/types";

const ROLE_KEY = "ai-screening.role";
const CALL_KEY = "ai-screening.call";

export type LoadState = "loading" | "ready" | "error";

export interface WorkspaceValue {
  role: Role;
  setRole: (role: Role) => void;
  client: ApiClient;
  calls: GrantCall[];
  callsState: LoadState;
  callsError: string | null;
  callId: string | null;
  setCallId: (id: string | null) => void;
  call: GrantCall | null;
  refreshCalls: () => Promise<void>;
}

export const WorkspaceContext = createContext<WorkspaceValue | null>(null);

export function useWorkspace(): WorkspaceValue {
  const value = useContext(WorkspaceContext);
  if (!value) throw new Error("useWorkspace must be used inside WorkspaceProvider");
  return value;
}

export function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  const [role, setRoleState] = useState<Role>(ACTIVE_DEMO_ROLES[0]);
  const [callId, setCallIdState] = useState<string | null>(null);
  const [calls, setCalls] = useState<GrantCall[]>([]);
  const [callsState, setCallsState] = useState<LoadState>("loading");
  const [callsError, setCallsError] = useState<string | null>(null);

  const client = useMemo(() => createClient({ role, userId: `demo-${role.toLowerCase().replace(/_/g, "-")}` }), [role]);

  useEffect(() => {
    const storedRole = window.localStorage.getItem(ROLE_KEY);
    const nextRole = normalizeDemoRole(storedRole);
    setRoleState(nextRole);
    if (storedRole !== nextRole) window.localStorage.setItem(ROLE_KEY, nextRole);
    setCallIdState(window.localStorage.getItem(CALL_KEY));
  }, []);

  const setRole = useCallback((next: Role) => {
    if (!isActiveDemoRole(next)) return;
    setRoleState(next);
    window.localStorage.setItem(ROLE_KEY, next);
  }, []);

  const setCallId = useCallback((next: string | null) => {
    setCallIdState(next);
    if (next) window.localStorage.setItem(CALL_KEY, next);
    else window.localStorage.removeItem(CALL_KEY);
  }, []);

  const refreshCalls = useCallback(async () => {
    try {
      const list = await client.listCalls();
      setCalls(list);
      setCallsState("ready");
      setCallsError(null);
      setCallIdState((current) => {
        // A stored selection can outlive the call it points at (for example after the
        // API is restarted). Fall back to a call that exists and persist the correction,
        // so the stale id does not come back on the next load.
        const next = current && list.some((c) => c.id === current) ? current : list[0]?.id ?? null;
        if (next) window.localStorage.setItem(CALL_KEY, next);
        else window.localStorage.removeItem(CALL_KEY);
        return next;
      });
    } catch (error) {
      setCallsState("error");
      setCallsError(error instanceof ApiError ? error.message : "Unable to load grant calls.");
    }
  }, [client]);

  useEffect(() => {
    refreshCalls();
  }, [refreshCalls]);

  const call = calls.find((c) => c.id === callId) ?? null;
  const value: WorkspaceValue = { role, setRole, client, calls, callsState, callsError, callId, setCallId, call, refreshCalls };
  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}
