# Intraday bars: complete trading days and lag-weighted volume profiles
The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input or convention, follow the task description.

`DataFrame.resample` returns one row for every interval of the whole time range, also for intervals with no observation (the afternoon of a half-day, nights, holidays, weekends). Those rows have a missing open, high, low and close and a volume of $0$, so counting rows per day makes every day look complete.

Inputs: timestamped observations (price, volume), the session bar start times, and the number of bars in a full day. Outputs: a per-day bar table of complete days, the list of excluded days, and a profile per test day.

1. Resample to the bar size with left labels and left-closed intervals (`resample(..., label="left", closed="left")`), taking first, max, min and last of the price and the sum of the volume.
2. Drop the empty intervals before counting: keep only rows whose first price is present (the interval had at least one observation).
3. Keep the session bars by bar start time, and count bars per calendar date.
4. A complete day has exactly the full count. Excluded days are the dates that have observations but fewer or more bars; a date with no observation at all is not a trading day and is not listed.
5. Daily volume shares on complete days: $s_{d,b} = V_{d,b} / \sum_{b} V_{d,b}$.
6. Rolling window: for each test day, the previous $K$ complete days, ordered oldest to most recent.
7. Lag weights: the most recent day has lag 0. With window index $i = 0, \dots, K-1$ (oldest first), the lag is $K - 1 - i$ and the weight $w_i = \exp(-\ln 2 \cdot \mathrm{lag}_i / h)$. Build the lags once; reversing both lags and weights puts the largest weight on the oldest day.
8. Profile: $\mathrm{profile}_b = \sum_i w_i s_{i,b} / \sum_i w_i$, then rescale so the profile sums to 1.

Checks:
- Every excluded day has observations and a bar count different from the full count; known half-days are among them; no weekend date is listed.
- In the weight vector ordered oldest to most recent, the last weight is the largest.
- Each profile sums to $1$, and the number of test days equals the number of complete days minus $K$.
