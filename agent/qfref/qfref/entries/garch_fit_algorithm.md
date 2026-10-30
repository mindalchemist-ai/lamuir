# Fitting a GARCH(1,1) with `arch`: units, convergence and conversion back

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input or convention, follow the task description.

## Algorithm

Inputs: daily decimal returns $r$; the mean model and distribution the task names (zero or constant mean; normal or Student t).

1. Units: if the task explicitly says to fit raw (unscaled) returns, fit $r$ (case 2); otherwise fit $100 r$ (case 1). Small decimal returns are not a reason for case 2: a fit on raw decimal returns often stops at its starting values.
2. Fit a GARCH(1,1) with `arch.arch_model(x, vol="GARCH", p=1, o=0, q=1, mean=..., dist=..., rescale=False)` and `.fit(disp="off")`.
3. Compare the fitted volatility parameters with the model's starting values (`res.model.volatility.starting_values` on the residuals); if they are equal, the optimizer did not move, so refit with case 1.
4. In case 1 convert back: divide $\omega$ and every variance by $100^2$, every volatility and the mean by 100; $\alpha$ and $\beta$ are unchanged.
5. Print $\omega$, $\alpha$, $\beta$, $\alpha + \beta$ and the mean conditional volatility in decimal units.

## Checks

1. $\alpha + \beta < 1$, and neither parameter equals its starting value.
2. In decimal units, $\omega$ is far below $10^{-3}$ and the daily conditional volatility is far below $0.1$.
3. Annualizing a daily volatility multiplies by $\sqrt{B}$ once; a quantity already in one-day units is not divided by $\sqrt{B}$ again.

## Topic: GARCH(1,1) by maximum likelihood without `arch`, reproducing its estimates

**Purpose:** Fit a GARCH(1,1) with `scipy.optimize.minimize` so that the parameters and conditional volatilities match what `arch.arch_model(...).fit()` would give.

**When to use:** The environment has no `arch` package (an import fails or the environment note says it is not installed) and the task asks for a GARCH(1,1) fit, conditional volatilities or GARCH-filtered quantities. When `arch` is installed, use it.

**Constraints:**
- Scale and mean as `arch` would: returns in percent (times 100) with the mean model the task names (zero mean: residuals are the returns; constant mean: subtract the fitted constant, estimated jointly).
- Variance recursion $h_t = \omega + \alpha \varepsilon_{t-1}^2 + \beta h_{t-1}$, started with the `arch` backcast for the unobserved lag: with $\tau = \min(75, T)$ and weights $w_i = 0.94^i / \sum_{j<\tau} 0.94^j$, $\mathrm{backcast} = \sum_{i=0}^{\tau-1} w_i \varepsilon_i^2$, and $h_1 = \omega + (\alpha + \beta)\,\mathrm{backcast}$. A start at the sample variance or at $\varepsilon_1^2$ gives different estimates.
- Normal log-likelihood $-\frac{1}{2}\sum_t \left(\ln 2\pi + \ln h_t + \varepsilon_t^2 / h_t\right)$, maximized subject to $\omega > 0$, $\alpha \ge 0$, $\beta \ge 0$, $\alpha + \beta < 1$.

**How to implement:**
1. Check the inputs and print them: the return series, its unit, the mean model, and the sample the task names for the fit.
2. Build the percent residuals and the backcast of the Constraints.
3. Minimize the negative log-likelihood with `scipy.optimize.minimize(method="SLSQP")`, bounds $\omega \in [10^{-6}, 10\,\mathrm{var}]$, $\alpha, \beta \in [0, 1]$, the inequality $1 - \alpha - \beta > 0$, and several starting points (for example $\alpha \in \{0.05, 0.1\}$, $\beta \in \{0.8, 0.9\}$, $\omega = \mathrm{var}(1 - \alpha - \beta)$); keep the lowest objective.
4. Conditional volatility in decimal units: $\sqrt{h_t} / 100$; standardized residuals $\varepsilon_t / \sqrt{h_t}$.
5. One-step-ahead variance, when the task needs the next day's volatility: $h_{T+1} = \omega + \alpha \varepsilon_T^2 + \beta h_T$.

**Limitations and cautions:** Fitting decimal returns directly is badly scaled and stops near the starting values; a different variance start or mean model shifts every estimate, and with it every GARCH-filtered quantile.

**Double check:** The optimizer reports success, $\alpha + \beta < 1$, and the parameters do not sit on a bound; the mean of $\varepsilon_t^2 / h_t$ is close to 1. If not, rescale, add starting points and refit.
