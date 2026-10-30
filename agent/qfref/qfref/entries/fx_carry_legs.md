# Currency carry legs: rate differential, carry return, signal activation and a hedge book with its own roll clock

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input, setting or convention, follow the task description.

Read the topics relevant to the task; a task usually needs several of them.

## Topic 1: Carry signal and carry-leg return

**Purpose:** Rank currencies by their interest-rate advantage and measure what a carry position earns.

**When to use:** The task builds an FX carry portfolio (long high-yield, short low-yield currencies) or reports carry returns.

**Constraints:**
- A carry signal is each currency's deposit rate minus the funding currency's rate, stored as that differential: the ranking is the same as for raw rates, but reported values and thresholds differ.
- A carry leg earns the currency's spot return against the funding currency plus the accrual of the rate differential over each holding interval, or equivalently the forward premium locked at entry.

**How to implement:**
1. Check the inputs and print them: the rate columns and their units (percent or decimal, annual), the funding currency, the spot quote direction of each pair (see the FX conventions entry), and the day count for accrual.
2. Signal on each signal date: rate differential per currency; rank and select the long and short baskets by the task's rule.
3. Daily leg return: spot return of the currency against the funding currency (in the direction of one unit of that currency) plus differential times the day-count fraction of that day.

**Limitations and cautions:** A spot-only return omits the intended source of profit and can reverse the Sharpe ratio's sign.

**Double check:** Over the whole sample, the accrual part of the long basket is positive and of the order of the average rate differential per year.

## Topic 2: Signal dates, activation and the active basket

**Purpose:** Apply each basket only after the information that formed it was available, so the backtest has no look-ahead.

**When to use:** Baskets are formed on signal dates (for example month-ends) and executed after a signal lag (for example the next business day).

**Constraints:**
- A daily strategy series lives on the trading dates of the price data, not on calendar days.
- A basket formed on signal date $d$ becomes active on its activation date: $d$ moved forward by the signal lag in business days of the price calendar. It applies from its activation date until the next activation.
- On the signal date itself, and on every day before the activation date, the previous basket is still active.

**How to implement:** As a line-by-line algorithm, with `dates` the sorted trading dates:
1. `signal_dates` = the signal dates by the task's rule (for month-end signals: the last trading date of each month in `dates`), and, when the strategy needs a position from its first day, the first date of the sample as an initial signal date if the task's rule allows it.
2. For each signal date `d`: `act = dates[dates.index(d) + lag]` (the `lag`-th trading date after `d`).
3. For each trading date `t`: the active signal date is the latest `d` with `act(d) <= t`; days before the first activation have no position.
4. Store both the active signal date and the basket on every row.

**Limitations and cautions:** Forming and applying on the same date uses that day's close twice (look-ahead) and moves every return by one day.

**Double check:** Print, for two consecutive signal dates, the signal date, its activation date, and the active signal date on the signal date and on the next trading date: on the signal date the active one is the previous signal date.

## Topic 3: A hedge book with its own roll schedule

**Purpose:** Overlay a forward hedge that is locked at each roll and stays unchanged until the next roll, independently of the monthly basket.

**When to use:** The task adds a forward-hedge overlay with its own roll frequency (for example quarterly) on top of a more frequently rebalanced portfolio.

**Constraints:**
- The hedge book keeps what it locked (currencies, spot, forward, delivery) until its own next roll, even when the carry basket changes; it uses its own signal dates and signal lag (Topic 2, steps 2 and 3).
- An overlay that hedges the portfolio from its start needs an initial book: the first roll is placed at the start of the strategy (the first signal date of the portfolio), then the rolls follow the configured roll months, unless the task places the first hedge elsewhere.

**How to implement:**
1. Roll signal dates: the initial roll at the start, then the last trading date of each configured roll month.
2. At each roll: lock the hedged currencies from the basket active at that roll, the spot and forward for the configured tenor, the delivery date (with the pair's calendar and business-day rule) and the hedge window to the next roll.
3. Hedge return over the window: the locked forward premium (forward over spot minus one), spread over the window's days as the task states.
4. On every daily row store which carry basket and which hedge book are in force.

**Limitations and cautions:** A book that waits for the first configured roll month leaves the first months unhedged and moves every hedge window by one period.

**Double check:** Print the first two rolls: signal date, effective date, currencies and window; the first roll is at the start of the strategy and the hedge currencies stay constant between rolls while the monthly basket changes.

References: Lustig, Roussanov and Verdelhan (2011), Common risk factors in currency markets, Review of Financial Studies 24(11); Burnside, Eichenbaum and Rebelo (2011), Carry trade and momentum in currency markets, Annual Review of Financial Economics 3.
