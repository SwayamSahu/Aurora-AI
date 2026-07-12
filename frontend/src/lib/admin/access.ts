import type { User } from "@/lib/api/auth";

/** Full admin: finance, user management, audit log, plus everything a
 * moderator can do. */
export const isAdmin = (u: User | null | undefined): boolean => !!u?.is_superuser;

/** Moderator OR admin — content moderation surfaces. */
export const isModerator = (u: User | null | undefined): boolean =>
  u?.role === "moderator" || !!u?.is_superuser;
