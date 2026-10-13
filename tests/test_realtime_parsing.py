from datetime import datetime, timedelta, timezone

from google.transit import gtfs_realtime_pb2

from src.ingestion.fetch_realtime import parse_trip_updates, parse_vehicle_positions

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
TS = int(NOW.timestamp())


def _feed():
    f = gtfs_realtime_pb2.FeedMessage()
    f.header.gtfs_realtime_version = "2.0"
    f.header.timestamp = TS
    return f


def test_vehicle_positions_filter_bad_rows():
    f = _feed()
    good = f.entity.add(); good.id = "1"
    good.vehicle.vehicle.id = "V1"; good.vehicle.position.latitude = -1.29; good.vehicle.position.longitude = 36.8
    good.vehicle.timestamp = TS
    bad = f.entity.add(); bad.id = "2"
    bad.vehicle.vehicle.id = "V2"; bad.vehicle.position.latitude = 0; bad.vehicle.position.longitude = 0
    future = f.entity.add(); future.id = "3"
    future.vehicle.vehicle.id = "V3"; future.vehicle.position.latitude = -1.3; future.vehicle.position.longitude = 36.8
    future.vehicle.timestamp = int((NOW + timedelta(hours=2)).timestamp())
    rows = parse_vehicle_positions(f, NOW)
    assert [r[0] for r in rows] == ["V1"]


def test_trip_updates_extract_delay():
    f = _feed()
    e = f.entity.add(); e.id = "1"
    e.trip_update.trip.trip_id = "T1"
    s = e.trip_update.stop_time_update.add(); s.stop_id = "B"; s.arrival.delay = 120
    s2 = e.trip_update.stop_time_update.add(); s2.stop_id = "C"  # no delay -> skipped
    rows = parse_trip_updates(f, NOW)
    assert len(rows) == 1 and rows[0][0] == "T1" and rows[0][4] == 120
