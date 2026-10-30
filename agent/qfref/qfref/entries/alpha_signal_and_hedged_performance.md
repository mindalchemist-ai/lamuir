# Cross-sectional return signals, financed long-short returns and factor-adjusted performance

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input, setting or convention, follow the task description.

Read the topics relevant to the task; a task usually needs several of them.

## Topic 1: Cleaning a return matrix and counting missing values

**Purpose:** Count the missing values of a raw asset-return matrix and apply the task's missing-value treatment before any signal is computed.

**When to use:** The input is a table of returns with a date column and one column per asset, and the task asks to clean it, to handle missing values, or to report how many values were missing.

**Constraints:**
- The count is taken on the raw matrix of asset returns, before any filling, dropping or shifting: every later step changes the number of missing cells.
- Asset columns are selected by name (every column except the date column), not by position: whether the date is still a column or already the index changes what a positional slice removes.

**How to implement:**
1. Check the inputs and print them: the shape of the table, the column names, which column holds the dates, and the dtype of every asset column (a column read as text hides non-numeric entries).
2. Select the asset columns by name: `assets = [c for c in df.columns if c != date_col]`, before or after `set_index`. After `df = df.set_index(date_col)` every remaining column is an asset; `df.iloc[:, 1:]` would then drop the first asset, not the date.
3. Count the missing values on the raw asset matrix: `int(df[assets].isna().sum().sum())`, and print it next to the shape.
4. Apply the treatment the task states (for example fill with 0, carry forward, or drop rows), and print the count after the treatment.

**Limitations and cautions:**
- Filling a missing return with 0 asserts that the asset earned nothing that day; it is an economic assumption, not a neutral data repair, and it changes the universe and possibly the ranking.
- A rolling statistic over a window that contains a missing value is missing for every date whose window covers it, so the treatment comes before rolling signals.

**Double check:** If two counts were printed for the same raw data (for example with and without a column), they must agree; if they differ, the asset-column selection is wrong, so select the columns by name and recount.

## Topic 2: Past-return signal (momentum or reversal)

**Purpose:** Score each asset by its past returns over a lookback window, as the task defines the measure and the direction.

**When to use:** The task builds a signal from each asset's recent return behaviour. Standardize it across assets with Topic 3.

