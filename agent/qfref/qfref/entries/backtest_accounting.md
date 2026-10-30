# Backtest accounting: timing, cash and holdings, returns, performance measures and rebalanced long-short books

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input, setting or convention, follow the task description.

Read the topics relevant to the task; a task usually needs several of them.

## Topic 1: Look-ahead-free timing (one-lag rule)

**Purpose:** Line up each position with the return it earns, so that the position uses only information available when it was decided.

**When to use:** Any backtest whose positions come from signals, forecasts, fitted transformations, rankings or volatility-based sizes. For the window over which statistics are computed use Topic 2.

**Constraints:**
- The position applied to the return of day $t$ is built only from data through day $t-1$: both its signal and its size.
- One lag in total: a series that is already aligned is not shifted again.
- The task's own execution rules come first. When the task sizes an order with its fill price (for example "shares from the next day's open"), compute the size with that price on the fill day: the order is sized when it executes, the price is known then, and this is not look-ahead. Replacing the stated fill price by the signal day's price to "avoid look-ahead" changes the task's rule.

**How to implement:**
1. Check the inputs and print them: the price series (close, open, adjusted or not, and the adjustment definition), the dates of the signal's data, the fill rule (same close, next open, next close) and the valuation price.
2. Write down, for one example date, the observation time, the decision time, the fill time and the valuation time.
3. Build each position from data through $t-1$ and apply it to the return of $t$. Apply this one lag in one place only: either shift the signal series, or read the previous row of an unshifted signal, not both.
4. When a position is a signal times a volatility-based size, lag the size together with the signal.
5. Apply the task's conventions for corporate actions, price units, fees, financing, rounding and final liquidation.
6. Before computing any statistic, print for the first trade date the last date of data that entered its signal and size; it must be the previous trading day. If it is two days earlier, the signal was lagged twice: remove one of the lags and rerun.

**Limitations and cautions:**
- A signal that uses a period's final price is not available earlier in that period.
- A fill at a later opening price does not earn the return between the decision and the fill on the newly bought shares.
- A size that uses a volatility including the same day's squared return is look-ahead even if the signal is lagged.
- Lagging a series that is already aligned shifts it twice and uses information two days old.
- An adjusted series may already include distributions; adding them again to a total-return-adjusted valuation counts them twice. Adjusted fractional holdings are an accounting convention and need not equal exchange share counts through a corporate action.
- Selecting a model on the full sample and evaluating it on the same sample is a retrospective comparison, not evidence of live performance; walk-forward evaluation separates estimation from later realizations.

**Double check:** For one trade, print the signal's last data date, the fill date and the first return the position earns; if the position earns a return from before its fill, or its data are two days old, fix the shift of the position and rerun.

## Topic 2: Evaluation window after a warm-up

**Purpose:** Compute performance statistics only over the stated evaluation period, leaving out the warm-up used to build the first signals.

**When to use:** The task states a trading or evaluation start after a signal or risk warm-up. A task that asks for full-history statistics keeps the full history.

**Constraints:** Every statistic and regression uses the returns from the stated start onward, flat or cash days inside the window included.

**How to implement:**
1. Check the inputs: the stated first trading or evaluation date and the warm-up length.
2. Treat the warm-up as the task states (dropped, or flat only if the task says so).
3. Take the portfolio returns from the stated start onward.
4. Compute every statistic and regression on that window only: mean, volatility, Sharpe ratio, drawdown, hit rate (the share of returns above zero) and factor regressions.

**Limitations and cautions:**
- A rule that defines a position on every date has no flat state; filling a warm-up with zero exposure silently changes the statistics.
- Trimming a sample that already excludes its warm-up shortens it twice.

**Double check:** The number of evaluated returns equals the number of dates on or after the stated start; if not, drop the warm-up rows or restore trimmed rows, then recompute every statistic.

## Topic 3: Trade accounting: cash and holdings

**Purpose:** Keep cash and share holdings consistent through each trade, and value the portfolio between trades.

**When to use:** The backtest holds cash and shares (share counts, capital, fees) rather than only weights. For weight-based books use Topics 10 and 11.

**Constraints:** At a trade the change in equity at the fill price equals minus the fees: a trade only exchanges cash for shares at that price, so anything else is a bookkeeping error.

