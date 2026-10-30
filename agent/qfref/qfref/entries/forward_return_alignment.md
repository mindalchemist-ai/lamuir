# Forward returns in rolling (walk-forward) prediction: one time label per array

Use this when a model predicts the return over the next step from information available at time $t$, and the predictions are scored against realized returns (information coefficient, hit rate, regression fit).

## Definitions

| symbol | meaning |
|---|---|
| $m_t$ | price or midpoint observed at time $t$ |
| $r^{\mathrm{fwd}}_{t}$ | one-step forward log return, labelled at the START of its interval |
| $\hat r_{t}$ | prediction made at time $t$ with information up to $t$ |

$$
r^{\mathrm{fwd}}_{t} = \ln (m_{t+1} / m_{t})
$$

In pandas, `r_fwd = np.log(m.shift(-1) / m)` produces exactly this array: row $t$ holds the return from $t$ to $t+1$, and the last row is undefined.

## Alignment rules

- A prediction made at time $t$ targets $r^{\mathrm{fwd}}_{t}$. Pair $\hat r_{t}$ with `r_fwd[t]`, not with `r_fwd[t+1]`: the shift is already inside the array, and indexing it at $t+1$ shifts a second time and scores the prediction against the return one step later.
- A training pair $(x_{s}, r^{\mathrm{fwd}}_{s})$ is usable at prediction time $t$ only if its target is already observed, that is $s + 1 \le t$. Follow the task's own window definition for which rows enter the window; this rule only says that no target from the future enters the fit.
- Reporting "the forward return at index $i$" means `r_fwd[i]` $= \ln(m_{i+1}/m_{i})$.
- Correlations between predictions and realized returns (Spearman or Pearson IC) use the same set of time labels on both sides: every $t$ that has both $\hat r_{t}$ and $r^{\mathrm{fwd}}_{t}$.

## Check before writing outputs

Store each step's result keyed by its time label (a `dict` or a `pd.Series` indexed by $t$), not in a list that starts at the first prediction time: `values[k]` holds label `start + k`, not label $k$. When an output names an index, read it by label (`series.loc[t]`) and assert, for every reported $t$, that the stored label equals $t$ before writing.
Before writing, refit the model from scratch at one reported label $t$ other than the first (its window, the same scaler, divisor and sign rule) and assert that its score and prediction equal the stored values at $t$; after z-normalizing a training window, assert that its column standard deviations equal 1 with the divisor used (`np.allclose(Z.std(axis=0, ddof=0), 1)` for the population divisor). This one check catches both a wrong divisor and a value read at the wrong position.

Print a few rows with $t$, $m_{t}$, $m_{t+1}$, `r_fwd[t]` and recompute one value by hand, for example `np.isclose(r_fwd[i], np.log(m[i+1] / m[i]))`. For the scored pairs, assert that each prediction and its realized return carry the same label $t$. A second shift shows up as `r_fwd[i]` matching $\ln(m_{i+2}/m_{i+1})$ instead.
