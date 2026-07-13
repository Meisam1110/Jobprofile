#!/usr/bin/env python3
"""CLI: import the Irancell master workbook into the application database.

Usage (from repo root):
    python scripts/import_excel.py [path-to-workbook] [--limit N]
Defaults to data/job_profiles_master.xlsm.
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.services.importer import import_workbook  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("workbook", nargs="?", default=str(Path(__file__).resolve().parent.parent / "data" / "job_profiles_master.xlsm"))
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    started = time.time()
    try:
        stats = import_workbook(db, args.workbook, limit=args.limit)
    finally:
        db.close()
    print(f"Imported in {time.time() - started:.1f}s: {stats}")


if __name__ == "__main__":
    main()
