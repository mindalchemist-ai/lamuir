# How many days was the 10-year minus 2-year U.S. Treasury yield spread negative in 2022–2025?

## Data

`/app/data/treasury_par_yield_curve_2022.csv` to `/app/data/treasury_par_yield_curve_2025.csv` are the U.S. Treasury's Daily Treasury Par Yield Curve Rates files, one per calendar year, exactly as published. Each row is one business day; `Date` is written `MM/DD/YYYY`; the other columns are par yields in percent for each tenor. Rows are in the order the Treasury publishes them, and the set of tenor columns differs between years. These are par yields, not zero-coupon rates.

## Task

1. Read all four files and keep the dates from 2022-01-03 to 2025-12-31.
2. For each date compute the 10-year minus 2-year spread in basis points: $s_t = 100\,(y^{10Y}_t - y^{2Y}_t)$, using the columns `10 Yr` and `2 Yr`. Skip a date if either yield is blank; do not fill it.
3. The curve is **inverted** on a date when $s_t < 0$.
4. A streak is a run of consecutive rows (in date order) that are all inverted.

## Output

Write to `/app/output/`:

- `analysis.csv`, one row per date used, in ascending date order, columns `date,yield_2y,yield_10y,spread_bp,inverted`. Here `date` is ISO `YYYY-MM-DD`, the yields are in percent as in the input, and `inverted` is `true` or `false`.
- `results.json` with these keys:
  - `n_days` (integer): dates used;
  - `mean_spread_bp`;
  - `min_spread_bp` and `min_spread_date` (ISO date; the first such date if tied);
  - `n_inverted_days` (integer);
  - `first_inverted_date` and `last_inverted_date` (ISO dates);
  - `longest_inverted_streak_days` (integer, counted in rows).
  
  Spreads are in basis points, unrounded.
- `chart.png`: the daily spread over time as a line, a horizontal line at 0, and the area between the spread and 0 filled only where the spread is below 0 (for example `fill_between(dates, spread, 0, where=spread < 0)`).
- `explanation.md`: start with one or two sentences that answer the question in the title directly, using the numbers you computed. Then give a short plain-English explanation of what the numbers show, stating that these are par yields and that an inversion describes the curve's shape, not a forecast.
