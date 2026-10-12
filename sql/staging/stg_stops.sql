CREATE TABLE IF NOT EXISTS stg_stops AS
SELECT stop_id, stop_name, stop_lat, stop_lon FROM raw_stops WHERE false;
TRUNCATE TABLE stg_stops;
INSERT INTO stg_stops (stop_id, stop_name, stop_lat, stop_lon)
SELECT stop_id, NULLIF(trim(stop_name), ''), stop_lat, stop_lon
FROM raw_stops
WHERE stop_id IS NOT NULL AND stop_lat BETWEEN -90 AND 90 AND stop_lon BETWEEN -180 AND 180;
