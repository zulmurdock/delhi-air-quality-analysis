# README and notes tracker: Delhi Air Quality project

This file collects everything that goes into the final README. It is updated after every step. Items marked TO VERIFY must be checked against an outside source before publishing. The thresholds and lockdown dates were verified on 18 Oct 2026 (section 6a).

## 1. Project summary

- Title: Delhi Air Quality, Where and When to Act
- Business problem: a pollution control board has a limited budget. Which stations, seasons and hours should it target first, and is the air improving?
- Tools: Python (pandas), MySQL, Excel
- Data: CPCB hourly station data for Delhi (Kaggle collection, one CSV per station per year, 2010 to 2026). Scope used here: 2018 to 2025 (eight full calendar years). Reason: 2010 to 2016 had only about 10 stations against about 36 from 2017 onward, so mixing them would compare very different sensor sets, and 2026 is a partial year. The earlier years remain in the source and could be used later for a small long-run analysis on the stations that reported from 2010.
- Size after loading: 36 stations, 288 station-year files, 2,524,608 hourly rows
- Timestamps: format YYYY-MM-DD HH:MM:SS. The timezone is not stated in the dataset. Assumed local time (IST). The daily pattern in Q4 is consistent with local time, but that is supporting evidence only.

## 2. Pipeline (what was done)

1. Inspected one station file (columns, date format, missing values)
2. Scanned 2024 coverage across all 36 stations
3. Python loader combined 288 files into one table, extracting site_id and station label from the filenames
4. Built a station-year completeness grid (share of hours with PM2.5)
5. Audited the data for impossible or suspicious values
6. Created a MySQL database with two tables: stations (36 rows) and aqi_hourly (2,524,608 rows), with a composite primary key (site_id, obs_time) and a foreign key to stations
7. Verified the load, created the aqi_clean view (cleaning rules applied in SQL, raw table untouched)
8. Built daily_pm25 (daily average per station)
9. Ran the analysis queries

## 3. Data quality checks and results

- Duplicate station-hour rows: 0
- Unparseable timestamps: 0
- Files whose timestamps do not match the folder year: 0
- Text placeholders found in numeric columns: 0
- Every station-year file is complete in rows (8,760 or 8,784 hourly rows); missing readings appear as blank values
- Two different stations are both named Pusa (site 106, agency IITM, and site 1563, agency DPCC). All analysis is keyed on site_id, never on station name.
- Weather columns (temperature, humidity, wind, rain) are missing entirely at some stations. IITM stations have no weather, SO2 or NH3. Weather analysis therefore covers only a subset of stations.
- Column TOT-RF (total rainfall) was dropped. In the checked file it showed 0.0 in every row while the rainfall column was fully empty, so it looks like a filler value, not a measurement.
- Only 12 numeric columns were kept: PM2.5, PM10, NO2, SO2, CO, ozone, NH3, temperature, humidity, wind speed, wind direction, rain.
- Units differ across columns (NOx is in ppb and CO in mg/m3, the rest mostly ug/m3), so columns were not combined.

## 4. Fixed panel and completeness rules

- Fixed panel: 25 stations with at least 75% of hours with PM2.5 in every year from 2018 to 2025. The 75% cutoff is a convention and a choice.
- Why a fixed panel: the number of stations changed over time, so averaging all stations per year could show a change that only reflects stations being added.
- 11 stations are outside the panel. Reasons: late starters in 2018 (Bawana, Mundka, Sri Aurobindo Marg, Pusa DPCC, Alipur), long outages (Burari Crossing in 2020 and 2021, Lodhi Road in most years), and one weak year each for IGI Airport, Pusa IITM, Dr. Karni Singh and Sirifort.
- Panel limitation: the panel under-represents peripheral and industrial areas such as Bawana, Mundka and Alipur.
- Daily rule: a station-day counts only if it has at least 18 valid hourly PM2.5 readings (75%). This produced 94,315 station-days out of a possible 105,192.
- Lodhi Road (site 5395, confirm with SELECT * FROM stations WHERE site_id = 5395) is excluded from the station ranking: 522 valid days in 2023 to 2025 against a threshold of 730, and the next lowest station has 941. Check done 19 Oct 2026.

## 5. Cleaning rules (applied in the aqi_clean view)

Counts are from MySQL. Some differ slightly from the raw Python audit because MySQL stores 2 decimals (1 for humidity).

