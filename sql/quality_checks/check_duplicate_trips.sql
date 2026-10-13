SELECT trip_id, count(*) FROM raw.trips
WHERE feed_id = (SELECT max(feed_id) FROM raw.feed_versions)
GROUP BY trip_id HAVING count(*) > 1;
