"""Ingestion and SQL execution functions used by the Airflow DAG."""
from __future__ import annotations

import csv
import io
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
import requests
from psycopg2.extras import Json, execute_values
from google.transit import gtfs_realtime_pb2

BASE_DIR = Path(__file__).resolve().parents[2]
SAMPLE_DIR = BASE_DIR / "data" / "sample"
SQL_DIR = BASE_DIR / "sql"
GTFS_FILES = {
    "stops.txt": ["stop_id", "stop_name", "stop_lat", "stop_lon"],
    "routes.txt": ["route_id", "agency_id", "route_short_name", "route_long_name", "route_type"],
    "trips.txt": ["route_id", "service_id", "trip_id", "trip_headsign", "direction_id"],
    "stop_times.txt": ["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"],
}


def connect():
    """Connect using the Airflow railway_db connection environment variable."""
    from urllib.parse import urlparse
    url = os.getenv("RAILWAY_DATABASE_URL", "postgresql://railway:railway@postgres:5432/railway")
    parsed = urlparse(url)
    return psycopg2.connect(
        host=parsed.hostname, port=parsed.port or 5432, dbname=parsed.path.lstrip("/"),
        user=parsed.username, password=parsed.password,
    )


def _ensure_tables(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS raw_stops (
                stop_id TEXT PRIMARY KEY, stop_name TEXT, stop_lat DOUBLE PRECISION,
                stop_lon DOUBLE PRECISION, ingested_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            CREATE TABLE IF NOT EXISTS raw_routes (
                route_id TEXT PRIMARY KEY, agency_id TEXT, route_short_name TEXT,
                route_long_name TEXT, route_type INTEGER, ingested_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            CREATE TABLE IF NOT EXISTS raw_trips (
                trip_id TEXT PRIMARY KEY, route_id TEXT, service_id TEXT, trip_headsign TEXT,
                direction_id TEXT, ingested_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            CREATE TABLE IF NOT EXISTS raw_stop_times (
                trip_id TEXT NOT NULL, stop_id TEXT NOT NULL, stop_sequence INTEGER NOT NULL,
                arrival_time TEXT, departure_time TEXT, ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                PRIMARY KEY (trip_id, stop_sequence)
            );
            CREATE TABLE IF NOT EXISTS raw_realtime_observations (
                id BIGSERIAL PRIMARY KEY, feed_timestamp TIMESTAMPTZ, observed_at TIMESTAMPTZ NOT NULL,
                trip_id TEXT, route_id TEXT, stop_id TEXT, stop_sequence INTEGER,
                arrival_delay_seconds INTEGER, departure_delay_seconds INTEGER,
                schedule_relationship TEXT, observation_type TEXT NOT NULL, payload JSONB NOT NULL
            );
            CREATE INDEX IF NOT EXISTS ix_realtime_trip_observed ON raw_realtime_observations(trip_id, observed_at);
        """)
    conn.commit()


def _read_gtfs_sources():
    """Return CSV rows from a configured static ZIP, or bundled sample files for a zero-setup demo."""
    url = os.getenv("GTFS_STATIC_URL", "").strip()
    if url:
        response = requests.get(url, timeout=90)
        response.raise_for_status()
        archive = zipfile.ZipFile(io.BytesIO(response.content))
        return {name: list(csv.DictReader(io.TextIOWrapper(archive.open(name), encoding="utf-8-sig")))
                for name in GTFS_FILES if name in archive.namelist()}
    return {name: list(csv.DictReader((SAMPLE_DIR / name).open(encoding="utf-8-sig", newline="")))
            for name in GTFS_FILES}


def load_schedule():
    """Load core GTFS tables idempotently; sample files are used unless a feed URL is configured."""
    sources = _read_gtfs_sources()
    conn = connect()
    try:
        _ensure_tables(conn)
        mappings = {
            "stops.txt": ("raw_stops", ["stop_id", "stop_name", "stop_lat", "stop_lon"],
                          lambda r: (r.get("stop_id"), r.get("stop_name"), _float_or_none(r.get("stop_lat")), _float_or_none(r.get("stop_lon")))),
            "routes.txt": ("raw_routes", ["route_id", "agency_id", "route_short_name", "route_long_name", "route_type"],
                           lambda r: (r.get("route_id"), r.get("agency_id"), r.get("route_short_name"), r.get("route_long_name"), _int_or_none(r.get("route_type")))),
            "trips.txt": ("raw_trips", ["trip_id", "route_id", "service_id", "trip_headsign", "direction_id"],
                          lambda r: (r.get("trip_id"), r.get("route_id"), r.get("service_id"), r.get("trip_headsign"), r.get("direction_id"))),
            "stop_times.txt": ("raw_stop_times", ["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"],
                               lambda r: (r.get("trip_id"), r.get("arrival_time"), r.get("departure_time"), r.get("stop_id"), _int_or_none(r.get("stop_sequence")))),
        }
        with conn.cursor() as cur:
            for filename, rows in sources.items():
                table, columns, mapper = mappings[filename]
                if not rows:
                    continue
                values = [mapper(row) for row in rows]
                if filename == "stop_times.txt":
                    # A feed refresh replaces this table so deleted schedule rows do not linger.
                    cur.execute("TRUNCATE TABLE raw_stop_times")
                cols = ",".join(columns)
                updates = ",".join(f"{c}=EXCLUDED.{c}" for c in columns if c not in ("stop_id", "route_id", "trip_id"))
                conflict = "(trip_id, stop_sequence)" if table == "raw_stop_times" else f"({columns[0]})"
                action = f"DO UPDATE SET {updates}" if updates else "DO NOTHING"
                execute_values(cur, f"INSERT INTO {table} ({cols}) VALUES %s ON CONFLICT {conflict} {action}", values)
        conn.commit()
        return f"Loaded static GTFS data from {'configured URL' if os.getenv('GTFS_STATIC_URL') else 'bundled sample files'}: " + ", ".join(f"{k}={len(v)}" for k,v in sources.items())
    finally:
        conn.close()


def _float_or_none(value):
    return float(value) if value not in (None, "") else None


def _int_or_none(value):
    return int(value) if value not in (None, "") else None


def load_realtime():
    """Capture a snapshot of available GTFS-Realtime trip updates and service alerts."""
    url = os.getenv("GTFS_REALTIME_URL", "https://realtime.gtfs.de/realtime-free.pb").strip()
    if not url:
        return "GTFS_REALTIME_URL is blank; realtime ingestion skipped."
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)
    observed_at = datetime.now(timezone.utc)
    feed_timestamp = datetime.fromtimestamp(feed.header.timestamp, timezone.utc) if feed.header.HasField("timestamp") else None
    records = []
    for entity in feed.entity:
        if entity.HasField("trip_update"):
            update = entity.trip_update
            trip_id = update.trip.trip_id or None
            route_id = update.trip.route_id or None
            relationship = str(update.trip.schedule_relationship) if update.trip.HasField("schedule_relationship") else None
            if update.stop_time_update:
                for stop_update in update.stop_time_update:
                    arrival_delay = stop_update.arrival.delay if stop_update.HasField("arrival") and stop_update.arrival.HasField("delay") else None
                    departure_delay = stop_update.departure.delay if stop_update.HasField("departure") and stop_update.departure.HasField("delay") else None
                    records.append((feed_timestamp, observed_at, trip_id, route_id, stop_update.stop_id or None,
                                    stop_update.stop_sequence or None, arrival_delay, departure_delay,
                                    relationship, "trip_update", Json({"entity_id": entity.id, "trip_id": trip_id,
                                    "stop_id": stop_update.stop_id, "arrival_delay": arrival_delay,
                                    "departure_delay": departure_delay})))
            else:
                records.append((feed_timestamp, observed_at, trip_id, route_id, None, None, None, None,
                                relationship, "trip_update", Json({"entity_id": entity.id, "trip_id": trip_id})))
        elif entity.HasField("alert"):
            alert = entity.alert
            description = ""
            if alert.HasField("description_text") and alert.description_text.translation:
                description = alert.description_text.translation[0].text
            records.append((feed_timestamp, observed_at, None, None, None, None, None, None, None,
                            "service_alert", Json({"entity_id": entity.id, "description": description,
                            "active_period_count": len(alert.active_period)})))
    conn = connect()
    try:
        _ensure_tables(conn)
        with conn.cursor() as cur:
            if records:
                execute_values(cur, """INSERT INTO raw_realtime_observations
                    (feed_timestamp, observed_at, trip_id, route_id, stop_id, stop_sequence,
                     arrival_delay_seconds, departure_delay_seconds, schedule_relationship,
                     observation_type, payload) VALUES %s""", records)
        conn.commit()
        return f"Captured {len(records)} realtime observations; feed entities={len(feed.entity)}."
    finally:
        conn.close()


def run_sql_models():
    conn = connect()
    try:
        with conn.cursor() as cur:
            for path in sorted((SQL_DIR / "staging").glob("*.sql")) + sorted((SQL_DIR / "marts").glob("*.sql")):
                cur.execute(path.read_text(encoding="utf-8"))
        conn.commit()
        return "Executed staging and mart SQL models."
    finally:
        conn.close()


def run_quality_checks():
    conn = connect()
    failures = []
    try:
        with conn.cursor() as cur:
            for path in sorted((SQL_DIR / "quality_checks").glob("*.sql")):
                cur.execute(path.read_text(encoding="utf-8"))
                result = cur.fetchone()
                count = int(result[0]) if result else 0
                if count:
                    failures.append(f"{path.name}: {count} failing rows")
        if failures:
            raise ValueError("Data quality checks failed: " + "; ".join(failures))
        return "All SQL quality checks passed."
    finally:
        conn.close()
