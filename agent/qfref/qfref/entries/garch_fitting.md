# GARCH fitting: numerical scale, optimizer termination and reported units

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input, setting or convention, follow the task description.

Use this implementation note with the conditional-volatility formulas. Preserve the specified return series, mean model, initialization, likelihood sample and parameter domain. Numerical scaling is optional only when the specification permits it; a native-unit fit requirement takes precedence.

## Recipe first (arch, daily returns)

Set `MEAN` to the mean model the task states (`"Zero"` or `"Constant"`). Do not silence warnings before the fit.

**A. The task leaves the estimation units open:** fit percent returns and convert back.

1. Fit `arch.arch_model(100 * r, vol="GARCH", mean=..., rescale=False).fit(disp="off")`; the default is GARCH(1,1).
2. Convert to decimal daily units: divide $\omega$ by $100^2$; $\alpha$ and $\beta$ are unchanged; divide the one-step variance forecast (`forecast(horizon=1, reindex=False).variance`, last row) by $100^2$ and the conditional volatility path by 100.
3. Apply the requested annualization only after returning to decimal daily units.

**B. The task fixes native units:** keep $r$ as given and maximize the Gaussian likelihood yourself.

1. Let $v$ be the sample variance of $r$ and write $\omega = v e^{\theta}$, so the optimizer works on $\theta$ and the scale of $\omega$ is never a problem.
2. Variance recursion: $h_1 = v$ and $h_t = \omega + \alpha r_{t-1}^2 + \beta h_{t-1}$.
3. Negative log-likelihood: $\tfrac12 \sum_t \left[\ln(2\pi h_t) + r_t^2 / h_t\right]$, set to a large penalty when $\alpha < 0$, $\beta < 0$ or $\alpha + \beta \ge 1$.
4. Minimize with Nelder-Mead (tight tolerances, for example $10^{-10}$, and a high iteration limit) from at least two starts, for example $(\alpha, \beta) = (0.05, 0.90)$ and $(0.10, 0.80)$ with $\theta = \ln(1 - \alpha - \beta)$; keep the start with the lower value.
5. Recover $\omega = v e^{\theta}$ with the fitted $\alpha$ and $\beta$.

After either: check that alpha and beta moved away from round starting values (such as 0.10 / 0.88 or 0.01 / 0.97), that `omega / (1 - alpha - beta)` is near the sample variance in the same units, and that persistence is below one. For many rolling-window refits, start each window from the previous window's estimate.

## Inputs and units

Before fitting, verify finite observations, date alignment, sample length and nonzero variation. Do not confuse raw portfolio returns, excess returns and model innovations. If a zero conditional mean is specified, fitting a constant mean is a different model.

When allowed, fitting small decimal returns on a percent scale can improve numerical conditioning. For a positive scale $c$ and $y_t=cr_t$, use the same transformed initialization:

$$
\mu_y=c\mu_r,\qquad \omega_y=c^2\omega_r,\qquad
h_{y,t}=c^2h_{r,t},\qquad \sigma_{y,t}=c\sigma_{r,t}.
$$

The dimensionless coefficients $\alpha,\beta$ stay unchanged. A percent-return fit has $c=100$; convert the intercept and variances back by $100^2$, and means/standard deviations by $100$. Report the factor actually applied, not a factor inferred from a parameter's size. Scaling data changes neither the return definition nor its observation clock.

For the same $n$ Gaussian likelihood observations, the reported log likelihood obeys:

$$
\ell_r=\ell_y+n\ln c.
$$

This comparison requires the same mean specification, transformed variance seed, innovation distribution, sample and likelihood normalization. Numerical optimizers need not return exactly equivalent parameter estimates after a scale change.

## Python arch scaling choices

In `arch_model`, `rescale=None` warns about poor scale without applying a change; `rescale=True` permits automatic power-of-ten scaling and the fitted result exposes `scale`; `rescale=False` disables that automatic adjustment/check. If scaling manually, track that factor and any automatic factor so conversion is applied once. Prefer one explicit scaling mechanism. An output-unit conversion does not retroactively change the units used for estimation.

## Fitting daily returns with arch

Daily decimal returns (of order 0.01) are badly scaled for arch's optimizer: it warns with a DataScaleWarning and can stop at or near its starting values (for example alpha 0.01, beta 0.97 exactly). Where the task leaves the estimation units open, one remedy is to fit on percentage returns, `arch_model(100 * r, ..., rescale=False)`, then convert back to the data's units before reporting or using the results: omega and every variance divided by $100^2$, volatilities divided by 100; alpha and beta are unit-free. Where the task fixes the units (for example native returns, no rescaling), keep them: pass `rescale=False`, try several feasible starting vectors through `fit(starting_values=...)`, tighten the optimizer tolerance if needed, and keep the start whose fit has the highest log-likelihood in those native units. A higher likelihood shows that an earlier fit was worse; it does not prove a global maximum. Estimates equal to round starting values are a lead to compare against other starts, not proof by themselves that the fit failed. In native daily units arch's optimizer can stay at every starting vector it is given, because omega is many orders of magnitude smaller than alpha and beta. Then reparameterize instead of rescaling the data: keep the returns in native units, write $\omega=\hat v\,e^{\theta}$ with $\hat v$ the sample variance, and maximize the Gaussian GARCH log-likelihood $-\tfrac12\sum_t(\ln 2\pi h_t+r_t^2/h_t)$ over $(\theta,\alpha,\beta)$ with scipy (for example Nelder–Mead from two or three starts), rejecting $\alpha<0$, $\beta<0$ or $\alpha+\beta\ge1$. Initialize $h_0$ as the task states; arch's default is a backcast, so a different $h_0$ moves the estimates slightly. Report $\omega$ in native units and confirm the log-likelihood is at least that of the arch result. Check that the reported omega/(1 - alpha - beta) equals the reported long-run variance in the same units.

## Diagnose an apparent fit

Do not silence warnings before a fit: arch's DataScaleWarning and convergence warnings are the first sign of a poorly scaled or failed optimization. A result object does not establish convergence. Inspect `convergence_flag`, `optimization_result`, finite objective value, admissible parameters and positive filtered variances. Compare the returned objective with its value at the actual starting vector. Repeated estimates at a library's starting grid, zero iterations or an almost unchanged vector are leads to inspect the stopping condition and scaling, not proof that the estimate is wrong. Initial grids are version-dependent; inspect the installed implementation instead of treating a remembered grid as a model identity.

When permitted, compare alternative feasible starts or scaled fits in common likelihood units. Do not select an infeasible point because its reported objective looks better, clip a result without refitting, substitute unconditional variance for a requested forecast, or change the prescribed estimator silently. A convergence flag alone does not prove a global optimum.

After fitting, keep filtered variance, the next-observation forecast and long-run variance separate. Their definitions and multi-step recursion are in the conditional-volatility entry. Validate all output units together, especially the intercept and long-run variance after a percent-scale fit.

## Sources

[arch model settings](https://arch.readthedocs.io/en/stable/univariate/introduction.html) and [result API](https://arch.readthedocs.io/en/stable/univariate/generated/arch.univariate.base.ARCHModelResult.html), scaling and optimizer diagnostics. The dimensional and likelihood identities follow directly by substituting $y=cr$ in the Gaussian conditional density. This is numerical implementation guidance, not a new volatility estimator.
