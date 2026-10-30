# Hull-White one-factor short-rate model (extended Vasicek): curve, bonds, bond options, caps, Jamshidian swaptions, trinomial tree, Bermudan swaptions and their exercise boundary

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input, setting or convention, follow the task description.

Read the topics relevant to the task; a task usually needs several of them.

Notation used in every topic:

| symbol | meaning | units |
|---|---|---|
| $P(0,T)$ | today's discount factor to time $T$ (from the given zero / swap curve) | none |
| $f(0,t)$ | instantaneous forward rate $-\mathrm{d}\ln P(0,t)/\mathrm{d}t$, continuously compounded | $1/\mathrm{year}$ |
| $a$ | mean-reversion speed (not a rate level) | $1/\mathrm{year}$ |
| $\sigma$ | ABSOLUTE (normal, basis-point) vol of the short rate; 1% = `0.01`. Not a Black/lognormal vol | $1/\sqrt{\mathrm{year}}$ in rate units |
| $t, T, S$ | times in years from today (day count of the curve, often ACT/365) | years |
| $\tau$ | accrual fraction of a coupon / caplet period (day count of the instrument, e.g. ACT/360, 30/360) | years |

## Topic 1: Model and the discount curve it reprices

**Purpose:** Set up the risk-neutral short-rate model so that it reprices today's discount curve exactly, from one curve function used everywhere.

**When to use:** Every Hull-White task: calibration, closed forms and trees all start from this curve.

**Constraints:**
- Short rate: $\mathrm{d}r = (\theta(t) - a r)\,\mathrm{d}t + \sigma\,\mathrm{d}W$, constant $a > 0$ and $\sigma$; $\theta(t)$ is chosen so the model reprices $P(0,T)$ exactly. Equivalently $r(t) = x(t) + \phi(t)$, $\mathrm{d}x = -a x\,\mathrm{d}t + \sigma\,\mathrm{d}W$, $x(0) = 0$, $\phi(t) = f(0,t) + \sigma^2/(2a^2)(1 - e^{-a t})^2$.
- Build ONE curve function and use it in every step: the calibration objective, the reported model prices, the tree fit and the analytic (Jamshidian) prices.
- A curve table written as an output keeps the input maturities as its rows, in their order: the point $(0, 1)$ is not a market quote.

**How to implement:**
1. Check the inputs and print them: the curve maturities and values (zero rates or discount factors, compounding), and the task's interpolation rule.
2. Add the point $(0, 1)$ to the discount-curve interpolant (internal only) and take the instantaneous forward from the same interpolant.
3. When the task names no interpolant, common choices are linear in continuously compounded zero rates (forwards continuous inside each segment) and linear in log discount factors (piecewise-flat forwards); they give prices that differ by a few basis points between curve nodes. State the choice.
4. Build the output curve table from the input rows, not from the interpolant's knots. Every row needs a finite forward: at the last maturity a forward difference has no next point, so take the forward from the interpolant's last segment (with log-linear discount factors, the flat forward of the last interval), not a blank or `nan`.
5. If the interpolant is changed after calibrating, calibrate again and recompute everything downstream.

**Implementation tips:** $\theta(t) = \mathrm{d}f(0,t)/\mathrm{d}t + a f(0,t) + \sigma^2/(2a)(1 - e^{-2 a t})$ and $r(0) = f(0,0)$; in practice $\theta$ is never needed explicitly: the closed forms and the tree calibration ($\alpha_i$) use $P(0,T)$ directly.

**Limitations and cautions:** Parameters fitted on one curve and prices reported on another give calibration residuals that grow with maturity and tree-versus-analytic mismatches. Gaussian rates can go negative; that is a model feature, not a bug.

**Double check:** The model bond price at time zero, with the short rate at the time-zero forward, reproduces every market discount factor exactly for any $a$ and $\sigma$. A residual there is a curve-construction error, not a parameter effect; a constant relative error at every maturity points at a curve whose value at time zero is not one.

## Topic 2: Zero-coupon bond prices in the model

