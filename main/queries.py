lost_minutes_query = """
WITH time_differences AS (
    SELECT 
        mt.user_id,
        uu.display_name,
        DATE(mt."timestamp") AS record_date,
        mt."timestamp",
        LAG(mt."timestamp") OVER (PARTITION BY mt.user_id, DATE(mt."timestamp") ORDER BY mt."timestamp") AS prev_timestamp
    FROM "main_telemetry" mt
    JOIN "users_user" uu ON mt.user_id = uu.id
),
delays AS (
    SELECT 
        user_id,
        display_name,
        record_date,
        EXTRACT(EPOCH FROM ("timestamp" - prev_timestamp)) / 60 AS delay_minutes
    FROM time_differences
    WHERE prev_timestamp IS NOT NULL
      AND EXTRACT(EPOCH FROM ("timestamp" - prev_timestamp)) / 60 > 1
),
recorded_minutes AS (
    SELECT 
        user_id,
        display_name,
        record_date,
        EXTRACT(EPOCH FROM (MAX("timestamp") - MIN("timestamp"))) / 60 AS total_recorded_minutes
    FROM time_differences
    GROUP BY user_id, display_name, record_date
)
SELECT 
    r.user_id,
    r.display_name,
    r.record_date,
    ROUND(r.total_recorded_minutes, 2) AS total_recorded_minutes,
    ROUND(COALESCE(SUM(d.delay_minutes), 0), 2) AS total_lost_minutes,
    ROUND(r.total_recorded_minutes - COALESCE(SUM(d.delay_minutes), 0), 2) AS total_valid_minutes,
    CASE 
        WHEN r.total_recorded_minutes > 0 THEN 
            ROUND((COALESCE(SUM(d.delay_minutes), 0) / r.total_recorded_minutes) * 100, 2)
        ELSE 
            0
    END AS percent_lost_minutes
FROM recorded_minutes r
LEFT JOIN delays d
    ON r.user_id = d.user_id AND r.record_date = d.record_date
GROUP BY r.user_id, r.display_name, r.record_date, r.total_recorded_minutes
ORDER BY r.record_date, r.user_id;
"""