# What was the 2025 percent change of the euro, pound, yen and Swiss franc against the U.S. dollar?

## Data

`/app/data/ecb_reference_rates_2025.csv` is the ECB Data Portal's CSV export of the daily euro foreign exchange reference rates for USD, GBP, JPY and CHF, for 2025, unchanged. It is in long format: one row per currency and date. `CURRENCY` is the currency code, `TIME_PERIOD` the date, and `OBS_VALUE` the rate. **Every rate is quoted as units of that currency per 1 EUR**; for example, USD 1.03 means 1 EUR = 1.03 USD.

## Task

1. Use only the dates on which all four currencies have a rate; do not fill missing dates.
2. On each date, compute the U.S. dollar value of one unit of each currency:
   - $\text{EUR} = \text{USD}$, the ECB rate itself;
   - $\text{GBP} = \text{USD}/\text{GBP}$, $\text{JPY} = \text{USD}/\text{JPY}$ and $\text{CHF} = \text{USD}/\text{CHF}$, each the ratio of the two ECB rates.
   
   Also compute the cross rate $\text{GBPJPY} = \text{JPY}/\text{GBP}$, in yen per 1 GBP.
3. The change over the year is $100\,(\text{last}/\text{first} - 1)$, in percent, using the first and last dates. A positive value means the currency gained against the dollar.
4. Check triangle consistency on every date: $\text{GBP\_USD}/\text{JPY\_USD}$ must equal $\text{GBPJPY}$.

## Output

Write to `/app/output/`:

- `analysis.csv`, one row per date used, in ascending order, columns `date,EUR_USD,GBP_USD,JPY_USD,CHF_USD,GBP_JPY`. Each `X_USD` column is the USD value of 1 unit of X.
- `results.json` with these keys:
  - `first_date`, `last_date` and `n_days`;
  - `change_pct`: an object with keys `EUR`, `GBP`, `JPY` and `CHF`;
  - `strongest` and `weakest` (currency codes);
  - `gbp_jpy_change_pct`;
  - `max_triangle_error`.
  
  Values are unrounded.
- `chart.png`: the cumulative percent change of the four currencies against the dollar over the year.
- `explanation.md`: start with one or two sentences that answer the question in the title directly, using the numbers you computed. Then give a short plain-English explanation of the moves, stating that the ECB rates are reference rates fixed once a day, not trading prices.
