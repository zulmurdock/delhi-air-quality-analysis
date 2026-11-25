
from pathlib import Path
import re
import pandas as pd

ROOT = Path(__file__).resolve().parent
PATTERN = re.compile(r"^site_(\d+)_(.+)_1Hr$")
cols = ["PM2.5 (µg/m³)", "PM10 (µg/m³)", "NO2 (µg/m³)", "SO2 (µg/m³)",
        "CO (mg/m³)", "Ozone (µg/m³)", "NH3 (µg/m³)",
        "AT (°C)", "RH (%)", "WS (m/s)", "RF (mm)"]

rows = []
for f in sorted((ROOT / "data" / "2024").glob("*.csv")):
    m = PATTERN.match(f.stem)
    d = pd.read_csv(f, usecols=lambda c: c == "Timestamp" or c in cols)
    share = d.notna().mean().round(2)          # fraction of rows with a value
    share["site_id"] = int(m.group(1))
    share["station"] = m.group(2)
    share["rows"] = len(d)
    rows.append(share)

cov = pd.DataFrame(rows).drop(columns=["Timestamp"])
short = {c: c.split(" ")[0] for c in cols}
cov = cov.rename(columns=short)
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 30)
print(cov.sort_values("PM2.5", ascending=False).to_string(index=False))
