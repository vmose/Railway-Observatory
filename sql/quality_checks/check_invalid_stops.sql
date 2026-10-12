SELECT COUNT(*) FROM raw_stops
WHERE stop_id IS NULL OR stop_lat IS NULL OR stop_lon IS NULL
   OR stop_lat NOT BETWEEN -90 AND 90 OR stop_lon NOT BETWEEN -180 AND 180;
