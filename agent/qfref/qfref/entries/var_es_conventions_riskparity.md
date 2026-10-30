# VaR and ES conventions: loss sign, quantile rules, tail means, weights, horizons, windows and simulation

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input, setting or convention, follow the task description.

Use this note for value-at-risk (VaR), expected shortfall (ES, CVaR) and related backtests on return series, simulated wealth paths or simulated credit losses. Most steps below have more than one standard reading. Each skeleton takes the choice as an argument: read its value from the task instructions, and when the instructions leave it open, pick one, write the choice in a comment, and use the same choice in every output. The skeletons assume `import numpy as np`, `import pandas as pd` and `from scipy import stats, special`.

## Decisions to make before coding

Each line below is one choice this note explains in its section; settle each one from the task text and write it in a comment.

- Observation counts (section 9): a count of valid observations is taken after cleaning and before any estimation window is cut; the window length is a different number.
- Which rows an estimate for day t uses (section 16): an estimate that labels day t or sets the weights earning day t's return uses only rows before day t. pandas `.rolling(W)` at row t includes row t, so such an estimate is `.rolling(W).stat().shift(1)` (or a loop over rows t - W to t - 1), and a series of length n then has n - W estimates, not n - W + 1.
- Rebalances (section 16): count the rebalances actually executed (an estimate exists and a later day holds the weights), not calendar month ends.
- Evaluated sample (section 16): a backtest driven by rolling estimates starts on the first day that has an estimate; warm-up rows enter neither the returns nor the metrics.
- Holdings before the first rebalance (section 16): hold an initial portfolio, hold cash, or start at the first rebalance. Under a fixed rebalance schedule, setting estimate-based weights before the first scheduled date is an extra, unscheduled rebalance. Filling the weights with 0 is the cash reading; it assumes an account the task may not describe. An inverse-volatility rule with no estimate yet has nothing to tilt the weights, so its uninformed portfolio is equal weights 1/n; a backtest of a strategy over the whole sample, with no cash account mentioned, holds that portfolio from its first day. Write the reading you use in a comment.
- Account for uninvested wealth and leverage (sections 11 and 15): the weighted sum unless the task describes a cash account; leverage without a qualifier is gross. An output named with "var" beside a VaR limit or VaR scale factor is value-at-risk, not the variance f' Sigma f.
- Standard deviations of reported series (section 16 summaries, Sharpe denominators, volatilities): use the ddof the task states; when the task states it for one series and not another, keep the same ddof throughout. `np.std` defaults to ddof=0 and pandas `.std()` to ddof=1.
- VaR and ES rules (sections 2 and 3): quantile rule and tail mean; a risk figure over a trailing window is one number from that window, not an average of rolling figures.

## 1. Loss sign and confidence level

A loss is the negative of a return or P&L, so the risky side is the upper tail of the loss. A confidence level such as 95% corresponds to the tail probability 1 - level. Some texts call the confidence level alpha, others call the tail probability alpha; decide from the numbers the task lists (0.95 and 0.99 are confidence levels, 0.05 and 0.01 are tail probabilities).

Losses are the negated returns, $L = -r$, keeping only finite values.

## 2. Empirical VaR: which quantile rule

With n scenarios the empirical quantile is not unique. "kth_worst" takes the k-th largest loss with k = ceil(n * tail), which is the classical historical-simulation order statistic and equals -np.quantile(returns, tail, method="inverted_cdf"). In floating point 1 - 0.95 is 0.05000000000000004, so when n * tail is a whole number a step rule can move one observation further; the skeleton rounds the tail probability first. A NumPy method name ("linear" is the NumPy default and interpolates between neighbouring order statistics; "lower", "higher", "nearest", "inverted_cdf" pick one observed value) applies np.quantile to the losses at the confidence level. "linear" is symmetric (the loss quantile at the level is minus the return quantile at the tail); the step rules are not, so np.quantile(loss, level, method="inverted_cdf") is the (k+1)-th worst loss when n * tail is a whole number k.

## 3. ES: which tail mean

