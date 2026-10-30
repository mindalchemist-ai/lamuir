# Gaussian hidden Markov regimes: filtering, smoothing, Baum-Welch estimation and regime use

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input, setting or convention, follow the task description.

Read the topics relevant to the task; a task usually needs several of them.

## Topic 1: Forward filter (Hamilton filter) and the likelihood

**Purpose:** Compute, at each date, the probability of each hidden regime given the observations so far (real time), and the log-likelihood of the model parameters.

**When to use:**
- A series (usually returns) is modeled as switching between $K$ hidden states, each with its own Gaussian distribution, and the task asks for real-time (filtered) state probabilities or the likelihood of given parameters.
- It is also the first half of the E-step of an estimation (Topic 3).
- For probabilities that use the whole sample, add Topic 2; for long series where the products underflow, use Topic 4 instead.

**Constraints:**
- $P_{ij}$ is the probability of moving from state $i$ today to state $j$ tomorrow, so each row of $P$ sums to 1, unless the task defines the orientation otherwise. The prediction step below depends on this orientation.
- Each state's variance is strictly positive; a zero variance makes its density infinite at the mean.

**How to implement:**
1. Check the inputs and print them: the series $y_1, \dots, y_T$ and its units (decimal or percent, matching the means), the number of states $K$, the initial probabilities $\pi$, the transition matrix $P$ and its orientation, and each state's mean $\mu_j$ and variance $v_j$ (say whether the task gives variances or standard deviations).
2. Emission densities: $b_j(y_t) = \frac{1}{\sqrt{2\pi v_j}} \exp\left(-\frac{(y_t - \mu_j)^2}{2 v_j}\right)$, or `scipy.stats.norm.pdf(y, loc=mu, scale=sd)` with the standard deviation. These are densities and can exceed 1.
3. Predicted probabilities: $p_1(j) = \pi_j$, and for $t \ge 2$, $p_t(j) = \sum_i f_{t-1}(i) P_{ij}$, the row vector times the matrix, $f_{t-1} P$ (`f_prev @ P`), not $P f_{t-1}$.
4. Normalizer (the predictive density of $y_t$): $c_t = \sum_j p_t(j)\, b_j(y_t)$.
5. Filtered probabilities: $f_t(j) = p_t(j)\, b_j(y_t) / c_t$.
6. Log-likelihood: $\log L = \sum_{t=1}^{T} \ln c_t$.

**Limitations and cautions:**
- Using `P.T`, or summing over the next state instead of the previous one, swaps the roles of the states; every $f_t$ still sums to 1, so the row sums do not reveal it.
- A normalizer of zero is usually numerical underflow (use Topic 4); a genuinely zero predictive density means the model gives the observation no support.
- Filtered probabilities use observations only up to their date, but parameters estimated on the whole sample still carry hindsight.
- With $K = 1$ the model is a single Gaussian; states with equal emissions carry no information from the observations, although the Markov prior still evolves.

**Double check:**
- Each $f_t$ sums to 1 with no negative entries, and $\log L$ is finite; if a sum is off, recheck step 5; if $\log L$ is $-\infty$, switch to Topic 4.
- Recompute $p_2$ by hand for one date from $f_1$ and the printed $P$; if it differs from step 3, the orientation is reversed, so use $f_{t-1} P$ and rerun.

## Topic 2: Forward-backward smoothing

**Purpose:** Compute, at each date, the probability of each hidden regime given the whole sample, and the probability of each pair of consecutive regimes.

**When to use:**
- The task asks for smoothed (retrospective, full-sample) state probabilities, or a state classification of past dates.
- Baum-Welch needs these quantities ($\gamma$ and $\xi$) in every E-step (Topic 3).
- For probabilities available in real time use Topic 1 only.

**Constraints:** The backward pass uses the same parameters and the same normalizers $c_t$ as the forward pass of Topic 1; mixing passes from different parameters gives probabilities that do not sum to 1.

