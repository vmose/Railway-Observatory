SELECT COUNT(*) FROM stg_stop_times st
LEFT JOIN stg_trips t ON t.trip_id = st.trip_id
LEFT JOIN stg_stops s ON s.stop_id = st.stop_id
WHERE t.trip_id IS NULL OR s.stop_id IS NULL;