Three tail means are in use. "strict" is E[L | L > VaR], the mean of losses above VaR; it is empty, hence undefined, when VaR is the largest loss. "inclusive" is E[L | L >= VaR], which always contains the VaR scenario. "tail_mean" averages exactly the worst tail * n outcomes and takes only the needed fraction of the boundary scenario (Acerbi and Tasche 2002); it equals min over c of c + mean(max(L - c, 0)) / tail. For continuous data the three nearly agree. For losses on a grid (a count of defaults times a fixed loss, rounded P&L) many scenarios sit exactly at VaR and the three can differ by a large amount. Wording such as "losses exceeding VaR" or "greater than VaR" reads as strict; "at or beyond VaR" or "not smaller than VaR" reads as inclusive; "integrated quantile", "average VaR over the tail" or "coherent ES" reads as tail_mean. "Conditional expected loss beyond VaR" is a conditional mean (strict or inclusive) and does not separate those two; state which one you use.

Empirical VaR and ES at level $c$ with tail $\tau = 1 - c$ (rounded to remove floating-point noise), with the losses sorted worst first:

1. VaR by the $k$-th worst loss: $k = \max(\lceil n\tau \rceil, 1)$; or by `numpy.quantile(L, c, method=...)` with the method the task names.
2. ES, strict: the mean of losses strictly above the VaR (undefined if there are none).
3. ES, inclusive: the mean of losses at or above the VaR.
4. ES, integrated tail mean: with $m = n\tau$ and $j = \lfloor m \rfloor$, $\left(\sum_{i \le j} L_{(i)} + (m - j)L_{(j+1)}\right)/m$.
5. Check: ES is not below VaR.

## 4. Probability-weighted (age-weighted) VaR and ES

Age weighting gives scenario i the probability decay**age_i / sum(decay**age), with age 0 for the newest observation. The weights stay attached to their scenarios when the losses are sorted. The tail is the worst losses, so sort the losses from the worst and accumulate weight from there until the tail probability is reached; sorting returns in ascending order and averaging the entries after the quantile position averages the gains instead. The rule below is the weighted form of "kth_worst" (equal weights give the same VaR as section 2) and equals -np.quantile(returns, tail, weights=w, method="inverted_cdf") with the rounded tail, except when the cumulative weight lands exactly on the tail probability, where summation rounding decides; the skeleton uses a small tolerance there.

Exponentially weighted historical VaR and ES with decay $\lambda$: weight the most recent return 1, the one before $\lambda$, and so on ($w_t \propto \lambda^{n-t}$), normalized to sum 1. Sort the losses worst first with their weights; the VaR is the first loss at which the cumulative weight reaches the tail $\tau$. Two ES readings: the weighted tail mean $\left(\sum_{i < k} p_i L_i + (\tau - \sum_{i<k} p_i) L_k\right)/\tau$, or the weighted mean of the losses at or above the VaR. Both are at least the VaR.

When a multi-period scenario is weighted, its age is counted from the scenario's last day.

## 5. Parametric VaR and ES

Normal: VaR = -mu + sd * z and ES = -mu + sd * pdf(z) / tail, with z = norm.ppf(level). "Absolute" VaR keeps the mean; "relative" or "zero-mean" VaR sets mu = 0. The standard deviation divisor is a separate choice: ddof=1 is the unbiased sample variance, ddof=0 the maximum-likelihood one.

Student-t: scipy.stats.t.fit returns (df, loc, scale) by maximum likelihood with all three free. The scale is not the standard deviation: sd = scale * sqrt(df / (df - 2)) for df > 2. The ES formula needs df > 1; check df after fitting. Fixed parameters are passed as floc, fscale or f0 (df).

1. Normal VaR and ES: with $\mu$ the sample mean (or 0 when the task says zero mean), $s$ the standard deviation with the stated divisor and $z = \Phi^{-1}(c)$: $\mathrm{VaR} = -\mu + s z$ and $\mathrm{ES} = -\mu + s\,\phi(z)/(1-c)$.
2. Student t VaR and ES: fit $(\nu, \mathrm{loc}, \mathrm{scale})$ with `scipy.stats.t.fit` (with any fixed parameters the task states); ES needs $\nu > 1$. With $q = t_\nu^{-1}(c)$ and $m$ the location (or 0): $\mathrm{VaR} = -m + \mathrm{scale}\cdot q$ and $\mathrm{ES} = -m + \mathrm{scale}\cdot f_\nu(q)\,\frac{\nu + q^2}{(\nu - 1)(1 - c)}$, where $f_\nu$ is the t density.

## 6. EWMA covariance