| Rule | Rows affected | Reason |
|---|---|---|
| PM2.5 of 1000 or more set to missing | 46 | Instrument ceiling. 40 of the 46 come from two stations (Sirifort 22, DTU 18), and several fall outside smog season, so mostly faulty sensors. PM2.5 values just below the cap (99.9th percentile is 748) were kept. |
| PM10 of 1000 or more set to missing | 329 | Same instrument ceiling |
| CO equal to 0 set to missing | 22,387 | Zeros appear at all 36 stations and every year, so not one broken sensor. Real ambient CO is rarely exactly 0. May be a placeholder or a below-detection value, so CO is not used for headline findings. |
| Temperature above 50 C set to missing | 68 | Implausible, and 30 of the 68 are in December |
| Wind speed above 20 m/s set to missing | 166 | Implausible as an hourly average at ground level |
| Humidity below 5% set to missing | 17,999 | Rule kept after the check in section 5a. Humidity is not used in any headline finding, so the impact is small. |
| PM2.5 more than 10% above PM10 | 6,631 flagged | Flag only (pm_inconsistent), nothing removed. The two come from separate instruments, so small mismatches are expected. |

## 5a. Humidity rule check (19 Oct 2026)

- Test: for hours with humidity below 5%, count rows and distinct values per station-year.
- Result: the low readings are not one stuck value (30 to 42 distinct values at the big cases, range 0.2 to 4.9). They are long runs at a few stations: site 1430 had 4,666 hours in 2019 and 605 in 2018, site 1432 had 3,829 in 2019, site 1424 had 2,489 in 2019, site 1426 had 1,604 in 2020. These four sites hold about 73% of the 17,999 flagged rows.
- Reading: thousands of hours in one year at one station is a sustained fault pattern, not weather, and hourly humidity under 5% is physically implausible for Delhi as far as I know (not checked against a source). The exact fault (drift, wrong scale, dead sensor) cannot be determined from this data.
- Decision: keep the rule, describe it as "sustained implausible low readings at a few stations", not "stuck sensors".
- Limit: values just above 5% from the same faulty sensors would not be caught. Humidity is not used in any headline finding, so this does not affect the results. Optional check: the humidity distribution of sites 1430, 1432 and 1424 in 2019.

- Raw data stays untouched in aqi_hourly. All analysis reads aqi_clean or tables built from it.
- Every threshold above is a judgment call and is documented with its reason.
- Extreme daily PM2.5 values were examined. The highest days cluster on the same dates across several stations (3 Nov 2019, 9 Nov 2020, 18 Nov 2024), which points to real city-wide smog episodes, and the lowest days fall in monsoon months across several stations. No removal rule was applied. One lone low value (Pusa IITM, 6 Aug 2024, 1.0) is unusual but kept.

## 6. Findings so far

Q1, headline numbers (all 36 stations, 2018 to 2025, daily averages):
- 94,315 valid station-days, mean daily PM2.5 of 104.7 ug/m3
- 61.4% of station-days above 60 ug/m3 and 98.5% above 15 ug/m3
- Thresholds verified, see section 6a.
- Note: these are station-days, not city-days.

Q2, station ranking (2023 to 2025, at least 730 valid days, 35 stations):
- Highest mean PM2.5: Anand Vihar 130.0, Jahangirpuri 129.0, Wazirpur 125.8, Bawana 124.1, Mundka 120.7
- Lowest of the 35: DTU 73.9, IHBAS Dilshad Garden 78.0, Aya Nagar 82.4
- Highest share of days above 60: Jahangirpuri 72.7%, Anand Vihar 70.7%
- The worst station averages about 1.8 times the cleanest (130.0 vs 73.9)
- Every station averages above 70 ug/m3, and even the cleanest has 48.1% of days above 60. The whole city is polluted, with a gap between hotspots and the rest.
- Cautions: do not over-read ranks in the middle (rank 20 and 21 differ by 0.7). Anand Vihar, Mandir Marg and Sirifort have the fewest valid days (941 to 954), so their averages could be biased downward if sensors dropped out during the worst smog. Agencies (DPCC, CPCB, IITM) differ in instruments and siting.

