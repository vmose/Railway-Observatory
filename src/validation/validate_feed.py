import csv
import io
import zipfile

# file -> required columns (also the columns loaded into raw.<name>)
REQUIRED = {
    "stops.txt": ["stop_id", "stop_name", "stop_lat", "stop_lon"],
    "routes.txt": ["route_id", "route_short_name", "route_long_name", "route_type"],
    "trips.txt": ["trip_id", "route_id", "service_id"],
    "stop_times.txt": ["trip_id", "stop_sequence", "stop_id", "arrival_time", "departure_time"],
}


class FeedValidationError(ValueError):
    pass


def validate_zip(zf: zipfile.ZipFile) -> None:
    names = set(zf.namelist())
    missing = [f for f in REQUIRED if f not in names]
    if missing:
        raise FeedValidationError(f"Missing required GTFS files: {missing}")
    for fname, cols in REQUIRED.items():
        with zf.open(fname) as f:
            header = next(csv.reader(io.TextIOWrapper(f, encoding="utf-8-sig")), [])
        absent = [c for c in cols if c not in header]
        if absent:
            raise FeedValidationError(f"{fname} is missing columns: {absent}")


def valid_coordinates(lat: float, lon: float) -> bool:
    return -90 <= lat <= 90 and -180 <= lon <= 180 and not (lat == 0 and lon == 0)


def run_quality_checks(sql_dir) -> None:
    """Each .sql file in quality_checks/ must return zero rows."""
    from pathlib import Path
    from src.db import connect

    failures = {}
    with connect() as conn, conn.cursor() as cur:
        for path in sorted(Path(sql_dir).glob("*.sql")):
            cur.execute(path.read_text())
            rows = cur.fetchall()
            if rows:
                failures[path.name] = rows[:5]
    if failures:
        raise FeedValidationError(f"Quality checks failed: {failures}")
