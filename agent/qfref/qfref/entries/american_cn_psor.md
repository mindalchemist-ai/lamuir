# American and European vanilla options by finite differences: grids, boundaries, Crank-Nicolson, PSOR, dividends and checks

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input, setting or convention, follow the task description.

Read the topics relevant to the task; a task usually needs several of them.

## Topic 1: Black-Scholes PDE and the American obstacle (linear complementarity) problem

**Purpose:** Give the Black-Scholes PDE that a European vanilla option satisfies and the obstacle (linear complementarity) conditions that an American one satisfies, written in time to maturity $\tau = T - t$ so that the solution starts from the payoff.

**When to use:**
- Any finite-difference valuation of a European or American call or put on one stock, with constant parameters between known dividend events. Read this topic first: it defines the notation of the other topics.
- Path dependence, stochastic volatility and several assets need extra state variables and are outside this card.

**Constraints:**
- Times are in years; $r$ (continuously compounded rate), $q$ (continuous yield) and $\sigma$ (volatility) are annual decimals (5% is 0.05).
- The solve runs in time to maturity $\tau = T - t$, from the payoff at $\tau = 0$ to the valuation layer at $\tau = T$: the payoff is the only layer known exactly, so the solution is built backward from it.

**How to implement:**
1. Check the inputs and print them: spot $S_0 > 0$, strike $K > 0$, maturity $T$, $r$, $q$, $\sigma > 0$, exercise style, any cash or proportional dividends with their dates and amounts, and the grid sizes the task gives.
2. Risk-neutral dynamics: $dS = (r - q) S\, dt + \sigma S\, dW$.
3. Payoffs: call $g(S) = \max(S - K, 0)$; put $g(S) = \max(K - S, 0)$.
4. Pricing operator: $\mathcal{L}V = \frac{1}{2}\sigma^2 S^2 V_{SS} + (r - q) S V_S - r V$.
5. Terminal condition: $V(S, \tau = 0) = g(S)$.
6. European: $V_\tau = \mathcal{L}V$.
7. American: $V_\tau - \mathcal{L}V \ge 0$, $V - g \ge 0$, and $(V_\tau - \mathcal{L}V)(V - g) = 0$ (a linear complementarity problem).
8. Choose independently: the exercise style selects the linear solve (Topic 5) or PSOR (Topic 6); the grid selects the coefficients (Topic 2 or 3); dividends select the event maps (Topic 8). Keep the grid and event conventions fixed through a solve.

**Limitations and cautions:**
- $V(S, 0)$ is the expiry payoff, not the value at calendar $t = 0$; the valuation layer has $\tau = T$ and $t = 0$. Do not reverse time labels without moving their value vectors.
- When coefficients change at known times, align time steps with the changes and use each interval's operator.
- Zero volatility needs a deterministic optimal-exercise calculation or a first-order scheme, not division by $\sigma$.

**Double check:** The first layer of the solve equals the payoff at every node; the last layer is the valuation layer. If the reported price equals the payoff at $S_0$ for a European option, the layers were read in the wrong order.

## Topic 2: Uniform stock-price grid

**Purpose:** Turn the Black-Scholes PDE into one linear equation per node on equally spaced stock prices, with a lower, main and upper coefficient for each node.

**When to use:** The task asks for a uniform stock grid, or a grid with an exact zero-stock node (where the boundary values of Topic 4 are exact). For a grid in log price use Topic 3.

**Constraints:**
- All coefficients belong to row $i$; do not shift a coefficient to a neighbouring row to fit packed array lengths.
- The coordinate array matches its stencil: do not move one node onto $S_0$ while keeping uniform-grid coefficients.
- $\Delta S$ is computed inside the pricing function from that call's own number of intervals.