**How to implement:**
1. Check the inputs: the filtered probabilities $f_t$, the normalizers $c_t$ and the emission densities $b_j(y_t)$ from Topic 1, all from the same parameters.
2. Scaled backward quantity: $B_T(j) = 1$, and for $t = T-1, \dots, 1$: $B_t(i) = \sum_j P_{ij}\, b_j(y_{t+1})\, B_{t+1}(j) / c_{t+1}$.
3. Smoothed state probabilities: $\gamma_t(j) = f_t(j)\, B_t(j)$.
4. Smoothed pairwise probabilities, for $t = 1, \dots, T-1$: $\xi_t(i, j) = f_t(i)\, P_{ij}\, b_j(y_{t+1})\, B_{t+1}(j) / c_{t+1}$.

**Limitations and cautions:** Smoothed probabilities use observations after $t$, so they are retrospective even with fixed parameters; they are not real-time signals and cannot drive a backtest without look-ahead.

**Double check:** Each $\gamma_t$ sums to 1; each $\xi_t$ sums to 1; the row sums of $\xi_t$ equal $\gamma_t$; its column sums equal $\gamma_{t+1}$; and $\gamma_T = f_T$. A failure points to a time index of $b$, $B$ or $c$ in step 2 or 4, or to the transition orientation; fix that step and recompute.

## Topic 3: Baum-Welch (EM) estimation

**Purpose:** Estimate the initial probabilities, the transition matrix and each regime's mean and variance of a Gaussian hidden Markov model from an observed series, by maximum likelihood.

**When to use:**
- The task asks to fit or estimate the HMM (Baum-Welch, EM), from given or chosen initial values.
- When the parameters are given and only probabilities are needed, use Topics 1 and 2 without this topic.

**Constraints:**
- Initial values, tolerance, iteration cap and stopping rule come from the task; the reported iteration count depends on the stopping rule exactly as worded.
- Count iterations with a variable of its own (for example `n_iter`), not with a name that a loop inside the iteration also uses: state indices are usually `i` and `j`, and in Python an inner `for i in ...` rebinds the outer `i`, so the loop still runs correctly but the count read after it is the inner index (for two states, always 2). Nothing raises an error.
- The variance update uses the new means and divides by the summed weights, with no degrees-of-freedom correction; this is what maximizes the likelihood.
- The initial distribution is re-estimated as $\gamma_1$ (standard Baum-Welch) unless the task says it is fixed, not re-estimated, or tied to the stationary distribution of each new $P$. A starting $\pi$ in the inputs, whatever it is called, is an initial value.
- Inside the loop, every quantity the E-step reads ($\ln \pi$, $\ln P$, the log densities) is recomputed from the current $\pi$, $P$, means and variances at the start of each iteration: a log taken once before the loop freezes the initial matrix while the M-step updates only $P$.
- Every forward, backward and E-step function takes the current $\pi$, $P$, means and variances as arguments at every iteration; a function that reads them from an outer scope keeps stale values after an update.
- Use the scaled passes of Topics 1 and 2 for the E-step by default: they are numerically stable for series of thousands of observations with a few states, and their matrix products (`f_prev @ P`, `P @ (b * B)`) fix the direction of every sum. Switch to the log-space passes of Topic 4 only after a scaled pass has returned a zero normalizer; in log space the summation axis must be chosen by hand, which is the most frequent source of silently wrong fits.

