-- GTFS times can exceed 24:00:00 for overnight trips, so they cannot be cast to TIME.
CREATE OR REPLACE FUNCTION stg.gtfs_seconds(t TEXT) RETURNS INT
LANGUAGE sql IMMUTABLE AS $$
    SELECT CASE WHEN trim(t) ~ '^[0-9]+:[0-5][0-9]:[0-5][0-9]$'
        THEN split_part(trim(t), ':', 1)::int * 3600
           + split_part(trim(t), ':', 2)::int * 60
           + split_part(trim(t), ':', 3)::int
    END
$$;