**How to implement:**
1. Check the inputs and print them: the number of space intervals $M$, the upper bound $S_{\max}$ (a starting value is 3 to 5 times $K$, larger for high volatility, long maturity or large $S_0$), $S_0$, $K$ and every dividend shift, all inside the domain.
2. Nodes: $S_i = i\,\Delta S$ for $i = 0, \dots, M$, with $\Delta S = S_{\max}/M$; node $S_0 = 0$ is distinct from the spot $S_0$.
3. Row coefficients for interior rows $i = 1, \dots, M-1$:
   1. Lower: $l_i = \frac{1}{2}(\sigma^2 i^2 - (r - q) i)$.
   2. Main: $c_i = -(\sigma^2 i^2 + r)$.
   3. Upper: $u_i = \frac{1}{2}(\sigma^2 i^2 + (r - q) i)$.
4. Operator on row $i$: $(\mathcal{L}V)_i = l_i V_{i-1} + c_i V_i + u_i V_{i+1}$.
5. Shifted grid $S_i = S_{\min} + i\,\Delta S$ with $S_{\min} > 0$: replace $i$ by $k_i = S_i/\Delta S$ in step 3 (the integer $i$ is not $S_i/\Delta S$ here), and use the positive lower boundary of Topic 4.
6. Choose $M$ so that $S_0$ is a node, or read the price by interpolation (Topic 9).

**Limitations and cautions:**
- These formulas assume constant spacing; a nonuniform grid needs its own stencil.
- A suggested $S_{\max}$ is a starting point, not an accuracy guarantee; check the boundary sensitivity (Topic 4).

**Double check:**
- Print the actual spacing of the array, not only the intended $\Delta S$.
- At interior nodes the assembled operator applied to $1$, $S$ and $S^2$ gives $-r$, $-qS$ and $(\sigma^2 + r - 2q) S^2$; a mismatch is a row-assembly error, so fix the coefficients before solving. These identities do not test boundaries or exercise.

## Topic 3: Uniform log-price grid

**Purpose:** Turn the Black-Scholes PDE into one linear equation per node on equally spaced log prices, where the three coefficients are the same on every node.

**When to use:** The task asks for a log-price grid, or specifies no grid (a log grid is often convenient because its coefficients are the same on every row). For a uniform stock grid use Topic 2.

**Constraints:** The same as Topic 2: coefficients belong to their row, the coordinate array matches the stencil, and $\Delta x$ is computed inside the pricing function.

**How to implement:**
1. Check the inputs and print them: the number of intervals $M$, and a range such as $\ln S_0 \pm 5$ to $6\,\sigma\sqrt{T}$, widened as needed.
2. Nodes: $x_i = x_{\min} + i\,\Delta x$ and $S_i = e^{x_i}$; place $\ln S_0$ on a node or interpolate consistently.
3. With $a = \frac{1}{2}\sigma^2$ and $\mu = r - q - \frac{1}{2}\sigma^2$, the operator is $\mathcal{L}V = a V_{xx} + \mu V_x - rV$ and the row coefficients are:
   1. Lower: $l_i = \frac{a}{\Delta x^2} - \frac{\mu}{2\Delta x}$.
   2. Main: $c_i = -\frac{2a}{\Delta x^2} - r$.
   3. Upper: $u_i = \frac{a}{\Delta x^2} + \frac{\mu}{2\Delta x}$.

**Limitations and cautions:** The lowest node is positive, so the zero-stock boundary values of Topic 4 are not exact there; use an asymptote and check the sensitivity to the lower bound.

**Double check:** Print the stock prices of the first and last nodes and the spacing; if a European price moves by more than the discretization error when the range is widened, the range is too narrow, so widen it and rerun.

## Topic 4: Boundary values for vanilla options

**Purpose:** Fix the option value at the lowest and highest stock nodes on every time step, so that the equations of the interior nodes can be solved.

**When to use:** Every finite-difference solve, after choosing the grid (Topic 2 or 3) and the exercise style. Assume no payments to the option holder before exercise or expiry.

**Constraints:**
- The boundary values are known numbers on every time layer; they enter the interior equations through the right-hand side (Topic 5, step 3), not as unknowns.
- They depend on the time to maturity, so they are recomputed on every layer and on each side of a dividend event.

**How to implement:**
1. Check the inputs: the lowest node (exactly 0 or positive), $S_{\max}$, exercise style, option type, and any future cash dividends.
2. Lowest node exactly 0 (the stock stays at 0):
   1. European put: $V(0, \tau) = K e^{-r\tau}$.
   2. American put: $V(0, \tau) = \max(K, K e^{-r\tau})$.
   3. Call, either style: $V(0, \tau) = 0$.
