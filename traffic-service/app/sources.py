"""Coordinate input sources (CSV and future Group 1 API)."""

from __future__ import annotations

import csv
import logging
from abc import ABC, abstractmethod
from pathlib import Path

logger = logging.getLogger(__name__)


class CoordinateSource(ABC):
    """Interface for obtaining real GPS points."""

    @abstractmethod
    def get_points(self) -> list[tuple[float, float]]:
        """Return list of (latitude, longitude) from a real source."""


class CsvSource(CoordinateSource):
    """Load lat,lon pairs from a CSV file of real GPS points."""

    def __init__(self, path: str) -> None:
        self.path = Path(path)

    def get_points(self) -> list[tuple[float, float]]:
        if not self.path.exists():
            raise FileNotFoundError(f"CSV not found: {self.path}")

        points: list[tuple[float, float]] = []
        with self.path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            if not reader.fieldnames:
                raise ValueError("CSV has no header row")

            field_map = {name.lower().strip(): name for name in reader.fieldnames}
            lat_key = field_map.get("lat") or field_map.get("latitude")
            lon_key = field_map.get("lon") or field_map.get("lng") or field_map.get("longitude")
            if not lat_key or not lon_key:
                raise ValueError("CSV must include lat/latitude and lon/longitude columns")

            for i, row in enumerate(reader, start=2):
                try:
                    lat = float(row[lat_key])
                    lon = float(row[lon_key])
                except (KeyError, TypeError, ValueError) as exc:
                    raise ValueError(f"Invalid lat/lon at CSV line {i}") from exc
                if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
                    raise ValueError(f"Out-of-range coordinates at CSV line {i}")
                points.append((lat, lon))

        logger.info("Loaded %s points from %s", len(points), self.path)
        return points


class Group1ApiSource(CoordinateSource):
    """
    Stub for fetching real GPS points from Group 1's API.

    TODO(G2): implement once G1 (or G4) publishes the coordinate feed contract.
    Uses GROUP1_API_URL from configuration when available.
    """

    def __init__(self, api_url: str | None) -> None:
        self.api_url = api_url

    def get_points(self) -> list[tuple[float, float]]:
        raise NotImplementedError(
            "TODO(G2): Group1ApiSource not implemented yet; "
            f"configured GROUP1_API_URL={self.api_url!r}"
        )