The recursion C_t = lam * C_(t-1) + (1 - lam) * x_t x_t' needs a starting matrix: the first observation's outer product, a sample covariance of the first m rows, or zero. It also needs a mean convention: raw returns (zero mean, the RiskMetrics form) or demeaned returns. The matrix after the last observation is the forecast for the next period, which is what "current" or "as of the last date" usually means. Annualize a volatility with the square root of the periods per year that the data frequency implies (for example 252 trading days, 52 weeks or 12 months); the frequency comes from the data, not from a fixed number.

EWMA covariance with decay $\lambda$ over return vectors $x_t$ (demeaned first when the task says so): $C_t = \lambda C_{t-1} + (1-\lambda)x_t x_t^{\top}$. The starting matrix is a choice that changes the numbers; use the one the task states: the first outer product $x_1 x_1^{\top}$ (recursion from the second observation), a zero matrix, or the sample covariance of the first $k$ observations (divisor $k-1$, recursion from observation $k+1$). Annualized portfolio volatility: $\sqrt{w^{\top} C w \cdot P}$ with $P$ periods per year.

For one series, seed "first_outer" with zero mean equals pd.Series(x**2).ewm(alpha=1 - lam, adjust=False).mean().

## 7. Multi-period horizons

Square-root-of-time scaling multiplies a one-period VaR or ES by sqrt(h); it is exact for independent normal returns with zero mean. With a mean, the h-period normal VaR is -h * mu + sqrt(h) * sd * z. For simulation-type methods an h-period scenario is the sum of h consecutive log returns, or the compounded product of h simple returns. Overlapping windows step one period at a time (n - h + 1 scenarios, strongly dependent); non-overlapping windows step h periods (about n / h scenarios) and need an anchor, either the first or the last observation.

Horizon returns over $h$ periods: the rolling sum of log returns, or for simple returns $\exp(\sum \ln(1 + r)) - 1$ over the window. Overlapping windows use every window; non-overlapping windows take every $h$-th one, anchored at the first window or at the last one as the task says.

## 8. Backtesting a VaR forecast

The forecast for day t uses data through day t - 1 only. An expanding window uses all earlier days; a rolling window uses the last W. A stated minimum number of observations sets the first test day. An exception is a loss above the forecast ("exceeds"); a loss equal to it counts only under an "at or above" wording. The Kupiec proportion-of-failures statistic is a likelihood ratio with one degree of freedom; scipy.special.xlogy keeps the log-likelihood finite when there are no exceptions or only exceptions.

Rolling or expanding VaR backtest at level $c$:

1. For each day $t$ from the first allowed index, the history is all returns before $t$ (expanding) or the last $W$ before $t$ (rolling).
2. Compute that history's VaR with the chosen quantile rule; the day is an exceedance when the loss $-r_t$ exceeds it (or reaches it, when the task says so).
3. With $T$ test days, $x$ exceedances and $p = 1 - c$, the Kupiec statistic is $-2\left[\ell(p) - \ell(x/T)\right]$ where $\ell(q) = x\ln q + (T - x)\ln(1 - q)$ (with $0\ln 0 = 0$, as `scipy.special.xlogy`); its p-value is the chi-square survival function with one degree of freedom. Report $T$, $x$, $x/T$ and the p-value.

## 9. Cleaning a data feed and counting observations

Invalid entries in a return table include missing values, text in numeric columns, infinities, unparseable dates and repeated dates. A return is a change, not a level, so forward-filling a missing return repeats an earlier day's move that did not happen; filling with zero asserts that nothing moved. Dropping each row with any invalid value (listwise) keeps the assets aligned on the same dates. A large but finite return is a data point, not an anomaly, unless the task gives a rule for it. A count of valid observations is the number of rows that survive cleaning; the number of rows inside an estimation window is a different count. An estimation window of the latest N rows is cut from the cleaned table, and an unset N means the full cleaned sample.

Cleaning a return table:

1. Parse the date column (unparseable dates become missing) and convert the value columns to numbers, turning non-numeric and infinite values into missing.
2. Drop rows without a date, drop duplicate dates keeping the record the task says (first or last), sort by date and index by it.
3. Missing values as the task says: drop the whole row, or fill with zero.
4. Report the rows read and the valid rows.
5. "The most recent $n$ observations" are the last $n$ valid rows after cleaning.

## 10. Rolling estimates, rebalance dates and the evaluated sample

