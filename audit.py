"""audit.py: read-only data validity audit of the combined Delhi AQI file.
Nothing is changed or deleted. It only measures problems so each cleaning rule has evidence."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
df = pd.read_csv(ROOT / "data" / "processed" / "delhi_aqi_2018_2025.csv",
                 parse_dates=["obs_time"])
df["year"] = df["obs_time"].dt.year
df["month"] = df["obs_time"].dt.month

num_cols = ["pm25", "pm10", "no2", "so2", "co", "ozone", "nh3",
            "temp_c", "humidity_pct", "wind_speed", "wind_dir", "rain_mm"]

# ---------------------------------------------------------------
# 1. Where does each column top out, and how often?
# ---------------------------------------------------------------
print("\n##### PART 1: maximums, percentiles, zeros")
rows = []
for c in num_cols:
    s = df[c].dropna()
    rows.append({"column": c, "values": len(s), "max": s.max(),
                 "rows_at_max": int((s == s.max()).sum()),
                 "p99": s.quantile(0.99), "p99.9": s.quantile(0.999),
                 "zeros": int((s == 0).sum())})
print(pd.DataFrame(rows).round(2).to_string(index=False))

# ---------------------------------------------------------------
# 2. Physical consistency checks
# ---------------------------------------------------------------
print("\n##### PART 2: physical consistency")
print("pm25 > pm10:", (df["pm25"] > df["pm10"]).sum())
print("pm25 > 1.1 x pm10:", (df["pm25"] > 1.1 * df["pm10"]).sum())
print("temp_c > 50:", (df["temp_c"] > 50).sum())
print("wind_speed > 20:", (df["wind_speed"] > 20).sum())
print("humidity_pct < 5:", (df["humidity_pct"] < 5).sum())

# ---------------------------------------------------------------
# 3. Are the PM2.5 = 1000 readings one broken sensor or real smog?
# ---------------------------------------------------------------
print("\n##### PART 3: PM2.5 cap readings by station and month")
cap = df[df["pm25"] >= 1000]
print(cap.groupby("site_id").size().sort_values(ascending=False).head(10))
print(cap.groupby(cap["obs_time"].dt.to_period("M")).size()
         .sort_values(ascending=False).head(10))

# ---------------------------------------------------------------
# 4. Lockdown window coverage (25 Mar to 31 May 2020 = 68 days)
# ---------------------------------------------------------------
print("\n##### PART 4: lockdown window coverage")
w = df[(df["obs_time"] >= "2020-03-25") & (df["obs_time"] < "2020-06-01")]
lock = w.groupby("site_id")["pm25"].count() / (68 * 24)
print(lock.round(2).sort_values().head(12))

# ---------------------------------------------------------------
# 5. Flags: do problem values come from a few stations (faults) or many?
# ---------------------------------------------------------------
print("\n##### PART 5: where do the suspicious values come from?")
flags = {
    "co == 0": df["co"] == 0,
    "humidity < 5": df["humidity_pct"] < 5,
    "wind_speed > 20": df["wind_speed"] > 20,
    "temp_c > 50": df["temp_c"] > 50,
}
for name, mask in flags.items():
    sub = df[mask]
    top = sub.groupby("site_id").size().sort_values(ascending=False)
    print(f"\n=== {name} | rows: {len(sub)} | stations affected: {len(top)}")
    print("share from top 3 stations:", round(top.head(3).sum() / len(sub), 2))
    print(top.head(5).to_string())
    print("by year:", sub.groupby("year").size().to_dict())
    print("top months:", sub.groupby("month").size().sort_values(ascending=False).head(4).to_dict())

# ---------------------------------------------------------------
# 6. Stuck-sensor test for humidity (2019 only, the year most low readings fall in)
#    A real sensor wobbles; a broken one repeats the same value for hours or days.
# ---------------------------------------------------------------
print("\n##### PART 6: stuck-sensor test, humidity in 2019")
d19 = df[df["obs_time"].dt.year == 2019].sort_values(["site_id", "obs_time"])

for sid in [1430, 1432, 1424, 1426, 301]:
    s = d19[d19["site_id"] == sid].set_index("obs_time")["humidity_pct"]
    low = s < 5
    print(f"\nsite {sid} | rows below 5%: {low.sum()}")
    print("by month:", low.groupby(s.index.month).sum().to_dict())
    run_id = (s != s.shift()).cumsum()
    runs = s.groupby(run_id).agg(value="first", hours="size")
    print(runs.sort_values("hours", ascending=False).head(3).to_string())