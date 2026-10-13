CREATE OR REPLACE VIEW stg.stop_times AS
SELECT trip_id, stop_id,
       stop_sequence::int AS stop_sequence,
       stg.gtfs_seconds(arrival_time)   AS arrival_seconds,
       stg.gtfs_seconds(departure_time) AS departure_seconds
FROM raw.stop_times
WHERE feed_id = (SELECT max(feed_id) FROM raw.feed_versions);
