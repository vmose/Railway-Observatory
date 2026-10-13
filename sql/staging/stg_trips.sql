CREATE OR REPLACE VIEW stg.trips AS
SELECT DISTINCT trip_id, route_id, service_id
FROM raw.trips
WHERE feed_id = (SELECT max(feed_id) FROM raw.feed_versions);
