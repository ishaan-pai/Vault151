import { Link } from "react-router-dom";

import { useFeaturedListings } from "../api/queries";
import { CardGrid } from "../components/CardGrid";
import { StateMessage } from "../components/StateMessage";

/**
 * The feature strip is simply the most expensive cards currently for sale. There is
 * no "featured" flag in the database: the data already knows which cards those are.
 */
export function HomePage() {
  const featured = useFeaturedListings();

  return (
    <div className="flex flex-col gap-10">
      <section className="rounded-lg border border-seam bg-surface px-6 py-10 sm:px-10 sm:py-14">
        <p className="text-xs uppercase tracking-[0.2em] text-brass">
          Single-seller consignment
        </p>
        <h1 className="mt-3 max-w-2xl text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
          One collection, one card of each.
        </h1>
        <p className="mt-4 max-w-xl text-sm leading-relaxed text-muted">
          Every listing is a specific physical card from a single collector&rsquo;s
          binder, photographed and graded as it is. When it sells, it is gone. No
          account needed to buy.
        </p>
        <Link
          to="/cards"
          className="mt-6 inline-flex rounded border border-brass/50 bg-brass/10 px-4 py-2 text-sm text-brass transition hover:bg-brass/20"
        >
          Browse the catalogue
        </Link>
      </section>

      <section>
        <div className="mb-4 flex items-baseline justify-between">
          <h2 className="text-lg font-medium text-ink">The vault</h2>
          <Link to="/cards" className="text-sm text-muted hover:text-brass">
            See everything
          </Link>
        </div>

        {featured.isPending ? (
          <StateMessage title="Opening the vault&hellip;" />
        ) : featured.isError ? (
          <StateMessage
            title="The shop is not answering."
            detail={featured.error.message}
          />
        ) : featured.data.length === 0 ? (
          <StateMessage title="Nothing is listed yet." />
        ) : (
          <CardGrid listings={featured.data} />
        )}
      </section>
    </div>
  );
}
