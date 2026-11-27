/**
 * The only place in the app that talks to the network.
 *
 * In development Vite proxies /api to the backend; in the container nginx does the
 * same. So the base is empty by default and requests are same-origin. VITE_API_BASE_URL
 * exists for a deployment where the API lives on another host.
 */

import type {
  ApiErrorBody,
  CardSetSummary,
  CreateOrderRequest,
  FilterOptions,
  ListingDetail,
  ListingPage,
  ListingQuery,
  ListingSummary,
  OrderSummary,
} from "./types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }

  get isNotFound(): boolean {
    return this.status === 404;
  }
}

/**
 * Turn a query object into a query string, dropping anything unset.
 *
 * Exported for its own tests: an empty string and `undefined` must not become
 * `?q=` or `?q=undefined`, both of which the API would reject or mis-handle.
 */
export function buildQueryString<T extends object>(query: T): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === null || value === "") continue;
    params.set(key, String(value));
  }
  const queryString = params.toString();
  return queryString ? `?${queryString}` : "";
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      ...init,
      headers: {
        Accept: "application/json",
        ...(init?.body ? { "Content-Type": "application/json" } : {}),
        ...init?.headers,
      },
    });
  } catch {
    // A network failure is not an HTTP status; say so plainly rather than
    // reporting a misleading code.
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
      // A non-JSON error body (a proxy error page, say) leaves the defaults.
    }
    throw new ApiError(response.status, code, message);
  }

  return (await response.json()) as T;
}

export const api = {
  searchListings(query: ListingQuery): Promise<ListingPage> {
    return request<ListingPage>(`/api/listings${buildQueryString(query)}`);
  },

  featuredListings(): Promise<ListingSummary[]> {
    return request<ListingSummary[]>("/api/listings/featured");
  },

  listing(listingId: number): Promise<ListingDetail> {
    return request<ListingDetail>(`/api/listings/${listingId}`);
  },

  cardSets(): Promise<CardSetSummary[]> {
    return request<CardSetSummary[]>("/api/sets");
  },

  filterOptions(): Promise<FilterOptions> {
    return request<FilterOptions>("/api/filter-options");
  },

  createOrder(order: CreateOrderRequest): Promise<OrderSummary> {
    return request<OrderSummary>("/api/orders", {
      method: "POST",
      body: JSON.stringify(order),
    });
  },

  payOrder(publicRef: string): Promise<OrderSummary> {
    // Safe to call twice: the API answers a repeated payment with the first one.
    return request<OrderSummary>(`/api/orders/${publicRef}/pay`, { method: "POST" });
  },

  findOrder(publicRef: string, email: string): Promise<OrderSummary> {
    return request<OrderSummary>(
      `/api/orders/${publicRef}${buildQueryString({ email })}`,
    );
  },
};
