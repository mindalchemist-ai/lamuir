# VaR and ES of return series: loss sign, quantile rules, tail means, weights, horizons and windows

Use this note for value-at-risk (VaR), expected shortfall (ES, CVaR) and related backtests on return series, simulated wealth paths or simulated credit losses. Most steps below have more than one standard reading. Each skeleton takes the choice as an argument: read its value from the task instructions, and when the instructions leave it open, pick one, write the choice in a comment, and use the same choice in every output. The skeletons assume `import numpy as np`, `import pandas as pd` and `from scipy import stats, special`.

## 1. Loss sign and confidence level

A loss is the negative of a return or P&L, so the risky side is the upper tail of the loss. A confidence level such as 95% corresponds to the tail probability 1 - level. Some texts call the confidence level alpha, others call the tail probability alpha; decide from the numbers the task lists (0.95 and 0.99 are confidence levels, 0.05 and 0.01 are tail probabilities).

Losses are the negated returns, $L = -r$, keeping only finite values.

## 2. Empirical VaR: which quantile rule

With n scenarios the empirical quantile is not unique. "kth_worst" takes the k-th largest loss with k = ceil(n * tail), which is the classical historical-simulation order statistic and equals -np.quantile(returns, tail, method="inverted_cdf"). In floating point 1 - 0.95 is 0.05000000000000004, so when n * tail is a whole number a step rule can move one observation further; the skeleton rounds the tail probability first. A NumPy method name ("linear" is the NumPy default and interpolates between neighbouring order statistics; "lower", "higher", "nearest", "inverted_cdf" pick one observed value) applies np.quantile to the losses at the confidence level. "linear" is symmetric (the loss quantile at the level is minus the return quantile at the tail); the step rules are not, so np.quantile(loss, level, method="inverted_cdf") is the (k+1)-th worst loss when n * tail is a whole number k.

## 3. ES: which tail mean

Three tail means are in use. "strict" is E[L | L > VaR], the mean of losses above VaR; it is empty, hence undefined, when VaR is the largest loss. "inclusive" is E[L | L >= VaR], which always contains the VaR scenario. "tail_mean" averages exactly the worst tail * n outcomes and takes only the needed fraction of the boundary scenario (Acerbi and Tasche 2002); it equals min over c of c + mean(max(L - c, 0)) / tail. For continuous data the three nearly agree. For losses on a grid (a count of defaults times a fixed loss, rounded P&L) many scenarios sit exactly at VaR and the three can differ by a large amount. Without ties at VaR (continuous data) the strict and inclusive means are equal. When losses tie at VaR (resampled or bootstrapped rows, simulated or discrete losses, rounded P&L), the default is the inclusive mean E[L | L >= VaR], the tail conditional expectation of Artzner, Delbaen, Eber and Heath (1999, Mathematical Finance 9(3), Definition 5.1: TCE = -E[X | X <= -VaR] on returns). Use the strict mean only when the task writes "strictly greater than VaR" or a formula with a strict inequality, and tail_mean when it asks for the "integrated quantile", "average VaR over the tail" or "coherent ES". Words such as "exceeding VaR" or "beyond VaR" do not by themselves ask for the strict mean. Compute both, print their difference and the number of losses equal to VaR, then report the one chosen.

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

A "standardized t" has two meanings. (1) scipy's t(df) itself, loc 0 and scale 1, whose variance is df / (df - 2). (2) a t rescaled to unit variance, with scale sqrt((df - 2) / df). Use (1), t(df) as it is, when the task rules out shifting or rescaling the distribution or gives quantiles of t(df) directly; rescale to (2) only when the task says "unit variance" or asks for a t with the same variance as a normal it is compared with. For a sample drawn from or fitted to a distribution, compare its variance with df / (df - 2) to see which one is in use.

1. Normal VaR and ES: with $\mu$ the sample mean (or 0 when the task says zero mean), $s$ the standard deviation with the stated divisor and $z = \Phi^{-1}(c)$: $\mathrm{VaR} = -\mu + s z$ and $\mathrm{ES} = -\mu + s\,\phi(z)/(1-c)$. "Fit a normal distribution to the returns" means estimating both the mean and the standard deviation, so $\mu$ is the sample mean: set it to 0 only when the task says zero mean or relative VaR. When the task says to scale the one-day VaR by $\sqrt{h}$, multiply this one-day VaR, mean included, by $\sqrt{h}$ as stated; the exact normal $h$-day form $-h\mu + \sqrt{h}\,s z$ applies only when the task gives no scaling rule, and the stated rule is never a reason to drop the mean from the one-day figure.
2. Student t VaR and ES: fit $(\nu, \mathrm{loc}, \mathrm{scale})$ with `scipy.stats.t.fit` (with any fixed parameters the task states); ES needs $\nu > 1$. With $q = t_\nu^{-1}(c)$ and $m$ the location (or 0): $\mathrm{VaR} = -m + \mathrm{scale}\cdot q$ and $\mathrm{ES} = -m + \mathrm{scale}\cdot f_\nu(q)\,\frac{\nu + q^2}{(\nu - 1)(1 - c)}$, where $f_\nu$ is the t density.