Q3, seasonal profile (25-station panel, averaged over 2018 to 2025):
- Monthly mean PM2.5: Jan 186.2, Feb 124.0, Mar 84.2, Apr 80.0, May 76.2, Jun 59.1, Jul 39.4, Aug 35.5, Sep 41.9, Oct 115.1, Nov 220.9, Dec 204.4
- Peak in November (220.9), trough in August (35.5), a ratio of about 6.2
- Winter (Nov, Dec, Jan) averages about 204, roughly 5 times the monsoon (Jul, Aug, Sep) average of about 39
- October is nearly triple September
- Caution: January has fewer valid station-days per day than December (about 22.3 vs 24.4 of 25 stations), so January may be understated if sensors fail in the worst smog.

Q4, hour-of-day profile (25-station panel, winter = Nov, Dec, Jan and monsoon = Jun to Sep):
- Winter: highest at 22:00 and 23:00 (249.0), lowest at 16:00 (135.3), a difference of about 114 ug/m3 and a ratio of about 1.8
- Monsoon: from 37.8 (17:00) to 49.8 (22:00), a much smaller cycle
- Same shape in both seasons: high late at night, falling through the morning, low in the late afternoon, steep evening rise (winter 17:00 to 22:00 rises about 77%). A smaller morning bump appears in winter (about 07:00 to 10:00).
- A winter afternoon (135.3) is still nearly three times worse than the worst monsoon hour (49.8)
- Cautions: timezone assumed local. Do not claim causes without a cited source. Winter has three months and monsoon four.

Q5, year-over-year change (25-station panel, annual mean of daily PM2.5):
- 2018: 118.1, 2019: 111.9 (-5.2%), 2020: 97.4 (-13.0%), 2021: 109.3 (+12.2%), 2022: 101.9 (-6.8%), 2023: 105.3 (+3.3%), 2024: 107.6 (+2.2%), 2025: 99.6 (-7.4%)
- Net change 2018 to 2025: about -15.7% (118.1 to 99.6). 2020 is the lowest year and 2025 the second lowest.
- No steady trend: after the 2021 rebound the values move between about 100 and 109, and single-year moves of 2 to 13% are large compared with the net change.
- Station-days per year: 8,113 to 8,686 out of a possible 9,125 (9,150 in leap years). Coverage is lowest in 2018 (about 89%) and highest in 2025 (about 95%).
- Cautions: the annual mean is dominated by the winter months, so one bad November moves the whole year. Weather differs between years. Eight data points are too few to claim a trend or credit any policy. Do not attribute the 2020 dip to the lockdown without the lockdown-window analysis (Q6), since the lockdown covers only about two months of that year.

Q6, lockdown window (25 Mar to 31 May, 68 days, same calendar window in every year):
- Only stations in the panel with at least 75% PM2.5 hours inside the window in all 8 years were used: 19 of the 25 panel stations. The same 19 stations are compared in every year.
- Mean PM2.5 in the window: 2018: 93.8, 2019: 89.6, 2020: 48.2, 2021: 71.8, 2022: 97.6, 2023: 69.1, 2024: 80.2, 2025: 72.0
- 2020 (48.2) is about 41% below the average of the other seven years (82.0), about 46% below 2019 (89.6), and about 30% below the lowest other year (2023, 69.1)
- 2020 sits about 21 ug/m3 below the lowest of the other years, while those other years differ among themselves by about 28 ug/m3 (69.1 to 97.6). So the drop is larger than ordinary year-to-year variation.
- Compare with the calendar-year panel mean, which fell only 13% in 2020 (Q5). The lockdown weeks account for a much larger drop than the full year.
- Cautions: this shows the drop coincided with the lockdown period, not that the lockdown caused all of it, since weather also varies. Surviving stations are the better-reporting ones. Lockdown dates verified, see section 6a. 6 panel stations were excluded for low coverage in the window; Anand Vihar and Narela are likely among them (about 48% and 73% coverage in 2020), but the full list still needs to be checked.

Q6b, bootstrap check on the lockdown result (NumPy, lockdown_bootstrap.py, 19 stations x 8 years from q6_by_station.csv, 10,000 resamples of stations with replacement, seed 42):
- Point estimate: 2020 mean 48.2 vs 82.0 for the other seven years, -41.2%
- 95% bootstrap interval for the change: -46.8% to -36.0%
- 2020 is the lowest year in all 10,000 resamples
- 2020 is the lowest year at 18 of the 19 stations. Per-station change in 2020 vs that station's average of the other years: -71.7% (largest drop) / -41.7% (median) / -18.4% (smallest drop), so every station was below its own other-year average in 2020.
- Each year vs the average of the other seven: 2018 +24.3%, 2019 +17.7%, 2020 -41.2%, 2021 -8.8%, 2022 +30.2%, 2023 -12.6%, 2024 +3.6%, 2025 -8.4%. The other seven years stay within -12.6% to +30.2%, so 2020 sits about 29 points below the next lowest year (2023).
- What the interval covers: only uncertainty from which stations were included. It does not cover year-to-year weather variation (that is what the each-year comparison is for). The 19 stations are the better-reporting ones, not a random sample of Delhi, so state the result as "among these 19 stations".
- The drop coincided with the lockdown window. It does not prove the lockdown caused all of it.

