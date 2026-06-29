export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const API_PREFIX = "/api/v1";

export const apiUrl = (path: string) =>
  `${API_BASE}${API_PREFIX}${path.startsWith("/") ? path : `/${path}`}`;
