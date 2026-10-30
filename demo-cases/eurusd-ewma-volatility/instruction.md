# How do EWMA (λ = 0.94) and 60-day rolling volatility estimates of EUR/USD compare over 2015–2025?

## Data

`/app/data/ecb_eurusd_2015_2025.csv` is the ECB Data Portal's CSV export of the daily euro reference rate against the U.S. dollar, from 2015-01-02 to 2025-12-31, unchanged. `TIME_PERIOD` is the date and `OBS_VALUE` the rate, in U.S. dollars per 1 euro. Days without a rate are simply absent.

## Task

Sort by date; call the rows days $0..n-1$ and the rates $P_t$. Do not fill missing days. Daily log returns are $r_t = \ln(P_t/P_{t-1})$ for $t = 1..n-1$. Annualize with 252 observations per year and report percent.

1. **60-day rolling volatility**, for $t \ge 60$: $\sigma^{roll}_t = 100\sqrt{252\cdot \text{var}(r_{t-59},\dots,r_t)}$, with sample variance (ddof = 1).
2. **EWMA volatility** (RiskMetrics, $\lambda = 0.94$):
   - start at $t = 60$ with $v_{60} = \frac{1}{60}\sum_{i=1}^{60} r_i^2$;
   - for $t > 60$, $v_t = \lambda v_{t-1} + (1-\lambda)\, r_t^2$;
   - $\sigma^{ewma}_t = 100\sqrt{252\, v_t}$.
3. Compare the two series on days $t \ge 60$.

## Output

Write to `/app/output/`:

- `analysis.csv`, one row per day $t \ge 60$, columns `date,rolling_vol_pct,ewma_vol_pct`, with ISO dates.
- `results.json` with these keys:
  - `first_date`, `last_date` and `n_days` (integer) of the rows in `analysis.csv`, i.e. of days $t \ge 60$ only;
  - `mean_rolling_vol_pct` and `mean_ewma_vol_pct`;
  - `max_rolling_vol_pct` and `max_rolling_vol_date`;
  - `max_ewma_vol_pct` and `max_ewma_vol_date` (the first date if tied);
  - `days_ewma_above_rolling` (integer).
  
  Values are unrounded.
- `chart.png`: both series over time.
- `explanation.md`: start with one or two sentences that answer the question in the title directly, using the numbers you computed. Then give a short plain-English explanation of how the two estimates respond to large moves in this sample, and how $\lambda$ and the window length affect their responses. It should state that neither is the "true" volatility.