**Purpose:** Price a zero-coupon bond at a future date as a function of the short rate.

**When to use:** Bond prices inside option formulas, Jamshidian strikes and tree exercise values.

**Constraints:**
- $P(t,T) = A(t,T)\exp(-B(t,T)\,r(t))$ with $B(t,T) = (1 - e^{-a(T-t)})/a$ (uses $a$ only, never $\sigma$) and $\ln A(t,T) = \ln(P(0,T)/P(0,t)) + B(t,T) f(0,t) - \sigma^2/(4a)(1 - e^{-2 a t}) B(t,T)^2$.
- Here $r(t)$ is the INSTANTANEOUS short rate; use $f(0,t)$, not a zero rate, in $\ln A$.

**How to implement:**
1. For the instantaneous state use $A$, $B$ above.
2. For the tree's $\Delta t$ period rate $R$ (continuously compounded over $[t, t + \Delta t]$, which is what the tree node rate is), use $P(t,T) = \hat{A}\exp(-\hat{B} R)$ with $\hat{B} = B(t,T)\Delta t / B(t, t+\Delta t)$ and $\ln \hat{A} = \ln(P(0,T)/P(0,t)) - [B(t,T)/B(t,t+\Delta t)]\ln(P(0,t+\Delta t)/P(0,t)) - \sigma^2/(4a)(1 - e^{-2 a t}) B(t,T)(B(t,T) - B(t,t+\Delta t))$.

**Limitations and cautions:** $a \to 0$ gives $B = T - t$ (Ho-Lee limit); never divide by $a = 0$. Using the tree's $\Delta t$ rate $R$ in the instantaneous $A$/$B$ formula is a common mistake.

**Double check:** $P(t,t) = 1$ and, at $t = 0$, $P(0,T)$ equals the curve.

## Topic 3: Bond options and caplets

**Purpose:** Price European options on zero-coupon bonds in closed form, and caplets and floorlets as bond options.

**When to use:** The task prices or calibrates to caps, floors or zero-coupon bond options.

**Constraints:**
- Option expiry $T$, bond maturity $S > T$, strike $K$ per unit face (a price, not a rate), face $L$; the total strike payment is $LK$.
- The option formula uses today's discount factors to both dates; $A(T,S)$ and $B(T,S)$ belong to the bond price at a future date and do not enter $h$.
- A caplet paying $N\tau\max(R - X, 0)$ at $t_{k+1}$ equals $N(1 + X\tau)$ European PUTS expiring $t_k$ on the zero maturing $t_{k+1}$ (unit face each) with strike $K = 1/(1 + X\tau)$; a floorlet is the same number of CALLS. Option expiry is the reset date, bond maturity the payment date.

**How to implement:** Name arguments by role (option expiry, bond maturity), not by letter.
1. Bond-price volatility (total, not annualized): $\sigma_P = \frac{\sigma}{a}\left(1 - e^{-a(S-T)}\right)\sqrt{\frac{1 - e^{-2aT}}{2a}}$.
2. $h = \frac{\ln\big(P(0,S)/(K P(0,T))\big)}{\sigma_P} + \frac{\sigma_P}{2}$.
3. Call $= L[P(0,S)\Phi(h) - K P(0,T)\Phi(h - \sigma_P)]$; Put $= L[K P(0,T)\Phi(-h + \sigma_P) - P(0,S)\Phi(-h)]$. Parity: Call $-$ Put $= L[P(0,S) - K P(0,T)]$.
4. Caplet with reset $t_r$, payment $t_p$, strike rate $X$ and accrual $\tau$ (notional 1): $(1 + X\tau)$ times the put with $K = 1/(1 + X\tau)$, $T = t_r$, $S = t_p$.
5. A cap (floor) is the sum over its caplets (floorlets); the first period whose rate is already fixed is usually excluded or valued as a known cash flow; follow the task.
6. Calibrate on (model minus market) in basis points, not on raw prices.