A rolling estimate dated t uses either rows t - W + 1 through t (it includes day t) or rows t - W through t - 1 (only earlier days). A quantity that sets the holdings earning day t's return must not contain day t; with the first form, apply it from day t + 1. pandas rolling uses min_periods equal to the window by default; min_periods=1 produces estimates from one or two rows. "Trailing N returns" means the last N values of the series, series.iloc[-N:], not the full history.

A month-end rebalance date is the latest date of that month present in the data. When the data stop before the month ends, the final row is not that month's last trading day.

Before the first rebalance there is no target portfolio. The evaluated sample can start at the first rebalance, hold no position until then, or hold a stated initial portfolio; the choice changes volatility, Sharpe ratio and drawdown. Days before the first available estimate are warm-up days.

Rolling windows of length $W$ for row $t$: rows $t-W+1$ to $t$ when the current row is included, or rows $t-W$ to $t-1$ when it is not; skip rows without a full window.

For a portfolio whose weights are set from rolling estimates on rebalance dates, use the rolling-estimate rebalance workflow (section 16 says when) for the rebalance list, the holdings before the first rebalance and the day the new weights start earning.

## 11. Portfolio return, leverage and scaling to a risk limit

With fractions w of wealth in risky assets with simple returns R, three account models are in use. "weighted_sum" is R @ w: the portfolio return is the weighted sum of the asset returns, and the remainder 1 - sum(w) earns nothing. "financed" is rf + (R - rf) @ w: the remainder is lent or borrowed at the cash rate. "excess_only" is (R - rf) @ w. When the task describes no cash account or financing rate for the remainder, the weighted sum is the literal reading and a cash leg is an added assumption; state it if you add one. The same period returns then drive wealth, Sharpe ratio and drawdown.

Gross exposure (leverage) is sum(|w|); net exposure is sum(w). "Leverage" without a qualifier is the gross figure; a signed sum is called net exposure or net leverage. A per-period cash rate from an annual rate is r / periods_per_year under simple division and (1 + r) ** (1 / periods_per_year) - 1 under compounding.

To meet a risk limit along a fixed direction, "comply with", "cap at" or "not exceed" reads as c = min(1, limit / risk), which scales down only; "scale to" or "target" reads as c = limit / risk.

1. Portfolio return per period from asset returns $R$, weights $w$ and the cash rate $r_f$ per period, by the task's accounting: weighted sum $Rw$; financed (the remainder earns the cash rate) $r_f + (R - r_f)w$; or excess $(R - r_f)w$.
2. Exposure: gross $\sum|w_i|$ and net $\sum w_i$.
3. Risk scaling to a limit: a cap scales by $\min(1, \text{limit}/\text{risk})$; a target scales by $\text{limit}/\text{risk}$.

## 12. Random streams and losses on a grid