3. Lowest node positive (shifted or log grid): these are not exact; use a justified asymptote and move the boundary outward to check sensitivity.
4. Highest node, European, continuous yield and no future cash dividend: call $V(S_{\max}, \tau) \approx S_{\max} e^{-q\tau} - K e^{-r\tau}$; put $V(S_{\max}, \tau) \approx 0$.
5. Highest node, American: at least the immediate-exercise value; for a call the common truncation is $\max(S_{\max} - K, S_{\max} e^{-q\tau} - K e^{-r\tau})$; for a put, 0.
6. Highest node with future cash dividends $D_j$ at dates $t_j$ before expiry, at calendar time $t$, with $J(t)$ the dividends still to be paid (including one paid exactly at $t$ on its pre-event side, excluding it on its post-event side):
   1. Pending-dividend adjustment: $A(t) = \sum_{j \in J(t)} D_j \exp(-r(t_j - t) - q(T - t_j))$.
   2. European call: $S_{\max} e^{-q(T - t)} - K e^{-r(T - t)} - A(t)$; European put: 0.
   3. American call with $q = 0$ and $r \ge 0$: the candidate exercise times $U$ are now, immediately before each pending dividend, and expiry; for $u \in U$, $B_u(t) = S_{\max} - \sum_{j \in J(t),\, t_j < u} D_j e^{-r(t_j - t)} - K e^{-r(u - t)}$, and the boundary is $\max(0, \max_{u \in U} B_u(t))$. American put: 0.
7. Recompute the boundary on every layer and on each side of an event.

**Limitations and cautions:**
- The far-field values are truncation approximations valid when $S_{\max}$ is far above $K$ and the dividends; the maximum of intrinsic and the European asymptote is not an exact American boundary.
- An American put at 0 need not equal $K$ when $r < 0$; negative rates or nonzero $q$ with cash dividends need boundaries derived for those assumptions (the candidate set in step 6.3 holds only for $q = 0$, $r \ge 0$).
- Subtracting dividends already paid, or a materially negative call value at $S_{\max}$, means the deep in-the-money premise fails.

**Double check:** Move $S_{\max}$ (or $S_{\min}$) outward and reprice; if the price at $S_0$ moves by more than the discretization error, widen the domain and rerun.

## Topic 5: Crank-Nicolson time step and the European linear solve

**Purpose:** Price a European option by stepping the discretized PDE backward from the payoff with the Crank-Nicolson (theta) scheme, solving one tridiagonal system per step.

**When to use:**
- Pricing a European option on a grid, between dividend events.
- Assembling the equations of each time step for an American option, which Topic 6 then solves instead of the linear solve.
- For the first steps after the payoff or a dividend, combine with Topic 7.

**Constraints:**
- The step $h > 0$ is a step in time to maturity; with a loop in decreasing calendar time, $h = t_{\mathrm{old}} - t_{\mathrm{new}}$, never negative (a negative step runs the PDE forward and explodes).
- Each grid's $h$, $\Delta S$ or $\Delta x$ is computed inside the pricing function from that call's own step counts.
- Boundary values enter the interior system only through the right-hand side, once.