**Limitations and cautions:** $\sigma$ is the normal vol of $r$; $\sigma_P$ is the vol of the bond price over the option life. Do not plug a Black cap or swaption vol in as $\sigma$, and do not annualize $\sigma_P$ again. Ho-Lee limit: $\sigma_P = \sigma(S - T)\sqrt{T}$. Constant $a$, $\sigma$ cannot fit a whole cap or swaption vol surface or a smile; calibrate to the instruments the task names (a time-dependent $\sigma(t)$ changes the formulas, not covered here).

**Double check:** Put-call parity holds for any $h$, so it cannot test $h$; these can. At the money ($X$ equal to the forward rate $(P(t_r)/P(t_p) - 1)/\tau$) the caplet equals $P(t_p)(2\Phi(\sigma_P/2) - 1)(1 + X\tau)$; with a near-zero volatility a caplet 1% in the money is worth its intrinsic value $P(t_p)\,\tau \cdot 0.01$. Recompute the reported caplet prices from the final curve function and the final $(a, \sigma)$ and confirm they equal the prices the optimiser minimised.

## Topic 4: European swaption by Jamshidian's decomposition

**Purpose:** Price a European swaption exactly as a portfolio of zero-coupon bond options.

**When to use:** The task asks for analytic European swaption prices in Hull-White.

**Constraints:**
- Swap starts at option expiry $T$, fixed payment dates $t_1 \ldots t_n$, accruals $\tau_i$, fixed rate $X$, notional $N$; coupons $c_i = X\tau_i$ for $i < n$ and $c_n = 1 + X\tau_n$ (per unit notional; the last coupon includes the notional).
- The standard decomposition requires a common monotone exercise region: nonnegative coupon weights $c_i$, at least one positive, and positive bond loadings provide it. Signed coupons can destroy monotonicity or produce multiple roots; a root alone does not justify the decomposition.

**How to implement:**
1. Solve for $r^*$: $\sum_i c_i A(T,t_i)\exp(-B(T,t_i) r^*) = 1$. The coupon-bond value is strictly decreasing in $r$, so bracket wide (for example from $-100\%$ to $+100\%$), check that the two ends have opposite signs, and solve with a bracketing routine that has an iteration cap (`scipy.optimize.brentq` with `maxiter`, or a fixed count of about sixty halvings).
2. Strikes $K_i = A(T,t_i)\exp(-B(T,t_i) r^*)$ (bond prices at $T$ when $r(T) = r^*$).
3. Receiver swaption (receive fixed) = call on the coupon bond with strike 1: $N\sum_i c_i\,\mathrm{Call}(T, t_i, K_i)$. Payer swaption (pay fixed) = put: $N\sum_i c_i\,\mathrm{Put}(T, t_i, K_i)$.

**Limitations and cautions:** Never loop until a residual or an interval width falls below a tolerance without a cap: once the width reaches the floating-point spacing of the rate the interval stops shrinking, and a mis-signed update never reaches the tolerance. The formulas assume a single-curve swap, physical settlement and per-unit-face strikes; a multi-curve or cash-settled swaption can need a different payoff; the argument does not extend directly to two factors. Common mistakes: forgetting the notional in the last coupon; calling payer = call (payer is a PUT on the coupon bond).

**Double check:** $\sum_i c_i K_i = 1$ within rounding; the payer minus receiver price equals the forward payer swap value.

## Topic 5: Trinomial tree and Arrow-Debreu fitting (Hull-White 1994)

**Purpose:** Build a recombining short-rate tree that reprices today's curve, for products with early exercise.

**When to use:** Bermudan or American exercise (Bermudan swaptions, callable or putable bonds, American bond options), or a tree price to compare with the closed forms.

**Constraints:**
- Store every time step as one array of length $2j_{\max} + 1$, where row $k$ holds node $j = k - j_{\max}$; never index an array by $j$ itself, because a negative $j$ reads from the far end of the array.
- Value and payoff arrays hold floats: create them with `np.zeros(n_nodes)`, not `np.zeros_like(j)` when `j` is the integer node-index array (that keeps the integer dtype and truncates every price to 0).
- Choose $\Delta t$ so that every exercise, reset and payment step $t/\Delta t$ is an integer; time 0 is step 0, so $n$ steps span $n\Delta t$. Calibrating $\alpha_i$ needs $P(0,(i+1)\Delta t)$, so the curve must extend one step past the last node used.

