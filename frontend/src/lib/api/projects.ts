import { apiFetch } from "@/lib/api/client";

export interface Project {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
  asset_count?: number;
}

export type ProjectSort = "recent" | "oldest" | "name";

export function listProjects(params?: { search?: string; sort?: ProjectSort }) {
  const q = new URLSearchParams();
  if (params?.search) q.set("search", params.search);
  if (params?.sort) q.set("sort", params.sort);
  const qs = q.toString();
  return apiFetch<Project[]>(`/projects${qs ? `?${qs}` : ""}`);
}

export function getProject(id: string) {
  return apiFetch<Project>(`/projects/${id}`);
}

export function createProject(input: { name: string; description?: string }) {
  return apiFetch<Project>("/projects", { method: "POST", json: input });
}

export function updateProject(
  id: string,
  input: { name?: string; description?: string },
) {
  return apiFetch<Project>(`/projects/${id}`, { method: "PATCH", json: input });
}

export function deleteProject(id: string) {
  return apiFetch<void>(`/projects/${id}`, { method: "DELETE" });
}

export function duplicateProject(id: string) {
  return apiFetch<Project>(`/projects/${id}/duplicate`, { method: "POST" });
}
