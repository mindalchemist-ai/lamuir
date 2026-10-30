# Calibrating mean-reverting processes: lag pairs, parameter maps, half-life units, simulation

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input, setting or convention, follow the task description.

Use this note when a task fits an Ornstein-Uhlenbeck (OU) process, with or without jumps, to a time series and then simulates it. Each block gives a short skeleton and asserts that catch the common silent errors. When the task fixes a formula, implement that formula; the asserts still apply.

## 1. Build lag pairs as plain arrays

A regression of x[t+1] on x[t] needs the two shifted copies paired by position. Pandas arithmetic pairs values by index label, so subtracting two slices of one Series lines up the same dates and gives residuals near zero without any error. Convert to NumPy first.

1. Keep the finite values $v_0, \dots, v_n$ in time order.
2. Pairs: $x_{\mathrm{prev}} = v_0, \dots, v_{n-1}$ and $x_{\mathrm{next}} = v_1, \dots, v_n$.
3. Regress $x_{\mathrm{next}}$ on $x_{\mathrm{prev}}$ with a constant: $x_{\mathrm{next}} = a + b\, x_{\mathrm{prev}} + e$; there are $n$ residuals.
4. Alignment check: the residual standard deviation divided by the standard deviation of the differences $v_{t+1} - v_t$ lies between about 0.3 and 1; far below 0.3 means the pairs were misaligned.

## 2. Two maps from regression coefficients to (kappa, theta, sigma)

The same data give either a levels slope b or a differences slope beta = b - 1, with the same intercept a. The exact map inverts the OU transition; the Euler (plug-in) map treats the step as small. They agree when kappa*dt is small and differ otherwise.

With $s$ the residual standard deviation (divisor $n-1$) and step $\Delta t$:

1. Exact OU discretization: $\kappa = -\ln b / \Delta t$, $\theta = a/(1-b)$, $\sigma = s\sqrt{2\kappa/(1-b^2)}$, using $1 - b^2 = 1 - e^{-2\kappa\Delta t}$; valid for $0 < b < 1$.
2. Euler discretization: with $\beta = b - 1$, $\kappa = -\beta/\Delta t$, $\mu = -a/\beta$, $\sigma = s/\sqrt{\Delta t}$.
3. The long-run mean is the same in both: $\theta = \mu$.

If a task says "sigma from the residual variance" without a formula, the two readings are sigma_exact (residual variance equals the exact transition variance) and sigma_euler (residual variance equals sigma**2 * dt). The residual degrees of freedom (ddof=1 on residuals, or n - 2 as in fit.mse_resid) is a separate choice the task may fix.

## 3. Half-life in the unit its name states

kappa carries the time unit of dt. ln 2 / kappa is in that unit (years if dt is in years). In observation periods it is ln 2 / (kappa * dt); in days multiply periods by the period length in days (1/3 for 8-hour periods).

1. Half-life in time units: $\ln 2/\kappa$; in periods: $\ln 2/(\kappa\Delta t)$; in days: periods times the period length in days.
2. Check: the half-life in periods is close to $\ln 2/(-\ln \rho_1)$, where $\rho_1$ is the lag-one autocorrelation of the series (the logarithms of the two agree within about 1).

A half-life far below one period while the lag-1 autocorrelation is clearly positive means kappa (per year) was divided into ln 2 without dt. The stationary standard deviation is sigma / sqrt(2 * kappa); with jumps add lambda * (mu_J**2 + sigma_J**2) to sigma**2.

## 4. Simulation

The exact transition draws one normal per path per step; Euler adds drift, diffusion and the step's jumps. Jumps per step are Poisson(lambda * dt); the sum of n normal sizes is normal with mean n * mu_J and sd sqrt(n) * sigma_J.

Exact OU simulation over steps of $\Delta t$: the step standard deviation is $\sqrt{\sigma^2(1 - e^{-2\kappa\Delta t})/(2\kappa)}$, and each step updates all paths at once by $x \leftarrow \theta + (x - \theta)e^{-\kappa\Delta t} + \text{(step sd)}\cdot Z$.

## 5. Comparing analytical and simulated moments

Put the analytical and simulated values for each horizon in one table with named columns, write it, and compute every
summary error from those columns in the cell that writes the summary. Pairing parallel lists with zip() depends on
argument order, and one swapped list divides a mean gap by a variance without any error. A summary value set in an
earlier cell and later recomputed differently in a diagnostic must be replaced before it is written.

Write the moment table (maturity, analytic and simulated mean, analytic and simulated variance) first, then read it back and compute the summary errors from the file by column name: the largest relative mean error and the largest relative variance error. Build the summary in the same cell that writes it, so that the summary always matches the table on disk.

## Task wording -> API arguments

Seeding: "np.random.seed(s)" sets the legacy global generator used by np.random.normal/poisson; "default_rng(s)" creates a separate Generator. They give different streams, and the order of draws inside the loop (normals before or after Poisson counts) changes every path.

statsmodels adfuller: regression "c" constant, "ct" constant and trend, "n" none; autolag "AIC"/"BIC" searches lags up to maxlag, autolag=None uses exactly maxlag. Wording "with drift/intercept" maps to "c".

Moments: np.std defaults to ddof=0, pandas .std() to ddof=1. scipy.stats.skew and kurtosis default to bias=True; "unbiased" means bias=False, which equals pandas .skew()/.kurt(). kurtosis fisher=True is excess kurtosis.

Autocorrelation: Series.autocorr(k) is the Pearson correlation of the overlapping pairs; statsmodels acf uses the full-sample mean and variance. Both are "lag-k autocorrelation"; they differ in short or trending samples.

np.percentile default method "linear" interpolates; "lower"/"higher"/"nearest" pick order statistics.

pd.to_datetime(ms, unit="ms", utc=True) then .dt.floor("s") truncates sub-second jitter; round("s") rounds it.

## Sources

Uhlenbeck and Ornstein (1930), Phys. Rev. 36, 823. Vasicek (1977), J. Financial Economics 5, 177, sec. 2. Gillespie (1996), Phys. Rev. E 54, 2084 (exact OU update). Glasserman, Monte Carlo Methods in Financial Engineering (2004), sec. 3.3 (OU) and 3.5 (jump processes). Tsay, Analysis of Financial Time Series, 3rd ed., ch. 2 (AR(1), ACF, unit-root tests). Docs: statsmodels adfuller and acf; SciPy stats.skew/kurtosis; NumPy random (legacy seeding vs Generator) and percentile.