## 6. EWMA covariance

The recursion C_t = lam * C_(t-1) + (1 - lam) * x_t x_t' needs a starting matrix: the first observation's outer product, a sample covariance of the first m rows, or zero. It also needs a mean convention: raw returns (zero mean, the RiskMetrics form) or demeaned returns. The matrix after the last observation is the forecast for the next period, which is what "current" or "as of the last date" usually means. Annualize a volatility with the square root of the periods per year that the data frequency implies (for example 252 trading days, 52 weeks or 12 months); the frequency comes from the data, not from a fixed number.

EWMA covariance with decay $\lambda$ over return vectors $x_t$ (demeaned first when the task says so): $C_t = \lambda C_{t-1} + (1-\lambda)x_t x_t^{\top}$. The starting matrix is a choice that changes the numbers; use the one the task states: the first outer product $x_1 x_1^{\top}$ (recursion from the second observation), a zero matrix, or the sample covariance of the first $k$ observations (divisor $k-1$, recursion from observation $k+1$). Annualized portfolio volatility: $\sqrt{w^{\top} C w \cdot P}$ with $P$ periods per year.

For one series, seed "first_outer" with zero mean equals pd.Series(x**2).ewm(alpha=1 - lam, adjust=False).mean().

## 7. Multi-period horizons

Square-root-of-time scaling multiplies a one-period VaR or ES by sqrt(h); it is exact for independent normal returns with zero mean. When the task states this scaling, apply it to the one-period figure, mean included, as stated. Only when the task gives no scaling rule and keeps a mean is the h-period normal VaR -h * mu + sqrt(h) * sd * z. For simulation-type methods an h-period scenario is the sum of h consecutive log returns, or the compounded product of h simple returns. Overlapping windows step one period at a time (n - h + 1 scenarios, strongly dependent); non-overlapping windows step h periods (about n / h scenarios) and need an anchor, either the first or the last observation.

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

1. Rolling windows of length $W$ for row $t$: rows $t-W+1$ to $t$ when the current row is included, or rows $t-W$ to $t-1$ when it is not; skip rows without a full window.
2. Month-end rebalance dates: the last trading date of each month in the data, excluding the final month when it is not complete (the next business day after the last date is in the same month).
3. Holding between rebalances: write each rebalance's complete target row on its date, shift by one row when the new weights take effect the next day, carry forward, and before the first rebalance either start at it or use the stated initial holding.

## 11. Portfolio return, leverage and scaling to a risk limit

With fractions w of wealth in risky assets with simple returns R, three account models are in use. "weighted_sum" is R @ w: the portfolio return is the weighted sum of the asset returns, and the remainder 1 - sum(w) earns nothing. "financed" is rf + (R - rf) @ w: the remainder is lent or borrowed at the cash rate. "excess_only" is (R - rf) @ w. When the task describes no cash account or financing rate for the remainder, the weighted sum is the literal reading and a cash leg is an added assumption; state it if you add one. The same period returns then drive wealth, Sharpe ratio and drawdown.

Gross exposure (leverage) is sum(|w|); net exposure is sum(w). A per-period cash rate from an annual rate is r / periods_per_year under simple division and (1 + r) ** (1 / periods_per_year) - 1 under compounding.

To meet a risk limit along a fixed direction, "comply with", "cap at" or "not exceed" reads as c = min(1, limit / risk), which scales down only; "scale to" or "target" reads as c = limit / risk.

1. Portfolio return per period from asset returns $R$, weights $w$ and the cash rate $r_f$ per period, by the task's accounting: weighted sum $Rw$; financed (the remainder earns the cash rate) $r_f + (R - r_f)w$; or excess $(R - r_f)w$.
2. Exposure: gross $\sum|w_i|$ and net $\sum w_i$.
3. Risk scaling to a limit: a cap scales by $\min(1, \text{limit}/\text{risk})$; a target scales by $\text{limit}/\text{risk}$.

## Random streams in a simulation

Create the random generator once, before the simulation (`rng = np.random.default_rng(seed)`), and take every draw from that same object. A sampler or loop that calls `np.random.default_rng(seed)` again restarts the stream each time: later draws repeat the first numbers, the simulated losses lose most of their variation, and simulated quantiles come out systematically too low.

Arrays drawn from one generator take consecutive numbers, so the order of the draws fixes every sample. For a mixture that draws one array per component and then selects, draw the components in the order the task lists them; inside a single expression such as `np.where(u < p, a(), b())` the arguments are evaluated left to right, so swapping them, or flipping the condition to select the other component first, changes which numbers each component gets.

Two-component normal mixture with a uniform selector: the order of the draws and how many values each component receives change the sample under a fixed seed. Follow the task's order (for example the selector first, then the components in the order listed). Two common readings of "draw from the selected component": draw $n$ values for each component and pick by the selector, or draw only as many values from each component as the selector assigns to it; use the one the task describes, and state it.

## 13. Group breakdowns of a portfolio loss

