/**
 * What sits inside the card window when the seller has not attached a photo yet.
 * Deliberately plain: black words on the white window, nothing decorative, so it
 * reads as "photo coming" rather than as a broken image.
 */
export function NoImage({ label = "no image" }: { label?: string }) {
  return <span className="text-sm text-black">{label}</span>;
}