Q7, PM2.5 vs wind speed (hourly, winter months Nov, Dec, Jan, only stations that report wind, 450,034 hours):
- Wind under 0.5 m/s: 233.6 ug/m3 (192,269 hours), 0.5 to 1: 200.5 (121,799), 1 to 1.5: 187.1 (69,045), 1.5 to 2.5: 166.8 (46,889), 2.5 and above: 155.5 (20,032)
- PM2.5 falls at every step as wind rises, about 33% lower at 2.5 m/s and above than in near-calm air
- Calm conditions (under 1 m/s) make up about 70% of the observed winter hours (42.7% are under 0.5 m/s)
- Even at the highest wind bucket, winter PM2.5 (155.5) is still far above the 60 ug/m3 level used earlier, so wind alone does not clear the air
- Cautions: covers only stations that report wind speed (a subset of Delhi). Wind speed and PM2.5 both change through the day (Q4), so part of this relationship may reflect time of day. It shows an association, not a cause.

Q8, ten worst city-wide days (25-station panel, at least 20 stations reporting, daily mean PM2.5 in ug/m3):
- 18 Nov 2024: 585.0 (24 stations), 3 Nov 2019: 537.6 (23), 9 Nov 2020: 515.3 (24), 23 Dec 2018: 435.4 (25), 13 Nov 2024: 428.0 (23), 17 Nov 2024: 425.4 (23), 5 Nov 2021: 425.2 (21), 15 Jan 2021: 418.4 (23), 1 Jan 2021: 407.5 (24), 14 Dec 2025: 406.0 (23)
- All ten fall between November and January: six in November, two in December, two in January
- The worst day (18 Nov 2024, 585.0) is about 5.6 times the overall mean daily value (104.7), nearly 10 times the 60 ug/m3 level, and 47 ug/m3 above the second-worst day
- 2024 and 2021 have three days each in the top ten, 2018, 2019, 2020 and 2025 one each, 2022 and 2023 none
- Consistent with the earlier extremes check, where several stations peaked on 3 Nov 2019, 9 Nov 2020 and 18 Nov 2024
- Cautions: do not state causes (festivals, crop burning, weather) unless each date is checked against a source. This data shows when, not why.

Q9, 7-day rolling mean of city-wide daily PM2.5 (25-station panel, days with at least 20 stations reporting, 2,820 days returned):
- Highest rolling values: 390.7 (window ending 19 Nov 2024), 370.8 (18 Nov 2024), 367.2 (20 Nov 2024), 355.8 (22 Nov 2024), 355.5 (21 Nov 2024)
- The top five rolling values are all in November 2024 and stay above about 355 from 18 to 22 November, so the 13, 17 and 18 November 2024 spikes from Q8 were part of one sustained episode, not isolated days
- A rolling weekly mean of 390.7 is about 6.5 times the 60 ug/m3 level 
- Other sustained episodes in the top 14 rolling values: early November 2019 (peak 343.4, windows ending 3 to 5 Nov), late December 2021 (335.2 ending 26 Dec) and late December 2018 (about 322 to 326, windows ending 26 to 28 Dec)
- 2,820 days out of 2,922 (8 years) have a city value, so 102 days (about 3.5%) were left out because fewer than 20 stations had a valid day. The rolling window counts rows, not calendar days, so it stretches slightly over those gaps. Which years lost the most days has not been checked.

Q10, concentration by season (25-station panel, 2018 to 2025, 68,115 station-days; exposure = sum of daily mean PM2.5):
- Nov to Jan: 17,372 station-days (25.5%), 49.0% of exposure, 17,114 days above 60 (40.3% of all exceedance days)
- Feb to Oct: 50,743 station-days (74.5%), 51.0% of exposure, 25,336 days above 60 (59.7%)
- 98.5% of Nov to Jan station-days are above 60, against 49.9% in Feb to Oct
- Reading: winter carries about twice its share of exposure, but it is not "most" of it, and most exceedance days (59.7%) fall outside Nov to Jan. Recommendation 1 was reworded to say so. Winter is the severity peak, and a year-round baseline is still needed.
- Caution: Jan has lower coverage (Q3), so the winter share may be slightly understated.