A seed alone does not fix the random numbers. np.random.seed(s) with np.random.* functions uses the legacy MT19937 RandomState; np.random.default_rng(s) uses PCG64. They give different streams for the same seed. The draw order also matters: all factor draws then all idiosyncratic draws, the reverse, or one simulation at a time (factor, then that simulation's names). For losses on a grid, a quantile can move by one grid step between streams when the in-sample CDF at a grid point is close to the confidence level; print that CDF value next to the reported quantile.

1. The same seed gives different numbers in the legacy generator (`numpy.random.seed` with `numpy.random.standard_normal`) and in `numpy.random.default_rng(seed)`; use the one the task names.
2. The order of the factor draws $M$ and the name draws $E$ changes every scenario; use the task's order: factor first, names first, or one block of $n_{\mathrm{names}} + 1$ columns per scenario with the factor in the first column.
3. Report with the VaR the empirical CDF at the VaR and at the next lower loss value.

## 13. Group breakdowns of a portfolio loss

For groups that partition the portfolio, two "mean loss" figures exist per group: the mean over scenarios of the group's total loss, and the mean loss of a single member. They differ by the group size. Group totals add up to the portfolio mean loss; per-member means do not. Wording such as "per name", "per bond" or "average member" points to the per-member figure; a table presented as the breakdown of a portfolio figure points to the group total. When the wording fits both, write the choice in a comment and check the sum.

Loss by group, two readings: the group total (the sum of its members' losses per scenario, averaged over scenarios) or the per-member mean; the total equals the number of members times the per-member mean, and the group totals add up to the portfolio mean loss.

## 14. After a correction, rewrite every file that used it

When a function is fixed after its results were written, the files written earlier still hold the old values. Recompute and rewrite every output that used it, read the files back, and check the invariants that hold under every convention above: ES >= VaR for the same level and method, VaR at a higher level >= VaR at a lower level for the same method, and the expected number of rows and labels.

## 15. Kelly sizing with a VaR limit

Use this section when the task instructions estimate Kelly fractions from sample means and covariances, scale the fractions to a
VaR limit, and compare sizing schemes on simulated wealth paths. Three steps below have more than one standard reading;
each is a named argument, with what each option means and which wording selects it. Read the value from the task text,
write the choice in a comment, and use the same choice in every output.

### Terms used in such tasks

- Sample statistics: the per-asset mean, the excess mean (mean minus the per-period risk-free rate) and the covariance matrix, all computed on the estimation window only, with the ddof the task states.
- Bankroll: the capital being sized; each simulated path starts at the initial capital and compounds its own period returns.
- Sizing schemes are fixed fraction vectors applied every period:
  - full Kelly: the Kelly fractions f;
  - fractional Kelly: k * f, with k read from the wording ("half Kelly" k = 0.5, "quarter Kelly" k = 0.25, "20% Kelly" or "0.2 Kelly" k = 0.2, "double Kelly" k = 2). Under the quadratic growth approximation the expected log growth is about k * (2 - k) times the full-Kelly growth, while volatility and VaR scale with k; above k = 1 growth falls;
  - risk-budgeted (VaR-constrained) Kelly: c * f, with c computed from the VaR limit as below; the direction of f is kept;
  - equal weight: 1/n in each of the n assets, fully invested.
  The schemes differ only in their fraction vectors, so the same simulated draws serve every scheme.
- Performance and risk metrics over simulated paths: compute each metric per path from that scheme's period returns, then summarise across paths as the task states. The mean and the median of terminal wealth across paths are different numbers (the mean exceeds the median for compounded wealth); when the task asks for both, compute both, e.g. `np.mean(W[:, -1])` and `np.median(W[:, -1])`. A drawdown is computed per path and then summarised (for example its median).

### Kelly fractions and leverage

Kelly fractions from cleaned returns:

1. Clean the table (dates parsed, duplicates and missing values handled as the task says); the count of valid observations is every row that survives cleaning.
2. The estimation window is cut from the cleaned table (the most recent $n$ rows when the task gives $n$); its length is not the count of valid observations.
3. Cash rate per period: the annual rate divided by the periods per year, or the compounded form when the task says so.
4. Excess mean $\mu - r_f$ and the sample covariance $\Sigma$ (divisor $n-1$) over the window.
5. Full Kelly fractions solve $\Sigma f = \mu - r_f$; $|f|$ above 1 is leverage. Gross exposure $\sum|f_i|$, net exposure $\sum f_i$.

- Leverage measures the size of the positions whatever their direction: a short position borrows as much as a long one
  of the same size, so "leverage" or "total leverage" without a qualifier is the gross figure, sum(|f|). The signed sum
  sum(f) is called net exposure (or net leverage) and can be near zero for a heavily levered long-short book.

### VaR of the fractions and the limit

VaR cap on the Kelly fractions with $z = \Phi^{-1}(\text{level})$ and $\sigma_p = \sqrt{f^{\top}\Sigma f}$:

1. Relative (zero-mean) VaR: $z\sigma_p$; absolute (mean-adjusted) VaR: $z\sigma_p - f^{\top}\mu$.
2. "Comply with" or "not exceed" a maximum VaR means scale down only: multiply $f$ by $\min(1, \text{max VaR}/\text{VaR})$, using the VaR form the task names.

- Two parametric normal VaRs are in use (Jorion, Value at Risk, ch. 5). The relative VaR z * sigma measures the loss
  below the expected outcome; the absolute VaR subtracts the expected return. Over one day the mean is small and is
  estimated with a large error, so daily risk limits and "parametric VaR" without a stated mean term are usually the
  relative form; the absolute form is meant when the task writes the mean into the VaR formula or speaks of the loss
  relative to zero or to initial value.
- "Scale to" or "target" the limit reads as scale = max_var / var_chosen, which can also lever up.

### Simulation of wealth paths

One set of draws is shared by every sizing scheme, so the schemes differ only in their weights.

Simulation of the schemes: draw multivariate normal simple asset returns with the window's mean and covariance for every path and day from the generator and seed the task names. For each scheme's weights, the period return is $Rw$ when the rest of the wealth earns nothing, or $r_f + (R - r_f)w$ when the rest is lent or borrowed at the cash rate. Wealth compounds from the starting wealth; the annualized Sharpe ratio is $\sqrt{P}\,\bar{x}/s_x$ (divisor $n-1$); the maximum drawdown per path is $\max_t(1 - W_t/\max_{s\le t}W_s)$, a positive magnitude.

- The account model says what the wealth not held in the risky fractions earns. When the task gives the portfolio
  return as fractions times asset returns, or describes no cash account or financing rate for the remainder, the
  weighted sum is the literal reading and a cash leg is an added assumption. "Financed" is meant when the task says
  the remainder earns, or the borrowing costs, the risk-free rate.
- A risk-free rate in the task can play three roles: forming the excess mean for the Kelly fractions, a deduction in a
  Sharpe ratio, or the return on a cash account. Only the third creates a cash leg in the simulated returns. A rate
  that is used to compute excess means, or that the task says not to subtract from the Sharpe numerator, does not by
  itself describe a cash account.
- Under the weighted sum, scaling every fraction by the same c > 0 leaves the Sharpe ratio unchanged; under the financed
  model it does not. Use the same period returns for wealth, Sharpe ratio and drawdown.
- Kelly growth-rate derivations (for example the qfref entry on Kelly growth and risk scaling) are written for the financed account, so their period return reads rf + f'(R - rf). That is an assumption of the derivation, not a description of the task's account: the Kelly fractions are the same under either reading, and the account for the simulated wealth is chosen from the task text as described above, not from the reference.
- An instruction not to subtract the risk-free rate from a Sharpe numerator fixes the Sharpe formula, mean(x) / std(x), under either account; it is not evidence of a cash leg. A rule that such a Sharpe ratio "includes the cash leg" applies when the account already has one and does not create one. Under the weighted sum, x = R @ w and the Sharpe ratio is the same for every positive multiple of w; under the financed account it is not.
- An output named with "var" beside a VaR limit or a VaR scale factor is value-at-risk (z * sigma_p or the mean-adjusted form), not the variance f' Sigma f.

## 16. Rebalanced portfolios driven by rolling estimates (regimes, inverse volatility)

Use this section when a rolling-window estimate (correlation eigenvalues, a regime label, volatilities) sets portfolio weights on rebalance dates and the portfolio is then backtested. The table below says which pattern fits the task; the rolling-estimate rebalance workflow entry holds the code.

Which backtest pattern applies depends on how the task schedules trades. The references describe more than one; match the task to a row and use that row's settings:

| Scenario in the task text | Rebalance dates | Book before the first rebalance | When new weights earn | Where the code is |
|---|---|---|---|---|
| Weights come from rolling estimates (regime, volatility, correlation) and the task fixes a calendar such as month ends, with no stated start date | the scheduled dates that have an estimate, excluding the last data row | a portfolio that needs no estimate (equal weights) or cash, chosen as in "Holdings before the first rebalance" below | from the day after the rebalance date | the rolling-estimate rebalance workflow |
| A long-short or signal book with a stated trading start, rebalanced at each later month start | the stated start row, then the first trading day of each later month | flat (no position) before the stated start, because the task names when trading begins | per the task; the backtest-accounting reference gives the lag rules | the qfref backtest-accounting entry |
| The task says the portfolio is allocated at the start of the backtest and then rebalanced on a calendar | the start, then the calendar dates | not applicable | from the day after each rebalance | that workflow with before_first = "first_estimate" |
| The task says the evaluation begins at the first rebalance | the calendar dates | rows before it are not evaluated | from the day after each rebalance | that workflow with before_first = "start_at_first" |

Reported statistics of a series (for example the standard deviation of an indicator across days) use the ddof the task states elsewhere, applied consistently.

The code for these steps, with a check after each step, is the qfref entry `rolling_estimate_rebalance_workflow`; use it rather than rebuilding the backtest from month ends.

- The evaluated sample is the days that have an estimate (len(r) - W of them). Days before the first estimate are warm-up rows: they have no regime and no weights, and they enter neither the returns nor the metrics.
- A rebalance is a date on which weights are actually set: it needs an estimate, and weights set at a close need a later day. Month ends before the first estimate, and the final row of the data, set nothing; count executed rebalances.

### Holdings before the first rebalance

- Which reading fits depends on how the task schedules trades:
  - The task fixes the rebalance dates (for example month-end dates) and says nothing about an allocation at the start: weights from an estimate may be set only on those dates. Setting estimate-based weights on the first estimated day, which is usually not a scheduled date, is an extra rebalance off the schedule. Before the first scheduled date the strategy holds either a portfolio that needs no estimate (equal weights 1/n) or cash; use "equal" or "cash" by the reasoning below.
  - The task says the portfolio is allocated at the start of the backtest (or rebalanced at the start and then on a schedule): "first_estimate".
  - The task says the evaluation starts at the first rebalance: "start_at_first".
  - The task says the book is flat or in cash until the first rebalance: "cash".

- Three readings: hold an initial portfolio from the first backtest day, hold cash (weights 0) until the first rebalance,
  or start the evaluated sample at the first rebalance. They change return, volatility, Sharpe ratio, drawdown and win
  rate over that stretch.
- An inverse-volatility rule with no volatility estimate yet has no information to tilt the weights; equal volatilities
  give equal weights 1/n, which is the uninformed inverse-volatility portfolio. A backtest described as running the
  strategy over the whole sample, with no cash account mentioned, is fully invested from its first day, so the
  initial portfolio is the reading that keeps it invested; a reference that fills the rows before the first rebalance
  with 0 (as the qfref backtest-accounting entry does) is choosing the cash reading, not stating a rule.

### When new weights start earning

- Weights computed from data through the close of a rebalance date earn from the next day: day t earns with the weights
  held at the start of day t, and the rebalance at the close of day t changes them for day t + 1.

## Task wording -> API arguments

np.quantile and np.percentile: method="linear" is the default and interpolates; "inverted_cdf" is the step inverse of the empirical CDF; "lower", "higher", "nearest" and "midpoint" choose between the two neighbouring order statistics; weights=... is accepted only with method="inverted_cdf". np.percentile takes the level in percent.

scipy.stats distribution fit: dist.fit(x) estimates every parameter by maximum likelihood; floc=..., fscale=... and f0=... (shape) hold a parameter fixed; the returned order is shapes, then loc, then scale. stats.norm.fit returns the mean and the ddof=0 standard deviation.

Standard deviation: np.std and np.var default to ddof=0; pandas Series.std, DataFrame.std and DataFrame.cov default to ddof=1. "Sample" or "unbiased" means ddof=1; "population" or "maximum likelihood" means ddof=0.

pandas ewm: ewm(alpha=1 - lam, adjust=False) is the recursion seeded with the first value; adjust=True divides by the sum of the weights used so far; span=s means alpha = 2 / (s + 1), halflife=h means alpha = 1 - 0.5 ** (1 / h), com=c means alpha = 1 / (1 + c).

pandas rolling: rolling(W) needs W values by default; min_periods lowers that; the window ends at and includes the current row, so .shift(1) moves it to earlier rows only.

Random numbers: np.random.seed(s) with np.random.normal / standard_normal / multivariate_normal uses the legacy RandomState; np.random.default_rng(s) returns a Generator whose normal, standard_normal and multivariate_normal give a different stream. Generator.multivariate_normal factorizes the covariance with method="svd" by default ("cholesky" and "eigh" change the draws).

scipy.stats.chi2.sf(lr, 1) is the upper-tail p-value of a one-degree-of-freedom likelihood ratio; scipy.special.xlogy(a, b) returns 0 when a = 0.

## Sources

Jorion, Value at Risk, 3rd ed. (2007), ch. 5 (historical simulation, parametric VaR) and ch. 6 (backtesting). Acerbi and Tasche (2002), J. Banking and Finance 26(7), 1487-1503 (tail mean and conditional means at atoms). Rockafellar and Uryasev (2002), J. Banking and Finance 26(7), 1443-1471 (CVaR minimization formula). Hyndman and Fan (1996), American Statistician 50(4), 361-365 (sample quantile definitions). Boudoukh, Richardson and Whitelaw (1998), Risk 11(5), 64-67 (age-weighted historical simulation). J.P. Morgan/Reuters, RiskMetrics Technical Document, 4th ed. (1996), sec. 5.2 (EWMA). Kupiec (1995), J. Derivatives 3(2), 73-84 (proportion of failures). J.P. Morgan, CreditMetrics Technical Document (1997), ch. 8 (simulation). Docs: NumPy numpy.quantile and Random Generator / legacy RandomState; SciPy rv_continuous.fit, stats.t, special.xlogy; pandas Series.ewm and Series.rolling.