**How to implement:**
1. Check the inputs: the row coefficients (Topic 2 or 3), the boundary values on the old and new layers (Topic 4), $h$, and the weight $\eta$ ($\eta = \frac{1}{2}$ Crank-Nicolson, $\eta = 1$ backward Euler; $\eta$ is not the Greek theta).
2. Right-hand side on interior row $i$: $\mathrm{rhs}_i = V_i^{\mathrm{old}} + (1 - \eta) h \left(l_i V_{i-1}^{\mathrm{old}} + c_i V_i^{\mathrm{old}} + u_i V_{i+1}^{\mathrm{old}}\right)$; old boundary values enter here through $V_0^{\mathrm{old}}$ and $V_M^{\mathrm{old}}$.
3. Add the new boundary values: first interior row $\mathrm{rhs}_1 \mathrel{+}= \eta h\, l_1 V_0^{\mathrm{new}}$; last interior row $\mathrm{rhs}_{M-1} \mathrel{+}= \eta h\, u_{M-1} V_M^{\mathrm{new}}$. If instead the boundary nodes are kept as unknowns with identity rows, do not add these terms.
4. Matrix on interior row $i$: lower $-\eta h\, l_i$, diagonal $1 - \eta h\, c_i$, upper $-\eta h\, u_i$. The first row has no lower entry and the last no upper entry.
5. European: solve the tridiagonal system with `scipy.linalg.solve_banded((1, 1), ab, rhs)`, where with $n$ unknowns indexed $0, \dots, n-1$, diagonal $d$, lower $\ell$, upper $u$: row 0 of `ab` holds $u_{j-1}$ in column $j \ge 1$, row 1 holds $d_j$, row 2 holds $\ell_{j+1}$ in column $j \le n - 2$, and the two unused corners are 0. Do not apply an exercise projection.
6. Keep every solved layer, so that prices, Greeks and value grids can be read from it (Topic 9).

**Implementation tips:**
- Build the coefficient arrays over all interior nodes at once; a dense matrix filled by nested loops costs $O(n^2)$ storage for no extra information.
- With a fixed grid, coefficients, step length and $\eta$, the matrix is the same on every step, so its factorization can be reused; repeated `solve_banded` calls do not cache a factorization. A change of step length, coefficient interval or boundary treatment needs a new matrix.
- Define the solver in one cell and call it in the next, so that each cell stays short.

**Limitations and cautions:**
- Thomas elimination needs well-behaved pivots; avoid explicit matrix inversion.
- Common distinct errors, each with its own check: $r$ in place of $r - q$ in the drift, the wrong direction of $\tau$, a European call payoff used as the far boundary, a narrow domain, and $S_0$ or $K$ poorly resolved by the grid.

**Double check:**
- Solve one small interior system with a dense solver and with the banded solver from the same right-hand side; they agree and the residual $A V - \mathrm{rhs}$ is near 0. A disagreement is a packing error in step 5, not a PDE error.
- Without dividends, the European prices agree with Black-Scholes to the grid's discretization error; if not, check the dense-versus-banded test, then the actual spacings and row coefficients, the old and new boundary terms, and the time coordinate, in that order.

## Topic 6: American exercise with projected SOR (PSOR)

**Purpose:** Price an American option by solving, on each time step, the discretized PDE under the condition that the value never falls below the exercise payoff, with projected successive over-relaxation.

**When to use:** The option can be exercised before expiry and the task asks for PSOR or for a constrained solve on each step. Brennan-Schwartz elimination is an alternative under its single-exercise-region conditions, not a replacement when PSOR is required.

**Constraints:**
- The matrix and right-hand side are those of Topic 5, steps 2 to 4, with the new boundary values already in the right-hand side.
- Neighbour terms refer only to interior unknowns: the first interior row has no lower-neighbour term and the last interior row no upper-neighbour term.
- The projection onto the payoff is inside every row update.

**How to implement:**
1. Check the inputs: the matrix rows of Topic 5, the right-hand side with the boundary terms, the nodal payoff $g_i$, the relaxation $\omega$ (typically $1 \le \omega < 2$, often 1.2 to 1.6), the tolerance and the iteration cap.
2. Start from the previous layer (warm start).
3. Sweep the interior rows in increasing order. On row $i$, the Gauss-Seidel value is $y_i = \left(\mathrm{rhs}_i - A_{i,i-1} V_{i-1} - A_{i,i+1} V_{i+1}\right) / A_{ii}$, using the already updated $V_{i-1}$ and the previous iterate of $V_{i+1}$, and leaving out $A_{i,i-1}V_{i-1}$ on the first interior row and $A_{i,i+1}V_{i+1}$ on the last, exactly as in the tridiagonal system.
4. Relax and project: $V_i \leftarrow \max\left(g_i,\; V_i + \omega (y_i - V_i)\right)$.
5. Stop when the largest scaled change in a sweep is below the tolerance and the complementarity gaps pass (Double check), or at the iteration cap; report nonconvergence.
6. Set the boundary nodes to the new boundary values after the sweep.

