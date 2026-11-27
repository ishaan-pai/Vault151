import type { ReactNode } from "react";

import { SORT_KEYS, SORT_LABELS, type SortKey } from "../api/types";
import { useCardSets, useFilterOptions } from "../api/queries";

export interface CatalogueFilters {
  sort: SortKey;
  setId?: number;
  rarity?: string;
  cardCondition?: string;
  graded?: boolean;
  minPrice?: string;
  maxPrice?: string;
  q?: string;
}

const controlClass =
  "rounded border border-seam bg-surface px-2 py-1.5 text-sm text-ink placeholder:text-muted/70";
const labelClass = "text-xs text-muted";

function Field({
  label,
  htmlFor,
  children,
}: {
  label: string;
  htmlFor: string;
  children: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1">
      <label className={labelClass} htmlFor={htmlFor}>
        {label}
      </label>
      {children}
    </div>
  );
}

/**
 * A single horizontal bar above the grid: filters on the left, sort and the result
 * count on the right, with one seam under it.
 *
 * Every control writes straight back to the URL, so a filtered catalogue is a
 * shareable link and the back button undoes one change at a time.
 *
 * The set list includes sets with nothing in stock on purpose: a shopper who picks
 * one and sees an empty grid has learned that none are for sale, which beats the
 * set being quietly missing from the list.
 */
export function FilterPanel({
  filters,
  totalItems,
  isLoading,
  onChange,
  onReset,
}: {
  filters: CatalogueFilters;
  totalItems: number;
  isLoading: boolean;
  onChange: (next: Partial<CatalogueFilters>) => void;
  onReset: () => void;
}) {
  const sets = useCardSets();
  const options = useFilterOptions();

  const hasFilters =
    filters.setId !== undefined ||
    filters.graded !== undefined ||
    Boolean(filters.rarity || filters.cardCondition || filters.minPrice) ||
    Boolean(filters.maxPrice || filters.q);

  return (
    <div className="flex flex-col gap-4 border-b border-seam pb-4 lg:flex-row lg:items-end lg:justify-between">
      <div className="flex flex-wrap items-end gap-3">
        <Field label="Card name" htmlFor="filter-q">
          <input
            id="filter-q"
            type="search"
            value={filters.q ?? ""}
            placeholder="Charizard"
            onChange={(event) => onChange({ q: event.target.value })}
            className={`${controlClass} w-40`}
          />
        </Field>

        <Field label="Set" htmlFor="filter-set">
          <select
            id="filter-set"
            value={filters.setId ?? ""}
            onChange={(event) =>
              onChange({
                setId: event.target.value ? Number(event.target.value) : undefined,
              })
            }
            className={controlClass}
          >
            <option value="">All sets</option>
            {(sets.data ?? []).map((cardSet) => (
              <option key={cardSet.setId} value={cardSet.setId}>
                {cardSet.setName}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Rarity" htmlFor="filter-rarity">
          <select
            id="filter-rarity"
            value={filters.rarity ?? ""}
            onChange={(event) => onChange({ rarity: event.target.value || undefined })}
            className={controlClass}
          >
            <option value="">Any</option>
            {(options.data?.rarities ?? []).map((rarity) => (
              <option key={rarity} value={rarity}>
                {rarity}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Condition" htmlFor="filter-condition">
          <select
            id="filter-condition"
            value={filters.cardCondition ?? ""}
            onChange={(event) =>
              onChange({ cardCondition: event.target.value || undefined })
            }
            className={controlClass}
          >
            <option value="">Any</option>
            {(options.data?.conditions ?? []).map((condition) => (
              <option key={condition} value={condition}>
                {condition}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Grading" htmlFor="filter-graded">
          <select
            id="filter-graded"
            value={filters.graded === undefined ? "" : String(filters.graded)}
            onChange={(event) =>
              onChange({
                graded: event.target.value === "" ? undefined : event.target.value === "true",
              })
            }
            className={controlClass}
          >
            <option value="">Any</option>
            <option value="true">Graded</option>
            <option value="false">Raw</option>
          </select>
        </Field>

        <Field label="Price (CAD)" htmlFor="filter-min-price">
          <div className="flex items-center gap-1">
            <input
              id="filter-min-price"
              type="number"
              min={0}
              step="1"
              inputMode="decimal"
              aria-label="Minimum price"
              placeholder="Min"
              value={filters.minPrice ?? ""}
              onChange={(event) =>
                onChange({ minPrice: event.target.value || undefined })
              }
              className={`${controlClass} w-20`}
            />
            <span className="text-muted">&ndash;</span>
            <input
              type="number"
              min={0}
              step="1"
              inputMode="decimal"
              aria-label="Maximum price"
              placeholder="Max"
              value={filters.maxPrice ?? ""}
              onChange={(event) =>
                onChange({ maxPrice: event.target.value || undefined })
              }
              className={`${controlClass} w-20`}
            />
          </div>
        </Field>

        {hasFilters ? (
          <button
            type="button"
            onClick={onReset}
            className="pb-1.5 text-xs text-muted underline hover:text-brass"
          >
            Clear
          </button>
        ) : null}
      </div>

      <div className="flex items-end gap-4">
        <Field label="Sort by" htmlFor="filter-sort">
          <select
            id="filter-sort"
            value={filters.sort}
            onChange={(event) => onChange({ sort: event.target.value as SortKey })}
            className={controlClass}
          >
            {SORT_KEYS.map((key) => (
              <option key={key} value={key}>
                {SORT_LABELS[key]}
              </option>
            ))}
          </select>
        </Field>

        <p className="pb-1.5 text-sm whitespace-nowrap text-muted">
          {isLoading ? "counting\u2026" : `${totalItems} card${totalItems === 1 ? "" : "s"}`}
        </p>
      </div>
    </div>
  );
}
