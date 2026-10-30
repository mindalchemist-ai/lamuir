# FX conventions: quote direction, crosses, covered forwards, signed positions

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input or convention, follow the task description.

## Topic: Quote direction and USD conversion

**Purpose:** Convert any currency to USD with one function so no pair is inverted by accident.

**When to use:** Any FX code: P&L, exposure, cross, forward. Always apply before other FX topics.

**How to implement:** In a quote BASE/TERMS the number is the amount of terms currency paid for one unit of base. Write one `usd_per(ccy, side)` returning the USD value of 1 unit of any currency, and reuse it everywhere. An X/USD quote already is USD per X. A USD/Y quote must be inverted, and inverting swaps bid and ask.
USD value of one unit of a currency $c$ from the quotes on the given side: 1 for USD; the $c$/USD quote if it exists; otherwise $1/(\text{USD}/c)$ taken from the opposite side (a bid of $c$ in USD comes from the ask of USD/$c$). Check: the USD value of one JPY times the USD/JPY mid is 1.

**Limitations and cautions:**

1. Build every cross rate, spot or forward for every tenor, from `usd_per` of its two currencies: cross(BASE/TERMS) = usd_per(BASE) / usd_per(TERMS). This works whatever the direction of the USD legs. Code that assumes one leg layout fails with a missing-pair KeyError on the other.
2. A pair quoted directly in the inputs is used as quoted unless the task asks to derive it from the legs.
3. `usd_per` already inverts a USD-base quote once and swaps its sides. Inverting or swapping again turns the cross upside down.

**Double check:**

1. A pair and its inverse multiply to one: `assert abs(cross(a, b) * cross(b, a) - 1) < 1e-12` for mids.
2. The USD value of a weak currency (JPY) is far below 1.

## Topic: Crosses with bid and ask

**Purpose:** Build cross bid, ask and mid for spot and for each forward tenor.

**When to use:** A cross pair is requested or needed and both legs are quoted against USD.

**How to implement:** Express both legs as USD per unit, then divide. Selling the base and buying the terms happens at the worst side of each leg: the cross bid is the base's USD bid over the terms' USD ask; the ask is the other way round.
Cross rate $X/Y$: bid $= \text{usd}_X(\text{bid})/\text{usd}_Y(\text{ask})$, ask $= \text{usd}_X(\text{ask})/\text{usd}_Y(\text{bid})$, mid $= \text{usd}_X(\text{mid})/\text{usd}_Y(\text{mid})$.
For two USD-base legs (USD/X, USD/Y) this gives bid = (USD/Y bid)/(USD/X ask). Multiplying legs takes the same side of both; dividing takes opposite sides. Dealer rule by leg layout (every row equals the `usd_per` construction):

| USD legs | cross X/Y | bid | ask |
|---|---|---|---|
| X/USD and USD/Y | multiply | (X/USD bid) * (USD/Y bid) | (X/USD ask) * (USD/Y ask) |
| X/USD and Y/USD | divide | (X/USD bid) / (Y/USD ask) | (X/USD ask) / (Y/USD bid) |
| USD/X and USD/Y | divide, terms leg on top | (USD/Y bid) / (USD/X ask) | (USD/Y ask) / (USD/X bid) |
| USD/X and Y/USD | invert the product | 1 / ((USD/X ask) * (Y/USD ask)) | 1 / ((USD/X bid) * (Y/USD bid)) |

One function for spot and for each tenor's outright forwards keeps the side mapping in one place:
The same construction applies to spot and to one tenor's outright forward bid, ask and mid. Check every cross: bid below ask, and the mid between them.

**Limitations and cautions:**

1. Writing the side mapping by hand is where crosses go wrong. A division that takes the same side of both legs puts bid above ask in about half of all quote sets.
2. Round only when writing output. Rounding legs first can make bid equal ask.
3. A forward cross takes each leg's outright forward bid and ask for that tenor and passes them through the same function. Crossing mids and adding a spread afterwards is a different quote.

**Double check:**

