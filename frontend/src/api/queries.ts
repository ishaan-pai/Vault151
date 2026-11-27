/** TanStack Query hooks. Keys mirror the endpoint and its arguments. */

import {
  useMutation,
  useQueries,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import { api } from "./client";
import type { CreateOrderRequest, ListingQuery } from "./types";

/** Reference data changes only when the seller edits inventory. */
const STATIC_DATA_STALE_MS = 5 * 60 * 1000;

export function useFeaturedListings() {
  return useQuery({
    queryKey: ["listings", "featured"],
    queryFn: () => api.featuredListings(),
  });
}

export function useListings(query: ListingQuery) {
  return useQuery({
    queryKey: ["listings", "search", query],
    queryFn: () => api.searchListings(query),
    // Keeps the previous page on screen while the next one loads, instead of
    // collapsing the grid to a spinner on every filter change.
    placeholderData: (previous) => previous,
  });
}

export function useListing(listingId: number) {
  return useQuery({
    queryKey: ["listings", "detail", listingId],
    queryFn: () => api.listing(listingId),
    retry: false, // a 404 is an answer, not a failure to retry
  });
}

export function useCardSets() {
  return useQuery({
    queryKey: ["sets"],
    queryFn: () => api.cardSets(),
    staleTime: STATIC_DATA_STALE_MS,
  });
}

export function useFilterOptions() {
  return useQuery({
    queryKey: ["filter-options"],
    queryFn: () => api.filterOptions(),
    staleTime: STATIC_DATA_STALE_MS,
  });
}

// --- Orders -----------------------------------------------------------------

export function useCartListings(listingIds: number[]) {
  /** One query per card in the cart. Carts here hold a handful of items. */
  return useQueries({
    queries: listingIds.map((listingId) => ({
      queryKey: ["listings", "detail", listingId],
      queryFn: () => api.listing(listingId),
      retry: false,
    })),
  });
}

export function useOrder(publicRef: string, email: string | null) {
  return useQuery({
    queryKey: ["orders", publicRef, email],
    queryFn: () => api.findOrder(publicRef, email ?? ""),
    enabled: Boolean(publicRef && email),
    retry: false,
  });
}

export function useCreateOrder() {
  return useMutation({
    mutationFn: (order: CreateOrderRequest) => api.createOrder(order),
  });
}

export function usePayOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (publicRef: string) => api.payOrder(publicRef),
    onSuccess: (order) => {
      // The cards just sold, so every catalogue page on screen is now stale.
      void queryClient.invalidateQueries({ queryKey: ["listings"] });
      queryClient.setQueryData(["orders", order.publicRef, order.email], order);
    },
  });
}
