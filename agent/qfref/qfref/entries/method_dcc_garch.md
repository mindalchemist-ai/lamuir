# Method: scalar DCC(1,1) correlations on GARCH residuals

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input, setting or convention, follow the task description.

When to use: the task instructions estimate dynamic conditional correlations (DCC) for several assets from univariate
GARCH fits.

Standardised residuals: column i of `Z` is `res_i.std_resid` from asset i's univariate fit (arch conventions entry,
section 4). They have no unit: a fit on percent returns gives the same `std_resid` as one on decimal returns, so do
not divide them by 100. Check before fitting the correlations:

Check before fitting the correlations: each column of $Z$ has a standard deviation near 1 (within about 0.2).
 `sigma[t]` is the vector of the assets' conditional volatilities in decimal units on day t.

With `z_t` the rows of `Z` (T x N): `Qbar = Z.T @ Z / T`, `Q_1 = Qbar`,
`Q_t = (1 - a - b) * Qbar + a * z_{t-1} z_{t-1}' + b * Q_{t-1}`, `R_t = diag(Q_t)^{-1/2} Q_t diag(Q_t)^{-1/2}`.
Which log-likelihood to report (all three have the same optimum `a, b`; the reported values differ by large amounts):

| Reported likelihood | Formula per day t | When |
|---|---|---|
| correlation component `L_C` (Engle 2002, second step) | `-0.5 * (log det R_t + z_t' R_t^{-1} z_t - z_t' z_t)` | a "DCC log-likelihood", "correlation-stage" or "second-step" likelihood with no formula given; this is the code below |
| correlation part without `z_t' z_t` | `-0.5 * (log det R_t + z_t' R_t^{-1} z_t)` | only when the task writes this formula |
| full (joint) log-likelihood | `-0.5 * (N log 2pi + 2 log det D_t + log det R_t + z_t' R_t^{-1} z_t)`, `D_t = diag(sigma_t)` | "total", "joint" or "full" log-likelihood, or a sum of the GARCH and correlation stages |


Estimation of the scalar DCC(1,1) parameters $(a, b)$:

1. $\bar{Q} = Z^{\top}Z/T$ and $Q_1 = \bar{Q}$; for $t > 1$, $Q_t = (1 - a - b)\bar{Q} + a\, z_{t-1} z_{t-1}^{\top} + b\, Q_{t-1}$.
2. $R_t = \operatorname{diag}(Q_t)^{-1/2} Q_t \operatorname{diag}(Q_t)^{-1/2}$.
3. Correlation-component log-likelihood (Engle 2002, second step): $\sum_t -\tfrac12\left(\ln\det R_t + z_t^{\top} R_t^{-1} z_t - z_t^{\top} z_t\right)$, using a stable log-determinant (`numpy.linalg.slogdet`) and a linear solve rather than an explicit inverse.
4. Minimize the negative log-likelihood with bounds $a, b \in [10^{-6}, 0.9999]$ (for example L-BFGS-B from $(0.05, 0.93)$), returning a large finite penalty such as $10^{10}$ when $a + b \ge 0.9999$: an infinite or undefined value makes a gradient-based optimizer stop falsely.
5. Report the log-likelihood at the optimum, and confirm $a + b < 1$ and that the residual columns have standard deviation near 1. Before optimizing, check the quadratic form on one date: `q1 = z @ np.linalg.solve(R, z)`; with a Cholesky factor `L = np.linalg.cholesky(R)` (lower), `y = scipy.linalg.solve_triangular(L, z, lower=True)` and `q2 = y @ y`; assert `np.isclose(q1, q2)`. Solving with `L.T` instead of `L` gives $z^\top R^{-2} z$, not $z^\top R^{-1} z$.

Notes:
- Use the optimizer and starting values the task instructions name; the ones above are an example.
- Keep the objective finite everywhere the optimizer may step: return a large number such as `1e10` outside the region, not `inf` or `nan`; then check that the fit reports success and moved from the starting values.
- Report the likelihood at the optimum, in the form chosen from the table; dropping `z_t' z_t` shifts it by about `-T * N / 2`.
- Portfolio volatility on day t: `ws = sigma[t] * w`, `sigma_p[t] = np.sqrt(ws @ R_t @ ws)`; portfolio return `r @ w`
  from the same return series the volatilities were fitted on.
