import { useSearchParams } from "react-router-dom";

import { useListings } from "../api/queries";
import { DEFAULT_SORT, SORT_KEYS, type SortKey } from "../api/types";
import { CardGrid } from "../components/CardGrid";
import { FilterPanel, type CatalogueFilters } from "../components/FilterPanel";
import { Pagination } from "../components/Pagination";
import { StateMessage } from "../components/StateMessage";

function isSortKey(value: string | null): value is SortKey {
  return value !== null && (SORT_KEYS as readonly string[]).includes(value);
}

function optional(value: string | null): string | undefined {
  return value ? value : undefined;
}

/**
 * Filters live in the URL rather than in component state, so a filtered view is a
 * link someone can share and the browser's back button undoes one change at a time.
 */
export function CataloguePage() {
  const [searchParams, setSearchParams] = useSearchParams();

  const sortParam = searchParams.get("sort");
  const gradedParam = searchParams.get("graded");
  const setIdParam = searchParams.get("setId");

  const filters: CatalogueFilters = {
    sort: isSortKey(sortParam) ? sortParam : DEFAULT_SORT,
    setId: setIdParam ? Number(setIdParam) : undefined,
    rarity: optional(searchParams.get("rarity")),
    cardCondition: optional(searchParams.get("cardCondition")),
    graded: gradedParam === null ? undefined : gradedParam === "true",
    minPrice: optional(searchParams.get("minPrice")),
    maxPrice: optional(searchParams.get("maxPrice")),
    q: optional(searchParams.get("q")),
  };

  const page = Math.max(1, Number(searchParams.get("page") ?? "1") || 1);

  const listings = useListings({ ...filters, page });

  /** Any filter change returns to page 1: page 4 of the old result set is meaningless. */
  function updateFilters(next: Partial<CatalogueFilters>) {
    const merged = { ...filters, ...next };
    const params = new URLSearchParams();
    if (merged.sort !== DEFAULT_SORT) params.set("sort", merged.sort);
    if (merged.setId !== undefined) params.set("setId", String(merged.setId));
    if (merged.rarity) params.set("rarity", merged.rarity);
    if (merged.cardCondition) params.set("cardCondition", merged.cardCondition);
    if (merged.graded !== undefined) params.set("graded", String(merged.graded));
    if (merged.minPrice) params.set("minPrice", merged.minPrice);
    if (merged.maxPrice) params.set("maxPrice", merged.maxPrice);
    if (merged.q) params.set("q", merged.q);
    setSearchParams(params);
  }

  function changePage(nextPage: number) {
    const params = new URLSearchParams(searchParams);
    if (nextPage <= 1) params.delete("page");
    else params.set("page", String(nextPage));
    setSearchParams(params);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-lg font-medium text-ink">Catalogue</h1>

      <FilterPanel
        filters={filters}
        totalItems={listings.data?.totalItems ?? 0}
        isLoading={listings.isPending}
        onChange={updateFilters}
        onReset={() => setSearchParams(new URLSearchParams())}
      />

      {listings.isPending ? (
        <StateMessage title="Pulling cards from the binder&hellip;" />
      ) : listings.isError ? (
        <StateMessage
          title="The shop is not answering."
          detail={listings.error.message}
        />
      ) : listings.data.items.length === 0 ? (
        <StateMessage
          title="No cards match those filters."
          detail="Nothing in this collection fits what you asked for - try widening the price range or clearing the set."
        />
      ) : (
        <>
          <CardGrid listings={listings.data.items} />
          <Pagination
            page={listings.data.page}
            totalPages={listings.data.totalPages}
            onPageChange={changePage}
          />
        </>
      )}
    </div>
  );
}