**Limitations and cautions:**
- Using the edge nodes as neighbours on the first and last interior rows counts the boundary twice, because it is already in the right-hand side. For a call the far boundary is large, so the American call is pushed above the European one.
- Projecting once after an unconstrained solve is a different method, not PSOR; projecting the right-hand side is wrong.
- Updating every node at once (Jacobi) or red-black ordering is a different iteration with its own convergence behaviour.
- Once converged to the same solution, $\omega$ changes the speed, not the value. Each sweep costs $O(n)$; the total depends on the iteration count.

**Double check:**
- Complementarity: with $a = V - g$ and $b = A V - \mathrm{rhs}$, $a \ge 0$, $b \ge 0$ and $\min(a, b) \approx 0$ at every interior node; a small iterate change alone does not prove a solved problem.
- Without dividends ($q = 0$, no cash dividends) and $r \ge 0$, the American call never exercises early, so its price equals the European call from the same grid to within the solver tolerance. A larger gap means the American solve differs from the European one somewhere other than the projection, most often the boundary terms of step 3; then the row coefficients, the time direction and, under Crank-Nicolson, the damped start (Topic 7). Compare the two solvers line by line and rerun. Do not carry this identity to negative rates.
- American values are at least the European values and the payoff at every node.

## Topic 7: Rannacher time stepping

**Purpose:** Remove the spurious oscillations that Crank-Nicolson produces next to a payoff kink or after a dividend jump, by taking the first steps fully implicit.

**When to use:** Crank-Nicolson (Topic 5) is used and the payoff has a kink (vanilla calls and puts), the task asks for a Rannacher start, or a dividend map has just been applied. Not needed with fully implicit stepping throughout.

**How to implement:**
1. Check the inputs: the number of damped steps and their size, as the task gives them.
2. Default when the task gives no detail: take the first two time steps with $\eta = 1$ (backward Euler) at the normal step size, then continue with $\eta = \frac{1}{2}$.
3. Variant when the task asks for half steps: replace the first one or two Crank-Nicolson steps by twice as many backward Euler steps of half the size, so that the total time covered is unchanged.
4. Restart the damping after each dividend map, with the same exercise rights.

**Limitations and cautions:** Damping is a chosen variant, not a claim that every contract needs it; it does not remove the need to check convergence.

**Double check:** Delta and gamma near the strike on the first layers have no sign oscillations; if they oscillate, check that the damped steps were applied at the start of each interval.

## Topic 8: Discrete dividend jump condition

**Purpose:** Carry the option value across a known dividend date, where the stock price drops by the dividend, during the backward solve.

**When to use:** The task specifies cash or proportional dividends at known dates. A continuous yield $q$ is already in the drift and needs no event; include only distinct income streams, not one dividend twice.

**Constraints:**
- The maximum with the payoff belongs to American options only. A European solve takes no maximum with the payoff anywhere, neither in the time steps nor in the event map: a European holder cannot exercise before the ex-date, so a projection there turns the European price into an American one.
- Use one clock: calendar time decreasing from $T$ to 0 with event time $t_d$, or time to maturity increasing from 0 to $T$ with event time $T - t_d$.
- Each event map is applied exactly once, including when its date falls on a time node; it takes no time.

**How to implement:**
1. Check the inputs: each dividend's date, amount (cash $D$) or fraction $\delta$, and the rule for $S \le D$.
2. Step backward to the event date, splitting a step if the date falls inside it.
3. With $V^{+}$ the post-event values just computed, form the continuation $C(S) = V^{+}(S - D)$ for a cash drop or $V^{+}(S(1 - \delta))$ for a proportional drop, by interpolation on the grid, flooring the stock at 0 (or as the task states).
4. European: $V^{-}(S) = C(S)$. American: $V^{-}(S) = \max(g(S), C(S))$. When one function prices both styles, pass the exercise style into the event map and take the maximum only for American.
5. Restart the damping of Topic 7 and continue backward from $V^{-}$ to valuation.
6. Before writing outputs, check European put-call parity with the cash dividends; with $q = 0$ it reads $C - P = S_0 - \sum_j D_j e^{-r t_j} - K e^{-rT}$. Print both sides; they agree to the discretization error. A larger gap means a projection or a wrong event map in the European solve: fix it and rerun.

