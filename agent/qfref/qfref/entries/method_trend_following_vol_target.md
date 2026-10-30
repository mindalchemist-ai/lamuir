# Method: trend-following signals with volatility-targeted sizing, decided at each day's close

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input, setting or convention, follow the task description.

When to use: the task instructions build moving-average crossover signals, size positions to a volatility target (EWMA
or GARCH volatility, optionally scaled by a volatility regime) and trade the next day.

## 1. Dates and signals

1. Index every table by the trading dates (a datetime index built from the date column), never by a $0, \dots, n-1$ position.
2. Compute the fast and slow EMAs of the prices with the initialization the task's wording selects (table below):
   1. `sma_seed`: the first $\mathrm{span} - 1$ values undefined, the value at position $\mathrm{span} - 1$ set to the mean of the first $\mathrm{span}$ prices, then the recursion `ewm(span=..., adjust=False)` from there.
   2. `first_price`: `ewm(span=..., adjust=False)` from the first price.
   3. `weighted`: `ewm(span=..., adjust=True)`.

| EMA initialization | What it does | Task wording that selects it |
|---|---|---|
| `sma_seed` | first value = average of the opening `span` prices, recursion from there | "seeded with / started from the simple moving average" |
| `first_price` | recursion from the first price (`adjust=False`) | "recursive EMA from the first observation", or a stated recursion with no seed |
| `weighted` | pandas `adjust=True`, normalized weights over all past prices | "exponentially weighted average" written as a weighted sum, or pandas defaults |

The three differ mainly in the opening rows; after a few spans they converge.

- Crossover signals compare moving averages of price levels (or of the series the task names); moving averages of returns hover around zero and their crossings carry no trend information. Returns feed the volatility estimate, prices feed the signal:

Check: every EMA value is positive and on the scale of the prices (far larger than the typical absolute return); otherwise the EMAs were taken over returns.

- Compute each EMA on the full price history; mask the warm-up rows (arch conventions entry, section 6).
- Put every day-t input on the return row of the same date by label (`signal.loc[returns.index]`); do not cut a
  price-dated table by position and relabel the rows; relabeling by position moves every row by one day.

## 2. Volatility for day t's sizing

- EWMA: annualize before dividing an annual target, `ewma_vol = np.sqrt(periods_per_year * ewma_var)`, with the periods per year the task uses (252 trading days is common; 365 for markets that trade every day).
- GARCH: a strategy decided at day t's close sizes with the volatility known once day t has closed, `sigma_close` (arch
  conventions entry, section 2, use case 2), one series per asset. Where the task instructions write the day-t GARCH
  volatility as `sigma[t]` or `conditional_volatility[t]` next to day-t signals, read the day-t GARCH volatility as `sigma_close`.

For each asset, on its daily decimal returns:

1. Fit a zero-mean GARCH(1,1) with normal errors on percent returns: `arch.arch_model(100 * r, vol="GARCH", p=1, o=0, q=1, mean="Zero", dist="normal", rescale=False).fit(disp="off")`.
2. The volatility known at day $t$'s close is the one-step-ahead forecast made at $t$: the square root of `forecast(horizon=1, start=0, align="origin").variance["h.1"]`, divided by 100, on row $t$. Do not use `conditional_volatility`, which is one day earlier.
3. Long-run variance in decimal daily units: $(\omega/100^2)/(1 - \alpha - \beta)$; its value should be far below $10^{-2}$, otherwise it is still in percent units.
4. Align the volatility series to the return dates by label.
- A composite across assets is built from the per-asset `sigma_close` series in the units the task instructions define; when the
  composite is annualized, the percentile thresholds and regime labels of the composite use the annualized composite.
- One long-run figure across assets has three readings: the arithmetic mean of the per-asset long-run variances, the square of the mean long-run volatility, or a weighted mean. Use the one the task describes; the code above computes the first.

## 3. Weights and returns

- Day t's weight uses day t's signal and volatility; the whole weight row is lagged once: `port = (weights.shift(1) * r).sum(axis=1)`,
  with no position (zero return) before the first weight.
