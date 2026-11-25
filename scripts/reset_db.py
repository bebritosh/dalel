"""Drop and recreate the SQLite database from the current models.

Startup already auto-migrates by adding missing columns (non-destructive), so a
reset is rarely needed. Use this only when you want a clean database, e.g. after
removing or renaming columns, which ADD COLUMN cannot handle.

This DELETES all rows. Uploaded files under data/ are left untouched.

Run:
    .venv/Scripts/python.exe scripts/reset_db.py          # asks for confirmation
    .venv/Scripts/python.exe scripts/reset_db.py --yes    # no prompt
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlmodel import SQLModel  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.db import engine  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    args = parser.parse_args()

    import app.models  # noqa: F401  (register tables)

    print(f"Database: {settings.database_url}")
    if not args.yes:
        answer = input("This DELETES all case data. Type 'reset' to continue: ")
        if answer.strip().lower() != "reset":
            print("Aborted. Nothing changed.")
            return 1

    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    print("Database reset: all tables dropped and recreated from current models.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
