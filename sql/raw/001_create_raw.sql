CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS stg;
CREATE SCHEMA IF NOT EXISTS mart;

CREATE TABLE IF NOT EXISTS raw.feed_versions (
    feed_id   SERIAL PRIMARY KEY,
    source    TEXT,
    sha256    TEXT UNIQUE NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Static GTFS: every value kept as text, tagged with the feed version it came from.
CREATE TABLE IF NOT EXISTS raw.stops (
    feed_id INT REFERENCES raw.feed_versions, stop_id TEXT, stop_name TEXT, stop_lat TEXT, stop_lon TEXT);
CREATE TABLE IF NOT EXISTS raw.routes (
    feed_id INT REFERENCES raw.feed_versions, route_id TEXT, route_short_name TEXT, route_long_name TEXT, route_type TEXT);
CREATE TABLE IF NOT EXISTS raw.trips (
    feed_id INT REFERENCES raw.feed_versions, trip_id TEXT, route_id TEXT, service_id TEXT);
CREATE TABLE IF NOT EXISTS raw.stop_times (
    feed_id INT REFERENCES raw.feed_versions, trip_id TEXT, stop_sequence TEXT, stop_id TEXT,
    arrival_time TEXT, departure_time TEXT);

-- Realtime snapshots: append-only; primary keys make re-runs idempotent.
CREATE TABLE IF NOT EXISTS raw.vehicle_positions (
    vehicle_id TEXT NOT NULL, trip_id TEXT, lat DOUBLE PRECISION, lon DOUBLE PRECISION,
    observed_at TIMESTAMPTZ NOT NULL, fetched_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (vehicle_id, observed_at));
CREATE TABLE IF NOT EXISTS raw.trip_updates (
    trip_id TEXT NOT NULL, stop_id TEXT NOT NULL DEFAULT '', stop_sequence INT, start_date TEXT,
    arrival_delay_s INT,  -- a PREDICTED delay reported by the operator, not a confirmed arrival
    observed_at TIMESTAMPTZ NOT NULL, fetched_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (trip_id, stop_id, observed_at));
