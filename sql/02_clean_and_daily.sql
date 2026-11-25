CREATE OR REPLACE VIEW aqi_clean AS
SELECT
  site_id,
  obs_time,
  CASE WHEN pm25 >= 1000 THEN NULL ELSE pm25 END AS pm25,
  CASE WHEN pm10 >= 1000 THEN NULL ELSE pm10 END AS pm10,
  no2, so2,
  CASE WHEN co = 0 THEN NULL ELSE co END AS co,
  ozone, nh3,
  CASE WHEN temp_c > 50 THEN NULL ELSE temp_c END AS temp_c,
  CASE WHEN humidity_pct < 5 THEN NULL ELSE humidity_pct END AS humidity_pct,
  CASE WHEN wind_speed > 20 THEN NULL ELSE wind_speed END AS wind_speed,
  wind_dir, rain_mm,
  CASE WHEN pm25 > 1.1 * pm10 THEN 1 ELSE 0 END AS pm_inconsistent
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