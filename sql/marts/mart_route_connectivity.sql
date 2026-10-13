DROP TABLE IF EXISTS mart.route_connectivity;
CREATE TABLE mart.route_connectivity AS
SELECT t.route_id,
       count(DISTINCT t.trip_id)  AS trips,
       count(DISTINCT st.stop_id) AS stops
FROM stg.trips t
JOIN stg.stop_times st USING (trip_id)
GROUP BY t.route_id;

-- Network graph: one edge per consecutive stop pair.
DROP TABLE IF EXISTS mart.stop_edges;
CREATE TABLE mart.stop_edges AS
WITH seq AS (
    SELECT t.route_id, st.stop_id,
           lead(st.stop_id) OVER (PARTITION BY st.trip_id ORDER BY st.stop_sequence) AS next_stop
    FROM stg.trips t JOIN stg.stop_times st USING (trip_id)
)
SELECT stop_id AS from_stop, next_stop AS to_stop,
       count(DISTINCT route_id) AS routes, count(*) AS trips
FROM seq WHERE next_stop IS NOT NULL
GROUP BY stop_id, next_stop;