**How to implement:**
1. Check the inputs: shares traded $q$ (positive to buy), fill price $p$, shares held before $h$, cash $B$, fee $F \ge 0$; settlement is immediate and there is no external cash flow at that instant unless the task says otherwise.
2. Cash after the trade: $B^{\mathrm{new}} = B - q\,p - F$.
3. Shares after the trade: $h^{\mathrm{new}} = h + q$.
4. Equity at the fill price: $B^{\mathrm{new}} + h^{\mathrm{new}}\,p = B + h\,p - F$.
5. Between trades, accrue financing by the stated lending and borrowing rates and mark holdings to the valuation price.

**Limitations and cautions:** Buying converts cash into an asset; it does not create a loss equal to the notional. Selling converts an asset into cash. Fees reduce equity.

**Double check:**
- With every position closed and no flows or financing, final cash minus initial cash equals the sum of net trade profits; with open positions, add their unrealized profit. If not, look for a fee charged twice or a trade not recorded.
- The product of the period returns from equity reproduces the ratio of final to initial equity on the same interval.

## Topic 4: Cash-constrained position sizing

**Purpose:** Find the largest whole number of shares that the available cash can buy after fees.

**When to use:** The task buys whole shares with the cash on hand, with flat or proportional fees. For weight-based sizing use Topic 10.

**Constraints:** Cash after the purchase, fees included, is not negative unless the task allows borrowing; fees are charged as the task states (per trade, per share or per value).

**How to implement:**
1. Check the inputs: available cash $B$, price $p$, flat fee $f$ and proportional rate $c$, charged only on a positive trade unless the task says otherwise.
2. Whole-share limit: $q_{\max} = \max\left(0, \left\lfloor \frac{B - f}{p\,(1 + c)} \right\rfloor\right)$.
3. Apply any other stated sizing rule (risk budget, target weight) and take the smaller quantity.

**Limitations and cautions:** A risk budget divided by a stop distance is a sizing rule, not a loss limit: a gap can fill the exit beyond the stop. A trailing stop depends on when its reference peak is observed; it does not fill at that peak or at the stop price.

**Double check:** Cash after the purchase is not negative, and one more share would make it negative; if either fails, recompute $q_{\max}$ with the fees included.

## Topic 5: Time-weighted return and wealth index

**Purpose:** Measure portfolio performance from its values without the effect of deposits and withdrawals, and compound the period returns into a wealth index.

**When to use:** The task reports returns of a portfolio valued in currency. For returns of a weight-based book see Topic 11, step 5.

**How to implement:**
1. Check the inputs: consecutive positive portfolio values $V_{t-1}$, $V_t$, and any deposits or withdrawals between them.
2. Simple return without external flows: $r_t = V_t / V_{t-1} - 1$.
3. With external flows, split the period at each flow and link the subperiod returns. Trades inside the portfolio are not external flows.
4. Wealth index: $W_t = \prod_{j=1}^{t} (1 + r_j)$.

**Limitations and cautions:**
- A raw value ratio across a deposit or withdrawal mixes capital flows with performance.
- A signal that sums past returns and one that compounds them are different ranking rules; switching one for the other is not a harmless numerical change.

**Double check:** $W_n$ equals the final value divided by the initial value when there are no external flows; if not, a return is missing or computed on the wrong dates.

## Topic 6: Annualized mean, growth and volatility

**Purpose:** Express a return series' average return, compound growth and volatility per year.

**When to use:** The task reports annual return, annual growth (CAGR) or annual volatility of a return series.

**Constraints:** Use the annualization factor and standard-deviation divisor the task gives.

**How to implement:**
1. Check the inputs: the returns over the evaluation window (Topic 2), observations per year $A$, the number of periods $n$, and the standard-deviation divisor ($n - 1$ is `ddof=1`; NumPy's `std` defaults to $n$, pandas' to $n - 1$).
2. Arithmetic annual mean: $\mu_{\mathrm{annual}} = A \cdot \operatorname{mean}(r)$.
3. Compound annual growth, for positive final wealth: $g_{\mathrm{annual}} = W_n^{A/n} - 1$.
4. Annual volatility: $\sigma_{\mathrm{annual}} = \sqrt{A}\, s_r$, with $s_r$ the per-period standard deviation.

