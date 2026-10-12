CREATE TABLE IF NOT EXISTS mart_route_connectivity AS
SELECT r.route_id, r.route_short_name, r.route_long_name,
       COUNT(DISTINCT t.trip_id) AS scheduled_trips,
       COUNT(DISTINCT st.stop_id) AS distinct_stops
FROM raw_routes r
LEFT JOIN stg_trips t ON t.route_id = r.route_id
LEFT JOIN stg_stop_times st ON st.trip_id = t.trip_id
GROUP BY r.route_id, r.route_short_name, r.route_long_name;
TRUNCATE TABLE mart_route_connectivity;
INSERT INTO mart_route_connectivity
SELECT r.route_id, r.route_short_name, r.route_long_name,
       COUNT(DISTINCT t.trip_id), COUNT(DISTINCT st.stop_id)
FROM raw_routes r
LEFT JOIN stg_trips t ON t.route_id = r.route_id
LEFT JOIN stg_stop_times st ON st.trip_id = t.trip_id
GROUP BY r.route_id, r.route_short_name, r.route_long_name;
