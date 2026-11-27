/**
 * Admin API calls.
 *
 * The session is an httpOnly cookie, which page scripts cannot read. That is the
 * point: nothing here handles a token, the browser simply attaches the cookie, and
 * `credentials: "include"` makes sure it does so even cross-origin in development.
 */

import { ApiError } from "./client";
import type {
  AdminListing,
  AdminOrderRow,
  NewCardRequest,
  Report,
  SessionInfo,
  ShipmentInfo,
  ShipmentInput,
} from "./adminTypes";
import type { ApiErrorBody } from "./types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

async function adminRequest<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      ...init,
      credentials: "include",
      headers: {
        Accept: "application/json",
        ...(init?.body instanceof FormData
          ? {}
          : init?.body
            ? { "Content-Type": "application/json" }
            : {}),
        ...init?.headers,
      },
    });
  } catch {
    throw new ApiError(0, "network_error", "Could not reach the shop. Is it running?");
  }

  if (!response.ok) {
    let code = "unknown_error";
    let message = `Request failed with status ${response.status}.`;
    try {
      const body = (await response.json()) as ApiErrorBody;
      if (body.error?.code) code = body.error.code;
      if (body.error?.message) message = body.error.message;
    } catch {
      // A non-JSON error body leaves the defaults.
    }
    throw new ApiError(response.status, code, message);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const adminApi = {
  signIn(username: string, password: string): Promise<SessionInfo> {
    return adminRequest<SessionInfo>("/api/admin/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
  },

  signOut(): Promise<unknown> {
    return adminRequest("/api/admin/logout", { method: "POST" });
  },

  session(): Promise<SessionInfo> {
    return adminRequest<SessionInfo>("/api/admin/session");
  },

  addCard(card: NewCardRequest): Promise<AdminListing> {
    return adminRequest<AdminListing>("/api/admin/cards", {
      method: "POST",
      body: JSON.stringify(card),
    });
  },

  listing(listingId: number): Promise<AdminListing> {
    return adminRequest<AdminListing>(`/api/admin/listings/${listingId}`);
  },

  setPrice(listingId: number, askingPrice: string): Promise<AdminListing> {
    return adminRequest<AdminListing>(`/api/admin/listings/${listingId}`, {
      method: "PATCH",
      body: JSON.stringify({ askingPrice }),
    });
  },

  setStatus(listingId: number, status: "Active" | "Withdrawn"): Promise<AdminListing> {
    return adminRequest<AdminListing>(
      `/api/admin/listings/${listingId}/status?status=${status}`,
      { method: "POST" },
    );
  },

  deleteListing(listingId: number): Promise<void> {
    return adminRequest<void>(`/api/admin/listings/${listingId}`, {
      method: "DELETE",
    });
  },

  uploadImage(listingId: number, file: File): Promise<AdminListing> {
    const form = new FormData();
    form.append("file", file);
    // No Content-Type header: the browser sets it with the multipart boundary.
    return adminRequest<AdminListing>(`/api/admin/listings/${listingId}/image`, {
      method: "POST",
      body: form,
    });
  },

  report(key: string, minCards?: number): Promise<Report> {
    const query = minCards === undefined ? "" : `?minCards=${minCards}`;
    return adminRequest<Report>(`/api/admin/reports/${key}${query}`);
  },

  orders(): Promise<AdminOrderRow[]> {
    return adminRequest<AdminOrderRow[]>("/api/admin/orders");
  },

  recordShipment(publicRef: string, shipment: ShipmentInput): Promise<ShipmentInfo> {
    return adminRequest<ShipmentInfo>(`/api/admin/orders/${publicRef}/shipment`, {
      method: "POST",
      body: JSON.stringify(shipment),
    });
  },

  markDelivered(publicRef: string): Promise<ShipmentInfo> {
    return adminRequest<ShipmentInfo>(`/api/admin/orders/${publicRef}/delivered`, {
      method: "POST",
    });
  },
};
