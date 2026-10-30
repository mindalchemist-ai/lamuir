# SVI smile fitting and Dupire local volatility from the fitted slices: slice fit, expiry selection, Gatheral's local-volatility formula and the local-volatility grid

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, an input or a convention, follow the task description.

Read the topics relevant to the task; a task usually needs several of them.

## Topic 1: Fitting one SVI slice

**Purpose:** Fit a smooth, analytically differentiable total-variance smile to the quotes of one expiry.

**When to use:** The task fits SVI (stochastic volatility inspired) smiles, or needs smooth smile derivatives for local volatility.

**Constraints:**
- Fit in total variance $w = \sigma_{\mathrm{BS}}^2 T$ against forward log-moneyness $k = \ln(K/F_T)$, $F_T = S_0 e^{(r-q)T}$.
- Slice: $w(k) = a + b\left[\rho(k-m) + \sqrt{(k-m)^2+s^2}\right]$. The width $s$ is the parameter usually written $\sigma$; output column names follow the task.
- Lee's bound: $b(1+|\rho|) \le 2$.

**How to implement:**
1. Check the inputs and print them per expiry: $T$, $F_T$, the quoted $k$ range, the number of quotes and $\min w$, $\max w$.
2. With `scipy.optimize.minimize` on all five parameters, use a restricted model with strictly positive lower bounds, for example $a \in [10^{-6}, \max w]$, $b \in [10^{-4}, 1]$, $\rho \in [-0.999, 0.999]$, $m \in [\min k, \max k]$, $s \in [10^{-3}, 1]$. These bounds are a modelling choice, not general SVI conditions.
3. Objective: residuals divided by the slice level $\overline{w}$ (total variance is about $10^{-4}$ for a few days, and an unscaled objective stops early).
4. Starts: $a$ near $\min w$, $b$ near $(\max w - \min w)/\mathrm{range}(k)$, $m$ at the $k$ of the smallest $w$, $s$ near $\mathrm{range}(k)/4$; try several starts and keep the lowest objective.
5. Print each slice's error in volatility units, $\mathrm{RMSE}\left(\sqrt{w_{\mathrm{SVI}}/T} - \sigma_{\mathrm{obs}}\right)$, and its parameters.

**Implementation tips:** Analytic derivatives in $k$: $w_k = b\left[\rho + \frac{k-m}{\sqrt{(k-m)^2+s^2}}\right]$ and $w_{kk} = \frac{b\,s^2}{\left((k-m)^2+s^2\right)^{3/2}}$. In strike, $w_K = w_k/K$ and $w_{KK} = (w_{kk}-w_k)/K^2$.

**Limitations and cautions:** $a$ ending on its lower bound or $\rho$ near $\pm 0.999$ is common for equity smiles and acceptable; $b$ or $s$ ending on its lower bound means a collapsed fit (a flat or kinked slice): refit from other starts. Common mistakes: spot moneyness $\ln(K/S_0)$ instead of $\ln(K/F_T)$ shifts the smile by $(r-q)T$; fitting $\sigma_{\mathrm{BS}}^2$ without the factor $T$; reporting an error in total variance where the task asks for it in volatility.

**Double check:** The volatility-unit RMSE of each slice meets the task's tolerance, and $b$, $s$ are off their lower bounds.

## Topic 2: Selecting the expiries for the surface

**Purpose:** Choose well-fitted expiries spread over the term structure so that the time derivative of total variance is stable.

**When to use:** The task asks for a given number of expiries, or builds a local-volatility surface from several slices.

**Constraints:**
- Fit EVERY candidate expiry (Topic 1), for screening; select exactly as many expiries as the task asks for, only among those whose fit meets the task's tolerance and whose $b$ and $s$ are off their lower bounds.
- Unless the task sets its own maturity range, select only expiries at least about one month away ($T \ge 1/12$): a slice a few days from expiry has total variance near zero, so $\partial_T w$ next to it is dominated by noise and gives local volatilities many times the implied ones and negative forward variances.

**How to implement:**
1. Fit and print all candidates in one cell (Topic 1, step 5).
2. Place as many target maturities as the task asks for evenly between the shortest and the longest eligible $T$, and take the eligible expiry nearest to each target, without repeats.
3. If the expiry picked for the shortest target has the largest fit error of the candidates or a nearly flat slice ($b$ close to its lower bound), take the next eligible expiry instead: one badly fitted short slice spoils $\partial_T w$ for every strike.
4. Print the $T$ of every selected expiry; if one is under the minimum, replace it with the next eligible expiry.
5. Store the selected list once and use it for every output and every count.

**Limitations and cautions:** Expiries a few days apart give a noisy $\partial_T w$ and can produce negative forward variances.

