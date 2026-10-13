# Railway Observatory

A data engineering project that collects GTFS timetables and GTFS Realtime snapshots,
models them in PostgreSQL, and lets you investigate schedules, connections and disruptions.

Stack: Python · SQL · Airflow · PostgreSQL · Docker

## Pipeline

    GTFS zip ──► validate ──► raw.*  ──► stg.* (views) ──► mart.* (tables) ──► quality checks
    GTFS-RT  ──► validate ──► raw.vehicle_positions / raw.trip_updates (append-only snapshots)

| Layer | What it holds |
|---|---|
| `raw.*` | Original values as text, tagged with `feed_id` (SHA-256 of the zip, so reloading is a no-op). |
| `stg.*` | Latest feed, typed. `stg.gtfs_seconds()` handles times past 24:00:00 for overnight trips. |
| `mart.*` | `journey_durations`, `route_connectivity`, `stop_edges` (network graph), `service_disruptions`. |

## Quick start (no operator needed, sample data)

    docker compose up -d postgres
    pip install -r requirements.txt
    export DATABASE_URL=postgresql://observatory:observatory@localhost:5432/observatory
    python -m src.cli init
    python -m src.cli load-sample
    python -m src.cli transform
    python -m src.cli check
    pytest

Then explore, e.g. `SELECT * FROM mart.journey_durations;` (trip T2 is an overnight trip with 24:10:00 times).

## Run with Airflow and a real operator

1. Pick an operator and find its GTFS zip URL and, if published, its GTFS-RT feeds
   (check their developer portal for licence, API keys and rate limits).
2. Fill in `.env` (see `.env.example`).
3. `docker compose up --build`, open http://localhost:8080 (the `standalone` command prints the admin password in the logs).
4. Enable `railway_schedule` first (creates the schema and staging views), then `railway_realtime`.

Adjust the realtime schedule to your operator's refresh rate.

## Design notes

- **Idempotent**: identical GTFS zips are skipped; realtime tables have primary keys with `ON CONFLICT DO NOTHING`.
- **History kept**: realtime rows are appended, never overwritten.
- **Predicted vs actual**: `trip_updates` delays are operator predictions; columns are named `predicted` on purpose.
- **Quality checks**: each file in `sql/quality_checks/` must return zero rows or the DAG fails.
- **Known limits**: GTFS loading buffers each file in memory (fine for most feeds; switch to chunked COPY for very large ones). Service-date and time-zone normalisation is not yet applied when joining realtime to scheduled stops.

## Ideas for next steps

Join `trip_updates` to scheduled `stop_times` using `start_date` + time zone; calendar/calendar_dates
handling; OpenRailwayMap infrastructure data; a small dashboard on top of `mart.*`.