**Limitations and cautions:**
- Read the post-event values at a smaller stock price, $S - D$, not $S + D$.
- A capped jump to zero and an uncapped cash subtraction are different models; an escrowed-dividend model ($S_0$ minus the present value of dividends) is another model.
- A combined event uses the stock map the task states; do not invent an order. Events at valuation or expiry follow the contract's event and payoff order.
- On a coarse and a fine grid, the event steps are recomputed for each grid's time step.

**Double check:**
- The positive step lengths add up to $T$ and each event was applied once.
- After each event map, compare the mapped values with the post-event values on the same nodes: for a put the mapped value is at least the post-event value at every node, for a call at most (the holder at $S$ just before the ex-date holds a stock worth $S - D$ just after it). If the inequality fails, the map read the post-event values at $S + D$: change the sign of the shift before looking for a timing cause.
- On the same model, adding nonnegative cash dividends weakly raises put values and weakly lowers call values; repricing without dividends is a separate solve, not a manual adjustment. If the direction is wrong, check the sign of the shift in step 3.

## Topic 9: Price, delta and gamma from the grid; writing value tables

**Purpose:** Read the option price at the spot, its delta and gamma, and any table of values by stock price and time from the solved grid.

**When to use:** After a converged solve, for every reported number and file.

**Constraints:** Compute every summary field (differences, premiums, flags) from the values just written to the output files, read back, not from session variables: after a fix, earlier variable names can still hold the old results.

**How to implement:**
1. Check the inputs: the solved layers, their time labels ($\tau$ or $t$), $S_0$, and the output format the task defines.
2. Price: the valuation layer at $S_0$, on a node or by a stated interpolation (for example quadratic or cubic in log price).
3. Uniform stock grid, interior node: $\Delta_i = \frac{V_{i+1} - V_{i-1}}{2\Delta S}$ and $\Gamma_i = \frac{V_{i+1} - 2V_i + V_{i-1}}{\Delta S^2}$, from the same contract, layer and event side.
4. Log grid: $\Delta = V_x / S$ and $\Gamma = (V_{xx} - V_x)/S^2$.
5. If $S_0$ is not a node, differentiate a consistent interpolant or interpolate the nodal Greeks, and state which.
6. Output defined in calendar time: convert layers with $t = T - \tau$ and order them as the output defines (ascending $t$ unless stated). An output defined in $\tau$ keeps $\tau$.
7. A table with one row per stock node and one column per time is the transpose of a solver array stored as [time, stock]. Build the full time and stock arrays before sampling the requested rows or columns.

**Limitations and cautions:**
- A stock-grid stencil uses $\Delta S$, not $\Delta x$, and is not centred at a domain endpoint.
- When the sampled counts are equal, a missing transpose raises no shape error.
- Sampling must not replace the solve, and a premium added to an analytic price is not a finite-difference solution. After correcting a solution, recompute every dependent output and rewrite every file that holds those values.
- When a runtime requirement applies to a program, time the whole program in a fresh process, not one kernel in a warm session.

**Double check:** Read the written table back: the entry at the stock node nearest $S_0$ in the $t = 0$ column (interpolated at $S_0$) equals the reported price within about 5%, and the $t = T$ column equals the payoff. If not, transpose or reorder the table and rewrite it. Also recompute each derived summary field from the read-back files and assert it equals the written value; re-run the task's own stated checks on those values. Parse every time header of the read-back table as a float and assert that the headers equal the time values of the sampled layers (`np.allclose(headers, t[idx])`), with the last header equal to the final time, not a node count; the $t = 0$ column alone cannot catch node indices used as headers, because node 0 has time 0. Run this before finishing, even when no error was raised.

## Topic 10: Early-exercise boundary extraction

**Purpose:** Find, on each time step, the stock price that separates exercising an American option early from holding it.

**When to use:** The task asks for the exercise boundary or a critical stock price of an American option.

**Constraints:** Only nodes with positive intrinsic value can mark exercise: put $S_i < K$, call $S_i > K$.

