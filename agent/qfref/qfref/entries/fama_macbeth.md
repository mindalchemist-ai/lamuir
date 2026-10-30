# Fama-MacBeth (1973) cross-sectional regressions: per-period slopes, standard errors, Newey-West, forecasts, Shanken correction, standardized characteristics and residual momentum

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input, setting or convention, follow the task description.

Read the topics relevant to the task; a task usually needs several of them.

Notation used in every topic:

| symbol | meaning |
|---|---|
| $y_{it}$ | dependent variable of asset $i$ for period $t$ (e.g. return from $t$ to $t+1$; align dates exactly as the task says) |
| $x_{it}$ | $K$ regressors of asset $i$ observed at $t$ (characteristics, or estimated betas $\hat{\beta}_{i}$) |
| $N_{t}$ | number of assets with complete data at $t$ (must exceed $K + 1$) |
| $T$ | number of periods with a valid cross-sectional regression (NOT the number of stock-month observations) |
| $\hat{\lambda}_{t}$ | $(K+1)$-vector of per-period coefficients (intercept first) |
| $L, h$ | Newey-West lag; return horizon in periods when returns overlap |

## Topic 1: Per-period cross-sectional regressions, one per model

**Purpose:** Estimate, for each period, the cross-sectional relation between outcomes and regressors known at the forecast date, so that the slopes form a time series.

**When to use:** A panel of assets $i$ over periods $t = 1 \ldots T$, and the task asks for Fama-MacBeth slopes, risk premia or characteristic returns, possibly for several models with different regressor sets.

**Constraints:**
- Regressors are known at the forecast date: firm characteristics, or betas estimated in a first pass.
- One regression per model. When the task compares models with different regressor sets (nested or not), run a separate cross-sectional regression for each model each period, on the rows complete for that model's own target and regressors. The coefficients of a smaller model are not a subset of a larger model's; copying them gives wrong slopes, wrong valid-period counts and wrong forecasts.
- Store the full fitted coefficient vector (intercept and every regressor, controls included) for each period, even when the deliverable reports only some slopes; the forecast step (Topic 4) needs all of them.

**How to implement:**
1. Check the inputs and print them: the date column, the target and its date alignment, each model's regressor list, and the minimum number of observations per regression.
2. Only if the regressors are betas (pass 1): for each asset, over the beta window, regress $R_{it} = a_{i} + b_{i}' f_{t} + e_{it}$ to get $\hat{\beta}_{i}$.
3. Pass 2, as a line-by-line algorithm:
   - `lam = {name: {} for name in models}`
   - `for date, month in panel.groupby(date_col):`
   - `    for name, cols in models.items():`
   - `        sub = month.dropna(subset=[target] + cols)`
   - `        if len(sub) < min_obs: continue`
   - `        lam[name][date] = sm.OLS(sub[target], sm.add_constant(sub[cols], has_constant="add")).fit().params`
   - after the loop, check `all(len(lam[m]) > 0 for m in models)`: each model keeps its own valid-period list.
