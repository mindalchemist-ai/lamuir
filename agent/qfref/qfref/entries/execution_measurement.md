# Execution benchmarks, participation and volume profiles

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input, setting or convention, follow the task description.

Use this reference to interpret execution costs, signed spread measures and quantity allocations. An execution schedule is a target; a fill record is a realized or explicitly modeled outcome. A volume cap alone is not a model of queue priority, available liquidity or market impact.

**Two checks before writing a volume profile or a schedule:**

1. Lag order of exponential weights. With lag 0 = most recent, the weights must line up with the window's order. A window sliced as `data[i - n:i]` runs oldest to newest, so pairing it with `np.arange(n)` as lags gives the oldest day the largest weight. Reverse exactly one side: keep the window oldest to newest and reverse the lags (`np.arange(n)[::-1]`), as in the code below. Reversing both the lags and the window cancels, and the largest weight lands on the oldest day again. Then check that the largest weight sits on the newest day.
2. A target day with no rows in the data. The day an order is scheduled on can be missing from the input (the data end before it, or cleaning removed it). Its bars are then generated from the session hours and the bar length, never taken from the data, and an empty schedule is not an answer: check that the scheduled quantities add up to the order quantity.

1. Exponentially weighted profile over a window of $n$ rows ordered oldest to newest: lag $= n - 1 - i$ for row $i$ (the newest row has lag 0), weight $w_i = \exp(-\ln 2\cdot\mathrm{lag}_i/h)$ normalized to sum 1, profile $= \sum_i w_i\cdot\mathrm{row}_i$; the largest weight is on the newest row.
2. Remaining bars of the target day: the session's bar starts strictly after the order time.
3. Integer allocation of a quantity $Q$ over those bars: take $\lfloor \text{share}\cdot Q\rfloor$ per bar and give the rounding remainder one unit at a time to the first bars, or by the task's rule; the allocations sum to $Q$.


## Reference prices and time

Map the trade side, quantity units, reference clock and quote-selection rule first. Transaction time, exchange publication time and local receipt time can differ. A quote known just before a decision and a quote first observed after it answer different questions. A retrospective specification can prescribe either; only information already available can drive a live decision.

For positive quantities $q_{i}$ and fill prices $p_{i}$, execution weighting uses quantities, not the count of fills.

**Average execution price**

$$
\bar{p}=\frac{\sum_i q_i p_i}{\sum_i q_i}
$$

Market VWAP uses the same weighted-price operation on its specified eligible market trades, which may differ from the order's fills. Both averages are undefined when the denominator is zero.

## Signed cost and spreads

Let $s=+1$ for a buy and $s=-1$ for a sell, $m_{0}$ a positive benchmark midpoint and $m_{H}$ a later midpoint. Positive cost denotes a worse price for the investor. The following expressions use one fixed reference denominator; definitions using different denominators must not be mixed.

**Executed-price slippage in basis points**

$$
\mathrm{cost}_{\mathrm{bps}} = 10000\cdot s\cdot (\bar{p}-m_{0})/m_{0}
$$

**Two-sided effective spread**

$$
\mathrm{effective}_{\mathrm{bps}} = 20000\cdot s\cdot (\bar{p}-m_{0})/m_{0}
$$

**Two-sided realized spread at the specified later benchmark**

$$
\mathrm{realized}_{\mathrm{bps}} = 20000\cdot s\cdot (\bar{p}-m_{H})/m_{0}
$$

**Signed reference-price movement**

$$
\begin{gathered}
\mathrm{movement}_{\mathrm{bps}} = 10000\cdot s\cdot (m_{H}-m_{0})/m_{0} \\
\mathrm{effective}_{\mathrm{bps}} = \mathrm{realized}_{\mathrm{bps}}+2\cdot \mathrm{movement}_{\mathrm{bps}}
\end{gathered}
$$

The identity is arithmetic, not evidence of causal impact. Arrival-reference order averages differ from measures using each fill's own reference midpoint. Averaging individual percentages is generally not equal to a percentage formed from aggregated prices when denominators vary. Fixing a later horizon does not establish permanent versus temporary impact economically.

Executed-price slippage excludes fees and nonexecution opportunity cost unless explicitly added. Full implementation shortfall can include both, relative to a stated decision portfolio. A report containing only the fills does not measure the cost of the unfilled balance.

## Participation and residual quantity

If a rule limits a child order by remaining quantity R, participation fraction p times eligible market volume v, and size cap M, its allowable quantity is the minimum of those nonnegative quantities. A filled amount can be smaller under a separate fill model. Distinguish target quantity, permitted order quantity and actual quantity. No-volume intervals do not imply zero price; they imply no observed volume for that interval.

Volume known only at the end of an interval cannot be used as a forecast at its beginning. Ex-post participation reconstructions are valid descriptive calculations but are not automatically implementable trading strategies.

