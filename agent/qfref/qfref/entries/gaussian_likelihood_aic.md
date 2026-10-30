# Gaussian likelihoods and information criteria for return models

Use this when a task fits several return models (random walk, drifted random walk or GBM, mean-reverting AR(1)/OU, jump mixtures) by likelihood and compares them with AIC or BIC. If the task text defines a formula, a parameter count or a variance estimator, the task text wins.

## Check first

1. **The variance term is part of the likelihood.** For n observations r_t with model mean m_t and variance s^2, the Gaussian negative log-likelihood is

   NLL = 0.5 * n * log(2 * pi) + 0.5 * n * log(s^2) + sum((r_t - m_t)^2) / (2 * s^2).

   Dropping 0.5 * n * log(s^2) (keeping only the squared-error sum) makes models with different variances incomparable and usually picks the wrong one. Dropping the constant 0.5 * n * log(2 * pi) is harmless only when every compared model drops it.
2. **Which variance estimate goes with which mean.** The maximum-likelihood variance is the mean of squared residuals around the fitted mean: for a zero-drift model (martingale, driftless random walk) it is mean(r^2) when the task leaves the variance to the likelihood; when the task prescribes a population (ddof=0) standard deviation for that model's sigma, use std(r, ddof=0) as written (it is centred on the sample mean) while the model's mean stays zero, and say so in a comment; for a drifted model it is mean((r - mean(r))^2), the ddof=0 variance. At the MLE the last term of the NLL equals n / 2. A task that prescribes a ddof=1 standard deviation for a parameter changes the plugged-in value; use it as written and say so.
3. **AIC = 2 k + 2 NLL and BIC = k log(n) + 2 NLL, with k the number of fitted parameters** (a variance counts; a parameter fixed in advance does not). When the task does not list k for each model, write the count used per model in a comment. All models must be scored on the same observations: a model whose likelihood conditions on a lagged value either adds the first observation's stationary likelihood or all models drop that observation. Print the number of terms each model's NLL sums and check they are all the same n: for AR(1)/OU that is n - 1 conditional residuals plus one stationary term for the first observation. A likelihood helper that sums over the full return series, reused with a residual mean or for the first observation alone, sums the wrong terms.
4. **Nested models.** When model B contains model A as a special case and both are fitted by maximum likelihood on the same data, B's NLL cannot be larger than A's (B can reproduce A). A larger NLL for the bigger model means a missing term, a different sample or a failed optimizer.
5. **AR(1) to OU mapping.** theta = -log(phi) / dt is defined only for 0 < phi < 1. When the fitted phi falls outside, the common choice is to clip phi into the interval (a small positive floor and a cap just below 1) and recompute the intercept and residuals with the clipped value, so that theta, the half-life and the stationary first term stay defined and the OU fit stays in the comparison. Leave the OU fit out of the comparison only when the task says so. State the choice in a comment.

1. Gaussian negative log-likelihood of residuals $e_1, \dots, e_n$ with variance $\sigma^2$: $\mathrm{NLL} = \tfrac{n}{2}\ln(2\pi) + \tfrac{n}{2}\ln \sigma^2 + \sum e_t^2 / (2\sigma^2)$.
2. AIC with $k$ estimated parameters: $\mathrm{AIC} = 2k + 2\,\mathrm{NLL}$.
3. Zero-drift model: residuals $r_t$, variance $\overline{r^2}$, $k = 1$. Drift model: residuals $r_t - \bar{r}$, variance their mean square, $k = 2$. The nested larger model never has a larger NLL; at the MLE variance the quadratic term equals $n/2$.
4. AR(1) exact likelihood: fit $\phi$ and the intercept $c$ by least squares on consecutive pairs; the $n-1$ conditional residuals have variance $s^2$, and the first observation is scored under the stationary law, with mean $c/(1-\phi)$ and variance $s^2/(1-\phi^2)$. The total NLL is the sum of both parts, with $k = 3$.
5. Compare models only when each is scored on the same $n$ observations.

## Sources

Hamilton, Time Series Analysis (1994), ch. 5 (maximum likelihood for Gaussian AR models, conditional and exact likelihood); Akaike (1974), IEEE Trans. Automatic Control 19(6), 716-723; Schwarz (1978), Annals of Statistics 6(2), 461-464; Burnham and Anderson, Model Selection and Multimodel Inference, 2nd ed. (2002), ch. 2 (counting parameters, same data for all models).