1. For every computed pair, spot and each tenor: `bid < ask` and `bid <= mid <= ask`. Bid above ask means a side was flipped twice or taken from the same side of both legs.
2. For one cross, recompute the mid by hand from the raw leg quotes (for example X/JPY $=$ USD/JPY $/$ USD/X with both USD-base legs) and compare with the function's result: an inverted cross passes the bid-ask check but is far off this number (a cross against JPY is in the tens or hundreds, a JPY-base cross far below 1).

## Topic: Covered forward and implied rates

**Purpose:** Compute the covered forward, forward points and implied deposit rates.

**When to use:** Spot and two interest rates (or discount factors) are given and a forward, forward points or an implied rate is asked.

**How to implement:** The terms currency plays the domestic role. Each currency uses its own day count. The accrual factor follows how the rates are quoted:

- money-market (simple) deposit rates: $(1+rt)$, the usual reading for deposit or LIBOR-style quotes up to a year;
- continuously compounded: $e^{rt}$;
- annually compounded: $(1+r)^t$;
- discount factors from curves: $F = S\,P_{base}(T)/P_{terms}(T)$.

The task's description of the rates ("deposit rate", "continuously compounded", "zero rate", a curve of discount factors) decides. The skeleton below is the simple-rate case; the implied-rate inversions change with the accrual form.
Covered-interest forward with simple rates, base currency rate $r_b$ over $t_b$ and terms currency rate $r_t$ over $t_t$ (use $e^{rt}$ or $(1+r)^t$ for other quote types):

1. $F = S\,\frac{1 + r_t t_t}{1 + r_b t_b}$.
2. Forward points: $(F - S)$ times the pip multiplier.
3. Implied base rate: $r_b = \left(\frac{S(1 + r_t t_t)}{F} - 1\right)/t_b$.
4. Implied terms rate: $r_t = \left(\frac{F}{S}(1 + r_b t_b) - 1\right)/t_t$.

**Limitations and cautions:**

1. Which implied-rate formula applies depends on where the unknown currency sits in the quote, not on which currency is "foreign" to the investor.
2. With one deposit rate per currency, apply the same accrual factor to spot bid and spot ask.
3. When a task maps bid/offer sides explicitly, write the mapping as a small table in code.

**Double check:**

1. Round trip: `abs(fwd(S, r_base_implied, t_base, r_terms, t_terms) - F) < 1e-10` and the same for `r_terms_implied`.
2. Implied bid < implied offer when sides are mapped.

## Topic: CIP deviation

**Purpose:** Measure a forward's deviation from covered interest parity in the right unit.

**When to use:** A CIP deviation or cross-currency basis is requested, on a pair that has both deposit rates.

**How to implement:** Compare a forward with the parity forward from the two deposit rates. Which forward depends on the inputs:

- market forwards or forward points are supplied: the deviation is usually not 0 (the cross-currency basis). Its unit follows the field. In bp of spot: `(F_market - F_cip) / S * 1e4`. In pips or forward points: `(F_market - F_cip) * point_multiplier`, with no division by S. For a deviation field, a key ending in `_pips` or `_points` is the second kind. A forward-points field itself is `(F - S) * point_multiplier`, not a deviation.
- the forward is built from parity in the code: the deviation is about 0, and the line is an identity check of the build.

The unit and which pairs to report follow the task's key names and unit notes.

**Limitations and cautions:**

1. The gap between an exact parity formula and its linear approximation is not a CIP deviation.
2. The forward premium $(F-S)/S\times 10^4$ is not a CIP deviation. It is the interest-rate differential parity predicts (about 35 bp over three months for a 140 bp rate gap), while the parity deviation of the same forward is 0.
3. A deviation subtracts the parity forward, never spot.

**Double check:**

1. A forward built from parity gives a deviation of about 0.
2. The unit matches the field name (bp of spot versus pips or points).

## Topic: Signed forward positions

**Purpose:** Compute forward P&L, spot and carry parts, and currency exposure with consistent signs.

**When to use:** Trades buy or sell a base currency forward and P&L or exposures are requested.

