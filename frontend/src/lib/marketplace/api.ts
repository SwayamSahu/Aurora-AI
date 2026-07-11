import { apiFetch } from "@/lib/api/client";
import { API_BASE } from "@/lib/api/config";
import { getToken } from "@/lib/api/token";
import type {
  AdminPlanInput,
  AdminPlanRead,
  CartRead,
  CreditPlanRead,
  ListingCommentRead,
  ListingDetail,
  ListingListResponse,
  MarketplaceListing,
  OrderRead,
  PlanPurchaseRead,
  SaleRead,
  SellableAsset,
  WalletHistoryResponse,
  WalletRead,
} from "@/lib/marketplace/types";

/** The backend returns media URLs as `/api/v1/…` paths (already prefixed)
 * — prepend only the origin, mirroring `lib/blog/api.ts`'s `absoluteMediaUrl`. */
export function absoluteMediaUrl(pathOrUrl: string): string {
  return pathOrUrl.startsWith("http") ? pathOrUrl : `${API_BASE}${pathOrUrl}`;
}

export interface ListingInput {
  title: string;
  description?: string | null;
  category?: string;
  tags?: string[];
  price_credits: number;
  stock?: number;
  source_asset_id: string;
  cover_media_id?: string | null;
  status?: "draft" | "active";
}

export interface ListingUpdateInput {
  title?: string;
  description?: string | null;
  category?: string;
  tags?: string[];
  price_credits?: number;
  stock?: number;
  cover_media_id?: string | null;
  status?: "draft" | "active" | "delisted";
}

// --------------------------------------------------------------------------- #
// Browse
// --------------------------------------------------------------------------- #
export function listListings(params: {
  category?: string;
  q?: string;
  sort?: string;
  limit?: number;
  offset?: number;
}) {
  const qs = new URLSearchParams();
  if (params.category && params.category !== "all") qs.set("category", params.category);
  if (params.q) qs.set("q", params.q);
  if (params.sort) qs.set("sort", params.sort);
  qs.set("limit", String(params.limit ?? 24));
  qs.set("offset", String(params.offset ?? 0));
  // Not `auth: false` — a logged-in seller's token must still be sent so
  // the backend's OptionalUser can resolve them (needed to see their own
  // drafts); it's simply omitted automatically when no token exists.
  return apiFetch<ListingListResponse>(`/marketplace/listings?${qs.toString()}`);
}

export function getListing(id: string) {
  return apiFetch<ListingDetail>(`/marketplace/listings/${encodeURIComponent(id)}`);
}

export function getCategoryCounts() {
  return apiFetch<Record<string, number>>("/marketplace/listings/categories");
}

/** Same-category first, capped and self-excluded — stand-in for vector
 * similarity until a real recommendation query exists. */
export async function getSimilar(id: string, category: string, limit = 12) {
  const page = await listListings({ category, limit: limit + 1 });
  return page.items.filter((item) => item.id !== id).slice(0, limit);
}

// --------------------------------------------------------------------------- #
// Seller: listings + assets
// --------------------------------------------------------------------------- #
export function getMyListings() {
  return apiFetch<MarketplaceListing[]>("/marketplace/me/listings");
}

export function getMySellableAssets() {
  return apiFetch<SellableAsset[]>("/marketplace/me/assets");
}

export function createListing(input: ListingInput) {
  return apiFetch<ListingDetail>("/marketplace/listings", { method: "POST", json: input });
}

export function updateListing(id: string, input: ListingUpdateInput) {
  return apiFetch<ListingDetail>(`/marketplace/listings/${id}`, {
    method: "PATCH",
    json: input,
  });
}

export function deleteListing(id: string) {
  return apiFetch<void>(`/marketplace/listings/${id}`, { method: "DELETE" });
}

export interface ListingMedia {
  id: string;
  url: string;
}

