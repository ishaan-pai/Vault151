/** The admin area's half of the API contract. */

export const CARD_CONDITIONS = [
  "NearMint",
  "LightlyPlayed",
  "ModeratelyPlayed",
  "HeavilyPlayed",
  "Damaged",
] as const;
export type CardCondition = (typeof CARD_CONDITIONS)[number];

export interface SessionInfo {
  username: string;
  expiresIn: number;
}

export interface GradingInput {
  company: string;
  grade: string;
  certificationNumber: string;
}

export interface NewCardRequest {
  setName: string;
  setReleaseDate: string;
  cardName: string;
  collectorNumber: string;
  cardLanguage: string;
  variant: string;
  rarity: string;
  cardCondition: CardCondition;
  description: string;
  askingPrice: string;
  grading: GradingInput | null;
}

export interface AdminListing {
  listingId: number;
  copyId: number;
  cardName: string;
  setName: string;
  collectorNumber: string;
  variant: string;
  rarity: string;
  cardCondition: string;
  description: string;
  askingPrice: string;
  status: string;
  listedAt: string;
  imageUrl: string | null;
  /** False once a card is reserved or sold: its price must not move under a buyer. */
  editable: boolean;
  /** False once the card appears on an order, because deleting would damage it. */
  deletable: boolean;
}

export interface ShipmentInfo {
  carrier: string;
  trackingNumber: string;
  shippedAt: string;
  deliveredAt: string | null;
}

export interface AdminOrderRow {
  publicRef: string;
  status: string;
  placedAt: string;
  customerName: string;
  email: string;
  cardCount: number;
  subtotal: string;
  shippingFee: string;
  total: string;
  shipment: ShipmentInfo | null;
}

export interface Report {
  key: string;
  title: string;
  description: string;
  /** The SQL feature the query demonstrates, e.g. "MINUS". */
  feature: string;
  /** The exact statement sent to Oracle, so the page can show its workings. */
  sql: string;
  columns: string[];
  rows: Record<string, string>[];
  rowCount: number;
}

export interface ShipmentInput {
  carrier: string;
  trackingNumber: string;
}
