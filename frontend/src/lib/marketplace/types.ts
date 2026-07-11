export type ListingKind = "video" | "image";
export type ListingStatus = "draft" | "active" | "sold" | "delisted";

export interface ListingSeller {
  id: string;
  full_name: string | null;
}

export interface MarketplaceListing {
  id: string;
  title: string;
  description: string | null;
  category: string;
  tags: string[];
  price_credits: number;
  stock: number;
  status: ListingStatus;
  like_count: number;
  comment_count: number;
  cover_media_id: string | null;
  cover_url: string | null;
  cover_content_type: string | null;
  kind: ListingKind;
  width: number | null;
  height: number | null;
  duration_seconds: number | null;
  seller: ListingSeller;
  created_at: string;
  updated_at: string;
}

export type ListingDetail = MarketplaceListing;

export interface ListingListResponse {
  items: MarketplaceListing[];
  total: number;
  next_offset: number | null;
}

export interface CartItemRead {
  id: string;
  listing: MarketplaceListing;
  created_at: string;
}

export interface CartRead {
  items: CartItemRead[];
  total_credits: number;
}

export interface OrderItemRead {
  id: string;
  listing_id: string | null;
  title: string;
  price_credits: number;
  cloned_asset_id: string | null;
}

export interface OrderRead {
  id: string;
  total_credits: number;
  status: string;
  items: OrderItemRead[];
  created_at: string;
}

export interface SaleRead {
  id: string;
  order_id: string;
  title: string;
  price_credits: number;
  buyer_id: string;
  created_at: string;
}

export interface WalletRead {
  balance_credits: number;
  listing_quota: number;
  active_plan_id: string | null;
}

export interface CreditTransactionRead {
  id: string;
  type: string;
  amount: number;
  balance_after: number;
  note: string | null;
  created_at: string;
}

export interface WalletHistoryResponse {
  items: CreditTransactionRead[];
  total: number;
  next_offset: number | null;
}

export interface CreditPlanRead {
  id: string;
  name: string;
  price_cents: number;
  credits_granted: number;
  listing_quota: number;
}

export interface PlanPurchaseRead {
  id: string;
  plan_id: string;
  status: string;
  price_cents: number;
  credits_granted: number;
  created_at: string;
}

export interface SellableAsset {
  id: string;
  name: string;
  kind: string;
  content_type: string;
  content_url: string;
  duration_seconds: number | null;
  width: number | null;
  height: number | null;
}
