CREATE OR REPLACE VIEW stg.stops AS
SELECT stop_id, stop_name,
       stop_lat::double precision AS lat,
       stop_lon::double precision AS lon
FROM raw.stops
WHERE feed_id = (SELECT max(feed_id) FROM raw.feed_versions)
  AND stop_lat ~ '^-?[0-9.]+$' AND stop_lon ~ '^-?[0-9.]+$';