**How to implement:**
1. Geometry: $M = -a\Delta t$ and $V = \sigma^2\Delta t$ (textbook), or exact $M = e^{-a\Delta t} - 1$, $V = \sigma^2(1 - e^{-2a\Delta t})/(2a)$; $\Delta x = \sqrt{3V}$ ($= \sigma\sqrt{3\Delta t}$ for the textbook form); $j_{\max}$ the smallest integer above $0.184/(-M)$ (equal to $0.184/(a\Delta t)$ only for the textbook $M$); for each row $m_k = (k - j_{\max})M$.
2. Branch table, built once: for each row $k$ three target rows and three probabilities, in the same order.
   1. Interior rows ($0 < k < 2j_{\max}$, normal branching): targets $k+1, k, k-1$ with probabilities $\tfrac16 + \tfrac12(m^2 + m)$, $\tfrac23 - m^2$, $\tfrac16 + \tfrac12(m^2 - m)$.
   2. Bottom row ($k = 0$, up branching): targets $k+2, k+1, k$ with probabilities $\tfrac16 + \tfrac12(m^2 - m)$, $-\tfrac13 - m^2 + 2m$, $\tfrac76 + \tfrac12(m^2 - 3m)$.
   3. Top row ($k = 2j_{\max}$, down branching): targets $k, k-1, k-2$ with probabilities $\tfrac76 + \tfrac12(m^2 + 3m)$, $-\tfrac13 - m^2 - 2m$, $\tfrac16 + \tfrac12(m^2 + m)$.
3. Arrow-Debreu prices: $Q_0$ is 1 in row $j_{\max}$ (the centre) and 0 elsewhere. For each step $n$:
   1. $\alpha_n = \left(\ln\sum_k Q_{n,k}\,e^{-(k - j_{\max})\Delta x\,\Delta t} - \ln P(0,(n+1)\Delta t)\right)/\Delta t$ (closed form, no iteration).
   2. Each row's weight $w_k = Q_{n,k}\,e^{-(\alpha_n + (k - j_{\max})\Delta x)\Delta t}$; add $w_k$ times each of its three probabilities to $Q_{n+1}$ at the three target rows with `numpy.add.at` (targets repeat across rows, and a plain fancy-index assignment keeps only one of the repeated contributions).
