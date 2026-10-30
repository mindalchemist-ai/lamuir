# Daily signal backtest: position state, next-day execution and one row per trading day

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input or convention, follow the task description.

## Algorithm

Inputs: daily bars in date order (signal price and execution price), indicator series, entry and exit rules, costs. Outputs: a trades table, a daily portfolio table with one row for every trading day, and a summary.

1. Start with the initial cash, no shares, not in position, no pending order and no peak.
2. Go through the trading days in order, warm-up days included; a day whose indicator is undefined gives no signal.
3. If an order is pending, execute it at this day's execution price: a buy adds the shares and pays the cost and marks the position open; a sell receives the revenue, sets the shares to zero, closes the position and clears the peak. Then clear the pending order.
4. Value the portfolio as cash plus shares times this day's mark price, and append this day's row.
5. While in position, update the peak or trailing levels with this day's signal price.
6. On this day's close, when the indicator exists: if not in position and the entry rule holds, set a pending buy (sized by the rules) and set the peak to the signal price; if in position and an exit rule holds, set a pending sell.
7. On the last day, close a position still held as the task says (forced close).

The state flag changes only when a fill executes (step 3); a signal only sets `pending`. Forgetting to set `in_position` after a BUY fill keeps the strategy from ever exiting.

## Checks

1. The daily table has exactly as many rows as there are trading days in the data window, warm-up days included, and its first cumulative return is 1.0.
2. Trades alternate BUY, SELL, BUY, ...; every SELL follows a BUY; the number of trades is even unless a forced close is written separately.
3. Final capital equals cash after the last fill; recompute it from the trades table and compare.
