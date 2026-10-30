# Tail VaR and ES: historical, normal, peaks over threshold, Hill tail index and GARCH-filtered EVT

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input, setting or convention, follow the task description.

Read the topics relevant to the task; a task usually needs several of them.

## Topic 1: Historical VaR and ES

**Purpose:** Estimate Value-at-Risk (VaR) and Expected Shortfall (ES) at confidence level $p$ directly from the empirical loss distribution.

**When to use:** The task asks for historical or empirical VaR or ES, or uses them as the benchmark for a parametric or EVT estimate. For a fitted tail beyond the sample's extremes use Topic 3; for a normal benchmark use Topic 2.

**Constraints:**
- Losses are positive numbers: $L_t = -r_t$ for returns $r_t$, unless the task defines losses differently.
- The quantile method and the ES tail definition are the ones the task names.

**How to implement:**
1. Check the inputs and print them: the return series and whether it is simple or log returns, the sign convention for losses, the confidence levels $p$ (for example 0.99, not 99), and the sample size $n$.
2. Form the losses $L_t = -r_t$.
3. Compute the VaR as the empirical $p$-quantile of the losses with `numpy.quantile(L, p, method=...)`, using the method the task names; without one, the default `linear` interpolation, and say so.
4. Compute the ES as the mean of the losses in the tail: $\mathrm{ES}_p = \operatorname{mean}\{L_t : L_t \ge \mathrm{VaR}_p\}$, or with $>$ or the Acerbi-Tasche weighted tail mean when the task writes that definition.

**Limitations and cautions:**
- In small samples the quantile methods `linear`, `lower`, `higher` and `nearest` differ by up to one order statistic, so the reported VaR moves with the method.
- The three ES definitions differ only when several losses tie at the VaR; with ties, the choice changes the result.

**Double check:**
- ES is not below VaR at the same level; if it is, the tail mean was taken over the wrong side or over returns instead of losses, so recompute it on $L_t \ge \mathrm{VaR}_p$.
- VaR increases with $p$; if it does not, the levels were written as percentages or swapped, so fix the levels and rerun.

## Topic 2: Normal VaR and ES

**Purpose:** Estimate VaR and ES assuming normally distributed losses with the sample mean and standard deviation.

**When to use:** The task asks for parametric, Gaussian or variance-covariance VaR, or a normal benchmark next to historical or EVT estimates. For heavy tails beyond the normal use Topic 3.

**How to implement:**
1. Check the inputs and print them: the losses, the confidence levels, and whether the task asks for the sample mean or zero mean.
2. Compute the sample mean $m$ and the sample standard deviation $s$; "sample standard deviation" means divisor $n-1$ (`ddof=1`). NumPy's `std` defaults to divisor $n$, pandas' to $n-1$, so set it explicitly.
3. Compute the VaR: $\mathrm{VaR}_p = m + s\,z_p$, where $z_p$ is `scipy.stats.norm.ppf(p)`.
4. Compute the ES: $\mathrm{ES}_p = m + s\,\frac{\phi(z_p)}{1-p}$, where $\phi$ is `scipy.stats.norm.pdf`.
5. Drop $m$ only when the task says zero mean or a short horizon.

**Limitations and cautions:** The normal model understates tail losses when returns are heavy-tailed; at 99% and above it is usually below the historical and EVT estimates.

**Double check:**
- At 99% the ratio $(\mathrm{VaR}_p - m)/s$ equals 2.326; if it does not, the quantile or the standard deviation is wrong, so recompute both.
- ES exceeds VaR; if it does not, the density term was divided by $p$ instead of $1-p$, so fix the denominator.

## Topic 3: Peaks over threshold with a generalized Pareto fit

**Purpose:** Estimate tail VaR and ES from a generalized Pareto distribution (GPD) fitted to the losses above a high threshold.

**When to use:** The task names peaks over threshold (POT), a GPD tail, or EVT VaR and ES. For a tail index only, use Topic 4; for losses standardized by a GARCH volatility, apply this topic inside Topic 5.

**Constraints:**
- The GPD is fitted to the **excesses** $y_i = L_i - u$ over the threshold $u$, not to the exceedances $L_i$ themselves.
- The VaR formula uses the ratio $n/N_u$ (all observations over the number above the threshold), which is greater than 1.

**How to implement:**
1. Check the inputs and print them: the losses, the threshold rule (for example the 95% quantile of the losses), the sample size $n$ and the confidence levels.
2. Set the threshold $u$ by the task's rule, using the same quantile method as Topic 1 unless the task names another.
3. Collect the excesses $y_i = L_i - u$ for every $L_i > u$, and their number $N_u$.
4. Fit the GPD to the excesses with the location fixed at zero: `scipy.stats.genpareto.fit(y, floc=0)` returns the shape $\xi$, the location 0 and the scale $\beta$.
5. Compute the VaR by inverting the fitted tail, scaled by the share of the sample above the threshold: $\mathrm{VaR}_p = u + \frac{\beta}{\xi}\left[\left(\frac{n}{N_u}(1-p)\right)^{-\xi} - 1\right]$.
6. Compute the ES from the same fit, valid for $\xi < 1$: $\mathrm{ES}_p = \frac{\mathrm{VaR}_p}{1-\xi} + \frac{\beta - \xi u}{1-\xi}$.

