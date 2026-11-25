USE delhi_aqi;

-- Q1 
SELECT COUNT(*)                               AS valid_station_days,
       ROUND(AVG(pm25_avg), 1)                AS mean_pm25,
       ROUND(100 * AVG(pm25_avg > 60), 1)     AS pct_days_over_60,
       ROUND(100 * AVG(pm25_avg > 15), 1)     AS pct_days_over_15
FROM daily_pm25;

(SELECT 'highest' AS kind, d.obs_date, s.site_id, s.station_name, d.pm25_avg, d.hours_valid
 FROM daily_pm25 d JOIN stations s ON s.site_id = d.site_id
 ORDER BY d.pm25_avg DESC LIMIT 10)
UNION ALL
(SELECT 'lowest', d.obs_date, s.site_id, s.station_name, d.pm25_avg, d.hours_valid
 FROM daily_pm25 d JOIN stations s ON s.site_id = d.site_id
 ORDER BY d.pm25_avg ASC LIMIT 10);

 -- Q2
 USE delhi_aqi;

SELECT s.site_id, s.station_name, s.agency,
       COUNT(*)                                    AS valid_days,
       ROUND(AVG(d.pm25_avg), 1)                   AS mean_pm25,
       ROUND(100 * AVG(d.pm25_avg > 60), 1)        AS pct_days_over_60,
       RANK() OVER (ORDER BY AVG(d.pm25_avg) DESC) AS risk_rank
FROM daily_pm25 d
JOIN stations s ON s.site_id = d.site_id
WHERE d.obs_date >= '2023-01-01'
GROUP BY s.site_id, s.station_name, s.agency
HAVING COUNT(*) >= 730
ORDER BY mean_pm25 DESC;

-- SELECT COUNT(*) FROM daily_pm25 WHERE site_id = 5395 AND obs_date >= '2023-01-01';

USE delhi_aqi;

-- Q3
SELECT MONTH(d.obs_date)          AS month,
       ROUND(AVG(d.pm25_avg), 1)  AS avg_pm25,
       COUNT(*)                   AS station_days
FROM daily_pm25 d
JOIN stations s ON s.site_id = d.site_id
WHERE s.in_panel = 1
GROUP BY MONTH(d.obs_date)
ORDER BY month;

USE delhi_aqi;

-- Q4
SELECT HOUR(c.obs_time) AS hr,
       ROUND(AVG(CASE WHEN MONTH(c.obs_time) IN (11,12,1) THEN c.pm25 END), 1) AS winter_avg,
       ROUND(AVG(CASE WHEN MONTH(c.obs_time) IN (6,7,8,9) THEN c.pm25 END), 1) AS monsoon_avg
FROM aqi_clean c
JOIN stations s ON s.site_id = c.site_id
WHERE s.in_panel = 1
GROUP BY HOUR(c.obs_time)
ORDER BY hr;
-- Q5

USE delhi_aqi;

WITH yearly AS (
  SELECT YEAR(d.obs_date)          AS yr,
         ROUND(AVG(d.pm25_avg), 1) AS avg_pm25,
         COUNT(*)                  AS station_days
  FROM daily_pm25 d
  JOIN stations s ON s.site_id = d.site_id
  WHERE s.in_panel = 1
  GROUP BY YEAR(d.obs_date)
)
SELECT yr, avg_pm25, station_days,
       ROUND(100 * (avg_pm25 - LAG(avg_pm25) OVER (ORDER BY yr))
                 / LAG(avg_pm25) OVER (ORDER BY yr), 1) AS yoy_pct
FROM yearly;

-- Q6
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
  SELECT site_id
  FROM win
  GROUP BY site_id
  HAVING COUNT(*) = 8 AND MIN(hrs) >= 0.75 * 68 * 24
)
SELECT yr, COUNT(*) AS stations, ROUND(AVG(pm), 1) AS avg_pm25
FROM win
WHERE site_id IN (SELECT site_id FROM ok)
GROUP BY yr
ORDER BY yr;

