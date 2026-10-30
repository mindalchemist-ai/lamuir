# Variance inflation factor (VIF) from auxiliary OLS regressions
The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input or convention, follow the task description.

The VIF of regressor $x_j$ measures how well the other regressors explain it: regress $x_j$ on all other regressors plus an intercept, take the centred $R^2_j$, and $\mathrm{VIF}_j = 1/(1-R^2_j)$. The usual error is computing $R^2$ from the wrong residual quantity.

1. Input: the regressor matrix $X$ ($T$ rows, $p$ columns, no constant column), rows aligned, no missing values.
2. For each column $j$:
   1. Take $y = x_j$ and $Z = [1, X_{-j}]$, an intercept column followed by the other regressors.
   2. Fit the least-squares coefficients $\hat{b}$ of $y$ on $Z$; with `numpy.linalg.lstsq` take only the first returned element, the coefficients.
   3. Form the residuals $e = y - Z\hat{b}$ (length $T$).
   4. Compute $\mathrm{SSR} = \sum e^2$ and the centred $\mathrm{SST} = \sum (y - \bar{y})^2$.
   5. Compute $R^2_j = 1 - \mathrm{SSR}/\mathrm{SST}$ and $\mathrm{VIF}_j = 1/(1 - R^2_j)$, infinite when $R^2_j = 1$.
3. Cross-checks (to verify, not to replace the task's method): the R-squared of `statsmodels` OLS of $y$ on the other regressors with a constant added; and $\mathrm{VIF}_j$ equals the $j$-th diagonal element of the inverse of the correlation matrix of $X$.

Note on `np.linalg.lstsq`: its second output is already the residual sum of squares (an array of shape (1,) for a 1-D target, empty if the system is rank-deficient), not the residual vector. Squaring it or summing its square gives a meaningless number that is far too small and pushes $R^2$ toward 1.

Checks:
- $1 \le \mathrm{VIF}_j$ for every j, and $0 \le R^2_j < 1$.
- VIF from step 2 matches the inverse-correlation-matrix diagonal to about 1e-8 relative.
- Pairwise correlations of the regressors are consistent: if all $|\rho| $ are small, no VIF should be large.
