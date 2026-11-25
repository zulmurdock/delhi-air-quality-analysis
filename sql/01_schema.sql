CREATE DATABASE IF NOT EXISTS delhi_aqi;
USE delhi_aqi;

CREATE TABLE stations (
  site_id      INT PRIMARY KEY,
  station_name VARCHAR(80) NOT NULL,
  agency       VARCHAR(10) NOT NULL,
  in_panel     TINYINT NOT NULL
);

CREATE TABLE aqi_hourly (
  site_id      INT NOT NULL,
  obs_time     DATETIME NOT NULL,
  pm25         DECIMAL(7,2),
  pm10         DECIMAL(7,2),
  no2          DECIMAL(7,2),
  so2          DECIMAL(7,2),
  co           DECIMAL(7,2),
  ozone        DECIMAL(7,2),
  nh3          DECIMAL(7,2),
  temp_c       DECIMAL(5,1),
  humidity_pct DECIMAL(5,1),
  wind_speed   DECIMAL(6,2),
  wind_dir     DECIMAL(6,1),
  rain_mm      DECIMAL(6,2),
  PRIMARY KEY (site_id, obs_time),
  FOREIGN KEY (site_id) REFERENCES stations(site_id)
);