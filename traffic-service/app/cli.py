"""CLI entrypoints: run batch ingestion and export CSV for Looker Studio."""

from __future__ import annotations

import argparse
import logging
import sys
import time

from app.config import get_settings
from app.main import process_reading
from app.sources import CsvSource
from app.storage import Storage

logger = logging.getLogger(__name__)


def cmd_run(args: argparse.Namespace) -> int:
    settings = get_settings()
    source = CsvSource(args.csv)
    points = source.get_points()
    if not points:
        logger.error("No points found in %s", args.csv)
        return 1

    storage = Storage(settings.db_path)
    iteration = 0
    while True:
        iteration += 1
        logger.info("Run iteration=%s points=%s", iteration, len(points))
        for lat, lon in points:
            result = process_reading(lat, lon, settings, storage=storage)
            logger.info(
                "point=(%s,%s) status=%s error=%s",
                lat,
                lon,
                result.status,
                result.error,
            )
        if not args.loop:
            break
        logger.info("Sleeping %s seconds", args.interval)
        time.sleep(args.interval)
    return 0


def cmd_export_csv(args: argparse.Namespace) -> int:
    settings = get_settings()
    storage = Storage(settings.db_path)
    count = storage.export_csv(args.out)
    print(f"Exported {count} rows to {args.out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.cli",
        description="Traffic ingestion CLI (Grupo 2)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Ingest points from a CSV of real GPS coordinates")
    run_p.add_argument("--csv", required=True, help="Path to CSV with lat,lon columns")
    run_p.add_argument("--loop", action="store_true", help="Repeat forever")
    run_p.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Seconds between loop iterations (default 300)",
    )
    run_p.set_defaults(func=cmd_run)

    export_p = sub.add_parser("export-csv", help="Export readings_raw to CSV")
    export_p.add_argument("--out", required=True, help="Output CSV path")
    export_p.set_defaults(func=cmd_export_csv)

    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