**Limitations and cautions:**
- The arithmetic annual mean and compound growth answer different questions; report the one the task names.
- $\sqrt{A}$ scaling assumes uncorrelated returns; serial correlation changes multi-period variance.

**Double check:** Recompute the annual volatility from the printed per-period standard deviation and $A$; a statistic off by a factor near $A$ or $\sqrt{A}$ was annualized twice or not at all.

## Topic 7: Sharpe ratio

**Purpose:** Measure a strategy's average excess return per unit of volatility, on an annual basis.

**When to use:** The task asks for a Sharpe ratio. A ratio of compound growth to volatility is a different convention and must be labelled as such.

**How to implement:**
1. Check the inputs: the returns over the evaluation window, the risk-free rate and its period, and whether the task uses excess returns.
2. Excess returns: subtract the per-period risk-free rate (an annual rate $R_f$ becomes $R_f / A$ per period, or $(1 + R_f)^{1/A} - 1$ if the task compounds), unless the task uses raw returns.
3. Sharpe ratio: annual mean excess return (Topic 6, step 2) divided by annual volatility (Topic 6, step 4).

**Limitations and cautions:** Zero volatility leaves the ratio undefined.

**Double check:** The ratio equals $\sqrt{A}$ times the per-period mean over the per-period standard deviation; if not, the annualization of the mean and of the volatility differ.

## Topic 8: Maximum drawdown

**Purpose:** Measure the largest percentage fall of the wealth curve from a previous peak.

**When to use:** The task asks for drawdown or maximum drawdown.

**Constraints:** The task decides whether the initial capital point starts the curve; state the choice.

**How to implement:**
1. Check the inputs: the wealth index over the evaluation window and the initial wealth.
2. High-water mark: $H_t = \max(W_{\mathrm{initial}}, W_1, \dots, W_t)$.
3. Drawdown: $d_t = 1 - W_t / H_t$.
4. Maximum drawdown: the largest $d_t$, reported as a positive fraction unless the task says otherwise.

**Limitations and cautions:**
- Leaving out the initial capital point can hide a loss in the first period.
- The drawdown of a position's price and of portfolio equity differ when cash, leverage or fees are present.

**Double check:** Maximum drawdown is between 0 and 1 for an unlevered long-only book and is 0 only when the wealth never falls; if it is negative, the sign convention was flipped.

## Topic 9: Signed-weight long-short P&L

**Purpose:** Compute the exposure and profit of a portfolio with long and short positions under one consistent sign convention.

**When to use:** The book holds short positions or reports net or gross exposure.

**Constraints:**
- Use one short convention, not both.
- Sizes named in the task's procedure text (for example a fixed weight for every name in a leg) are used as stated. A limit that appears only in a parameter list and contradicts them does not override them: report the conflict and keep the stated sizes. A limit that the procedure text itself says to apply (for example "clip each position to the cap") is applied.

**How to implement:**
1. Check the inputs: the long and short names, their sizes, and whether the task states sizes as signed weights, positive short sizes, or gross exposure to split.
2. Net exposure: $\sum_i w_i$; gross exposure: $\sum_i |w_i|$.
3. Signed weights: each short weight is negative (gross $g$ split equally over $n$ shorts gives $-g/n$ each), and P&L is $\sum_i w_i r_i$.
4. Positive short sizes: P&L is the long leg minus the short leg.
5. Take each sign from the long or short label of the position.

**Limitations and cautions:**
- A negative short weight combined with subtracting the short leg cancels the short side.
- A unit long leg minus a unit short leg has gross exposure 2, so its reported return needs a stated capital base.
- Equity weights, return-spread indices and invested dollars are not interchangeable.

**Double check:** The short leg's P&L has the opposite sign to its names' average return; if not, a sign was applied twice, so keep one convention and rerun.

## Topic 10: Holding target weights between rebalances

**Purpose:** Build the daily weights of a strategy that sets target weights on rebalance dates and holds them until the next rebalance.

**When to use:** The strategy holds constant target weights from one rebalance date to the next. When it holds share counts whose weights drift with prices, carry the shares and recompute the weights each day instead.

**How to implement:**
1. Check the inputs: the rebalance dates, the target weights on each, and the first rebalance date.
2. Start a weights table of missing values on the trading-day index, one column per asset.
3. On each rebalance date write the complete target row: every asset, 0 for the assets exited.
4. Carry each row forward to the following dates (`ffill`) and set the rows before the first rebalance to 0.