4. Each fit is $X_{t} = [1, x_{\cdot t}]$ of shape $N_{t} \times (K+1)$ and $\hat{\lambda}_{t} = (X_{t}' X_{t})^{-1} X_{t}' y_{t}$.

**Limitations and cautions:** Unbalanced panels are fine; $T$ counts only periods actually regressed. Small $N_{t}$ makes per-period slopes noisy. With estimated betas the slopes have errors-in-variables bias in finite $T$ (Topic 5).

**Double check:** Print, per model, the number of valid periods and the first period's coefficient names; models with different regressors must show different counts or different coefficients, not copies.

## Topic 2: Fama-MacBeth estimate and standard error

**Purpose:** Average the per-period slopes and measure their uncertainty from their time-series variability.

**When to use:** The task asks for average slopes, their standard errors, t-statistics, p-values or an average $R^2$.

**Constraints:**
- The standard error is NOT the per-period OLS standard error, not an average of per-period standard errors, and not the standard error of one pooled regression.
- This handles cross-sectional correlation of returns automatically; it assumes the slopes are uncorrelated over time (otherwise Topic 3).

**How to implement:**
1. Estimate: $\bar{\lambda} = (1/T) \sum_{t} \hat{\lambda}_{t}$, with `numpy.mean` over the slope series.
2. Standard error: $s_{j}^{2} = (1/(T-1)) \sum_{t} (\hat{\lambda}_{jt} - \bar{\lambda}_{j})^{2}$ and $\mathrm{se}_{j} = s_{j} / \sqrt{T}$.
3. t-statistic $t_{j} = \bar{\lambda}_{j} / \mathrm{se}_{j}$; p-value from $t(T-1)$ or the normal, as the task says.
4. Covariance: $V_{\mathrm{FM}} = (1/(T(T-1))) \sum_{t} (\hat{\lambda}_{t} - \bar{\lambda})(\hat{\lambda}_{t} - \bar{\lambda})'$.
5. Average $R^2$: average the per-period $R^2$ values.

**Limitations and cautions:** Robust to cross-sectional correlation but not to serial correlation of $\hat{\lambda}_{t}$ (persistent characteristics, overlapping returns); then use Topic 3. With estimated betas, see Topic 5.

**Double check:** $T$ equals the number of valid periods of that model (Topic 1), not the number of rows in the panel.

## Topic 3: Newey-West standard errors for persistent or overlapping slopes

**Purpose:** Correct the Fama-MacBeth standard error for serial correlation of the slopes.

**When to use:** Overlapping returns, persistent characteristics, or the task asks for Newey-West (HAC) t-statistics.

**Constraints:**
- With $h$-period overlapping returns the slopes are serially correlated up to lag $h - 1$: use $L \ge h - 1$ unless the task sets $L$.
- A task asking for the textbook Newey-West form with the $1/T$ autocovariance denominator means the formula below, computed directly.

**How to implement:**
1. Average slope $\bar{\lambda}_{j}$ with `numpy.mean` of the slope series.
2. $\gamma_{l} = (1/T) \sum_{t=l+1}^{T} (\hat{\lambda}_{jt} - \bar{\lambda}_{j})(\hat{\lambda}_{j,t-l} - \bar{\lambda}_{j})$.
3. $\mathrm{se}_{\mathrm{NW},j} = \sqrt{[\gamma_{0} + 2 \sum_{l=1}^{L} (1 - l/(L+1)) \gamma_{l}] / T}$ and $t_{\mathrm{NW},j} = \bar{\lambda}_{j} / \mathrm{se}_{\mathrm{NW},j}$.
4. Before reporting, check that each reported average slope equals `numpy.mean` of its monthly series.

**Implementation tips:** If the mean and its HAC standard error are obtained instead by regressing the slope series on a constant, the design matrix must hold exactly one column of ones: `sm.add_constant(np.ones(T))` adds a second, identical constant column, and OLS then splits the mean between the two columns, so the reported average slope is half the true one while its t-statistic is unchanged. See the Newey-West entry for lag rules.

**Limitations and cautions:** $L = 0$ gives the standard deviation with divisor $T$, slightly smaller than the plain Fama-MacBeth standard error.

**Double check:** Step 4; and $\mathrm{se}_{\mathrm{NW}}$ at $L = 0$ equals $\mathrm{se}_{j}\sqrt{(T-1)/T}$.

## Topic 4: Forecasts from averaged slopes

**Purpose:** Predict each asset's outcome at a date from slopes estimated before that date.

**When to use:** The task asks for out-of-sample forecasts, predicted returns or portfolios ranked on the fitted model.

**Constraints:**
- Calendar periods versus estimated periods: a start rule stated in calendar periods ("forecasts begin after the $n$-th month") counts the sample's calendar periods, including periods that produced no regression. Test the date's position in the full date list, not its position among estimated periods.
- An expanding average at a forecast date uses every slope estimated before that date.
- The forecast uses the whole fitted model: averaged intercept plus averaged slopes times every regressor of that model, controls included, standardized exactly as in the fit. Leaving the controls out ranks the assets on a different model.

**How to implement:**
1. `all_dates = sorted(panel[date_col].unique())` and `pos = {d: i for i, d in enumerate(all_dates)}`.
2. For each `d` in `all_dates`: skip it when `pos[d] < n`.
3. `past = [lam[name][e] for e in lam[name] if e < d]` and `avg = sum(past) / len(past)`.
4. `z = month_d[cols]` (standardized as in the fit) and `pred = avg["const"] + z @ avg[cols]`.
5. Check `list(avg.index) == ["const"] + cols`.

**Limitations and cautions:** Early forecast dates average few slopes and are noisy; this is part of the method, not an error to fix.

**Double check:** The first forecast date is the $(n+1)$-th calendar date of the sample; print it with the number of slopes averaged there.

## Topic 5: Shanken (1992) correction for estimated betas

**Purpose:** Inflate the Fama-MacBeth covariance for the estimation error of first-pass betas.

**When to use:** Only when the pass-2 regressors are ESTIMATED betas and the task asks for Shanken-corrected standard errors. Not for observed characteristics (they are not estimated).

**Constraints:**
- $\Gamma = (\gamma_{0}, \gamma_{a}')'$, with $\gamma_{a}$ the $K$ factor premia (per period, same frequency as returns).
- $c = \gamma_{a}' \Sigma_{f}^{-1} \gamma_{a}$, with $\Sigma_{f}$ the $K \times K$ covariance of the factors $f_{t}$ over the pass-1 sample; $c$ is not annualized when the data are monthly.
- $\Sigma_{f}^{*}$ is block-diagonal: 0 for the intercept, $\Sigma_{f}$ for the factors.

**How to implement:**
1. Compute $V_{\mathrm{FM}}$ (Topic 2) and $c$.
2. Practical form: $V_{\mathrm{Shanken}} = (1 + c)(V_{\mathrm{FM}} - \Sigma_{f}^{*} / T) + \Sigma_{f}^{*} / T$.
3. Without an intercept in pass 2, drop its row and column.

**Implementation tips:** The asymptotic form it comes from is $\operatorname{Cov}(\hat{\Gamma}) = (1/T) [(1 + c) A \Sigma A' + \Sigma_{f}^{*}]$, $A = (X'X)^{-1} X'$, $X = [1, \hat{\beta}]$, $\Sigma$ = pass-1 residual covariance. Both forms agree asymptotically, not exactly.

**Limitations and cautions:** The non-factor variance component receives the multiplier $1 + c$; the corresponding standard-error multiplier is $\sqrt{1 + c}$, not $1 + c$. The full covariance also contains the separate factor component.

**Double check:** Corrected standard errors are at least as large as the uncorrected ones.

## Topic 6: Cross-sectional standardization of characteristics

**Purpose:** Put characteristics on a common scale within each date before the cross-sectional regression.

**When to use:** The task asks for z-scored, standardized or ranked characteristics.

**Constraints:**
- $z_{it} = (x_{it} - \operatorname{mean}_{t}(x)) / \operatorname{sd}_{t}(x)$, mean and standard deviation over the $N_{t}$ assets present at date $t$.
- Standardize within each date (groupby date), never over the pooled panel (look-ahead).

**How to implement:**
1. Drop or fill missing values and winsorize first if the task says so.
2. Standardize over exactly the assets used in that date's regression.
3. Set ddof explicitly: population sd divides by $N_{t}$ (ddof 0), sample sd by $N_{t} - 1$ (ddof 1). numpy `std` defaults to ddof 0, pandas `.std()` to ddof 1; the z-scores differ by the factor $\sqrt{N_{t}/(N_{t}-1)}$.
4. Rank variant: replace $x$ by its cross-sectional rank (often scaled to $[0, 1]$ or demeaned) before regressing.

**Limitations and cautions:** On dates with few assets the sd is noisy; a constant characteristic on a date has sd 0 and its z-scores are undefined, so follow the task's rule for such dates.

**Double check:** Each date's z-scores have mean 0 and the standard deviation 1 under the chosen ddof.

## Topic 7: Residual momentum (Blitz, Huij and Martens 2011)

**Purpose:** Rank stocks on past factor-model residual returns scaled by their residual volatility, instead of total returns.

**When to use:** The task asks for residual momentum or idiosyncratic momentum.

**Constraints:**
- Residuals exclude $\alpha$; factor betas use only data up to $t - 1$.
- Scale by the residual sd over the same formation months (standardization as in Gutierrez and Prinsky 2007), unless the task defines it otherwise.

**How to implement:** For each stock $i$ and formation date $t$ (ranking for the holding period that starts at $t$):
1. Over the $W$ months $t - W \ldots t - 1$ regress excess returns on the factor model (BHM: Fama-French three factors) with an intercept: $r_{is} = \alpha_{i} + \beta_{i}' f_{s} + \varepsilon_{is}$; keep only stocks with a complete window.
2. Residuals: $\hat{\varepsilon}_{is} = r_{is} - \hat{\alpha}_{i} - \hat{\beta}_{i}' f_{s}$ (do not add $\alpha$ back).
3. Formation months: $s = t - J \ldots t - 1 - S$ ($S$ = skip months; BHM use the past year and skip the most recent month).
4. Score: $\sum \hat{\varepsilon}_{is} / \operatorname{sd}(\hat{\varepsilon}_{is})$ over the formation months (sd over the SAME months; ddof per task). mean/sd ranks identically when every stock has the same number of formation months.
5. Sort stocks on the score each date (e.g. deciles), long the top, short the bottom, weighting as the task says. Unless the task gives its own bucketing rule, quantile groups are equal-count bins of the sorted values: `pd.qcut(score, q, labels=False)` (group 0 is the lowest), with `score.rank(method='first')` passed instead of the score when ties would make the edges repeat. A percentile-rank threshold such as `(rank - 1) / (n - 1) < 0.2` is a different rule: it changes how many names fall in the end groups when $n$ is not a multiple of $q$.

**Limitations and cautions:** Common mistakes: regressing without an intercept; including month $t - 1$ when it should be skipped; using betas estimated with data after $t - 1$; scaling by total-return volatility or by the whole $W$-month residual sd (only if the task defines it that way).

**Double check:** Print, for one stock and date, the window months, the formation months and the score.

References: Fama and MacBeth (1973), Journal of Political Economy 81(3):607-636; Shanken (1992), Review of Financial Studies 5(1):1-33; Shanken and Zhou (2007), Journal of Financial Economics 84(1):40-86 (eq. 9); Newey and West (1987), Econometrica 55(3):703-708; Blitz, Huij and Martens (2011), Journal of Empirical Finance 18(3):506-521; Gutierrez and Prinsky (2007), Journal of Financial Markets 10(1):48-75 (cited via BHM; original not read).
