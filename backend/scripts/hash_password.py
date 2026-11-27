"""Generate ADMIN_PASSWORD_HASH for .env.

    cd backend
    uv run python scripts/hash_password.py

Asks for the password without echoing it, so the plaintext never reaches your shell
history or a file. Paste the printed hash into .env; the password itself is stored
nowhere.
"""

import getpass
import sys
from pathlib import Path

# Running a file inside scripts/ puts scripts/ on the path, not the backend root, so
# `app` would not be importable. Importing the real hasher rather than calling argon2
# directly keeps one definition of the hashing parameters.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.security import hash_password  # noqa: E402


def main() -> int:
    password = getpass.getpass("New admin password: ")
    if not password:
        print("Nothing entered.", file=sys.stderr)
        return 1
    if password != getpass.getpass("Again: "):
        print("They do not match.", file=sys.stderr)
        return 1

    print("\nAdd this line to .env:\n")
    print(f"ADMIN_PASSWORD_HASH={hash_password(password)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
