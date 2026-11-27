import type { ListingSummary } from "../api/types";
import { CardTile } from "./CardTile";

/**
 * items-stretch is the grid default, and each tile carries h-full, so every tile in
 * a row ends up the same height no matter how long its card name is.
 */
export function CardGrid({ listings }: { listings: ListingSummary[] }) {
  return (
    <ul className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
      {listings.map((listing) => (
        <li key={listing.listingId}>
          <CardTile listing={listing} />
        </li>
      ))}
    </ul>
  );
}
