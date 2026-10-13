SELECT st.trip_id, st.stop_id FROM stg.stop_times st
WHERE NOT EXISTS (SELECT 1 FROM stg.trips t WHERE t.trip_id = st.trip_id)
   OR NOT EXISTS (SELECT 1 FROM stg.stops s WHERE s.stop_id = st.stop_id);