**How to implement:**
1. Check the inputs and print them: the series, $K$, the initial $\pi$, $P$, means and standard deviations or variances, the tolerance, the iteration cap and the stopping rule as the task words it.
2. E-step with the current parameters: run Topic 1 and Topic 2 (or Topic 4) to get $\gamma$, $\xi$ and $\log L$. Record $\log L$; it belongs to the parameters used in this pass, not to the updated ones.
3. Before the first update, test the E-step on the initial parameters and print the results: every $\gamma_t$ sums to 1; for every $t$ and $i$, $\sum_j \xi_t(i, j) = \gamma_t(i)$ and $\sum_i \xi_t(i, j) = \gamma_{t+1}(j)$; and in log space the likelihood from $\ln\alpha_T$ equals the one from $\ln\alpha_1 + \ln\beta_1$. If any test fails, fix the E-step (the summation axes and the normalizer of $\xi$) before iterating: a wrong E-step still converges, to wrong parameters.
4. Initial distribution: $\pi^{\mathrm{new}}_j = \gamma_1(j)$, or keep it as the task says.
5. Transitions: $P^{\mathrm{new}}_{ij} = \frac{\sum_{t=1}^{T-1} \xi_t(i, j)}{\sum_{t=1}^{T-1} \gamma_t(i)}$.
6. Means: $\mu^{\mathrm{new}}_j = \frac{\sum_{t=1}^{T} \gamma_t(j)\, y_t}{\sum_{t=1}^{T} \gamma_t(j)}$.
7. Variances about the new means: $v^{\mathrm{new}}_j = \frac{\sum_{t=1}^{T} \gamma_t(j)\, (y_t - \mu^{\mathrm{new}}_j)^2}{\sum_{t=1}^{T} \gamma_t(j)}$.
8. Stopping: test exactly the quantity the task names (for example the largest absolute change in the means) against its tolerance, and nothing more; the iteration count is the first iteration at which that test passes. Otherwise stop at the iteration cap and report that the fit did not converge. Record the count in the iteration counter of the Constraints at the moment the test passes, and print it with the last change of the tested quantity, which must be below the tolerance while the change one iteration earlier was not.

**Implementation tips:** Print $\log L$ and the means at every iteration; the trace makes most errors visible.

**Limitations and cautions:**
- Adding variance or transition tests to a stopping rule that names only the means changes the iteration count. Without a stated rule, small mean changes alone do not prove that the variances or transitions have converged.
- A state with zero occupancy leaves its update undefined; a variance collapsing to zero makes the likelihood unbounded. A stated positive variance floor prevents this but changes the optimization problem.
- EM never lowers the likelihood but can stop at a local optimum that depends on the initial values.
- Fixed parameters, priors or variance floors define different updates from those above.

**Double check:**
- $\log L$ never decreases from one iteration to the next; a drop means a bug in the E-step or the updates, so recheck the summation axes and time indices before using the fit.
- Fixed-point test after stopping: pass the returned $\pi$, $P$, means and variances explicitly to a fresh E-step and one M-step; the largest change of the tested quantity is of the order of the tolerance and $P$ barely moves. A larger change means the loop's E-step used stale parameters: fix it and refit. A non-decreasing $\log L$ does not catch this.
- The states differ in mean or variance; identical states usually come from an update that mixes shapes ($\gamma$ summed over the wrong axis, $y$ broadcast as $(K, T)$), so fix the update rather than report the collapsed fit or an iteration count of 0.
- The rows of $P^{\mathrm{new}}$ sum to 1; if not, the denominator of step 5 sums over the wrong index.
- Print the states that are never the most likely on any date; a rare state can be legitimate, so check the updates before calling it a collapse.

## Topic 4: Log-space forward-backward

**Purpose:** Compute the same filtered and smoothed probabilities as Topics 1 and 2 with logarithms, so that long series or extreme observations do not underflow.

**When to use:**
- Only when a scaled pass of Topics 1 and 2 has underflowed (a normalizer of zero, a log-likelihood of $-\infty$), or the task asks for a log-space implementation.
- Otherwise use Topics 1 and 2: they give the same numbers, and their matrix products leave no summation axis to choose.

**Constraints:** The forward sum runs over the previous state $i$ and the backward sum over the next state $j$; on an array with rows $i$ and columns $j$ these are different axes.

