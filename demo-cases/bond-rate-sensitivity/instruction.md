# How much would a 10-year, 4%-coupon bond's price fall if its yield rose 100 bp from the end-2024 10-year Treasury yield?

This is an example with a hypothetical bond, not a quote for a real Treasury bond.

## Data

`/app/data/treasury_par_yield_curve_2024.csv` is the U.S. Treasury's Daily Treasury Par Yield Curve Rates file for 2024, as published. `Date` is `MM/DD/YYYY`; the other columns are par yields in percent by tenor; rows are in the Treasury's order (latest first).

## Task

1. **Yield.** Take the `10 Yr` yield on the last date of 2024 and use it as the bond's yield to maturity $y$, as a decimal with annual compounding (for example 4.58 becomes 0.0458).
2. **Bond.** Face value 100, annual coupon 4 (4% of face), 10 annual payments at $t = 1, \dots, 10$; the face value is repaid with the last coupon. Price it just after a coupon date: $P = \sum_{t=1}^{10} CF_t/(1+y)^t$.
3. **Sensitivity.**
   - Macaulay duration $D_{mac} = \sum_t t\,PV_t / P$, where $PV_t = CF_t/(1+y)^t$;
   - modified duration $D_{mod} = D_{mac}/(1+y)$;
   - convexity $C = \sum_t t(t+1)\,PV_t / \big(P(1+y)^2\big)$.
4. **Rate rise.** Reprice the bond exactly at $y + 0.01$. Also compute the approximation $P\,(1 - D_{mod}\cdot 0.01 + \tfrac12 C \cdot 0.01^2)$ and its error (approximation minus exact price).
5. **Chart data.** For yield changes $\Delta y = -0.03, -0.0275, \dots, +0.03$ (25 values), compute the exact price at $y + \Delta y$, the duration-only approximation $P(1 - D_{mod}\Delta y)$, and the duration-plus-convexity approximation $P(1 - D_{mod}\Delta y + \tfrac12 C\,\Delta y^2)$.

## Output

Write to `/app/output/`:

- `analysis.csv`, one row per payment, columns `t,cashflow,pv`, computed at the base yield $y$.
- `price_curve.csv`, one row per yield change in ascending order, columns `yield_change_bp,exact_price,duration_approx,duration_convexity_approx`. Here `yield_change_bp` is $10000\,\Delta y$.
- `results.json` with these keys:
  - `yield_date` (ISO date) and `yield` (decimal);
  - `price`, `macaulay_duration`, `modified_duration` and `convexity`;
  - `price_up_100bp` (the exact price at $y + 0.01$) and `price_change_pct` ($100\,(P_{up}/P - 1)$, in percent);
  - `approx_price_up_100bp` and `approximation_error`.
  
  Values are unrounded.
- `chart.png`: price against yield change, showing the exact price curve and the two approximations.
- `explanation.md`: start with one or two sentences that answer the question in the title directly, using the numbers you computed. Then give a short plain-English explanation of how much the price falls when rates rise one point, what duration and convexity mean, and why the duration-only line falls below the exact curve. It should state that the bond is hypothetical.