**Limitations and cautions:** A weights table started with zeros instead of missing values stays zero between rebalances after `ffill`, so positions exist only on rebalance days.

**Double check:** Every non-rebalance day carries the most recent target row, an all-zero target included; if a day between rebalances is all zero while its last target was not, rebuild the table from step 2.

## Topic 11: Monthly cross-sectional long-short ranking backtest

**Purpose:** Backtest a book that ranks assets on a daily signal, holds the top names long and the bottom names short, and rebalances on the first trading day of each month.

**When to use:** The task describes a cross-sectional long-short book rebalanced monthly from a daily signal, with a stated trading start. For other schedules or sizing rules use Topic 10 with the task's rules.

**Constraints:**
- The book opens on the stated trading start (even mid-month) and rebalances on the first trading day of each later month.
- Each rebalance ranks the previous row of the signal, known at that close.
- The signal shares the returns' date index; row $t$ of the signal uses data through row $t$ and carries no shift of its own.
- The per-name weights named in the procedure text are the position sizes; a position limit that only appears in the parameters and contradicts them is reported, not applied (Topic 9).

**How to implement:**
1. Check the inputs and print them: daily simple returns (one column per asset, missing values handled as the task says), the signal on the same index and columns, the trading start as a row position, the numbers of long and short names, the per-name long and short weights, the cost rate, and every position limit the task states.
2. Rebalance dates: build the list as the trading start date itself, followed by the first trading day of each later month, taken from the dates of the return index (for example the minimum date of each `index.to_period('M')` group, keeping those after the start). The trading start is in the list even when it falls mid-month: the book is opened that day, not at the next month start. `resample('MS')` labels each month by its calendar first day, which is not a trading day when the month starts on a weekend or holiday, so do not use those labels. Print the number of rebalance dates and the first two dates as soon as the list is built.
3. On each rebalance date, rank the signal known at the previous close: the previous row of an unshifted signal, or the same row of a signal series that was already shifted by one day (never both), which needs at least $n_{\mathrm{long}} + n_{\mathrm{short}}$ valid and varying values; give the $n_{\mathrm{long}}$ largest the long weight, the $n_{\mathrm{short}}$ smallest minus the short weight, and every other asset 0.
4. Hold the rows as in Topic 10, with nothing held before the start.
5. Daily cost: the sum of absolute weight changes from the previous day times the cost rate. Daily return: $\sum_i w_{t,i}\, r_{t,i}$ minus the cost; the rebalance row's weights earn from that row.
6. Evaluate from the trading start onward (Topic 2).
7. Before writing outputs, print the rebalance dates and, for the first one, the date of the signal row that was ranked; every month after the start has exactly one rebalance date that is a trading day in the index, and the ranked row is the previous trading day. If not, fix step 2 or the lag and rerun.

**Implementation tips:** The Python session provides `backtest_tools.monthly_long_short(returns, signal, first_trade_row, n_long, n_short, w_long, w_short, cost_bps)`, which runs steps 2 to 5 with this contract: it ranks row $i-1$ of the unshifted signal for the book of row $i$, writes the whole book at each rebalance (exits at 0), charges `cost_bps` per unit of turnover on the first row the new book earns, and returns the daily returns from `first_trade_row` on, the rebalance rows and their count. Write your own loop where the task's rules differ from this contract.

**Limitations and cautions:**
- Shifting the signal before ranking the previous row lags it twice.
- A signal built on an integer index and reindexed to dates is all missing.
- The helper's optional argument `max_position=` (default: not applied) clips every position to $\pm$ that value after the weights are set; pass it only when the procedure text says to apply the limit to the positions.

**Double check:** The number of rebalances is one plus the number of month starts after the trading start; the first evaluated row is the trading start; the long and short weights on a rebalance row equal the per-name weights the procedure text names, and any conflicting limit is reported. If any differ, recheck the rebalance dates and the ranking row, then rerun.

References: CFA Institute, GIPS Standards for Asset Owners (2020), calculation methodology, for external-flow treatment and linked returns (https://www.cfainstitute.org/-/media/documents/code/gips/2020-gips-standards-asset-owners.pdf). Cash conservation, annualization and gross and net exposure are accounting or algebraic identities; this card does not assert GIPS compliance of a backtest.
