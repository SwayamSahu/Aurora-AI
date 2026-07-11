import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  addToCart,
  checkout,
  createListing,
  deleteListing,
  getCart,
  getCategoryCounts,
  getListing,
  getSimilar,
  getMyListings,
  getMyOrders,
  getMySales,
  getMySellableAssets,
  getWallet,
  getWalletTransactions,
  listListings,
  listPlans,
  purchasePlan,
  removeFromCart,
  updateListing,
  type ListingInput,
  type ListingUpdateInput,
} from "@/lib/marketplace/api";

const PAGE_SIZE = 24;

export function useListingsInfinite(category: string, query: string, sort = "recent") {
  return useInfiniteQuery({
    queryKey: ["mk-listings", category, query, sort],
    queryFn: ({ pageParam }) =>
      listListings({ category, q: query, sort, limit: PAGE_SIZE, offset: pageParam }),
    initialPageParam: 0,
    getNextPageParam: (last) => last.next_offset,
  });
}

export function useCategoryCounts() {
  return useQuery({ queryKey: ["mk-categories"], queryFn: getCategoryCounts });
}

export function useListing(id: string) {
  return useQuery({
    queryKey: ["mk-listing", id],
    queryFn: () => getListing(id),
    enabled: !!id,
  });
}

export function useSimilarListings(id: string, category: string) {
  return useQuery({
    queryKey: ["mk-similar", id, category],
    queryFn: () => getSimilar(id, category),
    enabled: !!id && !!category,
  });
}

export function useMyListings() {
  return useQuery({ queryKey: ["mk-my-listings"], queryFn: getMyListings });
}

export function useMySellableAssets() {
  return useQuery({ queryKey: ["mk-my-assets"], queryFn: getMySellableAssets });
}

export function useCreateListing() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: ListingInput) => createListing(input),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["mk-listings"] });
      qc.invalidateQueries({ queryKey: ["mk-my-listings"] });
      qc.invalidateQueries({ queryKey: ["mk-categories"] });
      qc.invalidateQueries({ queryKey: ["mk-wallet"] });
    },
  });
}

export function useUpdateListing(id?: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id: listingId, input }: { id: string; input: ListingUpdateInput }) =>
      updateListing(listingId, input),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["mk-listings"] });
      qc.invalidateQueries({ queryKey: ["mk-my-listings"] });
      if (id) qc.invalidateQueries({ queryKey: ["mk-listing", id] });
    },
  });
}

export function useDeleteListing() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteListing(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["mk-listings"] });
      qc.invalidateQueries({ queryKey: ["mk-my-listings"] });
    },
  });
}

// --------------------------------------------------------------------------- #
// Cart + checkout + orders
// --------------------------------------------------------------------------- #
export function useCart(enabled = true) {
  return useQuery({ queryKey: ["mk-cart"], queryFn: getCart, enabled });
}

export function useAddToCart() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (listingId: string) => addToCart(listingId),
    onSuccess: (cart) => qc.setQueryData(["mk-cart"], cart),
  });
}

export function useRemoveFromCart() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (cartItemId: string) => removeFromCart(cartItemId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["mk-cart"] }),
  });
}

export function useCheckout() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => checkout(),
    onSuccess: (order) => {
      qc.invalidateQueries({ queryKey: ["mk-cart"] });
      qc.invalidateQueries({ queryKey: ["mk-wallet"] });
      qc.invalidateQueries({ queryKey: ["mk-orders"] });
      qc.invalidateQueries({ queryKey: ["mk-listings"] });
      for (const item of order.items) {
        if (item.listing_id) {
          qc.invalidateQueries({ queryKey: ["mk-listing", item.listing_id] });
        }
      }
    },
  });
}

export function useMyOrders() {
  return useQuery({ queryKey: ["mk-orders"], queryFn: getMyOrders });
}

export function useMySales() {
  return useQuery({ queryKey: ["mk-sales"], queryFn: getMySales });
}

// --------------------------------------------------------------------------- #
// Wallet + plans
// --------------------------------------------------------------------------- #
export function useWallet(enabled = true) {
  return useQuery({ queryKey: ["mk-wallet"], queryFn: getWallet, enabled });
}

export function useWalletTransactions(limit = 24, offset = 0) {
  return useQuery({
    queryKey: ["mk-wallet-tx", limit, offset],
    queryFn: () => getWalletTransactions(limit, offset),
  });
}

export function usePlans() {
  return useQuery({ queryKey: ["mk-plans"], queryFn: listPlans });
}

export function usePurchasePlan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (planId: string) => purchasePlan(planId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["mk-wallet"] }),
  });
}
