"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import {
  DEMO_SESSION_EXPIRED_EVENT,
  loginDemo as requestLogin,
  logoutDemo as requestLogout,
  type DemoIdentity,
  type DemoWorkspace,
} from "../../lib/api";

export interface DemoAuthValue {
  accessToken: string | null;
  identity: DemoIdentity | null;
  login: (credentials: {
    email: string;
    password: string;
    workspace: DemoWorkspace;
  }) => Promise<DemoIdentity>;
  logout: () => Promise<void>;
}

export const DemoAuthContext = createContext<DemoAuthValue | null>(null);

export function useDemoAuth(): DemoAuthValue {
  const value = useContext(DemoAuthContext);
  if (!value) throw new Error("useDemoAuth must be used inside DemoAuthProvider");
  return value;
}

export function DemoAuthProvider({ children }: { children: React.ReactNode }) {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [identity, setIdentity] = useState<DemoIdentity | null>(null);
  const [expiresAt, setExpiresAt] = useState<number | null>(null);

  const clearSession = useCallback(() => {
    setAccessToken(null);
    setIdentity(null);
    setExpiresAt(null);
  }, []);

  useEffect(() => {
    window.addEventListener(DEMO_SESSION_EXPIRED_EVENT, clearSession);
    return () => window.removeEventListener(DEMO_SESSION_EXPIRED_EVENT, clearSession);
  }, [clearSession]);

  useEffect(() => {
    if (expiresAt === null) return;
    const timeout = window.setTimeout(
      clearSession,
      Math.max(0, expiresAt - Date.now()),
    );
    return () => window.clearTimeout(timeout);
  }, [clearSession, expiresAt]);

  const login = useCallback(async (credentials: {
    email: string;
    password: string;
    workspace: DemoWorkspace;
  }) => {
    const session = await requestLogin(credentials);
    setAccessToken(session.access_token);
    setIdentity(session.identity);
    setExpiresAt(Date.now() + session.expires_in * 1000);
    return session.identity;
  }, []);

  const logout = useCallback(async () => {
    const token = accessToken;
    clearSession();
    if (token) await requestLogout(token);
  }, [accessToken, clearSession]);

  const value = useMemo(
    () => ({ accessToken, identity, login, logout }),
    [accessToken, identity, login, logout],
  );
  return <DemoAuthContext.Provider value={value}>{children}</DemoAuthContext.Provider>;
}
