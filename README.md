# Railway Observatory

An Airflow + Python + PostgreSQL + SQL portfolio project for exploring railway schedules and available real-time service updates. It starts with a small bundled GTFS-shaped sample dataset so the stack can be tested locally without signing up for an API. You can configure a static GTFS ZIP URL to ingest real schedules and the public GTFS Germany realtime feed for TripUpdates and ServiceAlerts.

## Architecture

1. **Schedule ingestion (Python):** load `stops.txt`, `routes.txt`, `trips.txt`, and `stop_times.txt` from a configured GTFS ZIP or bundled sample files.
2. **Realtime ingestion (Python):** capture GTFS-Realtime TripUpdates and ServiceAlerts as timestamped observations. The provider's feed is not guaranteed to cover every operator or service.
3. **SQL staging:** standardize stop, trip, and stop-time records.
4. **SQL marts:** summarize route connectivity and preserve realtime delay observations for exploration.
5. **Quality gates:** validate coordinates and referential integrity; failed checks fail the Airflow task.

## Data sources

- **GTFS Germany static feeds:** https://www.gtfs.de/en/feeds/ . The site offers separate long-distance rail, regional rail, local transit, and full feeds. For a first real run, choose a manageable rail-only feed (regional rail or long-distance rail), open its Download link, and set `GTFS_STATIC_URL` to the direct ZIP URL.
- **GTFS Germany realtime:** https://www.gtfs.de/en/realtime/ ; stream URL: `https://realtime.gtfs.de/realtime-free.pb`. It contains TripUpdates and ServiceAlerts, is described as updating every 10 seconds, and is published with coverage/completeness caveats. It does not guarantee vehicle-position records.
- **Railway infrastructure extension:** https://openrailwaymap.app/ and https://wiki.openstreetmap.org/wiki/OpenRailwayMap/API . Use the public API only for small, on-demand requests; for larger geographic analyses use an appropriately licensed extract and follow OpenStreetMap attribution/licensing requirements.

## Requirements

- Docker Desktop with Docker Compose
- Approximately 4 GB RAM available to Docker is a reasonable starting point
- Internet access for the realtime feed (optional; the pipeline currently treats realtime fetch failure as a task failure so Airflow retries it)

## Run locally

1. Clone the repository and enter its directory.
2. Copy `.env.example` to `.env` (PowerShell: `Copy-Item .env.example .env`). Leave `GTFS_STATIC_URL` blank for the sample data.
3. Start services: `docker compose up --build -d`. The first startup builds the image and initializes the Airflow metadata database.
4. Open http://localhost:8080 and sign in with `admin` / `admin` for this local development setup. The webserver and scheduler run as separate containers.
5. Unpause `railway_observatory` and trigger it. The DAG runs hourly; manual triggering is supported.
6. Query the database from your host using `localhost:5433`, database `railway`, user `railway`, password `railway`.

Example query (inside a psql client connected to the `railway` database):

```sql
SELECT * FROM mart_route_connectivity ORDER BY scheduled_trips DESC;
SELECT observation_type, COUNT(*)
FROM mart_realtime_delay_observations
GROUP BY observation_type;
```

## Configure a real static feed

Set `GTFS_STATIC_URL` in `.env` to the **direct downloadable ZIP URL** from GTFS Germany. Restart the Airflow service after changing environment variables:

```bash
docker compose up -d --build airflow
```

Start with a rail-only feed rather than the full Germany feed, which is much larger. Check the source's current license and attribution requirements before redistributing downloaded data or derived extracts.

## Useful next iterations

- Add GTFS `calendar.txt` and `calendar_dates.txt` so trips can be resolved to actual service dates.
- Add a proper GTFS-RT alert table with active periods and translated descriptions.
- Implement feed versioning and atomic schedule refreshes (current demo is intentionally a starter implementation).
- Add a delay analysis mart only after matching real-time trip IDs to the selected static feed and validating provider coverage.
- Add PostGIS and a map of station connectivity.
- Add GitHub Actions to run pytest and SQL linting on every push.

## Limitations

The bundled schedule is synthetic demo data, not a real timetable. GTFS static feeds can be large and contain fields beyond the four files loaded by this starter. Realtime trip IDs may not always match a given static feed, and a feed with no observations should not be interpreted as on-time service. Credentials and default passwords in this local compose file are for development only; do not deploy them publicly.
