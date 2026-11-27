/**
 * The API contract, written by hand to mirror the backend's Pydantic models.
 *
 * Field names are camelCase because the backend serialises through an alias
 * generator. Prices are STRINGS, not numbers: they are Oracle NUMBER(10,2), and a
 * JSON float can turn 663.00 into 662.99999999. Format them for display; never do
 * arithmetic on them without parsing deliberately.
 *
 * Dates are ISO calendar dates ("2026-11-26"), not timestamps.
 */

export interface GradingInfo {
  company: string;
  grade: string;
  certificationNumber: string;
}

export interface ListingSummary {
  listingId: number;
  cardName: string;
  setName: string;
  collectorNumber: string;
  variant: string;
  rarity: string;
  cardCondition: string;
  askingPrice: string;
  currency: string;
  /** Null until the seller attaches a photo; the UI shows a plain "no image" box. */
  imageUrl: string | null;
  listedAt: string;
  /** Null for raw (ungraded) cards, which is every card currently listed. */
  grading: GradingInfo | null;
}

export interface ListingDetail extends ListingSummary {
  copyId: number;
  setId: number;
  cardLanguage: string;
  description: string;
}

export interface ListingPage {
  items: ListingSummary[];
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
}

export interface CardSetSummary {
  setId: number;
  setName: string;
  releaseDate: string;
}

export interface FilterOptions {
  rarities: string[];
  variants: string[];
  conditions: string[];
}

/** Every failure from the API arrives in this one envelope. */
export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details?: { field: string; message: string }[];
  };
}

/** Must match SORT_FRAGMENTS in the backend's catalogue repository. */
export const SORT_KEYS = ["price_desc", "price_asc", "name_asc", "newest"] as const;
export type SortKey = (typeof SORT_KEYS)[number];

/** Must match DEFAULT_SORT in the backend, so an unfiltered URL needs no sort param. */
export const DEFAULT_SORT: SortKey = "price_desc";

export const SORT_LABELS: Record<SortKey, string> = {
  price_desc: "Price: high to low",
  price_asc: "Price: low to high",
  name_asc: "Name: A to Z",
  newest: "Recently listed",
};

/** Query parameters for the catalogue search, named as the API expects them. */
export interface ListingQuery {
  page?: number;
  pageSize?: number;
  sort?: SortKey;
  setId?: number;
  rarity?: string;
  variant?: string;
  cardCondition?: string;
  graded?: boolean;
  minPrice?: string;
  maxPrice?: string;
  q?: string;
}

// --- Orders -----------------------------------------------------------------

/** The two countries the shop posts to. Matches the backend's Literal. */
export const SHIPPING_COUNTRIES = ["CA", "US"] as const;
export type ShippingCountry = (typeof SHIPPING_COUNTRIES)[number];

export const COUNTRY_LABELS: Record<ShippingCountry, string> = {
  CA: "Canada",
  US: "United States",
};

export interface ShippingAddress {
  recipientName: string;
  street: string;
  city: string;
  province: string | null;
  postalCode: string;
  country: ShippingCountry;
}

export interface CreateOrderRequest {
  email: string;
  displayName: string;
  listingIds: number[];
  shippingAddress: ShippingAddress;
}

export interface OrderLineItem {
  lineNo: number;
  listingId: number;
  cardName: string;
  cardLanguage: string;
  variant: string;
  cardCondition: string;
  agreedPrice: string;
}

export interface PaymentSummary {
  paidAt: string;
  amount: string;
  method: string;
  reference: string;
}

export interface OrderSummary {
  publicRef: string;
  status: string;
  placedAt: string;
  /** When an unpaid hold lapses. Null once the order is no longer awaiting payment. */
  expiresAt: string | null;
  items: OrderLineItem[];
  subtotal: string;
  shippingFee: string;
  total: string;
  currency: string;
  shippingAddress: ShippingAddress;
  email: string;
  payment: PaymentSummary | null;
}
