import { apiFetch } from "@/lib/api/client";
import { API_BASE, apiUrl } from "@/lib/api/config";
import { getToken } from "@/lib/api/token";

export type BlogStatus = "draft" | "published";

export interface BlogAuthor {
  id: string;
  full_name: string | null;
}

export interface BlogPostSummary {
  id: string;
  slug: string;
  title: string;
  subtitle: string | null;
  excerpt: string | null;
  category: string;
  tags: string[];
  status: BlogStatus;
  read_minutes: number;
  like_count: number;
  comment_count: number;
  cover_media_id: string | null;
  cover_url: string | null;
  author: BlogAuthor;
  created_at: string;
  updated_at: string;
}

export interface BlogPostDetail extends BlogPostSummary {
  body_html: string;
  body_json: Record<string, unknown>;
  liked_by_me: boolean;
}

export interface BlogListResponse {
  items: BlogPostSummary[];
  total: number;
  next_offset: number | null;
}

export interface BlogComment {
  id: string;
  body: string;
  author: BlogAuthor;
  created_at: string;
  is_hidden: boolean;
}

export interface BlogPostInput {
  title: string;
  subtitle?: string | null;
  excerpt?: string | null;
  category?: string;
  tags?: string[];
  body_html?: string;
  body_json?: Record<string, unknown>;
  cover_media_id?: string | null;
  status?: BlogStatus;
}

export function listPosts(params: {
  category?: string;
  q?: string;
  sort?: string;
  limit?: number;
  offset?: number;
}) {
  const qs = new URLSearchParams();
  if (params.category && params.category !== "all")
    qs.set("category", params.category);
  if (params.q) qs.set("q", params.q);
  if (params.sort) qs.set("sort", params.sort);
  qs.set("limit", String(params.limit ?? 24));
  qs.set("offset", String(params.offset ?? 0));
  return apiFetch<BlogListResponse>(`/blog/posts?${qs.toString()}`);
}

export function getFeatured() {
  return apiFetch<BlogPostSummary[]>("/blog/featured");
}

export function getCategoryCounts() {
  return apiFetch<Record<string, number>>("/blog/categories");
}

export function getMyPosts() {
  return apiFetch<BlogPostSummary[]>("/blog/me/posts");
}

export function getPost(slug: string) {
  return apiFetch<BlogPostDetail>(`/blog/posts/${encodeURIComponent(slug)}`);
}

export function getComments(slug: string) {
  return apiFetch<BlogComment[]>(
    `/blog/posts/${encodeURIComponent(slug)}/comments`,
  );
}

export function createPost(input: BlogPostInput) {
  return apiFetch<BlogPostDetail>("/blog/posts", { method: "POST", json: input });
}

export function updatePost(id: string, input: Partial<BlogPostInput>) {
  return apiFetch<BlogPostDetail>(`/blog/posts/${id}`, {
    method: "PATCH",
    json: input,
  });
}

export function deletePost(id: string) {
  return apiFetch<void>(`/blog/posts/${id}`, { method: "DELETE" });
}

export function toggleLike(postId: string, liked: boolean) {
  return apiFetch<BlogPostDetail>(`/blog/posts/${postId}/like`, {
    method: "POST",
    json: { liked },
  });
}

export function addComment(postId: string, body: string) {
  return apiFetch<BlogComment>(`/blog/posts/${postId}/comments`, {
    method: "POST",
    json: { body },
  });
}

export function deleteComment(commentId: string) {
  return apiFetch<void>(`/blog/comments/${commentId}`, { method: "DELETE" });
}

export interface BlogMedia {
  id: string;
  url: string;
}

/** Uploads a cover/inline image. Used by the cover uploader and the rich
 * text editor's image button/paste/drag-drop handlers. */
export async function uploadBlogMedia(file: File): Promise<BlogMedia> {
  const form = new FormData();
  form.append("file", file);
  const token = getToken();
  const res = await fetch(apiUrl("/blog/media"), {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    body: form,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json())?.detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json();
}

/** The backend returns media/cover URLs as `/api/v1/…` paths (already
 * prefixed) — prepend only the origin to get a fully-qualified, publicly
 * fetchable URL for <img src>. */
export function absoluteMediaUrl(pathOrUrl: string): string {
  return pathOrUrl.startsWith("http") ? pathOrUrl : `${API_BASE}${pathOrUrl}`;
}

// --------------------------------------------------------------------------- #
// Admin console
// --------------------------------------------------------------------------- #
export function listAllPostsAdmin(params: {
  status?: string;
  author_id?: string;
  q?: string;
  limit?: number;
  offset?: number;
}) {
  const qs = new URLSearchParams();
  if (params.status) qs.set("status", params.status);
  if (params.author_id) qs.set("author_id", params.author_id);
  if (params.q) qs.set("q", params.q);
  qs.set("limit", String(params.limit ?? 24));
  qs.set("offset", String(params.offset ?? 0));
  return apiFetch<BlogListResponse>(`/admin/blog/posts?${qs.toString()}`);
}

export function getAdminPostComments(postId: string) {
  return apiFetch<BlogComment[]>(`/admin/blog/posts/${postId}/comments`);
}

export function moderateComment(
  commentId: string,
  input: { body?: string; is_hidden?: boolean },
) {
  return apiFetch<BlogComment>(`/admin/blog/comments/${commentId}`, {
    method: "PATCH",
    json: input,
  });
}

export interface BulkActionResult {
  succeeded: string[];
  failed: string[];
}

export function bulkDeletePosts(ids: string[]) {
  return apiFetch<BulkActionResult>("/admin/blog/posts/bulk-delete", {
    method: "POST",
    json: { ids },
  });
}

export function bulkHideComments(ids: string[]) {
  return apiFetch<BulkActionResult>("/admin/blog/comments/bulk-hide", {
    method: "POST",
    json: { ids },
  });
}
