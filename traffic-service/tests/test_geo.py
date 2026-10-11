"""Geodesic destination tests."""

from app.geo import destination_point, haversine_m


def test_destination_distance_approx_segment_length() -> None:
    origin_lat, origin_lon = 14.6349, -90.5069
    segment_m = 400.0
    dest_lat, dest_lon = destination_point(origin_lat, origin_lon, segment_m, 0.0)
    dist = haversine_m(origin_lat, origin_lon, dest_lat, dest_lon)
    assert abs(dist - segment_m) < 1.0  # within 1 meter


def test_bearing_east_changes_longitude() -> None:
    lat, lon = 0.0, 0.0
    dest_lat, dest_lon = destination_point(lat, lon, 1000.0, 90.0)
    assert abs(dest_lat) < 0.01
    assert dest_lon > 0
