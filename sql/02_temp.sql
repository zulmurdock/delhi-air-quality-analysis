USE delhi_aqi;

SELECT COUNT(*) FROM aqi_hourly;                      -- expect 2524608
SELECT COUNT(*), SUM(in_panel) FROM stations;         -- expect 36 and 25
SELECT MIN(obs_time), MAX(obs_time) FROM aqi_hourly;  -- 2018-01-01 to 2025-12-31 23:00

CREATE INDEX idx_time ON aqi_hourly(obs_time);        -- speeds up date filters

SELECT
  SUM(pm25 >= 1000)      AS pm25_capped,
  SUM(pm10 >= 1000)      AS pm10_capped,
  SUM(co = 0)            AS co_zero,
  SUM(temp_c > 50)       AS temp_over_50,
  SUM(humidity_pct < 5)  AS humidity_under_5,
  SUM(wind_speed > 20)   AS wind_over_20,
  COUNT(*)               AS total_rows
FROM aqi_hourly;

CREATE OR REPLACE VIEW aqi_clean AS
SELECT
  site_id,
  obs_time,
  CASE WHEN pm25 >= 1000 THEN NULL ELSE pm25 END AS pm25,   -- instrument cap, mostly 2 faulty sensors
  CASE WHEN pm10 >= 1000 THEN NULL ELSE pm10 END AS pm10,   -- instrument cap
  no2,
  so2,
  CASE WHEN co = 0 THEN NULL ELSE co END AS co,             -- zeros at all 36 stations, treated as missing
  ozone,
  nh3,
  CASE WHEN temp_c > 50 THEN NULL ELSE temp_c END AS temp_c,                    -- impossible, many in December
  CASE WHEN humidity_pct < 5 THEN NULL ELSE humidity_pct END AS humidity_pct,   -- PROVISIONAL, 75% of rows are in 2019
  CASE WHEN wind_speed > 20 THEN NULL ELSE wind_speed END AS wind_speed,        -- implausible at ground level
  wind_dir,
  rain_mm,
  CASE WHEN pm25 > 1.1 * pm10 THEN 1 ELSE 0 END AS pm_inconsistent  -- flag only, nothing removed
FROM aqi_hourly;

CREATE TABLE daily_pm25 AS
SELECT site_id,
       DATE(obs_time)       AS obs_date,
       ROUND(AVG(pm25), 1)  AS pm25_avg,
       COUNT(pm25)          AS hours_valid
FROM aqi_clean
GROUP BY site_id, DATE(obs_time)
HAVING COUNT(pm25) >= 18;

ALTER TABLE daily_pm25 ADD PRIMARY KEY (site_id, obs_date);

SELECT COUNT(*) FROM daily_pm25;   -- roughly 100,000 or more station-days

USE delhi_aqi;

SELECT COUNT(*)              AS total_rows,
       COUNT(pm25)           AS pm25_valid,
       COUNT(co)             AS co_valid,
       SUM(pm_inconsistent)  AS pm_flagged
FROM aqi_clean;

SELECT YEAR(obs_date)          AS yr,
       COUNT(*)                AS station_days,
       COUNT(DISTINCT site_id) AS stations,
       ROUND(AVG(pm25_avg), 1) AS avg_pm25,
       MIN(pm25_avg)           AS min_day,
       MAX(pm25_avg)           AS max_day
FROM daily_pm25
GROUP BY YEAR(obs_date)
ORDER BY yr;

-- bootstrap
USE delhi_aqi;

WITH win AS (
  SELECT c.site_id, YEAR(c.obs_time) AS yr,
         COUNT(c.pm25) AS hrs, AVG(c.pm25) AS pm
  FROM aqi_clean c
  JOIN stations s ON s.site_id = c.site_id
  WHERE s.in_panel = 1
    AND DATE_FORMAT(c.obs_time, '%m-%d') BETWEEN '03-25' AND '05-31'
  GROUP BY c.site_id, YEAR(c.obs_time)
),
ok AS (
  SELECT site_id FROM win
  GROUP BY site_id
  HAVING COUNT(*) = 8 AND MIN(hrs) >= 0.75 * 68 * 24
)
SELECT w.site_id, s.station_name, w.yr, ROUND(w.pm, 2) AS avg_pm25
FROM win w
JOIN stations s ON s.site_id = w.site_id
WHERE w.site_id IN (SELECT site_id FROM ok)
ORDER BY w.site_id, w.yr;