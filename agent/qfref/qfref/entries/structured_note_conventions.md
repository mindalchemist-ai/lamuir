# Principal-protected note on a down-and-out call: conventions and formulas

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input, setting or convention, follow the task description.

When to use: a task values a note that repays principal at maturity and adds participation in a down-and-out call, then reports Greeks, delta-based VaR / ES or the issuer's premium.

Several quantities in such a report have more than one accepted definition. The table lists each choice point with its readings. Take the reading the task's text defines; when the text does not define it, pick one, and write the choice and the reason in a code comment next to the line that uses it.

## 1. Choice points

| Choice point | Readings | Situation -> what to do |
|---|---|---|
| Expected shortfall formula | textbook normal ES: `es = sd * pdf(z) / (1 - c)`, with `sd` the P&L standard deviation and `z = norm.ppf(c)` (McNeil, Frey and Embrechts; equivalently `var * pdf(z) / (z * (1 - c))` when `var = z * sd`) | the task writes an ES formula -> use it exactly; otherwise use this form and check `es / var = pdf(z) / (z * (1 - c))`, about 1.15 at 99% |
| GARCH mean equation | zero mean (`mean="Zero"`), constant mean (`mean="Constant"`, the `arch` default), or another mean model | the task names the mean -> use it; returns were demeaned in the task, or it says zero mean -> zero; nothing said -> pick one and comment; the fitted omega, alpha, beta move slightly between the two |
| Return scaling for the fit | fit on returns times 100 (percent) and divide omega by 100**2 afterwards, or fit on raw decimals | the task fixes the fitting units -> use them; otherwise fit percent returns. On raw daily decimals the optimizer can stop at its starting values and still report `convergence_flag == 0`; check that alpha and beta moved, for example by refitting on percent returns and comparing after the conversion |
| Variance and volatility units | daily variance (decimal squared), annualized variance (daily times periods per year), daily or annualized volatility | the task's field name or text says which -> use it; a volatility that is the pricing input, or that is reported beside a breakeven or implied volatility, is reported in the pricing units (annualized when maturity is in years), the same number that enters the option formula; per-period figures such as `omega / (1 - alpha - beta)` stay per period unless labeled annualized |
| Volatility used for pricing | (a) final in-sample value of `conditional_volatility` (the variance for the last observed day, built from information up to the day before); (b) one-step-ahead forecast `res.forecast(horizon=1).variance` (includes the last return); (c) the long-run volatility `sqrt(omega / (1 - alpha - beta))`; (d) a given implied volatility | the task names one -> use it; annualize a daily figure by `sqrt(periods_per_year)` (252 for daily trading data) and say so |
| Issue price | stated offer price, or par (`issue_price = N`) | a stated price -> use it; none -> par, commented |
| Premium / markup denominator | over fair value: `(issue - fair) / fair`; over issue price: `(issue - fair) / issue`; investor view `fair - issue` | the wording decides: "over fair value", "relative to theoretical value" -> fair; "margin on the issue price", "as a share of what the investor pays" -> issue; state the sign convention |
| Number of options | `N * p / S0` (participation in the percentage return of the underlying), `N * p / K`, or a stated count | follow the payoff the task writes: `p * N * max(S_T / S0 - 1, 0)` gives `N * p / S0` |
| Delta bump | relative (`dS = h * S0`) or absolute (`dS` in price units); central `(f(S+dS) - f(S-dS)) / (2 dS)` or one-sided; or the analytic delta | the task gives the bump -> use it; none -> central difference with a small relative bump, and confirm the delta does not change when the bump is halved |
| Exposure inside VaR | (a) equity delta only: `delta_total * S0 * sigma_daily`; (b) whole note: equity delta plus the bond's rate exposure (PV01 times a rate volatility); (c) full revaluation of bond and option | the task names the risk factors -> include those; it names only the underlying's returns -> (a), and comment that the bond's rate risk is left out |
| Volatility inside VaR | the annual pricing volatility divided by `sqrt(periods_per_year)`, or a daily estimate such as the GARCH one-step forecast | the volatility the task names for risk; it may differ from the pricing one |
| Horizon and confidence | one day, ten days (square root of time), or the stated horizon; the stated confidence level `c` | always from the task; no default |