**Constraints:**
- The return measure, the direction, the window and the admitted information come from the task; "recent return behaviour" alone does not name a unique signal.
- A score uses only data available at the decision time (one lag in total; see the backtest card's look-ahead-free timing).
- A score exists only from the first date on which the full lookback is available.

**How to implement:**
1. Check the inputs and print them: the cleaned returns (Topic 1), the lookback $w$, the measure and the direction the task names.
2. Compounded return over the window $\mathcal{W}$: $s_{\mathrm{compound}} = \prod_{u \in \mathcal{W}} (1 + R_u) - 1$.
3. Arithmetic mean over the window: $s_{\mathrm{mean}} = \frac{1}{|\mathcal{W}|} \sum_{u \in \mathcal{W}} R_u$.
4. In pandas use `rolling(w, min_periods=w)`, so that a partial window gives a missing score, and drop those dates.
5. Momentum keeps the sign (higher past performance, higher score); reversal flips it. Risk-normalizing, skipping the most recent observations, or using factor residuals defines another signal; use it only when the task says so.

**Limitations and cautions:**
- `min_periods=1` followed by `fillna(0)` turns the warm-up into spurious signal days.
- Reindexing a frame built on an integer index to a date index returns all missing values.
- A score vector that is all equal or all zero carries no ranking; selecting from it picks names by column order.

**Double check:** On the first ranking date every score is finite and the scores are not all equal; if not, check the warm-up, the index alignment and the missing-value treatment, then recompute.

## Topic 3: Cross-sectional z-score

**Purpose:** Standardize the scores of one date across the eligible assets, so that they are comparable across dates.

**When to use:** The task asks for a cross-sectional z-score or standardized signal.

**Constraints:** The mean and standard deviation are those of the same date across the eligible universe, with the standard-deviation divisor the task names.

**How to implement:**
1. Check the inputs: the scores of each date and the eligible universe on that date.
2. For each date: $z_i = \frac{s_i - \bar{s}}{\operatorname{sd}_{\mathcal{U}}(s)}$, with $\bar{s}$ the date's cross-sectional mean (in pandas, per row: `sub(mean(axis=1), axis=0)` and `div(std(axis=1, ddof=...), axis=0)`).
3. When the dispersion of a date is zero, that date has no standardized ranking; treat it as the task states (for example no trade).

**Limitations and cautions:** A positive affine transformation keeps the ranking; a negative one reverses it. The missing-data policy changes the universe and can change the ranking.

**Double check:** Each date's z-scores have mean 0 and the stated standard deviation (1 with the same divisor); if not, the statistics were taken along the wrong axis, so recompute per date.

## Topic 4: Financed long-short return and trading cost

**Purpose:** Compute the return of a portfolio of signed weights with cash financing, and the cost of trading it.

**When to use:** The task reports the return of a long-short or leveraged book, its exposure, or costs proportional to turnover.

**Constraints:** A per-position cap and a gross-exposure cap are different restrictions; apply each as the task states (see the backtest card for sizes named in the procedure text).

**How to implement:**
1. Check the inputs: the signed weights $w_i$, the period cash return $r_f$, the financing convention, and the cost rate and the quantity it applies to.
2. Funded return before costs, with symmetric financing: $R_p = r_f + \sum_i w_i (R_i - r_f)$; a zero-net-investment basket without a cash account earns $\sum_i w_i R_i$.
3. Gross exposure $\sum_i |w_i|$; net exposure $\sum_i w_i$.
4. Cost with a proportional charge $c$ per unit of traded notional: $c \sum_i |\Delta w_i|$, where $\Delta w$ compares the target weights with the pre-trade holdings under the task's rebalance convention.

**Limitations and cautions:**
- A one-way turnover statistic $\frac{1}{2}\sum_i |\Delta w_i|$ is a reporting choice and does not halve the cost; a rate quoted per unit of one-way turnover is applied to that statistic.
- Subtracting the last target weights is not the same as subtracting drifted holdings, unless the task defines it that way.
- A signal derived from a close cannot earn returns before that close.

**Double check:** Gross and net exposure on a rebalance date match the sizes the task names; total cost equals the rate times the summed turnover; if not, recheck the weights and the turnover definition.

## Topic 5: Factor regression: alpha and residual beta

**Purpose:** Decompose a portfolio's returns into an intercept (alpha) and factor exposures (betas) by an OLS regression with an intercept.

**When to use:** The task asks for alpha, factor betas or the residual factor exposure of a strategy. For annualized alpha, tracking error and information ratio, add Topic 6.

**Constraints:** The regression uses the portfolio returns of the evaluation window and the factor returns of the same dates; whether the portfolio return is total, excess or a self-financing spread follows the task.

**How to implement:**
1. Check the inputs: the portfolio returns $y_t$ (net of costs when net performance is asked), the factor columns, their dates and units.
2. Regress $y_t = \alpha + \beta' f_t + e_t$ by OLS with an intercept (for example `numpy.linalg.lstsq` on a design matrix with a column of ones, or `statsmodels.api.OLS` with `add_constant`).
3. Report the fitted $\beta$ of the original portfolio as its residual factor exposure.

**Limitations and cautions:**
- A portfolio called hedged or residual-alpha need not have zero beta.
- In a same-sample OLS fit with an intercept, $\sum_t e_t = 0$ and $\sum_t f_t e_t = 0$, so regressing the residuals on the same factors gives zero slopes; that is a different diagnostic from the portfolio's betas. Out-of-sample residuals need not be orthogonal.
- A factor that is already an excess return is not reduced by the cash return again.
- A different covariance estimator changes standard errors, not the OLS coefficients.

**Double check:** The residuals sum to about 0 and are uncorrelated with each factor in the sample; if not, the intercept is missing or the dates are misaligned, so refit.

## Topic 6: Annualized alpha, tracking error and information ratio

**Purpose:** Convert the regression intercept and residual volatility to annual terms and form the information ratio.

**When to use:** The task reports annualized alpha, tracking error or information ratio of a strategy against factors.

**How to implement:**
1. Check the inputs: the intercept $\alpha$ and residuals $e_t$ from Topic 5, observations per year $A$, and the residual standard-deviation divisor the task names.
2. Annualized alpha: $\alpha_{\mathrm{ann}} = A\,\alpha$ (arithmetic, not compounded).
3. Tracking error: $\mathrm{TE}_{\mathrm{ann}} = \sqrt{A}\, s_e$, with $s_e$ the residual standard deviation.
4. Information ratio: $\mathrm{IR} = \frac{\alpha_{\mathrm{ann}}}{\mathrm{TE}_{\mathrm{ann}}} = \sqrt{A}\, \frac{\alpha}{s_e}$.

**Limitations and cautions:**
- The information ratio is not the Sharpe ratio unless its numerator and denominator coincide with the Sharpe ratio's.
- The residual sample standard deviation and the regression's residual standard error use different degrees of freedom.
- $\sqrt{A}$ scaling assumes uncorrelated returns.

**Double check:** Recompute IR as $\sqrt{A}\,\alpha / s_e$ from the printed values; if it differs from step 4, one of the annualizations was applied twice.

References: Sharpe (1994), The Sharpe Ratio (https://web.stanford.edu/~wfsharpe/art/sr/SR.htm), for differential-return ratios and time aggregation. Regression, financing and ranking identities are direct derivations under their stated definitions; this card does not choose an unspecified momentum or reversal rule.