**How to implement:**
1. Check the inputs: the solved American layers, the payoff on the grid, and a scale-aware tolerance.
2. Put: on each layer, the boundary $S^{*}$ is the largest node with $S_i < K$ where $V - g \le$ tolerance, taken from the exercise region that starts at the low end of the grid. Call: the smallest node with $S_i > K$ on the high side.
3. When no node qualifies, report no exercise boundary as the task defines it; a domain endpoint is not a substitute.
4. At expiry every node has $V = g$; use the task's convention for the expiry layer (positive-payoff scanning there gives the node next to $K$).
5. Write the boundary file and every summary value from the same extracted series.

**Limitations and cautions:**
- Far out of the money both $V$ and $g$ are numerically 0, so a scan of all nodes for $|V - g| \le$ tolerance returns the upper truncation node or another out-of-the-money node.
- The boundary is resolved to about one grid spacing; interpolation can refine it.
- A literal equality scan and an economic exercise threshold are different diagnostics; when the task leaves the distinction open, state the interpretation used.

**Double check:**
- For $t < T$ a put boundary lies below $K$ (a call boundary above $K$), and between dividend dates it moves monotonically toward the strike as expiry approaches.
- Limits as expiry approaches ($\sigma > 0$, $r > 0$, $q \ge 0$, no dividend events in the last interval): put $S^{*}(T^{-}) = K$ if $q \le r$ and $K r / q$ if $q > r$; call with $q > 0$: $\max(K, K r / q)$; call with $q = 0$ and no remaining cash dividends: no finite boundary. Check the approach to these limits under refinement; do not overwrite computed values with them.
- Smooth fit: just on the continuation side of a regular boundary for $t < T$ and away from dividends, delta approaches $-1$ for a put and $+1$ for a call. If a check fails, restrict the scan to positive-intrinsic nodes and recompute.

## Topic 11: Richardson extrapolation and grid convergence

**Purpose:** Estimate the discretization error, and a more accurate price, by combining prices computed on grids of different fineness.

**When to use:** The task asks for prices on several grids, a convergence study or Richardson extrapolation.

**Constraints:** Changing the resolution must not change the contract, the event schedule or the event-side convention.

**How to implement:**
1. Check the inputs: the grid sizes, the refinement ratio $R$ (coarse spacing over fine spacing) and the assumed order $p$.
2. Price on each grid with that grid's own step sizes and event steps.
3. Richardson estimate: $P_{\mathrm{ext}} = \frac{R^p P_{\mathrm{fine}} - P_{\mathrm{coarse}}}{R^p - 1}$.

**Limitations and cautions:**
- The ratio $|P_{\mathrm{coarse}} - P_{\mathrm{ext}}| / |P_{\mathrm{fine}} - P_{\mathrm{ext}}|$ equals $R^p$ by algebra; it is not a convergence test, and equal prices make it 0/0.
- Kinks, the exercise obstacle, central drift differences and event interpolation can lower the observed order below the nominal second order of Crank-Nicolson; do not promise a fixed error reduction per refinement.
- Refine space, time, domain and solver tolerance separately to find the error source; stability alone does not prove positivity, monotonicity or accuracy.

**Double check:** The fine and coarse prices differ by less than 1% of the fine price and are not identical. A larger gap means one run reused the other grid's state (a step size read from outside the pricing function, or event steps not recomputed); identical values mean both runs used the same grid. Fix the function, rerun both grids and rewrite every output that holds them.

References: Crank and Nicolson (1947), Proceedings of the Cambridge Philosophical Society 43(1), 50-67. Cryer (1971), SIAM Journal on Control 9(3), 385-392 (projected SOR). Rannacher (1984), Numerische Mathematik 43, 309-327. Brennan and Schwartz (1977), Journal of Finance 32, 449-462. Evans, Kuske and Keller (2002), American options on assets with dividends near expiry (https://doi.org/10.1111/1467-9965.02008). Jourdain and Vellekoop (2012), Regularity of the American put option in the Black-Scholes model with general discrete dividends. SciPy `solve_banded` documentation for the banded layout.
