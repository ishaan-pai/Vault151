import { Link, useParams } from "react-router-dom";

import { useListing } from "../api/queries";
import { ApiError } from "../api/client";
import { AddToCartButton } from "../components/AddToCartButton";
import { Badge } from "../components/Badge";
import { CardImage } from "../components/CardImage";
import { Price } from "../components/Price";
import { StateMessage } from "../components/StateMessage";

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 border-b border-seam py-2 last:border-0">
      <dt className="text-sm text-muted">{label}</dt>
      <dd className="text-right text-sm text-ink">{value}</dd>
    </div>
  );
}

export function CardDetailPage() {
  const { listingId } = useParams();
  const listing = useListing(Number(listingId));

  if (listing.isPending) {
    return <StateMessage title="Fetching the card&hellip;" />;
  }

  if (listing.isError) {
    const notFound = listing.error instanceof ApiError && listing.error.isNotFound;
    return (
      <StateMessage
        title={notFound ? "That card is no longer for sale." : "The shop is not answering."}
        detail={notFound ? undefined : listing.error.message}
      >
        <Link to="/cards" className="text-sm text-brass underline">
          Back to the catalogue
        </Link>
      </StateMessage>
    );
  }

  const card = listing.data;

  return (
    <article className="flex flex-col gap-8 lg:flex-row">
      <div className="lg:w-2/5">
        <div className="rounded-lg border border-seam bg-surface p-4">
          <CardImage src={card.imageUrl} alt={card.cardName} />
        </div>
      </div>

      <div className="flex-1">
        <nav className="mb-4 text-sm text-muted">
          <Link to="/cards" className="hover:text-brass">
            Catalogue
          </Link>
          <span className="px-2">/</span>
          <span>{card.setName}</span>
        </nav>

        <h1 className="text-2xl font-semibold tracking-tight text-ink">
          {card.cardName}
        </h1>
        <p className="mt-1 text-sm text-muted">
          {card.setName} &middot; {card.collectorNumber} &middot; {card.variant}
        </p>

        <div className="mt-4 flex flex-wrap gap-2">
          <Badge>{card.cardCondition}</Badge>
          <Badge>{card.rarity}</Badge>
          {card.grading ? (
            <Badge tone="brass">
              {card.grading.company} {card.grading.grade}
            </Badge>
          ) : (
            <Badge>Raw / ungraded</Badge>
          )}
        </div>

        <Price
          amount={card.askingPrice}
          currency={card.currency}
          className="mt-6 block text-3xl font-semibold text-brass"
        />

        <AddToCartButton listingId={card.listingId} className="mt-6 w-full sm:w-64" />

        <p className="mt-6 text-sm leading-relaxed text-ink">{card.description}</p>

        <dl className="mt-8 rounded-lg border border-seam bg-surface px-4 py-2">
          <Detail label="Set" value={card.setName} />
          <Detail label="Collector number" value={card.collectorNumber} />
          <Detail label="Variant" value={card.variant} />
          <Detail label="Rarity" value={card.rarity} />
          <Detail label="Language" value={card.cardLanguage} />
          <Detail label="Condition" value={card.cardCondition} />
          {card.grading ? (
            <Detail
              label="Certification"
              value={`${card.grading.company} ${card.grading.grade} #${card.grading.certificationNumber}`}
            />
          ) : null}
          <Detail label="Listed" value={card.listedAt} />
        </dl>

        <p className="mt-6 text-xs text-muted">
          One physical card, sold once. No account needed to buy.
        </p>
      </div>
    </article>
  );
}
