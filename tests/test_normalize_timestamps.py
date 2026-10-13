from src.transformations.normalize_timestamps import gtfs_time_to_seconds


def test_regular_and_overnight_times():
    assert gtfs_time_to_seconds("08:15:30") == 8 * 3600 + 15 * 60 + 30
    assert gtfs_time_to_seconds("25:10:00") == 25 * 3600 + 600


def test_invalid_times():
    for bad in (None, "", "8:15", "ab:cd:ef", "10:75:00"):
        assert gtfs_time_to_seconds(bad) is None
