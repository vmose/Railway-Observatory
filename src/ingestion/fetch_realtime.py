from datetime import datetime, timedelta, timezone

import requests
from google.transit import gtfs_realtime_pb2
from psycopg2.extras import execute_values

from src.config import auth_headers, env
from src.db import connect
from src.validation.validate_feed import valid_coordinates


def fetch_feed(url: str):
    r = requests.get(url, headers=auth_headers(), timeout=30)
    r.raise_for_status()
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(r.content)
    return feed


def _ts(value, fallback):
    return datetime.fromtimestamp(value, tz=timezone.utc) if value else fallback


def parse_vehicle_positions(feed, fetched_at):
    header_ts = _ts(feed.header.timestamp, fetched_at)
    rows = []
    for e in feed.entity:
        if not e.HasField("vehicle") or not e.vehicle.HasField("position"):
            continue
        v = e.vehicle
        lat, lon = v.position.latitude, v.position.longitude
        observed = _ts(v.timestamp, header_ts)
        if not valid_coordinates(lat, lon) or observed > fetched_at + timedelta(minutes=5):
            continue  # reject bad coordinates and impossible (future) timestamps
        rows.append((v.vehicle.id or e.id, v.trip.trip_id or None, lat, lon, observed, fetched_at))
    return rows


def parse_trip_updates(feed, fetched_at):
    header_ts = _ts(feed.header.timestamp, fetched_at)
    rows = []
    for e in feed.entity:
        if not e.HasField("trip_update"):
            continue
        tu = e.trip_update
        if not tu.trip.trip_id:
            continue
        observed = _ts(tu.timestamp, header_ts)
        if observed > fetched_at + timedelta(minutes=5):
            continue
        for stu in tu.stop_time_update:
            if not (stu.HasField("arrival") and stu.arrival.HasField("delay")):
                continue
            rows.append((
                tu.trip.trip_id, stu.stop_id or "", stu.stop_sequence or None,
                tu.trip.start_date or None, stu.arrival.delay, observed, fetched_at,
            ))
    return rows


def run_realtime() -> dict:
    fetched_at = datetime.now(timezone.utc)
    counts = {}
    with connect() as conn, conn.cursor() as cur:
        vp_url, tu_url = env("GTFS_RT_VEHICLE_POSITIONS_URL"), env("GTFS_RT_TRIP_UPDATES_URL")
        if vp_url:
            rows = parse_vehicle_positions(fetch_feed(vp_url), fetched_at)
            execute_values(cur,
                "INSERT INTO raw.vehicle_positions (vehicle_id, trip_id, lat, lon, observed_at, fetched_at) "
                "VALUES %s ON CONFLICT DO NOTHING", rows)
            counts["vehicle_positions"] = len(rows)
        if tu_url:
            rows = parse_trip_updates(fetch_feed(tu_url), fetched_at)
            execute_values(cur,
                "INSERT INTO raw.trip_updates (trip_id, stop_id, stop_sequence, start_date, "
                "arrival_delay_s, observed_at, fetched_at) VALUES %s ON CONFLICT DO NOTHING", rows)
            counts["trip_updates"] = len(rows)
    return counts
