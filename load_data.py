from pathlib import Path
import re
import pandas as pd

ROOT = Path(__file__).resolve().parent
YEARS = range(2018, 2026)                 # 2018 to 2025 inclusive
TS_FORMAT = "%Y-%m-%d %H:%M:%S"                       # set after Step 2, e.g. "%d-%m-%Y %H:%M"

KEEP = {
    "PM2.5 (µg/m³)": "pm25", "PM10 (µg/m³)": "pm10",
    "NO2 (µg/m³)": "no2", "SO2 (µg/m³)": "so2", "CO (mg/m³)": "co",
    "Ozone (µg/m³)": "ozone", "NH3 (µg/m³)": "nh3",
    "AT (°C)": "temp_c", "RH (%)": "humidity_pct",
    "WS (m/s)": "wind_speed", "WD (deg)": "wind_dir", "RF (mm)": "rain_mm",
}
PATTERN = re.compile(r"^site_(\d+)_(.+)_1Hr$")

frames, coerced_total = [], 0
for year in YEARS:
    for f in sorted((ROOT / "data" / str(year)).glob("*.csv")):
        m = PATTERN.match(f.stem)
        if not m:
            print("skipped (name pattern):", f.name)
            continue
        site_id, label = int(m.group(1)), m.group(2)

        d = pd.read_csv(f)
        d = d[["Timestamp"] + [c for c in KEEP if c in d.columns]].rename(columns=KEEP)

        for col in KEEP.values():
            if col not in d.columns:
                d[col] = pd.NA
            before = d[col].isna().sum()
            d[col] = pd.to_numeric(d[col], errors="coerce")
            coerced_total += d[col].isna().sum() - before

        d["obs_time"] = pd.to_datetime(d.pop("Timestamp"), format=TS_FORMAT, errors="coerce")
        d["site_id"], d["station_label"], d["file_year"] = site_id, label, year
        frames.append(d)

df = pd.concat(frames, ignore_index=True)
print("rows:", len(df), "| stations:", df["site_id"].nunique())
print("text placeholders converted to missing:", coerced_total)
print("bad timestamps:", df["obs_time"].isna().sum())
print("duplicate site+time rows:", df.duplicated(["site_id", "obs_time"]).sum())
print("timestamp year != file year:", (df["obs_time"].dt.year != df["file_year"]).sum())

df = df.dropna(subset=["obs_time"]).drop_duplicates(["site_id", "obs_time"])
(ROOT / "data" / "processed").mkdir(exist_ok=True)
df.to_csv(ROOT / "data" / "processed" / "delhi_aqi_2018_2025.csv", index=False)
print(df.describe().T)

# ---- Completeness check per station per year (PM2.5) ----
df["year"] = df["obs_time"].dt.year
hours_in_year = {y: (366 if pd.Timestamp(y, 1, 1).is_leap_year else 365) * 24
                 for y in YEARS}

cov = df.groupby(["site_id", "year"])["pm25"].count().unstack("year")
for y in cov.columns:
    cov[y] = (cov[y] / hours_in_year[y]).round(2)

names = df.drop_duplicates("site_id").set_index("site_id")["station_label"]
cov.insert(0, "station", names)
cov.to_csv(ROOT / "data" / "processed" / "coverage_pm25_station_year.csv")

pd.set_option("display.width", 250)
print(cov.to_string())

valid = cov[list(YEARS)].ge(0.75)
print("stations with >=75% PM2.5 in every year:", valid.all(axis=1).sum())
print(cov.loc[valid.all(axis=1), "station"].to_string())