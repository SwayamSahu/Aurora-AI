import { apiFetch } from "@/lib/api/client";

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
  preferences: Record<string, unknown>;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export function register(input: {
  email: string;
  password: string;
  full_name?: string;
}) {
  return apiFetch<AuthResponse>("/auth/register", {
    method: "POST",
    json: input,
    auth: false,
  });
}

export function login(email: string, password: string) {
  return apiFetch<AuthResponse>("/auth/login", {
    method: "POST",
    form: { username: email, password },
    auth: false,
  });
}

export function fetchMe() {
  return apiFetch<User>("/auth/me");
}

export function requestPasswordReset(email: string) {
  return apiFetch<{ message: string; reset_token: string | null }>(
    "/auth/password-reset/request",
    { method: "POST", json: { email }, auth: false },
  );
}

export function confirmPasswordReset(token: string, newPassword: string) {
  return apiFetch<User>("/auth/password-reset/confirm", {
    method: "POST",
    json: { token, new_password: newPassword },
    auth: false,
  });
}

export function updateProfile(input: {
  full_name?: string;
  preferences?: Record<string, unknown>;
}) {
  return apiFetch<User>("/users/me", { method: "PATCH", json: input });
}

export function changePassword(currentPassword: string, newPassword: string) {
  return apiFetch<void>("/users/me/change-password", {
    method: "POST",
    json: { current_password: currentPassword, new_password: newPassword },
  });
}