**How to implement:** Let $s=+1$ when buying the base currency forward, $-1$ when selling. Apply $s$ to every component, then convert terms-currency amounts with `usd_per(terms)`. The terms leg of a position is $-N\times$ leg_rate in the terms currency; for exposures of an existing contract, leg_rate is its contract rate $K$.
Forward trade on notional $N$ of the base currency at strike $K$, with sign $s = +1$ to buy the base and $-1$ to sell it:

1. Mark-to-market P&L in terms currency: $s N (F_{\mathrm{now}} - K)$.
2. Spot component: $s N (S_{\mathrm{now}} - S_{\mathrm{then}})$; carry component: $s N (F_{\mathrm{now}} - S_{\mathrm{now}})$; the residual is the P&L minus both.
3. Convert each to USD with the terms currency's USD value.
4. Leg cash flows: $s N$ units of the base currency, and $-s N$ times the leg rate in the terms currency, each in USD.
The terms leg can be read two ways: the contract amount (rate = K, the cash actually exchanged) or a mark-to-market delta (rate = current forward F). Both are standard; the task's wording decides.

**Limitations and cautions:**

1. In a per-trade loop, read every trade field (notional, side, contract rate K, tenor) from the current row. A name left over from an earlier loop silently prices every trade at the last trade's value.
2. The residual sums to the total by construction, so checking the sum is useless.

**Double check:**

1. Buy and sell of the same trade are exact negatives: `all(abs(b + c) < 1e-6 for b, c in zip(buy, sell))`.
2. `(buy[1] > 0) == (S_now > S_then)`.
3. Check the size of the residual, not the sum.

## Topic: Swap points and roll quotes

**Purpose:** Express a swap (roll) quote in the right unit.

**When to use:** Near and far forward points or outrights are given and a swap or roll is requested.

**How to implement:** A swap (roll) quote is far points minus near points. In dealer quoting it is stated in pips, the unit of the points columns. As a price difference it is far outright minus near outright $=(\text{far points}-\text{near points})/\text{multiplier}$.

**Limitations and cautions:**

1. The two forms differ only by the multiplier. Pick the unit the output field's name and the task's unit notes describe.

**Double check:**

1. The output unit matches the field name (pips versus price difference).

## Topic: Daily series from monthly data

**Purpose:** Align monthly values to a daily trading-date index without look-ahead.

**When to use:** A daily output is built from monthly signals or data.

**How to implement:** Index the daily output on the trading dates present in the daily price file, then carry the latest monthly value forward (`merge_asof` with `direction="backward"`). A "month-end" signal is the last trading date of that month in the data.

**Limitations and cautions:**

1. A calendar-day range adds weekends and holidays.

**Double check:**

1. Every output date exists in the daily price file.

## Topic: Pandas arguments, rounding and day count

**Purpose:** Map task wording to correct pandas, rounding and day-count choices.

**When to use:** The task says "daily", "month end", "lag", "round to n decimals", "ACT/360" or similar.

**How to implement:**

- `pd.date_range` freq: "D" calendar days, "B" weekdays. Neither equals the data's trading dates. Wording "daily" in a backtest usually means the price file's rows.
- `pd.merge_asof` direction: "backward" uses the last known value (information available on that date). "forward" or "nearest" can look ahead.
- `DataFrame.shift(k)` with positive k moves values later. "Active the next business day after the signal" is a shift by the lag on the trading-date index, not a calendar offset.
- Rounding "to n decimals" in the output is applied once at serialization.
- Day count "ACT/360" and "ACT/365": $t$ = actual days / 360 or / 365, counted from the spot date to delivery unless the task names other dates.

**Limitations and cautions:**

1. The month-end alias "M" gives a FutureWarning in late pandas 2 releases and raises in pandas 3. Use "ME" for month end and "MS" for month start, which work in both.
2. Python `round()` rounds the stored binary value half-to-even (`round(2.675, 2)` gives 2.67).

**Double check:**

1. No look-ahead: each output date uses only information available on that date.
