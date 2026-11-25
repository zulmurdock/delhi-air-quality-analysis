from pathlib import Path
from getpass import getpass
from urllib.parse import quote_plus
import pandas as pd
from sqlalchemy import create_engine

ROOT = Path(__file__).resolve().parent
YEARS = [str(y) for y in range(2018, 2026)]

pwd = quote_plus(getpass("MySQL root password: "))
engine = create_engine(f"mysql+pymysql://root:{pwd}@localhost:3306/delhi_aqi")

# ---- stations table ----
cov = pd.read_csv(ROOT / "data" / "processed" / "coverage_pm25_station_year.csv")
parts = cov["station"].str.extract(r"^(.+)_Delhi_([A-Za-z]+)$")
assert parts.notna().all().all(), "a station label did not match the pattern"
stations = pd.DataFrame({
    "site_id": cov["site_id"],
    "station_name": parts[0].str.replace("_", " "),
    "agency": parts[1],
    "in_panel": (cov[YEARS] >= 0.75).all(axis=1).astype(int),
})
stations.to_sql("stations", engine, if_exists="append", index=False)
print("stations loaded:", len(stations), "| in panel:", stations["in_panel"].sum())

# ---- hourly table ----
df = pd.read_csv(ROOT / "data" / "processed" / "delhi_aqi_2018_2025.csv",
                 parse_dates=["obs_time"])
df = df.drop(columns=["station_label", "file_year"])
df = df.sort_values(["site_id", "obs_time"])

CHUNK = 20000
for i in range(0, len(df), CHUNK):
    df.iloc[i:i + CHUNK].to_sql("aqi_hourly", engine, if_exists="append",
                                index=False, method="multi")
    if (i // CHUNK) % 25 == 0:
        print(f"{i:,} rows loaded")
print("done:", len(df))