export async function uploadListingMedia(file: File): Promise<ListingMedia> {
  const form = new FormData();
  form.append("file", file);
  const token = getToken();
  const res = await fetch(`${API_BASE}/api/v1/marketplace/listings/media`, {
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

// --------------------------------------------------------------------------- #
// Cart + checkout + orders
// --------------------------------------------------------------------------- #
export function getCart() {
  return apiFetch<CartRead>("/marketplace/cart");
}

export function addToCart(listingId: string) {
  return apiFetch<CartRead>("/marketplace/cart", {
    method: "POST",
    json: { listing_id: listingId },
  });
}

export function removeFromCart(cartItemId: string) {
  return apiFetch<void>(`/marketplace/cart/${cartItemId}`, { method: "DELETE" });
}

export function checkout() {
  return apiFetch<OrderRead>("/marketplace/checkout", { method: "POST" });
}

export function getMyOrders() {
  return apiFetch<OrderRead[]>("/marketplace/orders");
}

export function getMySales() {
  return apiFetch<SaleRead[]>("/marketplace/orders/sales");
}

// --------------------------------------------------------------------------- #
// Wallet + plans
// --------------------------------------------------------------------------- #
export function getWallet() {
  return apiFetch<WalletRead>("/marketplace/wallet");
}

export function getWalletTransactions(limit = 24, offset = 0) {
  return apiFetch<WalletHistoryResponse>(
    `/marketplace/wallet/transactions?limit=${limit}&offset=${offset}`,
  );
}

export function listPlans() {
  return apiFetch<CreditPlanRead[]>("/marketplace/plans", { auth: false });
}

export function purchasePlan(planId: string) {
  return apiFetch<PlanPurchaseRead>(`/marketplace/plans/${planId}/purchase`, {
    method: "POST",
  });
}

// --------------------------------------------------------------------------- #
// Engagement — likes + comments
// --------------------------------------------------------------------------- #
export function toggleListingLike(listingId: string, liked: boolean) {
  return apiFetch<ListingDetail>(`/marketplace/listings/${listingId}/like`, {
    method: "POST",
    json: { liked },
  });
}

export function getListingComments(listingId: string) {
  return apiFetch<ListingCommentRead[]>(`/marketplace/listings/${listingId}/comments`);
}

export function addListingComment(listingId: string, body: string) {
  return apiFetch<ListingCommentRead>(`/marketplace/listings/${listingId}/comments`, {
    method: "POST",
    json: { body },
  });
}

export function deleteListingComment(commentId: string) {
  return apiFetch<void>(`/marketplace/comments/${commentId}`, { method: "DELETE" });
}

// --------------------------------------------------------------------------- #
// Admin console
// --------------------------------------------------------------------------- #
export function listAdminPlans() {
  return apiFetch<AdminPlanRead[]>("/admin/marketplace/plans");
}

export function createAdminPlan(input: AdminPlanInput) {
  return apiFetch<AdminPlanRead>("/admin/marketplace/plans", {
    method: "POST",
    json: input,
  });
}

export function updateAdminPlan(id: string, input: Partial<AdminPlanInput>) {
  return apiFetch<AdminPlanRead>(`/admin/marketplace/plans/${id}`, {
    method: "PATCH",
    json: input,
  });
}

export function listAdminListings(status?: string) {
  const qs = status ? `?status=${encodeURIComponent(status)}` : "";
  return apiFetch<MarketplaceListing[]>(`/admin/marketplace/listings${qs}`);
}

export function adminDelistListing(id: string) {
  return apiFetch<MarketplaceListing>(`/admin/marketplace/listings/${id}/delist`, {
    method: "POST",
  });
}

export function adminAdjustWallet(userId: string, amount: number, note: string) {
  return apiFetch<{ balance_credits: number }>(
    `/admin/marketplace/wallets/${userId}/adjust`,
    { method: "POST", json: { amount, note } },
  );
}

export function adminRefundOrder(orderId: string) {
  return apiFetch<OrderRead>(`/admin/marketplace/orders/${orderId}/refund`, {
    method: "POST",
  });
}

export function getAdminListingComments(listingId: string) {
  return apiFetch<ListingCommentRead[]>(
    `/admin/marketplace/listings/${listingId}/comments`,
  );
}

export function moderateListingComment(
  commentId: string,
  input: { body?: string; is_hidden?: boolean },
) {
  return apiFetch<ListingCommentRead>(`/admin/marketplace/comments/${commentId}`, {
    method: "PATCH",
    json: input,
  });
}
