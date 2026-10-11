#!/usr/bin/env python3
"""
Coverage check: query Mapbox driving-traffic and driving for each CSV point.

Purpose: run at peak and off-peak hours to verify live traffic durations vary,
and append evidence rows to coverage_log.csv for the project report.

Usage (from traffic-service/):
  python scripts/coverage_check.py --csv points.csv [--log coverage_log.csv]
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow running as a script from traffic-service/
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import get_settings
from app.congestion import CongestionError, congestion_index
from app.geo import destination_point
from app.mapbox_client import MapboxClient, MapboxError
from app.sources import CsvSource


def main() -> int:
    parser = argparse.ArgumentParser(description="Mapbox traffic coverage check")
    parser.add_argument("--csv", required=True, help="CSV with real lat,lon points")
    parser.add_argument(
        "--log",
        default="coverage_log.csv",
        help="Append-only log CSV (default: coverage_log.csv)",
    )
    args = parser.parse_args()

    settings = get_settings()
    points = CsvSource(args.csv).get_points()
    if not points:
        print("No points in CSV", file=sys.stderr)
        return 1

    run_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    log_path = Path(args.log)
    write_header = not log_path.exists()
    fieldnames = [
        "run_timestamp",
        "lat",
        "lon",
        "t_traffic_s",
        "t_free_s",
        "dist_traffic_m",
        "dist_free_m",
        "congestion_numeric_avg",
        "traffic_congestion_index",
        "error",
    ]

    print(
        f"{'lat':>10} {'lon':>10} {'t_traf':>8} {'t_free':>8} "
        f"{'dist_m':>8} {'index':>8} {'cong_avg':>8} error"
    )
    print("-" * 80)

    with MapboxClient(settings.mapbox_access_token) as client, log_path.open(
        "a", newline="", encoding="utf-8"
    ) as log_fh:
        writer = csv.DictWriter(log_fh, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()

        for lat, lon in points:
            dest_lat, dest_lon = destination_point(
                lat,
                lon,
                settings.segment_length_m,
                settings.segment_bearing_deg,
            )
            row = {
                "run_timestamp": run_ts,
                "lat": lat,
                "lon": lon,
                "t_traffic_s": "",
                "t_free_s": "",
                "dist_traffic_m": "",
                "dist_free_m": "",
                "congestion_numeric_avg": "",
                "traffic_congestion_index": "",
                "error": "",
            }
            try:
                dual = client.fetch_dual_route(lat, lon, dest_lat, dest_lon)
                idx: float | str
                try:
                    idx = congestion_index(dual.traffic.duration_s, dual.free.duration_s)
                except CongestionError as exc:
                    idx = ""
                    row["error"] = str(exc)

                row.update(
                    {
                        "t_traffic_s": dual.traffic.duration_s,
                        "t_free_s": dual.free.duration_s,
                        "dist_traffic_m": dual.traffic.distance_m,
                        "dist_free_m": dual.free.distance_m,
                        "congestion_numeric_avg": dual.traffic.congestion_numeric_avg
                        if dual.traffic.congestion_numeric_avg is not None
                        else "",
                        "traffic_congestion_index": idx,
                    }
                )
                print(
                    f"{lat:10.5f} {lon:10.5f} "
                    f"{dual.traffic.duration_s:8.1f} {dual.free.duration_s:8.1f} "
                    f"{dual.traffic.distance_m:8.1f} "
                    f"{(idx if idx != '' else float('nan')):8} "
                    f"{(dual.traffic.congestion_numeric_avg or float('nan')):8} "
                    f"{row['error']}"
                )
            except MapboxError as exc:
                row["error"] = str(exc)
                print(
                    f"{lat:10.5f} {lon:10.5f} "
                    f"{'':>8} {'':>8} {'':>8} {'':>8} {'':>8} {exc}"
                )

            writer.writerow(row)

    print(f"\nAppended {len(points)} rows to {log_path} (run_timestamp={run_ts})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