4. Node rate $R_{n,k} = \alpha_n + (k - j_{\max})\Delta x$.
5. One step back from $n+1$ to $n$: $V_{n,k} = e^{-R_{n,k}\Delta t}\sum_{c=1}^{3} p_{k,c}\,V_{n+1,\mathrm{target}(k,c)}$.
6. Zero-coupon bond $P(t_e, t_i)$ in every row of step $e$: start with an array of ones at step $i$ and step back to step $e$ (or use $\hat{A}$, $\hat{B}$ of Topic 2 with the node's $R$).
7. Backward induction ends once, at step 0; the price is row $j_{\max}$ at step 0, never continued past the root.

**Implementation tips:** With these arrays a full set of builds and repricings takes milliseconds, so a cell that runs for minutes has an unterminated loop, not a large tree.

**Limitations and cautions:** The curve check and the swap check of Topic 6 hold for any branch wiring, because $\alpha$ is refitted at every step; only the moment check (below) tests where each row's branches land.

**Double check:**
1. The Arrow-Debreu prices at each step sum to the market discount factor of that step (within $10^{-10}$).
2. Every row's probabilities sum to 1, every target lies in $[0, 2j_{\max}]$, and the extreme targets are exactly $0$ and $2j_{\max}$.
3. On every row, edges included, the mean of $x$ at the next step is $x(1 - a\Delta t)$ and the variance is $\sigma^2\Delta t$; a failure here is in the branch targets or probabilities (a target written as $j$ instead of the row index $j + j_{\max}$ sends negative rows to the far end of the array).

## Topic 6: Swaps and European swaptions on the tree

**Purpose:** Value swaps and European swaptions at tree nodes, and check the tree against the closed form.

**When to use:** After Topic 5, before any Bermudan valuation.

**Constraints:**
- Payer swap at $T_0$ (pay fixed $X$, receive floating) per unit notional: $\mathrm{payer}(T_0) = 1 - \sum_i c_i P(T_0, t_i) = 1 - P(T_0, t_n) - X\sum_i\tau_i P(T_0, t_i)$ with $c_i$ as in Topic 4. The final principal belongs to the coupon bond; dropping it (writing $1 - X\sum\tau P$) gives values near 1 instead of a few percent. A receiver swap is the negative.
- At a later date $t_k$ only payments strictly after $t_k$ remain in the sum.

**How to implement:**
1. Expiry step $n_0 = T_0/\Delta t$ and payment steps $n_i = t_i/\Delta t$ (integers, Topic 5).
2. European payer swaption: at step $n_0$ the exercise value in each row is $\max\left(1 - \sum_i c_i P(t_0, t_i), 0\right)$; step back to step 0 and read row $j_{\max}$.

**Limitations and cautions:** A swaption far from the closed form while the tree checks and the swap check pass points to the payoff or the exercise dates.

**Double check:**
1. The forward-starting swap valued on the tree (state-price weighted at $T_0$) equals $P(0,T_0) - \sum_i c_i P(0,t_i)$, which is zero at the at-the-money rate; a failure is in the bond values or the swap formula.
2. The European tree price is within a few basis points of the Jamshidian price (Topic 4); for a tolerance see Topic 8.

## Topic 7: Bermudan swaption and its exercise boundary

**Purpose:** Value on the tree a Bermudan swaption whose exercises all enter swaps ending on one final date (co-terminal) and report, at each exercise date, the lowest short rate at which exercising is optimal.

**When to use:** The task asks for a Bermudan swaption price, the early-exercise premium or the exercise boundary.

**Constraints:**
- Exercise dates $T_0, T_0 + \delta, \ldots, T_n - \delta$: one per coupon period, the first at the expiry $T_0$ (step $n_0$) and the last one period before the final payment $T_n$. Build them from the expiry; the payment dates start one period after the expiry, so slicing them (all but the last) starts one period late and misses the expiry.
- The exercise value at date $t_k$ uses only payments strictly after $t_k$, with the contract's fixed coupons.
- An exercise node is a node where the exercise value is POSITIVE and at least the continuation value. Where both are zero (deep out of the money) the node is not an exercise node; a test written as `exercise >= continuation` alone marks the whole bottom of the tree.
- Every exercise date has a boundary entry, the last date included.

**How to implement:** As a line-by-line algorithm, with `ex_steps` the exercise steps in increasing order:
1. `boundary = []`
2. `V = exercise_value(ex_steps[-1])` (array over rows); continuation at the last exercise date is 0.
3. Record the boundary at `ex_steps[-1]` (step 6 below, with `cont = zeros`); this is the step the backward loop starts from, so it is easy to drop.
4. For `n` from `ex_steps[-1] - 1` down to 0: `V = step_back(V, n)` (Topic 5, step 5).
5. When `n` is in `ex_steps`: `ex = exercise_value(n)`, `cont = V`; record the boundary; then `V = np.maximum(cont, ex)`.
6. Record the boundary: `mask = (ex > 0) & (ex >= cont)`; if `mask.any()`, `k = np.flatnonzero(mask)[0]`, $j^* = k - j_{\max}$, $r^* = \alpha_n + j^*\Delta x$; append date $n\Delta t$ (time from today, not from the expiry), $j^*$ and $r^*$. If no row qualifies, report what the task says for a date without exercise; never a placeholder index.
7. Price: row $j_{\max}$ of `V` at step 0. Sort `boundary` by date (the loop produces it in reverse).

**Limitations and cautions:** For a payer swaption the boundary $j^*$ is weakly decreasing as maturity approaches (fewer remaining cash flows), and $r^*$ is positive in usual markets; a $j^*$ at the lowest row ($-j_{\max}$) means the tie of zeros was counted as exercise.

**Double check:**
1. The number of boundary entries equals the number of exercise dates, the first at $T_0$ and the last at $T_n - \delta$.
2. Run, before writing: `assert all(b['j_star'] > -jmax and ex_at[b['date']][b['j_star'] + jmax] > 0 for b in boundary)` (the exercise value at the recorded node is positive and the node is above the bottom row); if it fails, the mask of step 6 lost `ex > 0`: rebuild it and recompute. Every $r^*$ is positive in usual markets.
3. The Bermudan price is at least the European price on the same tree and equals a multi-exercise European routine on the same steps.

## Topic 8: Tolerance for a tree-versus-analytical consistency flag

**Purpose:** Set an objective tolerance for "the tree agrees with the closed form" from the tree's own discretisation error.

**When to use:** The task asks for such a flag but gives no tolerance.

**Constraints:** Use this only after the tree passes its own checks (Topic 5, Topic 6); a tolerance measured on a broken tree is as large as the error and hides it.

**How to implement:**
1. Price the same instrument with $N/2$ (if cheap), $N$ and $2N$ time steps over the same horizon, so $\Delta t$ halves with each refinement (adding steps at the same $\Delta t$ only extends the tree and changes nothing).
2. The change between the last two refinements estimates the remaining error of the finest tree.
3. Tolerance: three times the larger of that estimate and half the previous difference (state the multiple); compare the analytical-minus-tree gap with it.
4. Record the step counts and the estimate next to the flag.

**Limitations and cautions:** A gap that keeps shrinking as $N$ grows is discretisation, not a bug; a gap that does not shrink points to a mismatch in the payoff, the exercise dates or the discounting.

**Double check:** If the $N$-step and $2N$-step prices are identical, the refinement did not take effect ($\Delta t$ did not change, or a later line reset the step count): fix that first; a tolerance of zero is never valid.

## Topic 9: DV01 with a frozen strike

**Purpose:** Measure the sensitivity of a swaption to a parallel curve shift for the same contract.

**When to use:** The task asks for DV01 or a bump-and-revalue sensitivity of swaptions.

**Constraints:** A bump revaluation holds the contract's fixed strike; re-striking at the bumped at-the-money rate measures a different instrument.

**How to implement:**
1. Fix each swaption's strike at its forward swap rate on the base curve and store it once.
2. Reprice on the curve shifted up by one basis point with that same strike, passing the stored strike to the pricer (a pricing function that derives the at-the-money rate from the curve it is given re-strikes silently).
3. DV01 $=$ (shifted minus base) $\times 10^4$ in the task's units.

**Limitations and cautions:** Mixing day counts changes every DV01: model time uses the curve's year fraction; $\tau$ uses the instrument's accrual convention.

**Double check:** A payer swaption gains when rates rise, so its DV01 for an upward bump is positive and of the order of the annuity times the probability of exercise; a small negative value means the strike moved with the curve.

References: Hull and White (1990), Pricing interest-rate-derivative securities, Review of Financial Studies 3(4):573-592; Hull and White (1993), One-factor interest-rate models and the valuation of interest-rate derivative securities, JFQA 28(2):235-254; Hull and White (1994), Numerical procedures for implementing term structure models I: single-factor models, Journal of Derivatives 2(1):7-16; Jamshidian (1989), An exact bond option formula, Journal of Finance 44(1):205-209; Vasicek (1977), Journal of Financial Economics 5(2):177-188; Brigo and Mercurio (2006), Interest Rate Models - Theory and Practice, 2nd ed., Springer (sec. 1.5, 3.3); Hull, Options, Futures, and Other Derivatives, 9th ed., ch. 31; NumPy reference for numpy.add.at.
