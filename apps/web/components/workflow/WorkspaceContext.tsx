"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { ApiError, createClient, type ApiClient } from "../../lib/api";
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
  const [role, setRoleState] = useState<Role>("GRANT_ADMINISTRATOR");
  const [callId, setCallIdState] = useState<string | null>(null);
  const [calls, setCalls] = useState<GrantCall[]>([]);
  const [callsState, setCallsState] = useState<LoadState>("loading");
  const [callsError, setCallsError] = useState<string | null>(null);

  const client = useMemo(() => createClient({ role, userId: `demo-${role.toLowerCase().replace(/_/g, "-")}` }), [role]);

  useEffect(() => {
    const storedRole = window.localStorage.getItem(ROLE_KEY) as Role | null;
    if (storedRole) setRoleState(storedRole);
    setCallIdState(window.localStorage.getItem(CALL_KEY));
  }, []);

  const setRole = useCallback((next: Role) => {
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
      setCallIdState((current) => (current && list.some((c) => c.id === current) ? current : list[0]?.id ?? null));
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