## 2. Formulas

Bond leg, rate `rate` with continuous compounding, `T` years:

Zero-coupon leg: $N e^{-rT}$ with a continuous rate, or $N/(1+r)^T$ with an annually compounded quote.

Down-and-out call, barrier `B` at or below strike `K`, continuous monitoring, no rebate, no dividends: vanilla call minus down-and-in call (Reiner and Rubinstein, Risk 4(8), 1991; Hull, Options, Futures, and Other Derivatives, barrier options section of the exotic options chapter). With a dividend yield `q`, use `rate - q` in `lam` and in `d1`, and multiply each spot term by `exp(-q T)`. A barrier above the strike, a rebate, or discrete monitoring needs other formulas (Broadie, Glasserman and Kou shift a down barrier by `exp(-0.5826 * sig * sqrt(dt))` for discrete monitoring).

Down-and-out call (barrier $B$ below the strike $K$, continuous monitoring, no rebate), zero when $S \le B$; with $\sigma_T = \sigma\sqrt{T}$:

1. Vanilla call: $C = S\Phi(d_1) - K e^{-rT}\Phi(d_2)$, $d_1 = \frac{\ln(S/K) + (r + \sigma^2/2)T}{\sigma_T}$, $d_2 = d_1 - \sigma_T$.
2. $\lambda = (r + \sigma^2/2)/\sigma^2$ and $y = \frac{\ln(B^2/(SK))}{\sigma_T} + \lambda\sigma_T$.
3. Down-and-in call: $C_{di} = S (B/S)^{2\lambda}\Phi(y) - K e^{-rT}(B/S)^{2\lambda - 2}\Phi(y - \sigma_T)$.
4. Down-and-out call: $\max(C - C_{di}, 0)$.

Sanity checks: `0 <= doc(S, sig) <= vanilla call`; `doc(B, sig) == 0`; `doc + down-and-in == vanilla`; `sig` is annual.

Note value and premium:

1. Number of options: $N p / S_0$ (see the table for other readings).
2. Fair value: zero-coupon leg plus the number of options times the down-and-out price at $(S_0, \sigma)$.
3. Premium: $(\text{issue price} - \text{fair})/\text{fair}$, or divided by the issue price, per the table.

Implied (breakeven) volatility: the `s` with `zero_leg_pv + option_count * doc(S0, s) == issue_price`. A down-and-out call is not always increasing in volatility (a higher volatility also raises the knock-out probability, so vega can turn negative when the barrier is near spot), so there may be no root or two roots. Scan a grid first and bracket only where the sign changes; `brentq` raises `ValueError` when the two ends have the same sign.

Implied (breakeven) volatility: scan the fair value minus the issue price over a volatility grid (for example 400 points from 0.01 to 2.0), and solve with a bracketing root finder (`scipy.optimize.brentq`) inside every interval where the sign changes. No sign change means no volatility reprices the note; report that rather than a number.

Delta and delta-normal risk for one period:

1. Bump $\Delta S = h S_0$ per the table; delta per option $= (\mathrm{DOC}(S_0 + \Delta S) - \mathrm{DOC}(S_0 - \Delta S))/(2\Delta S)$; total delta = number of options times that.
2. P&L standard deviation over the horizon: $|\text{total delta}| \cdot S_0 \cdot \sigma_{\mathrm{period}}$.
3. With $z = \Phi^{-1}(c)$ at the confidence level $c$: VaR $= z \cdot \mathrm{sd}$ and ES $= \mathrm{sd}\cdot\phi(z)/(1-c)$; their ratio is $\phi(z)/(z(1-c))$.

GARCH fit with the `arch` package and the two volatility readings:

GARCH volatility for pricing: fit on percent returns with the task's mean model, convert $\omega$ by $100^2$; persistence is $\alpha + \beta$ and the per-period long-run variance $\omega/(1 - \alpha - \beta)$. Reading (a) is the last in-sample conditional volatility divided by 100; reading (b) is the square root of the one-step forecast variance, divided by 100. Annualize the chosen daily volatility by $\sqrt{\text{periods per year}}$ before pricing, and report a pricing volatility in those units.
