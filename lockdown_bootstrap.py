from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
df = pd.read_csv(ROOT / "excel" / "q6_by_station.csv")

# 1. Turn the long table into a matrix: 19 stations (rows) x 8 years (columns)
wide = df.pivot(index="site_id", columns="yr", values="avg_pm25")
assert wide.shape == (19, 8) and wide.notna().all().all(), "unexpected shape or gaps"
years = wide.columns.to_numpy()
X = wide.to_numpy()
n = X.shape[0]
i = int(np.where(years == 2020)[0][0])        # column index of 2020

# 2. Point estimate: 2020 vs the average of the other seven years
year_means = X.mean(axis=0)
others = np.delete(year_means, i).mean()
point = year_means[i] / others - 1
print(f"2020 mean {year_means[i]:.1f} vs other years {others:.1f}: {point:+.1%}")

# 3. Bootstrap: resample the 19 stations with replacement, 10,000 times
rng = np.random.default_rng(42)
B = 10_000
idx = rng.integers(0, n, size=(B, n))          # B lists of 19 station numbers
Xb = X[idx]                                    # shape (B, 19, 8)
ym = Xb.mean(axis=1)                           # shape (B, 8): year means per resample
boot = ym[:, i] / np.delete(ym, i, axis=1).mean(axis=1) - 1

lo, hi = np.percentile(boot, [2.5, 97.5])
print(f"95% bootstrap interval for the 2020 change: {lo:+.1%} to {hi:+.1%}")
print(f"2020 is the lowest year in {(ym.argmin(axis=1) == i).mean():.1%} of resamples")

# 4. Does the pattern hold station by station?
per_station = X[:, i] / np.delete(X, i, axis=1).mean(axis=1) - 1
print(f"2020 is the lowest year at {int((X.argmin(axis=1) == i).sum())} of {n} stations")
print("per-station change, min / median / max:",
      " / ".join(f"{v:+.1%}" for v in np.percentile(per_station, [0, 50, 100])))

# 5. How unusual is 2020 compared with each of the other years?
print("\nEach year vs the average of the other seven:")
for k, y in enumerate(years):
    rest = np.delete(year_means, k).mean()
    print(f"  {y}: {year_means[k]:.1f}  {year_means[k] / rest - 1:+.1%}")

# 6. Chart for the README
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.hist(boot * 100, bins=60, color="#2b6cb0")
ax.axvline(lo * 100, color="black", linestyle="--", linewidth=1)
ax.axvline(hi * 100, color="black", linestyle="--", linewidth=1,
           label=f"95% interval: {lo:+.1%} to {hi:+.1%}")
ax.axvline(point * 100, color="#c53030", linewidth=2, label=f"Point estimate: {point:+.1%}")
ax.set_xlabel("2020 lockdown window vs other years (%)")
ax.set_ylabel("Number of resamples")
ax.set_title("Bootstrap of the 2020 change (19 stations, 10,000 resamples)")
ax.legend()
(ROOT / "images").mkdir(exist_ok=True)
fig.savefig(ROOT / "images" / "09_lockdown_bootstrap.png", dpi=150, bbox_inches="tight")
print("saved 09_lockdown_bootstrap.png")