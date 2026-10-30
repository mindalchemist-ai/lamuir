# Signal, order and fill: when the position state changes in a single-asset backtest

Use this when a rule-based strategy decides on one bar (a close-price signal, a stop-loss or take-profit test) and the
trade fills on a later price (the next open, the next close). The decision day and the fill day are different, and the
position state must follow the fills, not the decisions.

## The state machine

- `position`, `shares` and `cash` change only on the fill bar, at the fill price.
- A fill bar is still a decision bar: after the order fills at the open, test that same bar's close for exits, stops and trailing-stop updates. A `continue` right after the fill skips that test, so an exit that fires on the entry day is missed and the trade closes later than the rules say, unless the task fills at the close or forbids a decision on a fill bar (see below).
- A decision made on bar t while flat creates a pending entry; while long it creates a pending exit. The pending order
  fills on the next bar; on that fill bar apply the fill first, then evaluate the bar's close-based rules (peak or
  trailing-stop update, stop test, signal exit, new entry) against the post-fill state.
- On the bar where an exit signal fires, the strategy is still long; an entry test on that same bar sees a long
  position and does nothing. After the exit fills, the next bars test for entry again.
- Several exit rules can fire on one bar (a stop-loss, a take-profit, a signal exit). Which one is recorded follows the
  task's order of checks; if the task lists them in a sequence, test them in that sequence and record the first that
  fires. If it states no order, state the order used. Exit labels are the task's labels, not the names in the sketch.
- A stop can fill in two ways: at the next fill price after a close-based test (decide on the close, fill on the next
  bar), or on the same bar at the stop price when the task says the stop triggers intrabar (the bar's low is at or
  below the stop level; a gap through the stop fills at the open instead). Use the one the task describes.
- Reversing in one step (sell and buy on the same fill) happens only when the task allows it.

Bar-by-bar state, with orders decided on one bar and filled on the next:

1. Keep the position (flat or long), the cash, the shares, the entry price and a pending order (side and reason) decided on the previous bar.
2. At the start of each bar, if an order is pending, fill it at the fill price the task names (for example this bar's open). A buy sizes the shares by the task's sizing rule, pays shares times fill price and records the entry price; a sell receives shares times fill price, records the closed trade (entry, exit, reason) and resets the shares to zero.
3. Then evaluate the close-based rules on this bar, which see the state after this bar's fill: when long, a stop or exit signal sets a pending sell with the task's reason label, checking the conditions in the task's order; when flat, an entry signal sets a pending buy.

Position size on entry follows the task's sizing rule:
- all available cash in whole shares, `floor(cash / fill)`: the task says to invest all cash and buy whole shares;
- all cash with fractional shares, `cash / fill`: fractional shares are allowed;
- a fixed number of shares or contracts, or a fixed notional (`notional / fill`): the task gives one;
- a risk-based size, `risk_budget / (entry - stop)` capped by cash: the task sizes by risk per trade; if
  `entry - stop <= 0` the size is undefined, so take no position unless the task states a fallback (never an
  unlimited or all-cash size);
- with a fee per trade or a cost rate, the cash available shrinks: `floor((cash - fixed_fee) / (fill * (1 + rate)))`.

Check after the loop: no bar has both a SELL fill and a BUY fill unless the task allows reversing, the number of BUY
fills equals the number of SELL fills (plus one if a position is open at the end), and every trade's exit date is
after its entry date. For each trade, recompute from the price series alone the first bar at or after the entry fill
on which the exit rule fires; it must equal the recorded exit-signal bar. The daily valuation table keeps every input
trading day, warm-up rows included, unless the task says to drop them.

The sketch fills at the bar's open and then tests that bar's close against the updated state. If the task fills at the
close or forbids a decision on a fill bar, follow the task and state the rule used.
