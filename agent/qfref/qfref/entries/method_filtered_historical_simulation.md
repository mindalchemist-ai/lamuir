# Filtered historical simulation (FHS): VaR and ES from resampled standardized residuals, with stationary-bootstrap row draws

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input, setting or convention, follow the task description.

Read the topics relevant to the task; a task usually needs several of them.

## Topic 1: FHS VaR and ES for each day

**Purpose:** Simulate a day's portfolio returns by rescaling resampled standardized residuals with that day's conditional volatilities, and read VaR and ES from the simulated distribution.

**When to use:** The task simulates portfolio returns by resampling standardized residuals (from a GARCH or DCC fit) and rescaling them with each day's conditional volatilities. For the row indices of a stationary bootstrap use Topic 2.

**Constraints:**
- One set of row indices is drawn once and reused on every day when the task describes a single set of $B$ bootstrap rows rescaled by each day's volatilities; a fresh set per day only when the task says to resample for each day (or window). With one seed, per-day draws come from the same generator in day order.
- The quantile method and the tail inequality are the ones the task writes.

**How to implement:**
1. Check the inputs and print them: the standardized residual matrix $Z$ ($T \times N$), each day's conditional volatilities $\sigma_t$ (one per asset), the weights $w$, the number of rows $B$ and the tail level $\tau$.
2. Draw the row indices `idx` (Topic 2).
3. For each day $t$: simulated portfolio returns $\mathrm{sim} = (Z_{\mathrm{idx}} \odot \sigma_t)\, w$, each resampled row scaled asset by asset by the day's volatilities.
4. Cut: the $\tau$-quantile of the simulated returns (for example $\tau = 0.01$ for a 1% VaR) with the task's quantile method (`numpy.percentile` with linear interpolation by default).
5. $\mathrm{VaR}_t = -\mathrm{cut}$ and $\mathrm{ES}_t = -\operatorname{mean}\{\mathrm{sim} \le \mathrm{cut}\}$.

**Implementation tips:** With one set of indices, $Z_{\mathrm{idx}}$ is computed once; the per-day work is a scaling and a quantile, which vectorizes over days.

**Limitations and cautions:** Linear interpolation and ES as the mean at or below the cut are one choice; state the choice used.

**Double check:** $\mathrm{ES}_t \ge \mathrm{VaR}_t$ on every day and both scale with the day's volatility; if not, the sign or the tail side is wrong.

## Topic 2: Stationary bootstrap row indices (Politis and Romano 1994)

**Purpose:** Draw $B$ row indices in random blocks of geometric length, so that resampled rows keep short-range dependence.

**When to use:** The task names the stationary bootstrap, a geometric block parameter $p$ (expected block length $1/p$) and a seed.

**Constraints:**
- When the task names the scheme and a seed but no order of the random draws, use this exact sequence of generator calls, because with a fixed seed the order of the calls decides every number: one `rng.integers(0, T)` before the loop; on row 0 one more `rng.integers(0, T)` and no `rng.random()`; on every later row one `rng.random()`, followed by one `rng.integers(0, T)` only when it is below $p$. In code the row test is `i == 0 or rng.random() < p`, which Python evaluates left to right, so no uniform is drawn on row 0. A loop without the draw before the loop, or with a uniform on row 0, is an equally valid bootstrap but a different, not reproducible, sample.
- When the task spells out another order, or names `arch.bootstrap.StationaryBootstrap(block_size, Z, seed=...)`, follow the task.

**How to implement:**
1. Check the inputs and print them: $T$, $B$, $p$, and the generator and seed the task names (for example `numpy.random.default_rng(seed)`).
2. Run this algorithm, line by line, with the generator `rng` the task names:
   1. `pos <- rng.integers(0, T)` (one draw before the loop).
   2. For `i = 0, 1, ..., B - 1`:
      1. If `i == 0`: `pos <- rng.integers(0, T)` (no `rng.random()` on this row).
      2. Else, draw `v <- rng.random()`; if `v < p`: `pos <- rng.integers(0, T)` (a new block start); otherwise `pos <- (pos + 1) mod T` (continue the block).
      3. `idx[i] <- pos`.
   3. Return `idx`.
3. Write the code with these branches in this order; the number of generator calls and their order must match the algorithm exactly, since every resampled row depends on them.
4. Print the first ten indices and the number of block starts.

**Limitations and cautions:** Implementations consume random numbers in different orders (no draw before the loop; a uniform on every row; the `arch` class's internal order), so the same seed gives different rows; each is a valid sample of the same scheme, and VaR and ES from $B$ rows differ between them by sampling noise. State the order used.

**Double check:** The number of block starts is close to $1 + p(B - 1)$ and every index lies in $0, \dots, T-1$; the code contains exactly one `rng.integers(0, T)` before the loop. If not, rewrite the loop as in step 3.