## Intraday share estimates

For historical session d and bucket b, let $v_{d,b}$ be volume and $V_{d}$ its full-session total, assumed positive.

**A session's volume fractions**

$$
s_{d,b} = v_{d,b}/V_{d}
$$

Averages of s give each session equal influence. Dividing pooled bucket volumes by pooled session volume instead weights high-volume sessions more heavily. Coordinatewise medians or winsorized means need not sum to one.

For historical lag l and positive half-life H, exponential weighting has:

**Decay weight by age**

$$
a_{l} = \exp (-\ln (2)\cdot l/H)
$$

A finite weighted average divides by the sum of the included weights. This is not automatically the same as a recursive infinite-history estimator with a particular initialization.

Given nonnegative predicted bucket scores $u_{b}$ and eligible set E with positive total mass:

**Conditional allocation over the remaining opportunities**

$$
w_b=\frac{u_b}{\sum_{j\in E}u_j},\qquad b\in E
$$

If E is empty or its total mass is zero, no proportional schedule is defined by these scores. A fallback requires an explicit convention. A bar timestamp can label its beginning or its end; that convention determines whether the bar is eligible at a decision time.

For integer total Q, allocations $Qw_b$ can be rounded down, then the remaining units assigned in descending fractional-remainder order with a specified tie rule. This preserves nonnegativity and the total; it does not guarantee participation constraints. Conflicting constraints require a different allocation problem.

When trades are resampled to fixed bars, `sum` and `count` return 0 for an empty interval while `first`, `last`, `max` and `min` return NaN. Identify empty bars by a NaN price column or a zero observation count, not by NaN volume, before counting bars per session; otherwise weekends, holidays and early-close afternoons appear as full-length days of zero volume.

A reference time defined by a horizon (the end of a window plus h, say) is that computed time; the quote matched at or after it has its own transaction and event times, which belong in their own fields. When several quotes share a timestamp, the earliest quote at or later than t is the earliest in the file's event order: pandas `sort_values` is not stable by default, so sort with `kind="stable"` or by (time, update id) before matching.

When a benchmark takes the earliest quote at or later than a time t and quotes can share a timestamp → match on a stably sorted copy:

Quote at or after time $t$: keep each quote's original file row, sort by time with a stable sort (ties keep file order), and take the first row with time $\ge t$ (`searchsorted` with `side="left"`); among quotes with the same time this is the earliest row in the file.


When trade records are aggregated trades (each row has its own aggregate id and also the first and last ids of the individual trades it groups) and an output asks for the first or last eligible trade's id in a set of rows → write the aggregate id of the first or last eligible row; the row's own first/last trade-id columns describe the trades inside that one row → check that the written ids are values of the aggregate-id column.

When a profile is an exponentially weighted average over a window stored oldest to newest and the weights are defined by lag (lag 0 = most recent) → build the lags from the window order so the newest day gets lag 0:

Weights with the window ordered oldest to newest: lags run from $n-1$ (oldest) down to 0 (newest), $w = \exp(-\ln 2\cdot\mathrm{lag}/h)$, and the profile is $\sum_i w_i\,\mathrm{row}_i/\sum_i w_i$; the newest day carries the largest weight.

When an order's quantity is scheduled over the bars of its own day that follow the order time → build that day's bar grid from the session hours and the bar length (not from the days kept for model fitting, which may exclude it), take the bars strictly after the order time, allocate, round as the task states, and check the result before writing:

Schedule after an order: build the session's bar-start grid for the order date from the session open to the last bar start at the bar frequency, keep the bars strictly after the order time (there must be at least one; otherwise check the session hours and the order time), key them by bar time into the profile, convert the shares to integer quantities as the task states, and check that the scheduled quantities sum to the order quantity.

When a bucket has no eligible trades and so no child order → it has no fill, and every fill-linked field (fill price, the benchmark quote's bid and ask, its ids and times) is left empty as the task specifies, not filled with the quote found for the bucket → check those fields on every empty-bucket row before writing.

## Checks and scope

Quantity reconciliation connects executed and residual quantities to the target. Conditional shares sum to one only on their declared eligible set. Out-of-sample profile R-squared can be negative; it is not bounded below by zero, and a flat realized profile needs a specified zero-denominator convention. Similar-looking timestamp or volume columns are different economic objects when their availability or aggregation differs.

## Sources

[SEC staff FAQ on Rule 605, execution-quality statistics](https://www.sec.gov/rules-regulations/staff-guidance/trading-markets-frequently-asked-questions/frequently-asked-questions-rule-605-regulation-nms), for benchmark-time and quantity-weighting distinctions. The formulas here state generic conventions, not a claim that every market or contract follows US equity reporting rules. Spread reconciliation and conditional allocation follow directly from the definitions above.
