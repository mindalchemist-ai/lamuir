# arch: conventions and calls, as code

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input, setting or convention, follow the task description.

How to use this entry:
- Use a line here only where the task instructions give no formula for that quantity; a formula in the task
  instructions replaces the line here.
- `r`: daily decimal returns (Series).
- `res`: an arch fit on `100 * r`.
- `B`: periods per year for annualizing, a task parameter (252 trading days is common; 260 and 365 also occur).
- The official description of each function is attached separately.

## 1. Fit a GARCH(1,1)

There are two cases, set by whether the task instructions fix the fitting units.

### Case 1 (default): the task instructions do not fix the fitting units

Fit percentage returns, `100 * r`, for numerical stability; then divide every output back to the units of `r`.

Case 1 (fit percent returns): fit `arch.arch_model(100 * r, vol="GARCH", p=1, o=0, q=1, mean="Zero", dist="normal", rescale=False).fit(disp="off")`, then convert back: divide $\omega$ and every variance by $100^2$, every volatility and mean by 100; $\alpha$ and $\beta$ are unchanged. Check: $\omega < 10^{-3}$ and the mean conditional volatility below 0.1, otherwise the values are still in percent units.

### Case 2: the task instructions fix the fitting units

For example "fit the raw returns, do not rescale": fit `r` as stated. Every output is already in the units of `r`;
no conversion.

Case 2 (fit raw decimal returns): the same call on $r$, with every parameter and volatility already in decimal units.

### Check either fit: did the optimizer move?

A fit can report `convergence_flag == 0` and still return the starting values unchanged; a case 2 fit on raw decimal
returns often does.

Check that the fit moved: compare the fitted volatility parameters with `res.model.volatility.starting_values` evaluated on the residuals; equal values mean the optimizer did not move.

Sections 2 and 3 write the case 1 conversions (`/ 100`, `/ 100**2`); in case 2 leave out the `/ 100` and `/ 100**2` conversions.

## 2. Pick the volatility the task instructions mean

There are two use cases. Match the task instructions to use case 1 or use case 2, then use the call listed under the matching use case.

### Use case 1: the volatility of a day inside the sample: `res.conditional_volatility`

Task instructions that ask for the "conditional volatility" of an in-sample day, or of the final in-sample day.
The value on day t is the volatility of day t's return, forecast on day t-1, so the value on day t does not use day t's return.

1. `conditional_volatility` on day $t$ is the volatility of $r_t$, forecast on day $t-1$ (divide by 100 in case 1).
2. Its last value is the volatility of the final in-sample day.

### Use case 2: a volatility forecast from a chosen day forward: `res.forecast(...)`

Task instructions that ask for a one-step-ahead forecast, the volatility of the next day, a volatility known at a
day's close, or a variance over the next H days. A forecast made on an origin day uses every return up to and
including that day.

1. Volatility of the first day after the sample: the square root of the last row of `forecast(horizon=1).variance`, divided by 100 in case 1.
2. Volatility known once day $t$ has closed (for a decision at $t$'s close): the square root of `forecast(horizon=1, start=0, align="origin").variance["h.1"]` on row $t$.
3. Variance of the next $H$ days from the last day: the sum of the last row of `forecast(horizon=H).variance`, divided by $100^2$ in case 1.

Notes:
- `sigma_close` on day t equals `sigma_for_t` on day t+1: the same number, labeled one day apart.
- When the task instructions mention both the final observation and a one-step-ahead forecast, the words
  "one-step-ahead forecast" decide: use case 2, `sigma_next`.
- A rolling estimate refits on each window `r.iloc[end - W:end]` for `end in range(W, len(r) + 1)` and uses the
  `sigma_next` of each window's fit.

## 3. Long-run variance and annualized values

Turns the daily parameters and volatilities into the long-run and annual figures that task instructions usually ask for.

1. Stationarity: $\alpha + \beta < 1$.
2. Long-run daily variance: $\omega/(1 - \alpha - \beta)$ in decimal units; annualized long-run volatility $\sqrt{B \cdot \omega/(1-\alpha-\beta)}$ with $B$ periods per year.
3. Annualize daily figures: volatility times $\sqrt{B}$, variance times $B$, mean log return times $B$.
4. Check: the annualized long-run and average volatilities lie between about 0.03 and 1.5.
- "Annualized" applies to every quantity labeled annualized: composite, portfolio and long-run volatilities alike.

## 4. Standardised residuals

The unit-free shocks used by EVT on GARCH residuals, filtered simulation and correlation models.

Standardized residuals `std_resid` are the residual over the same day's conditional volatility, so the percent scaling cancels; their standard deviation is within about 0.2 of 1.

## 5. VaR and ES as positive losses

Parametric normal VaR and ES at a tail probability, reported as positive numbers.

Normal VaR and ES from a conditional mean $\mu$ and volatility $\sigma$, with the tail probability $\tau = 1 - \text{level}$ ("1% VaR" and "99% VaR" both mean $\tau = 0.01$) and $z_\tau = \Phi^{-1}(\tau)$:

1. $\mathrm{VaR} = -(\mu + \sigma z_\tau)$, with $\mu$ the conditional mean, or 0 for a zero-mean VaR (common at short horizons); use the task's choice and state it.
2. $\mathrm{ES} = -\mu + \sigma\,\phi(z_\tau)/\tau$, dividing by the tail probability, not by the confidence level.
3. Check: $\mathrm{ES} > \mathrm{VaR} > 0$.
- If the task instructions define their own ES or VaR formula, that formula replaces the `var_t` and `es_t` lines; otherwise these are the standard normal VaR and ES.

## 6. Warm-up of indicator signals

Rows where an indicator does not exist yet must carry no position.

Crossover signal: +1 where the fast average is above the slow one and -1 otherwise, but only where both averages exist; keep the warm-up rows undefined, since a comparison with a missing value would otherwise produce a full short.

## 7. Two consistency rules

- Every later step uses the return series the task instructions defined first (log or simple); do not rebuild returns from prices with
  the other definition, backtests included.
- `StationaryBootstrap` draws random numbers in the internal order of `StationaryBootstrap`; when the task instructions prescribe the random
  draws, write the prescribed draws directly instead of using `StationaryBootstrap`.

Sources: Bollerslev (1986) and Engle (2001) for GARCH variance; McNeil, Frey and Embrechts, Quantitative Risk
Management (VaR, ES, standardised residuals); arch API reference.