For groups that partition the portfolio, two "mean loss" figures exist per group: the mean over scenarios of the group's total loss, and the mean loss of a single member. They differ by the group size. Group totals add up to the portfolio mean loss; per-member means do not. Wording such as "per name", "per bond" or "average member" points to the per-member figure; a table presented as the breakdown of a portfolio figure points to the group total. When the wording fits both, write the choice in a comment and check the sum.

Loss by group, two readings: the group total (the sum of its members' losses per scenario, averaged over scenarios) or the per-member mean; the total equals the number of members times the per-member mean, and the group totals add up to the portfolio mean loss.

## 14. After a correction, rewrite every file that used it

When a function is fixed after its results were written, the files written earlier still hold the old values. Recompute and rewrite every output that used it, read the files back, and check the invariants that hold under every convention above: ES >= VaR for the same level and method, VaR at a higher level >= VaR at a lower level for the same method, and the expected number of rows and labels.

## Task wording -> API arguments

np.quantile and np.percentile: method="linear" is the default and interpolates; "inverted_cdf" is the step inverse of the empirical CDF; "lower", "higher", "nearest" and "midpoint" choose between the two neighbouring order statistics; weights=... is accepted only with method="inverted_cdf". np.percentile takes the level in percent.

scipy.stats distribution fit: dist.fit(x) estimates every parameter by maximum likelihood; floc=..., fscale=... and f0=... (shape) hold a parameter fixed; the returned order is shapes, then loc, then scale. stats.norm.fit returns the mean and the ddof=0 standard deviation.

Standard deviation: np.std and np.var default to ddof=0; pandas Series.std, DataFrame.std and DataFrame.cov default to ddof=1. "Sample" or "unbiased" means ddof=1; "population" or "maximum likelihood" means ddof=0.

pandas ewm: ewm(alpha=1 - lam, adjust=False) is the recursion seeded with the first value; adjust=True divides by the sum of the weights used so far; span=s means alpha = 2 / (s + 1), halflife=h means alpha = 1 - 0.5 ** (1 / h), com=c means alpha = 1 / (1 + c).

pandas rolling: rolling(W) needs W values by default; min_periods lowers that; the window ends at and includes the current row, so .shift(1) moves it to earlier rows only.


scipy.stats.chi2.sf(lr, 1) is the upper-tail p-value of a one-degree-of-freedom likelihood ratio; scipy.special.xlogy(a, b) returns 0 when a = 0.

## Sources

Jorion, Value at Risk, 3rd ed. (2007), ch. 5 (historical simulation, parametric VaR) and ch. 6 (backtesting). Acerbi and Tasche (2002), J. Banking and Finance 26(7), 1487-1503 (tail mean and conditional means at atoms). Rockafellar and Uryasev (2002), J. Banking and Finance 26(7), 1443-1471 (CVaR minimization formula). Hyndman and Fan (1996), American Statistician 50(4), 361-365 (sample quantile definitions). Boudoukh, Richardson and Whitelaw (1998), Risk 11(5), 64-67 (age-weighted historical simulation). J.P. Morgan/Reuters, RiskMetrics Technical Document, 4th ed. (1996), sec. 5.2 (EWMA). Kupiec (1995), J. Derivatives 3(2), 73-84 (proportion of failures). J.P. Morgan, CreditMetrics Technical Document (1997), ch. 8 (simulation). Docs: NumPy numpy.quantile and Random Generator / legacy RandomState; SciPy rv_continuous.fit, stats.t, special.xlogy; pandas Series.ewm and Series.rolling.

## Sign summary

| Quantity | Readings | Pick by |
|---|---|---|
| Loss | loss = -return (or -P&L); a "negative log-return" series is already a loss | the task's definition; with returns, VaR is the lower tail of returns, with losses the upper tail of losses |
| Reported VaR / ES | a positive loss magnitude, or the return quantile with its negative sign | "loss", "magnitude", "positive" → positive; "return quantile", a formula written with the minus sign, or "≤ 0" → keep the sign; neither → positive magnitude, the usual reporting form, and say so |
| Confidence level vs tail probability | $c = 0.99$ corresponds to tail $\alpha = 1 - c = 0.01$ | the numbers listed (0.95, 0.99 are levels; 0.05, 0.01 are tails); pass the tail probability to a return quantile and the level to a loss quantile |
| ES tail | mean at or below the return VaR (`<=`), or strictly beyond it (`<`) | `<=` unless the task writes a strict inequality or "strictly"; the two differ only when values tie at the VaR (resampled, simulated or discrete samples) |
| Currency VaR | portfolio value × return-scale VaR | the value the task names (start-of-period value unless stated otherwise) |
| Position direction | a short position's P&L moves opposite to the price; pay/receive and buy/sell legs flip the sign the same way | the position or leg the task describes; compute P&L with the sign before forming losses |

VaR as a positive loss: the $(1-c)$-quantile of the returns, negated, equals the $c$-quantile of the losses; ES is the negated mean of the returns at or below that return quantile, and it is at least the VaR.
