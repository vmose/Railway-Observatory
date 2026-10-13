-- Predicted delays reported by the operator's trip_updates feed. Not confirmed arrivals.
DROP TABLE IF EXISTS mart.service_disruptions;
CREATE TABLE mart.service_disruptions AS
SELECT t.route_id, tu.stop_id, s.stop_name,
       count(*) AS observations,
       round(avg(tu.arrival_delay_s) / 60.0, 2) AS avg_predicted_delay_min,
       round(max(tu.arrival_delay_s) / 60.0, 2) AS max_predicted_delay_min
FROM raw.trip_updates tu
LEFT JOIN stg.trips t USING (trip_id)
LEFT JOIN stg.stops s USING (stop_id)
GROUP BY t.route_id, tu.stop_id, s.stop_name;
