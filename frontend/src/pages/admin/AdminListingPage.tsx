import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import {
  useAdminListing,
  useDeleteListing,
  useSetPrice,
  useSetStatus,
  useUploadImage,
} from "../../api/adminQueries";
import { CardImage } from "../../components/CardImage";
import { StateMessage } from "../../components/StateMessage";

const dangerButton =
  "rounded border border-danger/50 bg-danger/10 px-3 py-2 text-sm text-danger transition enabled:hover:bg-danger/20 disabled:opacity-40";

export function AdminListingPage() {
  const { listingId = "" } = useParams();
  const id = Number(listingId);
  const navigate = useNavigate();

  const listing = useAdminListing(id);
  const setPrice = useSetPrice(id);
  const setStatus = useSetStatus(id);
  const uploadImage = useUploadImage(id);
  const deleteListing = useDeleteListing();

  const [price, setPriceInput] = useState("");
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  // Fill the price box once the card loads, without clobbering an edit in progress.
  useEffect(() => {
    if (listing.data) setPriceInput((current) => current || listing.data.askingPrice);
  }, [listing.data]);

  if (listing.isPending) return <StateMessage title="Loading the card&hellip;" />;
  if (listing.isError) {
    return (
      <StateMessage title="Could not load that card." detail={listing.error.message}>
        <Link to="/admin" className="text-sm text-brass underline">
          Back to inventory
        </Link>
      </StateMessage>
    );
  }

  const card = listing.data;
  const withdrawn = card.status === "Withdrawn";
  const anyError =
    setPrice.error ?? setStatus.error ?? uploadImage.error ?? deleteListing.error;

  function handlePrice(event: FormEvent) {
    event.preventDefault();
    setPrice.mutate(price);
  }

  function handleFile(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) uploadImage.mutate(file);
    // Clear it so choosing the same file twice still fires a change event.
    event.target.value = "";
  }

  return (
    <div className="flex flex-col gap-6 lg:flex-row lg:items-start">
      <div className="flex flex-col gap-3 lg:w-64">
        <div className="rounded-lg border border-seam bg-surface p-3">
          <CardImage src={card.imageUrl} alt={card.cardName} />
        </div>

        <input
          ref={fileInput}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={handleFile}
          className="hidden"
        />
        <button
          type="button"
          onClick={() => fileInput.current?.click()}
          disabled={uploadImage.isPending}
          className="rounded border border-seam px-3 py-2 text-sm text-ink transition enabled:hover:border-brass/50 enabled:hover:text-brass disabled:opacity-50"
        >
          {uploadImage.isPending
            ? "Uploading\u2026"
            : card.imageUrl
              ? "Replace photo"
              : "Add photo"}
        </button>
        <p className="text-xs text-muted">
          JPEG, PNG or WebP, up to 5 MB. Stored as uploaded, so a smaller file makes a
          faster shop.
        </p>
      </div>

      <div className="flex min-w-0 flex-1 flex-col gap-5">
        <div>
          <h2 className="text-lg font-medium text-ink">{card.cardName}</h2>
          <p className="mt-1 text-sm text-muted">
            {card.setName} &middot; {card.collectorNumber} &middot; {card.variant}{" "}
            &middot; {card.rarity} &middot; {card.cardCondition}
          </p>
          <p className="mt-2 text-xs text-muted">
            Listing {card.listingId} &middot; copy {card.copyId} &middot; listed{" "}
            {card.listedAt} &middot; status{" "}
            <span className={withdrawn ? "text-danger" : "text-brass"}>
              {card.status}
            </span>
          </p>
        </div>

        {anyError ? (
          <p className="rounded border border-danger/40 bg-danger/10 p-3 text-sm text-ink">
            {anyError.message}
          </p>
        ) : null}

        {card.editable ? (
          <form onSubmit={handlePrice} className="flex items-end gap-3">
            <div>
              <label className="block text-xs text-muted" htmlFor="price">
                Asking price (CAD)
              </label>
              <input
                id="price"
                type="number"
                min="0.01"
                step="0.01"
                value={price}
                onChange={(event) => setPriceInput(event.target.value)}
                className="mt-1 w-36 rounded border border-seam bg-canvas px-3 py-2 text-sm text-ink"
              />
            </div>
            <button
              type="submit"
              disabled={setPrice.isPending || price === card.askingPrice}
              className="rounded border border-brass/50 bg-brass/10 px-4 py-2 text-sm text-brass transition enabled:hover:bg-brass/20 disabled:opacity-40"
            >
              {setPrice.isPending ? "Saving\u2026" : "Save price"}
            </button>
          </form>
        ) : (
          <p className="rounded border border-seam bg-surface p-3 text-sm text-muted">
            This card is {card.status.toLowerCase()}, so its price is fixed. Changing
            it now would alter what a buyer is about to pay, or rewrite a completed
            sale.
          </p>
        )}

        <p className="text-sm text-ink">{card.description}</p>

        <div className="flex flex-col gap-3 rounded-lg border border-seam bg-surface p-4">
          <h3 className="text-sm font-medium text-ink">Remove from sale</h3>

          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              disabled={!card.editable || setStatus.isPending}
              onClick={() => setStatus.mutate(withdrawn ? "Active" : "Withdrawn")}
              className={dangerButton}
            >
              {setStatus.isPending
                ? "Saving\u2026"
                : withdrawn
                  ? "Re-enable"
                  : "Disable"}
            </button>

            {confirmingDelete ? (
              <>
                <button
                  type="button"
                  disabled={deleteListing.isPending}
                  onClick={() =>
                    deleteListing.mutate(card.listingId, {
                      onSuccess: () => void navigate("/admin"),
                    })
                  }
                  className={dangerButton}
                >
                  {deleteListing.isPending ? "Deleting\u2026" : "Yes, delete it"}
                </button>
                <button
                  type="button"
                  onClick={() => setConfirmingDelete(false)}
                  className="rounded border border-seam px-3 py-2 text-sm text-muted hover:text-ink"
                >
                  Cancel
                </button>
              </>
            ) : (
              <button
                type="button"
                disabled={!card.deletable}
                onClick={() => setConfirmingDelete(true)}
                className={dangerButton}
              >
                Delete
              </button>
            )}
          </div>

          <p className="text-xs text-muted">
            {!card.editable
              ? `This card is ${card.status.toLowerCase()}, so it can be neither disabled nor deleted. ${
                  card.status === "Reserved"
                    ? "A buyer is holding it while they check out; it frees itself if they do not pay."
                    : "It has been sold, and its order needs the record to stay intact."
                }`
              : card.deletable
                ? "Disabling takes the card off the shop and can be undone at any time. Deleting removes the card and its record permanently."
                : "Disabling takes the card off the shop and can be undone at any time. This card appears on an order, so it cannot be deleted without damaging that order's history."}
          </p>
        </div>
      </div>
    </div>
  );
}
