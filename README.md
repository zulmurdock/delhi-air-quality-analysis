# Delhi Air Quality: Where and When to Act

An analysis of eight years of hourly PM2.5 data from Delhi's monitoring stations, built with Python, MySQL and Excel. It answers two questions: **where** in Delhi the air is worst, and **when** it is worst, so that action can be aimed at the right place and the right time.

**Author:** Mohammadzulnoon Attar

## Key findings

| Finding | Result |
| --- | --- |
| Station-days above the national daily limit (60 µg/m³) | 61.4% |
| Station-days above the WHO guideline (15 µg/m³) | 98.5% |
| Mean daily PM2.5 | 104.7 µg/m³ |
| Worst month against best month | November 220.9 against August 35.5 (6.2 times) |
| Worst stations | Anand Vihar 130.0, Jahangirpuri 129.0, Wazirpur 125.8, Bawana 124.1, Mundka 120.7 |
| Trend on a fixed 25-station panel | 118.1 in 2018 to 99.6 in 2025 (down 15.7%) |
| 2020 lockdown window (25 Mar to 31 May) | 48.2 against 82.0 in other years (down 41.2%, 95% interval 36.0% to 46.8%) |
| Winter hourly peak | 22:00 to 23:00 (249.0 µg/m³) |
| Winter PM2.5 in low wind (under 0.5 m/s) against high wind (2.5 m/s and above) | 234 against 156 |
| Worst day | 18 November 2024 (585.0 µg/m³ city-wide mean) |
| November to January | 25.5% of days but 49.0% of total exposure |

## Data

- **Source:** Central Pollution Control Board (CPCB) hourly station exports, 2018 to 2025.
- **Size:** 288 CSV files (one per station per year), 2,524,608 hourly rows, 36 stations.
- **Main variable:** PM2.5 in µg/m³. PM10, CO, temperature, humidity and wind speed are used as supporting variables.
- **Not included in this repository.** The raw files are large. Download them and place them under `data/<year>/`. File names follow the pattern `site_<id>_<Station>_Delhi_<Agency>_1Hr.csv`.

## Method in brief

1. **Combine and clean** the 288 files into one table. Unreadable values become missing, duplicates are removed, and checks stop the script if counts are wrong.
2. **Store in MySQL** with a composite primary key on station and time, so a duplicate reading cannot exist.
3. **Never edit the raw data.** A view called `aqi_clean` turns impossible values into missing and flags suspect rows.
4. **Daily table.** `daily_pm25` keeps station-days with at least 18 of 24 hours of data (94,315 of 105,192).
5. **Fixed panel.** Trends use only the 25 stations with at least 75% of PM2.5 hours in every year, so the same stations are compared over time.
6. **Lockdown comparison.** The same calendar window is compared across years, using the 19 stations with enough data in every year.
7. **Uncertainty.** A bootstrap resamples the 19 stations 10,000 times (seed 42) to give a 95% interval.
8. **Robustness.** A sensitivity script changes one threshold at a time and checks that the headline results hold.

Missing readings are kept as missing and never treated as zero.

## Project structure

    delhi-air-quality/
      data/
        2018/ ... 2025/           raw CPCB files (not committed)
        processed/
          delhi_aqi_2018_2025.csv combined output of load_data.py
      sql/                        schema, aqi_clean view, daily_pm25 table, queries Q1 to Q10
      excel/                      exported query tables
      charts/                     PNG figures
      load_data.py
      load_to_mysql.py
      audit.py
      sensitivity.py
      lockdown_bootstrap.py
      charts.py
      requirements.txt
      README.md

## How to run

**Requirements:** Python 3.10 or newer, MySQL 8, and the packages in `requirements.txt` (pandas, numpy, matplotlib, sqlalchemy, pymysql).

    python -m venv myenv
    myenv\Scripts\activate          (Linux or Mac: source myenv/bin/activate)
    pip install -r requirements.txt

    python load_data.py              # combine the 288 files into one CSV
    (run sql/01_schema.sql in MySQL)
    python load_to_mysql.py          # load into MySQL (asks for the password)
    (run sql/02_clean_and_daily.sql, then the queries in sql/03_queries.sql)
    python audit.py                  # data quality checks
    python sensitivity.py            # threshold robustness check
    python lockdown_bootstrap.py     # lockdown change with 95% interval
    python charts.py                 # figures

The database password is requested at run time and is never stored in the code.

## Queries

| Query | Question |
| --- | --- |
| Q1 | How bad is it overall? |
| Q2 | Which stations are worst? (ranked, 2023 to 2025) |
| Q3 | Which months are worst? |
| Q4 | Which hours are worst? (winter against monsoon) |
| Q5 | Is it improving? (year-on-year change on the panel) |
| Q6 | What did the lockdown show? |
| Q7 | Does wind help? |
| Q8 | Which days were worst? |
| Q9 | Are bad days isolated? (7-day rolling mean) |
| Q10 | How concentrated is the exposure? |

## Limitations

- The lockdown result is an **association, not proof of cause**. Weather and other differences between years are not adjusted for.
- The 75% coverage rule and the 18-hour rule are judgement calls. The sensitivity script tests alternatives, but they are not unique.
- The fixed panel covers 25 of 36 stations, so trend results describe those stations.
- The station ranking chart uses 2023 to 2025 means for the 35 stations with data in that period.
- Station readings do not equal each person's exposure.
- Only PM2.5 is analysed in depth. Other pollutants answer different questions and are measured at fewer stations.

## Possible next steps

- Adjust for weather (wind, rain, temperature) to separate the lockdown effect from meteorology.
- Extend the analysis to other pollutants and other cities.
- Publish an interactive Power BI version of the dashboard.

## Data source and licence

Data: Central Pollution Control Board (CPCB), Government of India. Check CPCB's terms before redistributing the raw files. Add a licence for your own code here (for example MIT).