# First passage of drifted Brownian motion and GBM: hitting probabilities, first-passage times, running extremes with the terminal value, Brownian-bridge correction and Monte Carlo

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input, setting or convention, follow the task description.

Read the topics relevant to the task; a task usually needs several of them.

## Topic 1: Probability that a level is reached by time T

**Purpose:** Compute the probability that the running maximum of a drifted Brownian motion (or GBM) reaches an upper level, or the running minimum a lower level, by a horizon $T$.

**When to use:** The task asks for the probability of hitting, touching or crossing a barrier, or for the distribution of the running maximum or minimum, under constant drift and volatility with continuous monitoring. For the time of the first hit use Topic 2; with the terminal value as well use Topic 3; for discrete monitoring use Topic 6.

**Constraints:**
- Arithmetic Brownian motion $X_t = x_0 + \mu t + \sigma W_t$ with constant $\mu$ and $\sigma > 0$. For continuous paths "reaches", "touches" and "crosses" are the same event; a start at or beyond the level is a hit at time 0.
- GBM $S_t = S_0 \exp(\nu t + \sigma W_t)$ uses the log drift $\nu = m - \sigma^2/2$, where $m$ is the drift of $dS/S$ ($r - q$ under the risk-neutral measure); then $X = \ln S$, $x_0 = \ln S_0$, $\mu = \nu$ and the level is $\ln H$. Keep $m$ and $\nu$ as two named inputs: subtracting $\sigma^2/2$ from a drift that is already $\nu$ changes the model.
- Times are in years, in the same unit as $\mu$ and $\sigma^2$; $\sigma$ of 30% is 0.30.

**How to implement:**
1. Check the inputs and print them: $x_0$ (or $S_0$), the level, $\mu$ or $m$ and which one it is, $\sigma$, the horizons, and whether monitoring is continuous.
2. Distance to the level $a = |b - x_0| > 0$, and the drift towards the level $\theta = \mu$ for an upper level, $\theta = -\mu$ for a lower level (for GBM, $a = |\ln(H/S_0)|$ and $\theta = \pm\nu$).
3. Hitting probability by $t$: $P(\tau \le t) = \Phi\left(\frac{\theta t - a}{\sigma\sqrt{t}}\right) + e^{2\theta a/\sigma^2}\, \Phi\left(\frac{-\theta t - a}{\sigma\sqrt{t}}\right)$. Evaluate the second term as $\exp(2\theta a/\sigma^2 + \ln\Phi(\cdot))$ (`scipy.stats.norm.logcdf`) when $\theta a/\sigma^2$ is large.
4. Upper level: $P(\max_{s \le T} X_s \ge b) = P(\tau_b \le T)$. Lower level: apply the same formula to $-X$ (levels and drift negated).
5. With $\mu = 0$: $P(\tau \le t) = 2\Phi(-a/(\sigma\sqrt{t}))$, twice the terminal probability (reflection principle).

**Limitations and cautions:**
- Using $m$ instead of $\nu$, or the price distance $H - S_0$ instead of $\ln(H/S_0)$, are the common GBM errors; so is the wrong sign of $\theta$ for a lower level.
- The terminal probability $P(X_T \ge b)$ is not the hitting probability.
- Exit from a corridor (two levels), jumps, stochastic or time-varying volatility and mean reversion need other formulas or simulation.

**Double check:**
- Probabilities lie in $[0, 1]$ and do not decrease as $T$ grows.
- "Increases with the barrier" means as the level rises in numeric value with everything else fixed: $P(\max \ge H)$ does not increase as $H$ rises, and $P(\min \le L)$ does not decrease as $L$ rises. Sort the levels in increasing numeric order before computing any monotonicity flag, and allow ties (equal probabilities at extreme levels still satisfy "does not decrease"). Compute each flag from the probability column itself (sorted by the level, then `numpy.all(numpy.diff(p) >= 0)` or `<= 0`), not from the signed log distance $a$, whose sign differs between up and down levels. If a flag fails, recheck the sorting and the sign of $\theta$.

## Topic 2: First-passage time distribution and moments

**Purpose:** Give the density, the probability of ever hitting, and the moments of the first-passage time $\tau$.

**When to use:** The task asks for the density, mean, variance, quantiles or empirical distribution of the first time a level is hit.

**Constraints:** $\theta$ and $a$ are those of Topic 1, step 2.

**How to implement:**
1. Check the inputs: $a$, $\theta$, $\sigma$ and the horizon.
2. Density for $t > 0$: $f(t) = \frac{a}{\sigma\sqrt{2\pi t^3}} \exp\left(-\frac{(a - \theta t)^2}{2\sigma^2 t}\right)$.
3. Probability of ever hitting: 1 for $\theta \ge 0$; $\exp(-2|\theta| a/\sigma^2)$ for $\theta < 0$. For GBM: $\min(1, (H/S_0)^{2\nu/\sigma^2})$.
4. For $\theta > 0$, $\tau$ is inverse Gaussian with mean $a/\theta$, shape $a^2/\sigma^2$ and variance $a\sigma^2/\theta^3$. For $\theta < 0$, conditional on hitting, $\tau$ has the same law with $|\theta|$. For $\theta = 0$, $\tau$ is finite but $E[\tau]$ is infinite.
5. When $E[\tau]$ is not finite, report what the task defines: $P(\tau \le T)$, $E[\tau \mid \tau \le T] = \int_0^T t f(t)\,dt / P(\tau \le T)$, or $E[\min(\tau, T)] = \int_0^T P(\tau > t)\,dt$.

