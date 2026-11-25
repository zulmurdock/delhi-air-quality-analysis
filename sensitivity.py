"""Sensitivity check: do the headline results survive different cleaning thresholds?
Changes ONE threshold at a time and recomputes four headline numbers."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
YEARS = list(range(2018, 2026))
HOURS = {y: (366 if pd.Timestamp(y, 1, 1).is_leap_year else 365) * 24 for y in YEARS}

df = pd.read_csv(ROOT / "data" / "processed" / "delhi_aqi_2018_2025.csv",
                 usecols=["site_id", "obs_time", "pm25"], parse_dates=["obs_time"])
df["year"] = df["obs_time"].dt.year
df["date"] = df["obs_time"].dt.normalize()
df["month"] = df["obs_time"].dt.month
df["day"] = df["obs_time"].dt.day


def run(cap, min_hours, cov_thr):
    pm = df["pm25"].where(df["pm25"] < cap)          # readings at or above the cap become missing
    d = df.assign(pm=pm)

    # 1) fixed panel: share of hours with PM2.5 per station-year
    cov = d.groupby(["site_id", "year"])["pm"].count().unstack("year")
    cov = cov.div(pd.Series(HOURS), axis=1)
    panel = cov.index[(cov >= cov_thr).all(axis=1)]

    # 2) daily means, only for days with enough valid hours
    g = d.groupby(["site_id", "date"])["pm"].agg(["count", "mean"])
    daily = g[g["count"] >= min_hours]["mean"].reset_index(name="pm25")
    daily["year"] = daily["date"].dt.year
    daily["month"] = daily["date"].dt.month
    daily["day"] = daily["date"].dt.day

    # headline A: share of station-days above India's standard
    share = (daily["pm25"] > 60).mean() * 100
    # headline B: November vs August
    m = daily.groupby("month")["pm25"].mean()
    ratio = m[11] / m[8]
    # headline C: yearly change on the fixed panel
    p = daily[daily["site_id"].isin(panel)]
    yr = p.groupby("year")["pm25"].mean()
    change = (yr[2025] / yr[2018] - 1) * 100
    # headline D: lockdown window (25 Mar to 31 May), same dates every year
    mask = ((p["month"] == 3) & (p["day"] >= 25)) | (p["month"] == 4) | (p["month"] == 5)
    w = p[mask]
    n = w.groupby(["site_id", "year"]).size().unstack().reindex(columns=YEARS).fillna(0)
    keep = n.index[(n >= 51).all(axis=1)]            # at least 75% of the 68 window days, every year
    ym = w[w["site_id"].isin(keep)].groupby("year")["pm25"].mean()
    drop = (ym[2020] / ym.drop(2020).mean() - 1) * 100
    return {"valid_station_days": len(daily), "panel_stations": len(panel),
            "pct_days_above_60": round(share, 1), "nov_vs_aug_ratio": round(ratio, 1),
            "panel_change_2018_2025_pct": round(change, 1),
            "lockdown_stations": len(keep), "lockdown_drop_pct": round(drop, 1)}


BASE = dict(cap=1000, min_hours=18, cov_thr=0.75)
VARIANTS = [("BASELINE (what the project uses)", {}),
            ("cap 500", {"cap": 500}), ("cap 1500", {"cap": 1500}), ("no cap", {"cap": 1e9}),
            ("min valid hours 12", {"min_hours": 12}), ("min valid hours 16", {"min_hours": 16}),
            ("min valid hours 20", {"min_hours": 20}),
            ("panel coverage 70%", {"cov_thr": 0.70}), ("panel coverage 80%", {"cov_thr": 0.80})]

rows = []
for label, change in VARIANTS:
    r = run(**{**BASE, **change})
    rows.append({"variant": label, **r})
    print("done:", label)

out = pd.DataFrame(rows).set_index("variant")
pd.set_option("display.width", 200)
print(out.to_string())
out.to_csv(ROOT / "excel" / "sensitivity.csv") if (ROOT / "excel").exists() else out.to_csv(ROOT / "sensitivity.csv")