from pathlib import Path
import calendar
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
EXCEL = ROOT / "excel"
IMAGES = ROOT / "images"
IMAGES.mkdir(exist_ok=True)

BLUE, RED, GREY = "#2b6cb0", "#c53030", "#a0aec0"


def save(fig, name):
    fig.savefig(IMAGES / name, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


# 1. Station ranking (Q2)
q2 = pd.read_csv(EXCEL / "q2_station_ranking.csv")
q2["label"] = q2["station_name"] + " (" + q2["agency"] + ")"
q2 = q2.sort_values("mean_pm25")
colors = [RED if r <= 5 else BLUE for r in q2["risk_rank"]]
fig, ax = plt.subplots(figsize=(8, 10))
ax.barh(q2["label"], q2["mean_pm25"], color=colors)
ax.set_xlabel("Mean daily PM2.5 (µg/m³), 2023 to 2025")
ax.set_title("Mean PM2.5 by station (35 stations, red = worst 5)")
save(fig, "01_station_ranking.png")

# 2. Monthly profile (Q3)
q3 = pd.read_csv(EXCEL / "q3_monthly_profile.csv")
labels = [calendar.month_abbr[m] for m in q3["month"]]
colors = [RED if v == q3["avg_pm25"].max() else BLUE for v in q3["avg_pm25"]]
fig, ax = plt.subplots(figsize=(9, 5))
ax.bar(labels, q3["avg_pm25"], color=colors)
for i, v in enumerate(q3["avg_pm25"]):
    ax.text(i, v + 3, f"{v:.0f}", ha="center", fontsize=9)
ax.set_ylabel("Mean daily PM2.5 (µg/m³)")
ax.set_title("Average PM2.5 by month, 25-station panel, 2018 to 2025")
save(fig, "02_monthly_profile.png")

# 3. Hour-of-day profile (Q4)
q4 = pd.read_csv(EXCEL / "q4_hourly_profile.csv")
fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(q4["hr"], q4["winter_avg"], color=RED, marker="o", label="Winter (Nov, Dec, Jan)")
ax.plot(q4["hr"], q4["monsoon_avg"], color=BLUE, marker="o", label="Monsoon (Jun to Sep)")
ax.set_xticks(range(0, 24, 2))
ax.set_xlabel("Hour of day (assumed local time)")
ax.set_ylabel("Mean PM2.5 (µg/m³)")
ax.set_title("Daily cycle of PM2.5, 25-station panel")
ax.set_ylim(0, None)
ax.legend()
save(fig, "03_hourly_profile.png")

# 4. Year-over-year (Q5)
q5 = pd.read_csv(EXCEL / "q5_yearly_change.csv")
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(q5["yr"], q5["avg_pm25"], color=BLUE, marker="o")
for x, y in zip(q5["yr"], q5["avg_pm25"]):
    ax.annotate(f"{y:.1f}", (x, y), textcoords="offset points",
                xytext=(0, 8), ha="center", fontsize=9)
ax.set_ylim(0, 140)
ax.set_ylabel("Annual mean PM2.5 (µg/m³)")
ax.set_title("Annual mean PM2.5, 25-station fixed panel")
save(fig, "04_yearly_change.png")

# 5. Lockdown window (Q6)
q6 = pd.read_csv(EXCEL / "q6_lockdown.csv")
others = q6.loc[q6["yr"] != 2020, "avg_pm25"].mean()
colors = [RED if y == 2020 else BLUE for y in q6["yr"]]
fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(q6["yr"].astype(str), q6["avg_pm25"], color=colors)
ax.axhline(others, color="black", linestyle="--", linewidth=1,
           label=f"Average of the other years: {others:.1f}")
ax.set_ylim(0, 115)
ax.legend(loc="upper right")
ax.set_ylabel("Mean PM2.5 (µg/m³)")
ax.set_title("PM2.5, 25 Mar to 31 May each year (19 stations)")
save(fig, "05_lockdown_window.png")

# 6. Wind speed (Q7)
q7 = pd.read_csv(EXCEL / "q7_wind.csv")
labels = [f"{b.split(': ')[1]}\n({h / 1000:.0f}k hours)"
          for b, h in zip(q7["wind_bucket"], q7["hours"])]
fig, ax = plt.subplots(figsize=(9, 5))
ax.bar(labels, q7["avg_pm25"], color=BLUE)
for i, v in enumerate(q7["avg_pm25"]):
    ax.text(i, v + 3, f"{v:.0f}", ha="center", fontsize=9)
ax.set_xlabel("Wind speed (m/s)")
ax.set_ylabel("Mean PM2.5 (µg/m³)")
ax.set_title("Winter PM2.5 by wind speed (Nov, Dec, Jan)")
save(fig, "06_wind_speed.png")

# 7. Ten worst days (Q8)
q8 = pd.read_csv(EXCEL / "q8_worst_days.csv", parse_dates=["obs_date"])
q8 = q8.sort_values("city_avg_pm25")
labels = q8["obs_date"].dt.strftime("%d %b %Y")
colors = [RED if v == q8["city_avg_pm25"].max() else BLUE for v in q8["city_avg_pm25"]]
fig, ax = plt.subplots(figsize=(8, 5))
ax.barh(labels, q8["city_avg_pm25"], color=colors)
ax.set_xlabel("City-wide mean PM2.5 (µg/m³)")
ax.set_title("Ten worst days, 25-station panel")
save(fig, "07_worst_days.png")

# 8. Rolling 7-day mean (Q9)
q9 = pd.read_csv(EXCEL / "q9_rolling.csv", parse_dates=["obs_date"])
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(q9["obs_date"], q9["city_pm25"], color=GREY, linewidth=0.6, label="Daily")
ax.plot(q9["obs_date"], q9["rolling_7d"], color=BLUE, linewidth=1.4, label="7-day rolling mean")
peak = q9.loc[q9["rolling_7d"].idxmax()]
ax.annotate(f"Peak {peak['rolling_7d']:.0f}\n{peak['obs_date']:%d %b %Y}",
            (peak["obs_date"], peak["rolling_7d"]),
            textcoords="offset points", xytext=(15, -5), fontsize=9)
ax.set_ylabel("City-wide PM2.5 (µg/m³)")
ax.set_title("City-wide PM2.5, daily and 7-day rolling mean, 2018 to 2025")
ax.legend()
save(fig, "08_rolling_7day.png")