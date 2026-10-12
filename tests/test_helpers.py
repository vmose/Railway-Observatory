from pathlib import Path


def test_sample_gtfs_files_exist():
    sample_dir = Path(__file__).resolve().parents[1] / "data" / "sample"
    for filename in ("stops.txt", "routes.txt", "trips.txt", "stop_times.txt"):
        assert (sample_dir / filename).is_file()


def test_sample_stop_times_have_required_headers():
    import csv
    path = Path(__file__).resolve().parents[1] / "data" / "sample" / "stop_times.txt"
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert {"trip_id", "stop_id", "stop_sequence", "arrival_time"}.issubset(reader.fieldnames)
        assert len(list(reader)) > 0