**How to implement:**
1. Check the inputs: log emission densities $\ln b_t(j)$ (`scipy.stats.norm.logpdf`), $\ln \pi$, and $\ln P$ with $P_{ij}$ the probability of moving from $i$ to $j$. Inside an estimation loop, recompute $\ln b_t$, $\ln\pi$ and $\ln P$ from the current parameters at the start of every E-step: logs taken once before the loop keep the initial matrix, and every later E-step then uses it while the M-step updates only $P$ and $\pi$.
2. Forward: $\ln\alpha_1 = \ln\pi + \ln b_1$, and $\ln\alpha_t(j) = \ln b_t(j) + \operatorname{logsumexp}_i\left(\ln\alpha_{t-1}(i) + \ln P_{ij}\right)$. On the array $\ln\alpha_{t-1}[:, \mathrm{None}] + \ln P$ (rows $i$, columns $j$) this is `scipy.special.logsumexp(..., axis=0)`. Here $\alpha_t$ is the unnormalized forward quantity: $\alpha_t(j) = f_t(j) \prod_{s \le t} c_s$.
3. Backward: $\ln\beta_T = 0$, and $\ln\beta_t(i) = \operatorname{logsumexp}_j\left(\ln P_{ij} + \ln b_{t+1}(j) + \ln\beta_{t+1}(j)\right)$, which on the same rows-$i$, columns-$j$ array is `axis=1`.
4. Log-likelihood: $\log L = \operatorname{logsumexp}(\ln\alpha_T)$.
5. Smoothed probabilities: $\ln\gamma_t = \ln\alpha_t + \ln\beta_t - \log L$; filtered probabilities: $\ln\alpha_t$ minus its own logsumexp at each date.
6. Pairwise probabilities, for $t = 1, \dots, T-1$: $\ln\xi_t(i, j) = \ln\alpha_t(i) + \ln P_{ij} + \ln b_{t+1}(j) + \ln\beta_{t+1}(j) - \log L$. As an array with rows $i$ and columns $j$: $\ln\alpha_t[:, \mathrm{None}] + \ln P + (\ln b_{t+1} + \ln\beta_{t+1})[\mathrm{None}, :] - \log L$. The normalizer is the same $\log L$ for every $t$; a per-date normalizer built from a transposed $\ln P$ or a differently broadcast sum gives rows of $P^{\mathrm{new}}$ that do not sum to 1.

**Limitations and cautions:** `axis=1` in the forward step sums over the next state instead of the previous one: the transition matrix silently drops out of the recursion, the results stay finite and normalized, and the fitted parameters are wrong.

**Double check:** Before using the fit, compare the log-likelihood from $\ln\alpha_T$ with the one from $\ln\alpha_1 + \ln\beta_1$ and with $\sum_t \ln c_t$ of the scaled pass (Topic 1) on the same parameters; if they differ, a summation axis in step 2 or 3 is wrong, so fix it and rerun.

## Topic 5: Regime labelling and current-regime classification

**Purpose:** Turn the fitted states into named regimes (for example bull and bear), decide which regime holds at the last date, and select that regime's parameters for later steps.

**When to use:** The task names regimes, asks for the current regime or its probability, or uses regime-conditional statistics in a later step such as an allocation.

**Constraints:** A state index has no economic meaning: the name comes from the task's rule, and any relabeling is applied to every array indexed by state.

**How to implement:**
1. Check the inputs: the fitted parameters, the filtered and smoothed probabilities, the task's rule for naming states, and which probability (filtered or smoothed) defines the current regime.
2. Name the states by the task's rule (for example by ordering them by fitted mean), and apply the same permutation to $\pi$, to both axes of $P$, and to every state summary and probability.
3. Classify the current regime as the state whose filtered or smoothed probability at the last date is largest, as the task specifies.
4. Use the parameters of that state in later steps (for example its mean or covariance).
5. For a regime-conditional asset covariance or return, use the estimator the task defines, with matching annualization; the HMM itself does not define it.

**Limitations and cautions:**
- State labels can be permuted without changing the likelihood, so a refit can swap them.
- The most likely state at each date is not the Viterbi most likely whole sequence.
- An emission variance weighted by $\gamma$ is not the same statistic as an asset covariance on hard-classified dates; a model of one market series does not by itself determine a covariance of several assets.

**Double check:** Every output agrees with the naming rule (for example the state named bull has the higher mean everywhere), and the reported probability of the current regime belongs to the state reported as current; if not, reapply the permutation of step 2 to every array and rewrite the outputs.

References: hmmlearn tutorial (https://hmmlearn.readthedocs.io/en/stable/tutorial.html) for the model definition, Gaussian emissions, Baum-Welch and decoding; the normalized forward-backward formulas follow from Bayes' rule and the Gaussian updates from maximizing the posterior-weighted complete-data log-likelihood.