-- Q7
USE delhi_aqi;

SELECT CASE WHEN wind_speed < 0.5 THEN '1: under 0.5'
            WHEN wind_speed < 1.0 THEN '2: 0.5 to 1'
            WHEN wind_speed < 1.5 THEN '3: 1 to 1.5'
            WHEN wind_speed < 2.5 THEN '4: 1.5 to 2.5'
            ELSE '5: 2.5 and above' END AS wind_bucket,
       COUNT(*)              AS hours,
       ROUND(AVG(pm25), 1)   AS avg_pm25
FROM aqi_clean
WHERE pm25 IS NOT NULL
  AND wind_speed IS NOT NULL
  AND MONTH(obs_time) IN (11, 12, 1)
GROUP BY wind_bucket
ORDER BY wind_bucket;

-- Q8

USE delhi_aqi;

SELECT d.obs_date,
       COUNT(*)                   AS stations_reporting,
       ROUND(AVG(d.pm25_avg), 1)  AS city_avg_pm25
FROM daily_pm25 d
JOIN stations s ON s.site_id = d.site_id
WHERE s.in_panel = 1
GROUP BY d.obs_date
HAVING COUNT(*) >= 20
ORDER BY city_avg_pm25 DESC
LIMIT 10;

-- Q9
USE delhi_aqi;

WITH city AS (
  SELECT d.obs_date, AVG(d.pm25_avg) AS a
  FROM daily_pm25 d
  JOIN stations s ON s.site_id = d.site_id
  WHERE s.in_panel = 1
  GROUP BY d.obs_date
  HAVING COUNT(*) >= 20
)
SELECT obs_date,
       ROUND(a, 1) AS city_pm25,
       ROUND(AVG(a) OVER (ORDER BY obs_date ROWS 6 PRECEDING), 1) AS rolling_7d
FROM city
ORDER BY obs_date;

WITH panel AS (
  SELECT site_id FROM (
    SELECT site_id, YEAR(obs_time) AS yr,
           COUNT(pm25) >= 0.75*24*IF(MAX(YEAR(obs_time))%4=0,366,365) AS ok
    FROM aqi_clean
    WHERE YEAR(obs_time) BETWEEN 2018 AND 2025
    GROUP BY site_id, YEAR(obs_time)
  ) t
  GROUP BY site_id HAVING SUM(ok) = 8
)
SELECT IF(MONTH(d.obs_date) IN (11,12,1),'Nov-Jan','Feb-Oct') AS season,
       COUNT(*) AS station_days,
       ROUND(100*COUNT(*)/SUM(COUNT(*)) OVER (),1) AS pct_of_days,
       ROUND(100*SUM(d.pm25_avg)/SUM(SUM(d.pm25_avg)) OVER (),1) AS pct_of_exposure,
       SUM(d.pm25_avg > 60) AS days_above_60,
       ROUND(100*SUM(d.pm25_avg > 60)/SUM(SUM(d.pm25_avg > 60)) OVER (),1) AS pct_of_exceedances
FROM daily_pm25 d JOIN panel p USING (site_id)
WHERE YEAR(d.obs_date) BETWEEN 2018 AND 2025
GROUP BY season;

SELECT site_id, COUNT(*) AS valid_days
FROM daily_pm25
WHERE obs_date >= '2023-01-01'
GROUP BY site_id ORDER BY valid_days LIMIT 5;

SELECT site_id, YEAR(obs_time) AS yr, COUNT(*) AS low_rows,
       COUNT(DISTINCT humidity_pct) AS distinct_values,
       MIN(humidity_pct) AS min_h, MAX(humidity_pct) AS max_h
FROM aqi_hourly
WHERE humidity_pct < 5
GROUP BY site_id, YEAR(obs_time)
ORDER BY low_rows DESC LIMIT 10;