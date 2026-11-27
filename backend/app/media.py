"""Saving card photos to disk.

Files land in a directory the web server also serves, so nginx returns them directly
without Python in the path. The database stores only the URL, which is why
cardcopy.imageurl is a varchar2 and not a BLOB.
"""

import logging
import secrets
from pathlib import Path

from .errors import AppError

logger = logging.getLogger(__name__)

# The first bytes of a file say what it really is. A name ending in .png is a claim,
# not a fact, so the extension is never trusted.
MAGIC_BYTES: list[tuple[bytes, str]] = [
    (b"\xff\xd8\xff", "jpg"),
    (b"\x89PNG\r\n\x1a\n", "png"),
]
WEBP_PREFIX = b"RIFF"
WEBP_MARKER = b"WEBP"


class UnsupportedImageError(AppError):
    status_code = 415
    code = "unsupported_image"


class ImageTooLargeError(AppError):
    status_code = 413
    code = "image_too_large"


class ImageNotSavedError(AppError):
    """The image was fine; writing it failed."""

    status_code = 500
    code = "image_not_saved"


def detect_extension(content: bytes) -> str:
    """The real file type, from its leading bytes. Raises if it is not an image."""
    for prefix, extension in MAGIC_BYTES:
        if content.startswith(prefix):
            return extension
    if content[:4] == WEBP_PREFIX and content[8:12] == WEBP_MARKER:
        return "webp"
    raise UnsupportedImageError("That file is not a JPEG, PNG or WebP image.")


def save_card_image(
    *, content: bytes, copy_id: int, media_dir: Path, url_prefix: str, max_bytes: int
) -> str:
    """Write the image and return the URL to store on the copy.

    Uploads are stored exactly as sent: no resizing, so what the seller uploads is
    what buyers download. A large photo therefore makes a slow catalogue page.
    """
    if len(content) > max_bytes:
        raise ImageTooLargeError(
            f"That image is {len(content) // 1_000_000} MB. The limit is "
            f"{max_bytes // 1_000_000} MB."
        )
    if not content:
        raise UnsupportedImageError("That file is empty.")

    extension = detect_extension(content)
    # A random suffix means re-uploading a photo for the same card never collides
    # with a cached copy of the old one.
    filename = f"card-{copy_id}-{secrets.token_hex(8)}.{extension}"

    try:
        media_dir.mkdir(parents=True, exist_ok=True)
        (media_dir / filename).write_bytes(content)
    except OSError:
        # Usually a permissions problem on the media volume. The operator needs the
        # path and the errno; the seller needs neither and should not be shown them.
        logger.exception("could not write card image to %s", media_dir)
        raise ImageNotSavedError(
            "The image could not be saved. The shop's storage is not writable."
        ) from None
    logger.info("saved card image", extra={"copy_id": copy_id, "bytes": len(content)})

    return f"{url_prefix.rstrip('/')}/{filename}"
