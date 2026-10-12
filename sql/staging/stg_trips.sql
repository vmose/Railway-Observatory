CREATE TABLE IF NOT EXISTS stg_trips AS
SELECT trip_id, route_id, service_id, trip_headsign, direction_id FROM raw_trips WHERE false;
TRUNCATE TABLE stg_trips;
INSERT INTO stg_trips (trip_id, route_id, service_id, trip_headsign, direction_id)
SELECT trip_id, route_id, service_id, trip_headsign, direction_id
FROM raw_trips WHERE trip_id IS NOT NULL;
