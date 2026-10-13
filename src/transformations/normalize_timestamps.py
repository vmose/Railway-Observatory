def gtfs_time_to_seconds(value):
    """GTFS times are HH:MM:SS measured from the service day's noon-minus-12h and
    can exceed 24:00:00 for overnight trips (e.g. '25:10:00'). Returns seconds
    since the start of the service day, or None for blank/invalid values."""
    if not value:
        return None
    parts = value.strip().split(":")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        return None
    h, m, s = map(int, parts)
    if m > 59 or s > 59:
        return None
    return h * 3600 + m * 60 + s
