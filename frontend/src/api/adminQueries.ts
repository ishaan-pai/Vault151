import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { adminApi } from "./adminClient";
import type { NewCardRequest, ShipmentInput } from "./adminTypes";

/** Whether this browser holds a valid session. A 401 is an answer, not a failure. */
export function useSession() {
  return useQuery({
    queryKey: ["admin", "session"],
    queryFn: () => adminApi.session(),
    retry: false,
    staleTime: 60_000,
  });
}

export function useSignIn() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ username, password }: { username: string; password: string }) =>
      adminApi.signIn(username, password),
    onSuccess: (session) => queryClient.setQueryData(["admin", "session"], session),
  });
}

export function useSignOut() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => adminApi.signOut(),
    onSuccess: () => queryClient.clear(),
  });
}

export function useAdminListing(listingId: number) {
  return useQuery({
    queryKey: ["admin", "listing", listingId],
    queryFn: () => adminApi.listing(listingId),
    retry: false,
  });
}

export function useAdminOrders() {
  return useQuery({
    queryKey: ["admin", "orders"],
    queryFn: () => adminApi.orders(),
    retry: false,
  });
}

/**
 * Anything that changes inventory invalidates the public catalogue too, so the
 * storefront never shows a card the seller has just withdrawn or repriced.
 */
function useInventoryMutation<TArgs, TResult>(
  mutationFn: (args: TArgs) => Promise<TResult>,
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["listings"] });
      void queryClient.invalidateQueries({ queryKey: ["admin"] });
      void queryClient.invalidateQueries({ queryKey: ["sets"] });
      void queryClient.invalidateQueries({ queryKey: ["filter-options"] });
    },
  });
}

export function useAddCard() {
  return useInventoryMutation((card: NewCardRequest) => adminApi.addCard(card));
}

export function useSetPrice(listingId: number) {
  return useInventoryMutation((askingPrice: string) =>
    adminApi.setPrice(listingId, askingPrice),
  );
}

export function useSetStatus(listingId: number) {
  return useInventoryMutation((status: "Active" | "Withdrawn") =>
    adminApi.setStatus(listingId, status),
  );
}

export function useDeleteListing() {
  return useInventoryMutation((listingId: number) => adminApi.deleteListing(listingId));
}

export function useUploadImage(listingId: number) {
  return useInventoryMutation((file: File) => adminApi.uploadImage(listingId, file));
}

export function useRecordShipment(publicRef: string) {
  return useInventoryMutation((shipment: ShipmentInput) =>
    adminApi.recordShipment(publicRef, shipment),
  );
}

export function useMarkDelivered(publicRef: string) {
  return useInventoryMutation(() => adminApi.markDelivered(publicRef));
}
