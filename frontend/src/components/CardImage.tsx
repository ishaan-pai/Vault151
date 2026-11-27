import { NoImage } from "./NoImage";

/**
 * The card window: one fixed-size white frame that every listing shares, whether or
 * not it has a photo.
 *
 * The size is fixed by aspect ratio rather than by the image, and the photo is
 * letterboxed inside with object-contain. That way a tall scan, a wide slab photo
 * and a missing image all occupy exactly the same space, so the grid lines up.
 */
export function CardImage({ src, alt }: { src: string | null; alt: string }) {
  return (
    <div className="flex aspect-[5/7] w-full items-center justify-center overflow-hidden rounded bg-white">
      {src ? (
        <img
          src={src}
          alt={alt}
          loading="lazy"
          className="h-full w-full object-contain"
        />
      ) : (
        <NoImage />
      )}
    </div>
  );
}
