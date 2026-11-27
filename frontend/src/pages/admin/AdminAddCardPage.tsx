import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { useAddCard } from "../../api/adminQueries";
import { CARD_CONDITIONS, type CardCondition } from "../../api/adminTypes";

const fieldClass =
  "mt-1 w-full rounded border border-seam bg-canvas px-3 py-2 text-sm text-ink placeholder:text-muted/70";
const labelClass = "block text-xs text-muted";

/**
 * One form for the whole chain: set, printing, physical copy, optional grading and
 * the listing. The backend reuses the set and printing when they already exist, so
 * adding a second card from a set already in stock does not duplicate anything.
 */
export function AdminAddCardPage() {
  const addCard = useAddCard();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    setName: "",
    setReleaseDate: "",
    cardName: "",
    collectorNumber: "",
    cardLanguage: "English",
    variant: "Normal",
    rarity: "",
    cardCondition: "NearMint" as CardCondition,
    description: "",
    askingPrice: "",
  });
  const [graded, setGraded] = useState(false);
  const [grading, setGrading] = useState({
    company: "",
    grade: "",
    certificationNumber: "",
  });

  function set<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    addCard.mutate(
      { ...form, grading: graded ? grading : null },
      {
        onSuccess: (listing) =>
          void navigate(`/admin/listings/${listing.listingId}`),
      },
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex max-w-2xl flex-col gap-5">
      <section className="flex flex-col gap-3 rounded-lg border border-seam bg-surface p-4">
        <h2 className="text-sm font-medium text-ink">The card</h2>

        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <label className={labelClass} htmlFor="setName">Set</label>
            <input id="setName" required value={form.setName}
              onChange={(e) => set("setName", e.target.value)}
              placeholder="Crown Zenith" className={fieldClass} />
          </div>
          <div>
            <label className={labelClass} htmlFor="setReleaseDate">Set released</label>
            <input id="setReleaseDate" type="date" required value={form.setReleaseDate}
              onChange={(e) => set("setReleaseDate", e.target.value)}
              className={fieldClass} />
          </div>
          <div>
            <label className={labelClass} htmlFor="cardName">Card name</label>
            <input id="cardName" required value={form.cardName}
              onChange={(e) => set("cardName", e.target.value)}
              placeholder="Giratina VSTAR" className={fieldClass} />
          </div>
          <div>
            <label className={labelClass} htmlFor="collectorNumber">Collector number</label>
            <input id="collectorNumber" required value={form.collectorNumber}
              onChange={(e) => set("collectorNumber", e.target.value)}
              placeholder="GG69" className={fieldClass} />
          </div>
          <div>
            <label className={labelClass} htmlFor="variant">Variant</label>
            <input id="variant" required value={form.variant}
              onChange={(e) => set("variant", e.target.value)}
              placeholder="Secret" className={fieldClass} />
          </div>
          <div>
            <label className={labelClass} htmlFor="rarity">Rarity</label>
            <input id="rarity" required value={form.rarity}
              onChange={(e) => set("rarity", e.target.value)}
              placeholder="Secret Rare" className={fieldClass} />
          </div>
          <div>
            <label className={labelClass} htmlFor="cardLanguage">Language</label>
            <input id="cardLanguage" required value={form.cardLanguage}
              onChange={(e) => set("cardLanguage", e.target.value)}
              className={fieldClass} />
          </div>
          <div>
            <label className={labelClass} htmlFor="cardCondition">Condition</label>
            <select id="cardCondition" value={form.cardCondition}
              onChange={(e) => set("cardCondition", e.target.value as CardCondition)}
              className={fieldClass}>
              {CARD_CONDITIONS.map((condition) => (
                <option key={condition} value={condition}>{condition}</option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className={labelClass} htmlFor="description">Description</label>
          <textarea id="description" required rows={3} value={form.description}
            onChange={(e) => set("description", e.target.value)}
            placeholder="Raw, Near Mint. Sharp corners, clean surface."
            className={fieldClass} />
        </div>
      </section>

      <section className="flex flex-col gap-3 rounded-lg border border-seam bg-surface p-4">
        <label className="flex items-center gap-2 text-sm text-ink">
          <input type="checkbox" checked={graded}
            onChange={(e) => setGraded(e.target.checked)} />
          This card is graded
        </label>

        {graded ? (
          <div className="grid gap-3 sm:grid-cols-3">
            <div>
              <label className={labelClass} htmlFor="company">Company</label>
              <input id="company" required value={grading.company}
                onChange={(e) => setGrading({ ...grading, company: e.target.value })}
                placeholder="PSA" className={fieldClass} />
            </div>
            <div>
              <label className={labelClass} htmlFor="grade">Grade</label>
              <input id="grade" required value={grading.grade}
                onChange={(e) => setGrading({ ...grading, grade: e.target.value })}
                placeholder="10" className={fieldClass} />
            </div>
            <div>
              <label className={labelClass} htmlFor="cert">Certification number</label>
              <input id="cert" required value={grading.certificationNumber}
                onChange={(e) =>
                  setGrading({ ...grading, certificationNumber: e.target.value })}
                className={fieldClass} />
            </div>
          </div>
        ) : null}
      </section>

      <section className="rounded-lg border border-seam bg-surface p-4">
        <label className={labelClass} htmlFor="askingPrice">Asking price (CAD)</label>
        <input id="askingPrice" type="number" min="0.01" step="0.01" required
          value={form.askingPrice}
          onChange={(e) => set("askingPrice", e.target.value)}
          className={`${fieldClass} max-w-40`} />
        <p className="mt-2 text-xs text-muted">
          The photo is added on the next screen, and can be changed at any time.
        </p>
      </section>

      {addCard.isError ? (
        <p className="text-sm text-danger">{addCard.error.message}</p>
      ) : null}

      <button type="submit" disabled={addCard.isPending}
        className="self-start rounded border border-brass/50 bg-brass/10 px-4 py-2 text-sm text-brass transition enabled:hover:bg-brass/20 disabled:opacity-50">
        {addCard.isPending ? "Adding\u2026" : "Add card and list it"}
      </button>
    </form>
  );
}
