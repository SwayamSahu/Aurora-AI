"use client";

import * as React from "react";

import {
  type AuthResponse,
  type User,
  fetchMe,
  login as apiLogin,
  register as apiRegister,
} from "@/lib/api/auth";
import { clearToken, getToken, setToken } from "@/lib/api/token";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

interface AuthContextValue {
  user: User | null;
  status: AuthStatus;
  login: (email: string, password: string) => Promise<void>;
  register: (input: {
    email: string;
    password: string;
    full_name?: string;
  }) => Promise<void>;
  logout: () => void;
  setUser: (user: User) => void;
}

const AuthContext = React.createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<User | null>(null);
  const [status, setStatus] = React.useState<AuthStatus>("loading");

  // Hydrate session from a stored token on first load.
  React.useEffect(() => {
    let cancelled = false;
    const token = getToken();
    if (!token) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setStatus("unauthenticated");
      return;
    }
    fetchMe()
      .then((u) => {
        if (cancelled) return;
        setUser(u);
        setStatus("authenticated");
      })
      .catch(() => {
        if (cancelled) return;
        clearToken();
        setStatus("unauthenticated");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const applyAuth = React.useCallback((res: AuthResponse) => {
    setToken(res.access_token);
    setUser(res.user);
    setStatus("authenticated");
  }, []);

  const login = React.useCallback(
    async (email: string, password: string) => {
      applyAuth(await apiLogin(email, password));
    },
    [applyAuth],
  );

  const register = React.useCallback(
    async (input: { email: string; password: string; full_name?: string }) => {
      applyAuth(await apiRegister(input));
    },
    [applyAuth],
  );

  const logout = React.useCallback(() => {
    clearToken();
    setUser(null);
    setStatus("unauthenticated");
  }, []);

  const value = React.useMemo<AuthContextValue>(
    () => ({ user, status, login, register, logout, setUser }),
    [user, status, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = React.useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within <AuthProvider>");
  return ctx;
}