## 6a. Outside facts verified (18 Oct 2026)

- India NAAQS, PM2.5: 60 ug/m3 for 24 hours and 40 ug/m3 annual. Notified 18 Nov 2009 (source: ies.gov.in). No later revision found. Confirm once on cpcb.nic.in before publishing.
- WHO 2021 air quality guidelines, PM2.5: 15 ug/m3 for 24 hours (99th percentile, meaning 3 to 4 exceedance days a year allowed) and 5 ug/m3 annual (WHO guideline compendium, chapter 2, Table 2.1; IQAir page agrees).
- Lockdown: phases 1 to 4 ran from 25 Mar to 31 May 2020, and Unlock 1.0 began on 1 June (Wikipedia, phases list). The analysis window 25 Mar to 31 May matches.
- Threshold lines (60 and 15) can now be drawn on charts.

## 7. Limitations (collect for the README)

- Station coverage changed over time, so trends use a fixed 25-station panel
- Station-day figures are not city-day figures
- Missing data may not be random. If sensors fail during the worst smog, averages for low-coverage stations or months are biased downward.
- Weather analysis only covers stations that report weather
- Differences between stations can reflect agency, instrument or siting, not only the air
- Cleaning thresholds are judgment calls (listed in section 5)
- The timezone is not stated by the source
- The data was not independently validated. CPCB documentation should be consulted before any health or regulatory use.
- Findings describe when and where pollution is high, not why

## 8. Still to do

- Q5b (optional): yearly winter-only (Nov, Dec) and monsoon-only (Jun to Sep) averages on the panel, to see which season drives the year-to-year changes
- Optional check: list which 6 panel stations were excluded from the lockdown comparison
- Q7b (optional): repeat the wind buckets separately for daytime and night hours, to check whether time of day explains the wind relationship
- Worst-day context: only mention festivals, crop burning or weather for those dates if each one is backed by a source (none are claimed yet)
- Optional check: how many of the 102 left-out days fall in each year (days with fewer than 20 reporting stations)
- NumPy step: DONE. lockdown_bootstrap.py was run and the result is in Q6b. Stack line for the resume: MySQL, Python (pandas, NumPy, matplotlib), Excel.
- Concentration query: DONE, see Q10. (Worst-5-station share was dropped: 5 of 35 stations is trivially small.)
- Excel dashboard: workbook built (delhi_aqi_dashboard.xlsx, 122 formulas, 0 errors; now also shows the 95% bootstrap interval). User adds the seven charts and pastes q9_rolling.csv (2,820 rows) into the q9 sheet. Not yet reviewed by the user.
- README write-up, resume bullets with real numbers
- Push to GitHub after the course (add myenv/ and data/ rules to .gitignore)

## 8b. Charts produced (images/ folder, made by charts.py from the exported CSVs)

- 01_station_ranking.png: mean PM2.5 by station, 35 stations, worst 5 in red (Q2)
- 02_monthly_profile.png: average PM2.5 by month, November highlighted (Q3)
- 03_hourly_profile.png: daily cycle, winter vs monsoon (Q4)
- 04_yearly_change.png: annual mean on the fixed panel, y-axis starts at zero so the changes show at true size (Q5)
- 05_lockdown_window.png: 25 Mar to 31 May by year, 2020 highlighted, dashed line at the average of the other years (Q6)
- 06_wind_speed.png: winter PM2.5 by wind speed bucket with hours per bucket (Q7)
- 07_worst_days.png: ten worst city-wide days (Q8)
- 08_rolling_7day.png: daily and 7-day rolling city-wide PM2.5, peak labelled (Q9)
- All eight were checked visually and match the query results. Fixes needed: the dashed-line label in chart 05 overlaps the bars (moved into a legend), and the peak label in chart 08 can get an arrow.
- Chart 08 starts in late January or February 2018, which suggests many of the 102 left-out days are at the start of 2018 (not yet checked).
- 09_lockdown_bootstrap.png: histogram of the 10,000 bootstrap results for the 2020 change, with the 95% interval and point estimate marked (Q6b)
- Threshold lines (60 and 15 ug/m3) are not drawn on any chart until the official values are verified.