**Double check:** The selected list has the requested length, every $T \ge 1/12$ (or inside the task's range), and the same list feeds every output file.

## Topic 3: Local volatility from total variance (Gatheral's form)

**Purpose:** Turn the fitted slices into Dupire local volatility at any $(k, T)$.

**When to use:** The task asks for Dupire local volatility from an implied-volatility surface.

**Constraints:**
- $\sigma_{\mathrm{loc}}^2(k,T) = \frac{\partial_T w(k,T)}{g(k,T)}$, with $g = \left(1 - \frac{k w_k}{2w}\right)^2 - \frac{w_k^2}{4}\left(\frac{1}{w} + \frac14\right) + \frac{w_{kk}}{2}$.
- $\partial_T w$ is taken at FIXED $k$ (not fixed strike) from the fitted slices; interpolate between expiries in total variance at fixed $k$, not in implied volatility.
- A local volatility is never set equal to an implied volatility, not even "as an approximation": they differ except on a flat surface.

**How to implement:**
1. Write ONE function `local_vol(k, T)` that evaluates the formula at any point, and call it for every local volatility the outputs report: each grid node, the at-the-money value of each expiry ($k = 0$), any summary value and the flat-volatility test.
2. $\partial_T w$ with the difference scheme the task names (for a forward difference, $(w(k;T_{i+1}) - w(k;T_i))/(T_{i+1}-T_i)$); for the last expiry use what the task says, otherwise a backward difference.
3. $w_k$ and $w_{kk}$ are analytic (Topic 1), so they exist at the ends of the strike grid too; do not use them as strike derivatives.
4. Flat check: a constant implied volatility $\sigma$ gives $w = \sigma^2 T$, $g = 1$, $\partial_T w = \sigma^2$, so the function must return $\sigma$; run the same function on such a surface. Its local volatility must come out of `local_vol` (an error of exactly 0 because the input volatility was copied tests nothing). Build the flat-check grid in the moneyness its output column reports: take the ratios $K/S_0$ with `numpy.linspace`, then $K = S_0 \cdot$ ratio, then $k = \ln(K/F_T)$ for each expiry; a grid built in $K/F_T$ and written as $K/S_0$ drifts outward by $F_T/S_0$, more at the longer expiries. After writing the file, read it back and assert that the minimum and maximum of that ratio column equal the endpoints you chose.

**Implementation tips:** This equals the call-price Dupire formula with dividend yield; if the task gives the price form, either is fine as long as derivatives are consistent.

**Limitations and cautions:** $g(k) < 0$ (butterfly arbitrage in the slice) or $\partial_T w < 0$ (calendar arbitrage at that $k$) makes the local variance negative. Diagnose at that point: check the fit of that slice, the calendar order at that $k$, and the grid.

**Double check:** The flat check returns the input $\sigma$; at-the-money local volatilities are of the same order as the implied ones, not many times larger.

## Topic 4: Building and writing the local-volatility grid

**Purpose:** Evaluate local volatility on a strike-maturity grid and write it without losing or corrupting nodes.

**When to use:** The task asks for a local-volatility surface, grid or table.

**Constraints:**
- A node where the local variance is negative or not finite is a finding to diagnose (Topic 3), not a row to delete or fill. When the grid is discretionary, such a node means the grid reaches beyond the quoted strikes: rebuild it inside the log-moneyness range quoted in every selected expiry (the largest per-expiry minimum to the smallest per-expiry maximum) before writing. Keep a non-finite node only when the task fixes the grid, and then write what the task says there.
- State which moneyness a strike grid is built in ($K/F_T$ or $K/S_0$) and convert when an output column uses the other one.

**How to implement:**
1. Build every strike grid, the diagnostic flat-volatility grid included, in the moneyness its output column reports: for a column that is a strike-to-spot ratio, take the ratios $K/S_0$ with `numpy.linspace` and set $K = S_0 \cdot$ ratio, then compute $k = \ln(K/F_T)$ from $K$. A grid built in $K/F_T$ and written as $K/S_0$ moves outward by $F_T/S_0$ at every expiry, so its written endpoints leave the range you chose. `numpy.linspace` keeps the endpoints exact and inside a stated range (repeated addition of a step can end at 1.2000000000000004).
2. Before writing the surface, check that total variance increases with $T$ at every grid $k$ between neighbouring selected expiries.
3. Where it does not, the grid reaches beyond the strikes the slices were fitted on: when the grid is discretionary, shrink it to the log-moneyness range quoted in every selected expiry and rebuild; if extrapolation is required, state and validate it.
4. Write categorical values (option type, side) with the codes the input data use unless the task names others, also after converting puts to calls by parity (keep each quote's original type code, for example `C` / `P`).
5. Write several output files per cell once their values are computed: the budget of replies is small.

**Limitations and cautions:** Outside the quoted strikes the SVI wings are extrapolation; local volatility there depends on the fitted wing slopes more than on data.

**Double check:** The number of grid rows equals the number of nodes built; no node shows a negative or `nan` local volatility without a diagnosis printed for it; the minimum and maximum of every written moneyness column equal the endpoints you chose for that grid.

References: Gatheral (2004), A parsimonious arbitrage-free implied volatility parameterization, Global Derivatives; Gatheral (2006), The Volatility Surface, Wiley, ch. 1-3; Gatheral and Jacquier (2014), Arbitrage-free SVI volatility surfaces, Quantitative Finance 14(1); Lee (2004), The moment formula for implied volatility at extreme strikes, Mathematical Finance 14(3); Dupire (1994), Pricing with a smile, Risk 7(1).
