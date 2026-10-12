CREATE TABLE IF NOT EXISTS stg_stop_times AS
SELECT trip_id, stop_id, stop_sequence, arrival_time, departure_time
FROM raw_stop_times WHERE false;
TRUNCATE TABLE stg_stop_times;
INSERT INTO stg_stop_times (trip_id, stop_id, stop_sequence, arrival_time, departure_time)
SELECT trip_id, stop_id, stop_sequence, arrival_time, departure_time
FROM raw_stop_times
WHERE trip_id IS NOT NULL AND stop_id IS NOT NULL AND stop_sequence IS NOT NULL;
