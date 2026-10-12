CREATE TABLE IF NOT EXISTS mart_realtime_delay_observations AS
SELECT observed_at, feed_timestamp, trip_id, route_id, stop_id, stop_sequence,
       arrival_delay_seconds, departure_delay_seconds, observation_type
FROM raw_realtime_observations WHERE false;
TRUNCATE TABLE mart_realtime_delay_observations;
INSERT INTO mart_realtime_delay_observations
SELECT observed_at, feed_timestamp, trip_id, route_id, stop_id, stop_sequence,
       arrival_delay_seconds, departure_delay_seconds, observation_type
FROM raw_realtime_observations;
