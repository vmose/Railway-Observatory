DROP TABLE IF EXISTS mart.journey_durations;
CREATE TABLE mart.journey_durations AS
SELECT t.trip_id, t.route_id,
       count(*) AS stop_count,
       min(st.departure_seconds) AS first_departure_s,
       max(st.arrival_seconds)   AS last_arrival_s,
       (max(st.arrival_seconds) - min(st.departure_seconds)) / 60.0 AS scheduled_duration_min
FROM stg.trips t
JOIN stg.stop_times st USING (trip_id)
GROUP BY t.trip_id, t.route_id;
