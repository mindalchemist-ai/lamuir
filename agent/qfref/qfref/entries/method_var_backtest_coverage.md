# Rolling VaR backtest and coverage tests: violations, Kupiec unconditional coverage, Christoffersen independence and conditional coverage

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input, setting or convention, follow the task description.

Read the topics relevant to the task; a task usually needs several of them.

## Topic 1: Rolling VaR forecasts and violations

**Purpose:** Produce one out-of-sample VaR forecast per day from a rolling estimation window and mark the days whose loss exceeds it.

**When to use:** The task backtests a VaR model over a rolling window. The coverage tests of Topics 2 to 4 use the violation series built here.

**Constraints:**
- Each forecast uses only the window before its day: the forecast for day $i$ is fitted on observations $i - W, \dots, i - 1$.
- A violation is a loss strictly greater than that day's VaR, unless the task defines it with "greater than or equal".

**How to implement:**
1. Check the inputs and print them: the loss (or return) series and its sign, the window length $W$, the VaR level, and the number of forecast days $T = N - W$.
2. For each day $i$ in `range(W, N)`: fit the model on the window `[i - W, i)`, forecast the VaR of day $i$, and record `v[i - W] = 1` when the loss of day $i$ exceeds it, else 0.
3. For a GARCH-based VaR, refit on each window and use the window fit's one-step-ahead volatility (`sigma_next`; see the arch conventions entry).

**Limitations and cautions:** Fitting on a window that includes day $i$ uses the realized loss in its own forecast and lowers the violation count.

**Double check:** The violation series has exactly $T$ entries and its mean is near the tail probability for a well-specified model; a mean of 0 or 1 points to a sign error between losses and VaR.

## Topic 2: Kupiec unconditional coverage test

**Purpose:** Test whether the violation rate equals the tail probability of the VaR.

**When to use:** The task asks for the Kupiec (proportion of failures) test or the unconditional coverage statistic.

**Constraints:** Use only the $T$ forecast days, not the estimation window; $0 \cdot \ln 0 = 0$ in every log-likelihood term.

**How to implement:**
1. Check the inputs: the violation series (Topic 1), $T$, the number of violations $x$ and the tail probability $\tau = 1 - \text{level}$ (see the arch conventions entry for the level convention).
2. $\hat{\pi} = x / T$.
3. $\mathrm{LR}_{uc} = -2\left[x \ln \tau + (T - x)\ln(1 - \tau) - x \ln \hat{\pi} - (T - x)\ln(1 - \hat{\pi})\right]$, writing each term $k \ln q$ with `scipy.special.xlogy(k, q)`, which returns 0 when $k = 0$ (a plain `k * np.log(q)` gives `nan` for $x = 0$ or $x = T$).
4. p-value: `scipy.stats.chi2.sf(LR_uc, 1)`.

**Limitations and cautions:** With few forecast days the chi-square approximation is rough; the test has low power against small deviations.

**Double check:** $\mathrm{LR}_{uc} \ge 0$ and equals 0 when $\hat{\pi} = \tau$; if it is negative or `nan`, a $0 \cdot \ln 0$ term was not handled.

## Topic 3: Christoffersen independence test

**Purpose:** Test whether a violation today makes a violation tomorrow more likely (clustering).

**When to use:** The task asks for the Christoffersen independence test, violation clustering, or the independence part of conditional coverage.

**Constraints:**
- Transitions are counted between consecutive forecast days: $T - 1$ pairs.
- $0 \cdot \ln 0 = 0$ in every term.

**How to implement:**
1. Check the inputs: the violation array `v` of length $T$ (Topic 1).
2. Previous-day states `prev = v[:-1]` and current-day states `cur = v[1:]`.
3. Counts $n_{ij}$ = `np.sum((prev == i) & (cur == j))` for $i, j \in \{0, 1\}$ (1 = violation). Print them: they sum to $T - 1$, and with at least one violation inside the sample $n_{01}$ and $n_{10}$ are not both zero; if they are, `prev` and `cur` are the same array, so rebuild them.
4. Probabilities: $\hat{p}_{01} = n_{01}/(n_{00} + n_{01})$, $\hat{p}_{11} = n_{11}/(n_{10} + n_{11})$ (0 when the denominator is 0), and $\hat{p} = (n_{01} + n_{11})/(n_{00} + n_{01} + n_{10} + n_{11})$.
5. Log-likelihoods: $\ell_0 = (n_{00} + n_{10})\ln(1 - \hat{p}) + (n_{01} + n_{11})\ln \hat{p}$ and $\ell_1 = n_{00}\ln(1 - \hat{p}_{01}) + n_{01}\ln \hat{p}_{01} + n_{10}\ln(1 - \hat{p}_{11}) + n_{11}\ln \hat{p}_{11}$, each term with `scipy.special.xlogy`.
6. $\mathrm{LR}_{ind} = -2(\ell_0 - \ell_1)$; p-value `scipy.stats.chi2.sf(LR_ind, 1)`.

**Limitations and cautions:** A single violation not followed by another gives $n_{11} = 0$ and a small but non-zero $\mathrm{LR}_{ind}$; with very few violations the test has little power.

**Double check:** $\mathrm{LR}_{ind} \ge 0$; a value of several hundred with few violations means the transition counts are wrong (step 3).

## Topic 4: Conditional coverage test

**Purpose:** Test jointly the violation rate and the independence of violations.

**When to use:** The task asks for the conditional coverage statistic or the joint Christoffersen test.

**How to implement:**
1. Check the inputs: $\mathrm{LR}_{uc}$ (Topic 2) and $\mathrm{LR}_{ind}$ (Topic 3) computed on the same $T$ days.
2. $\mathrm{LR}_{cc} = \mathrm{LR}_{uc} + \mathrm{LR}_{ind}$.
3. p-value: `scipy.stats.chi2.sf(LR_cc, 2)`; reject at the task's significance level when the p-value is below it.

**Limitations and cautions:** The two parts use slightly different samples ($T$ days and $T - 1$ pairs); this is the standard construction.

**Double check:** $\mathrm{LR}_{cc}$ equals the sum of the two printed statistics and its p-value uses two degrees of freedom; if not, recompute from Topics 2 and 3.

References: Kupiec (1995), Techniques for verifying the accuracy of risk measurement models, Journal of Derivatives 3(2); Christoffersen (1998), Evaluating interval forecasts, International Economic Review 39(4).
