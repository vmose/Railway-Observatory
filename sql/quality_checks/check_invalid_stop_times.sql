SELECT trip_id, stop_id FROM stg.stop_times
WHERE arrival_seconds IS NULL OR departure_seconds IS NULL
   OR arrival_seconds > departure_seconds;
