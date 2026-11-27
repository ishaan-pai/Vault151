"""Loader for the ``.sql`` files that sit beside this module.

The SQL lives in its own files rather than in Python string literals so that it stays
readable, syntax-highlighted, and can be handed to a reader on its own. Statements are
read once and cached for the life of the process.

Every statement uses bind variables. Never build SQL by formatting values into a
string, and never pass a caller-supplied name to :func:`load_sql`.
"""

from functools import cache
from pathlib import Path

_SQL_DIR = Path(__file__).parent


@cache
def load_sql(name: str) -> str:
    """Return the statement in ``<name>.sql``.

    ``name`` is always a literal written in the repository layer, but it is validated
    anyway so that a future caller cannot reach outside this directory.
    """
    if not name.replace("_", "").isalnum():
        raise ValueError(f"not a valid SQL file name: {name!r}")

    path = _SQL_DIR / f"{name}.sql"
    if not path.is_file():
        raise FileNotFoundError(f"no SQL file named {name}.sql in {_SQL_DIR}")

    # Oracle rejects a trailing semicolon on a statement sent through the driver,
    # so the files may end with one for readability and it is stripped here.
    return path.read_text(encoding="utf-8").strip().rstrip(";")