**Limitations and cautions:** $f$ integrates to the probability of ever hitting, so it is a defective density for $\theta < 0$; a quantile $q$ of $\tau$ exists only for $q$ below that probability (within the horizon, $q \le P(\tau \le T)$).

**Double check:** $\int_0^T f(t)\,dt$ equals $P(\tau \le T)$ of Topic 1 (numerical integration); if not, $a$ or $\theta$ differs between the two.

## Topic 3: Running maximum or minimum jointly with the terminal value

**Purpose:** Compute joint probabilities of the running maximum (or minimum) and the terminal value, such as $P(M_T \le m, X_T \le x)$.

**When to use:** The task asks for a probability that involves both the terminal value and the running maximum or minimum (reflection principle), such as the probability of ending below one level while never rising above another.

**Constraints:** All levels are shifted to the start and, for GBM, mapped to logs: $m' = m - x_0$, $l' = l - x_0$, $y = x - x_0$, $s = \sigma\sqrt{T}$, with the log drift $\mu = \nu$.

**How to implement:**
1. Check the inputs and print them: the event in words (which extreme, which inequality for each variable), $m'$ or $l'$, $y$, $\mu$, $\sigma$, $T$.
2. For $m' \ge 0$ and $y \le m'$:
   1. $P(M_T \ge m, X_T \le x) = e^{2\mu m'/\sigma^2}\, \Phi\left(\frac{y - 2m' - \mu T}{s}\right)$.
   2. $P(M_T \le m, X_T \le x) = \Phi\left(\frac{y - \mu T}{s}\right) - e^{2\mu m'/\sigma^2}\, \Phi\left(\frac{y - 2m' - \mu T}{s}\right)$.
   3. $P(M_T \le m) = \Phi\left(\frac{m' - \mu T}{s}\right) - e^{2\mu m'/\sigma^2}\, \Phi\left(\frac{-m' - \mu T}{s}\right) = 1 - P(\tau_m \le T)$.
3. Edge cases: for $P(M_T \le m, X_T \le x)$, replace $y$ by $m'$ when $y > m'$, and the probability is 0 when $m' < 0$. For $P(M_T \ge m, X_T \le x)$: if $m' \le 0$ it is $\Phi((y - \mu T)/s)$; if $m' > 0$ and $y > m'$ it is $e^{2\mu m'/\sigma^2}\Phi((-m' - \mu T)/s) + \Phi((y - \mu T)/s) - \Phi((m' - \mu T)/s)$.
4. Minimum, for $l' \le 0$ and $y \ge l'$: $P(L_T \ge l, X_T \ge x) = \Phi\left(\frac{\mu T - y}{s}\right) - e^{2\mu l'/\sigma^2}\, \Phi\left(\frac{2l' - y + \mu T}{s}\right)$; other minimum events follow from the maximum formulas applied to $-X$ with drift $-\mu$.
5. Joint density of $(M_T, X_T)$ at $(m', y)$ with $m' \ge \max(0, y)$: $\frac{2(2m' - y)}{\sigma^3\sqrt{2\pi T^3}} \exp\left(-\frac{(2m' - y)^2}{2\sigma^2 T} + \frac{\mu y}{\sigma^2} - \frac{\mu^2 T}{2\sigma^2}\right)$.

**Limitations and cautions:** The joint probability is not the product of the two marginals; the maximum and the terminal value are dependent.

**Double check:** $P(M_T \le m, X_T \le x) \le \min(P(M_T \le m), P(X_T \le x))$, and with $m'$ very large it tends to $P(X_T \le x) = \Phi((y - \mu T)/s)$; if not, recheck the shifts and the sign of the exponent.

## Topic 4: Brownian-bridge crossing probability between grid points

**Purpose:** Give the probability that a Brownian path touches a level between two observed points, used to correct grid-based simulations.

**When to use:** A Monte Carlo of continuously monitored hitting is run on a time grid (Topic 5), or the task asks for hitting given the endpoints.

**How to implement:**
1. Check the inputs: the two endpoints $x_u$, $x_v$ (logs for GBM), the level $b$, $\sigma$ (log volatility for GBM) and $v - u$.
2. Both endpoints strictly on the starting side of $b$: $P(\text{touch on } [u, v] \mid x_u, x_v) = \exp\left(-\frac{2(b - x_u)(b - x_v)}{\sigma^2 (v - u)}\right)$; it is 1 if either endpoint is at or beyond $b$. It does not depend on the drift, and the same expression holds for a lower level.
3. A path's hit probability is one minus the product over steps of one minus these terms.

**Limitations and cautions:** The bridge probability assumes Brownian motion within each step.

**Double check:** The term lies in $[0, 1]$ and tends to 1 as either endpoint approaches the level; if not, the sign of a distance is wrong.

## Topic 5: Monte Carlo of running extremes, terminal values and first-passage times

**Purpose:** Simulate paths and estimate hitting probabilities, first-passage times and joint events, to compare with the closed forms.

**When to use:** The task asks for a Monte Carlo estimate or a comparison of simulation with Topics 1 to 3.

**Constraints:**
- The seed, number of paths, step and horizon come from the task; GBM is simulated exactly in logs.
- Every path counts: paths that do not hit by the horizon have $\tau = +\infty$ (censored).

**How to implement:**
1. Check the inputs and print them: the seed and generator the task names, $N$, $\Delta t$, the horizon, and the drift in the form the simulation uses (log drift $\nu$ for log increments $\Delta \ln S = \nu\Delta t + \sigma\sqrt{\Delta t}\,Z$).
2. Build a price array of shape (paths, steps + 1) whose column 0 is $S_0$.
3. From it compute three separately named arrays, one per quantity: the terminal value `S_T = paths[:, n]` (the last column of the horizon), the running maximum `run_max = paths[:, :n + 1].max(axis=1)` and the running minimum `run_min = paths[:, :n + 1].min(axis=1)`. When a helper returns several arrays, unpack them in the order it returns them and print one value of each next to the matching path.
4. Before a joint event, check each marginal: the simulated $P(S_T \le S_0)$ against $\Phi((\ln(S_0/S_0) - \nu T)/(\sigma\sqrt{T}))$, and the simulated $P(\max \ge H)$ against Topic 1. Then estimate the joint event from the same arrays.
5. First-passage time of a path: the first grid time with $S \ge H$ (upper) or $S \le L$ (lower), else $+\infty$. Empirical CDF: $F(t) = \#\{i : \tau_i \le t\} / N$ over all paths.
6. Continuous monitoring on a grid: add the bridge probabilities of Topic 4 (draw $U < p_k$ to flag a hit in a step, or carry the survival weight $\prod_k (1 - p_k)$, whose mean estimates $P(\tau > t_k)$ and $E[1\{X_T \le x\}\prod_k(1 - p_k)]$ estimates $P(M_T \le b, X_T \le x)$).

**Implementation tips:** Draw all normal increments at once and take cumulative sums along the time axis; the running extremes and first-hit indices are then vectorized reductions (`max`, `min`, `argmax` of a boolean array).

**Limitations and cautions:**
- Checking only grid dates misses crossings between dates: hitting probabilities come out too low and first-passage times too long, by an amount of order $\sigma\sqrt{\Delta t}$.
- Dropping never-hit paths gives $P(\tau \le t \mid \tau \le T)$, which reaches 1 at $T$; setting them to $T$ creates a false atom; averaging $\tau$ over a sample containing $\infty$, or with `nanmean`, is wrong.

**Double check:** Each marginal and joint estimate agrees with its closed form within about four standard errors $\sqrt{p(1-p)/N}$ (a grid-only hitting estimate lies below the continuous one). A gap larger than that points to a wrong array (for example a running minimum used as the terminal value), the drift, the event direction or the monitoring: fix it before reporting.

## Topic 6: Discrete monitoring and the continuity correction

**Purpose:** Price or estimate hitting when the level is checked only at discrete dates.

**When to use:** The task says the barrier is monitored at dates spaced $\Delta t$ (for example daily closes).

**How to implement:**
1. Check the inputs: the monitoring step $\Delta t$ and whether the task wants the discrete or the continuous probability.
2. Discrete target: simulate on the monitoring dates without bridge correction, or use the continuous formula with the level moved away from the start (Broadie-Glasserman-Kou): $b' = b + \beta\sigma\sqrt{\Delta t}$ for an upper level and $b - \beta\sigma\sqrt{\Delta t}$ for a lower level (GBM: $H e^{\pm\beta\sigma\sqrt{\Delta t}}$), with $\beta = -\zeta(1/2)/\sqrt{2\pi} \approx 0.5826$.

**Limitations and cautions:** The shift is asymptotic: it is less accurate with few monitoring dates or a start within a few $\sigma\sqrt{\Delta t}$ of the level. Never compare a discretely monitored simulation with the continuous formula directly.

**Double check:** The discrete-date hitting probability is not above the continuous one for the same process and level; a material excess points to the drift, the event direction or the endpoints.

References: Shreve (2004), Stochastic Calculus for Finance II, Sec. 7.2; Borodin and Salminen (2002), Handbook of Brownian Motion; Chhikara and Folks (1978), J. R. Statist. Soc. B 40, 263-289 (inverse Gaussian); Beaglehole, Dybvig and Zhou (1997), Financial Analysts Journal 53(1), 62-68, and Glasserman (2004), Monte Carlo Methods in Financial Engineering (Brownian-bridge correction); Broadie, Glasserman and Kou (1997), Mathematical Finance 7(4), 325-349 (continuity correction).