**Limitations and cautions:**
- Fitting the exceedances instead of the excesses puts the location at the threshold and inflates the scale.
- Writing $N_u/n$ instead of $n/N_u$ inflates the VaR several-fold.
- With few exceedances (a few dozen) the shape estimate is noisy, and $\xi \ge 1$ makes the ES infinite.
- For $\xi$ near zero the VaR formula loses precision; its limit is $u - \beta \ln\left(\frac{n}{N_u}(1-p)\right)$.

**Double check:**
- The POT VaR at a level inside the sample is close to the historical VaR at the same level; if it is far off, check the excesses and the $n/N_u$ ratio first, then refit.
- $\xi < 1$ before reporting an ES; otherwise report that the ES does not exist under the fit, or use a higher threshold if the task allows.

## Topic 4: Hill tail index

**Purpose:** Estimate the tail index $\xi$ of a heavy-tailed loss distribution from its largest order statistics.

**When to use:** The task asks for a Hill estimator or a tail index. For VaR and ES from a fitted tail use Topic 3.

**How to implement:**
1. Check the inputs and print them: the losses (positive values only), the rule for $k$, and which order statistic is the threshold.
2. Sort the losses in descending order: $L_{(1)} \ge L_{(2)} \ge \dots$.
3. Choose $k$ by the task's rule, for example $\lfloor\sqrt{n}\rfloor$, a fixed tail fraction, the POT exceedance count, or a stable region of the Hill plot.
4. Compute the estimator as the mean log excess of the $k$ largest losses over the threshold order statistic: $\hat{\xi} = \frac{1}{k}\sum_{i=1}^{k} \ln L_{(i)} - \ln L_{\mathrm{thr}}$, with $L_{\mathrm{thr}} = L_{(k+1)}$ or $L_{(k)}$ as the task writes it.

**Limitations and cautions:** The estimate depends on both $k$ and the threshold convention; it is defined only for positive losses.

**Double check:** For equity returns $\hat{\xi}$ is usually between 0.1 and 0.5; a negative value or one above 1 points to returns used instead of losses or to non-positive values in the logarithm, so recheck the sign and the selection, then recompute.

## Topic 5: GARCH-filtered EVT

**Purpose:** Combine a GARCH conditional volatility with an EVT tail fitted to standardized losses, to get VaR and ES that react to current volatility.

**When to use:** The task asks for GARCH-EVT, filtered historical simulation with an EVT tail, or conditional EVT VaR.

**Constraints:** The volatility that scales the standardized quantile refers to the day the task's VaR is about.

**How to implement:**
1. Check the inputs and print them: the return series and its scaling (percent or decimal), the GARCH specification the task gives, the threshold rule and the confidence levels.
2. Fit the GARCH model as the GARCH entry describes, and take the standardized residuals $\varepsilon_t/\sigma_t$.
3. Form the standardized losses $z_t = -\varepsilon_t/\sigma_t$.
4. Apply Topic 3 to $z_t$, with a threshold quantile chosen for $z_t$, to get $\mathrm{VaR}^z_p$ and $\mathrm{ES}^z_p$.
5. Choose the volatility $\sigma^*$: the last in-sample conditional volatility for a figure about the last observed day, or the one-step-ahead forecast for a figure about the next day.
6. Scale to the loss level: $\mathrm{VaR}_p = \sigma^* \, \mathrm{VaR}^z_p$ and $\mathrm{ES}_p = \sigma^* \, \mathrm{ES}^z_p$, converting back to decimal units if the model was fitted on percent returns.

**Limitations and cautions:** The result inherits any misspecification of the GARCH model; percent-scaled fits return volatilities 100 times the decimal ones.

**Double check:** The standardized 99% VaR is usually between 2 and 4 (the standard normal value is 2.33); if it is outside, check the sign of $z_t$ and the threshold, then refit.

## Topic 6: Reporting choices and result keys

**Purpose:** Report the conventions behind each number so the result can be compared with the task's definitions.

**When to use:** Any task in this card whose output records VaR or ES by method and level.

**How to implement:**
1. Print each choice made (quantile method, standard-deviation divisor, ES definition, Hill $k$ and threshold, GARCH-EVT volatility) next to the words of the task that fixed it.
2. Numbers inside result keys (a confidence level, a horizon) take the form the task's own examples show; the output contract in the first message lists those examples, `output_contract.key(template, level=..., method=...)` builds the key in that form, and the submission check flags a key that writes the number another way. As soon as the keys are built, print the level-to-key mapping and compare it with the task's example keys.
3. Write method names inside result keys in full, exactly as the task's output section lists them.

**Limitations and cautions:** An output key that differs from the task's list in one character is a missing result for whoever reads the file, however correct its value.

**Double check:** Every key in the output matches the task's list character for character; if not, rename the key and rewrite the file.

Rolling backtests and coverage tests: see the VaR backtest card.
