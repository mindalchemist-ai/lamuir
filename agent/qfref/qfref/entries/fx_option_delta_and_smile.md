# FX options: Garman-Kohlhagen value, delta conventions, strike from delta, smile wings, premium and Greek units

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input or convention, follow the task description. Explicit input conventions override market shorthand; a currency-pair name alone does not establish a delta convention.

Read the topics relevant to the task; a task usually needs several of them.

Notation used in every topic: $S$ is instantaneous domestic (terms) currency per foreign (base) unit, $K$ the same quote, $T_e > 0$ time to expiry, $T_d$ delivery time. $D_d, D_f$ discount to delivery under the specified deterministic domestic and foreign curves, with compatible collateral treatment. $\sigma > 0$ is annualized volatility, $\phi = 1$ for a call on the foreign currency, $\phi = -1$ for a put. $N$ is the standard normal CDF, $n$ its density.

## Topic 1: Option value and dates

**Purpose:** Price a European currency option from forward, volatility and discount factors.

**When to use:** European currency options. Map the quote direction, premium currency, notional, expiry and delivery separately.

**Constraints:**
- In a Garman-Kohlhagen setting the drift is $r_{\mathrm{terms}} - r_{\mathrm{base}}$.
- Total volatility $a = \sigma\sqrt{T_e}$ everywhere $a$ appears.

**How to implement:**
1. Check the inputs and print them: pair, base and terms currency, spot, strike, expiry and delivery times, both discount factors (or rates and their day counts), volatility in decimal.
2. $F = S\,D_f/D_d$ and $a = \sigma\sqrt{T_e}$.
3. $d_1 = \log(F/K)/a + a/2$, $d_2 = d_1 - a$.
4. $V_\phi = \phi D_d\{F N(\phi d_1) - K N(\phi d_2)\}$, the domestic value per foreign notional (terms pips).

**Limitations and cautions:**
1. A quoted spot with a future spot value date is not instantaneous $S$. Forward construction uses discount-factor ratios from that value date, while present value discounts from valuation. Adjust dates consistently before applying derivatives.
2. Stochastic rates, FX/reset convexity and collateral optionality require additional modelling.

**Double check:** Put-call parity: $V_{1} - V_{-1} = D_d(F - K)$ to rounding error.

## Topic 2: Delta conventions

**Purpose:** Compute the right one of four delta conventions.

**When to use:** A delta is requested, or a delta quote must be interpreted.

**Constraints:**
- Every delta is a dimensionless fraction per unit of base notional, between $-1$ and $1$. The words "pips delta" and "percentage delta" name the premium convention (premium in terms pips: excluded; premium in base-currency percent: included), not a unit: never multiply a delta by a point multiplier or by $10^4$.
- Spot delta carries $D_f$; unadjusted forward delta carries no discount factor.

**How to implement:**
1. Spot delta (holding curves and volatility fixed, derivative of domestic value in $S$): $\Delta_s = \phi D_f N(\phi d_1)$.
2. Unadjusted forward delta (spot delta divided by $D_f$): $\Delta_f = \phi N(\phi d_1)$. It is an undiscounted quotation; the literal derivative $\partial V/\partial F$ is $D_d\Delta_f$.
3. Premium-adjusted (premium-included) spot delta, the standard present-valued foreign-premium hedge: subtract the premium measured in foreign units, $\Delta_{s,\mathrm{pa}} = \Delta_s - V/S = \phi D_f (K/F) N(\phi d_2)$.
4. Premium-adjusted forward delta: $\Delta_{f,\mathrm{pa}} = \phi (K/F) N(\phi d_2)$.
5. Report each delta under the convention its field names; pips delta is the ordinary unadjusted delta (step 1 or 2, as the task says).

**Limitations and cautions:**
1. A later premium date requires its present value before conversion.
2. A premium-adjusted hedge is not an extra adjustment to option value.

**Double check:**
1. Every reported delta lies in $[-1, 1]$; a value such as $2500$ means a delta was scaled by a point multiplier.
2. For otherwise identical call and put, the ordinary spot-delta difference is $D_f$; the premium-adjusted spot-delta difference is $D_f K/F$.

## Topic 3: Strike from delta

**Purpose:** Invert a delta quote to a strike.

**When to use:** A strike is needed from a delta target, unadjusted or premium-adjusted.

**Constraints:**
- The strike must reproduce the target in the convention of the quote: a premium-adjusted target is met by the premium-adjusted delta (Topic 2, step 3 or 4), not by the unadjusted one.
- Put targets are normally negative; absolute-delta quotes first require the call/put sign.

**How to implement:**
1. Unadjusted forward target $\delta_f$ with $0 < \phi\delta_f < 1$: $K = F\exp\{-\phi a N^{-1}(\phi\delta_f) + a^2/2\}$. For an unadjusted spot target use $\delta_f = \delta_s/D_f$. The inverse-normal term is multiplied by the total volatility $a$, not by $\sigma$.
2. Premium-adjusted target (no closed form), as a line-by-line algorithm:
   1. `f(K) = delta_pa(K) - target`, with `delta_pa` from Topic 2 (spot or forward form, as quoted).
   2. Puts: `delta_pa` is monotone in $K$ at fixed volatility; bracket between a strike far below and one far above $F$ (for example $F e^{\pm 6a}$).
   3. Calls: at fixed volatility the premium-adjusted call delta can have two roots; the usual wing convention takes the larger-strike root, to the right of its delta maximum. Find the peak strike from $a N(d_2) = n(d_2)$, then bracket between that strike and the unadjusted-delta strike for the same target and spot/forward convention.
   4. Check that `f` has opposite signs at the bracket ends, then `K = scipy.optimize.brentq(f, lo, hi, xtol=1e-12)`.
   5. Recompute `delta_pa(K)` and print it next to the target.

**Limitations and cautions:**
1. Check that the target lies below the maximum of the call's premium-adjusted delta.
2. If volatility itself varies with strike, solve under the specified smile construction rather than assuming the fixed-volatility derivative still locates the peak.
3. A strike on a bracket end, or a premium near zero, means the root was not found.

**Double check:** The recomputed delta in the quote's convention equals the target within $10^{-8}$ (with the put formula for puts); a gap of a few hundredths means the strike was solved with the other convention.

## Topic 4: Smile wings from risk reversal and butterfly

**Purpose:** Build call-wing and put-wing volatilities and ATM strikes.

**When to use:** A smile is quoted by ATM, risk reversal and butterfly.

**Constraints:** Risk reversal means call-wing volatility minus put-wing volatility, and butterfly the arithmetic wing average minus ATM volatility, unless the task defines them otherwise.

**How to implement:**
1. $\sigma_c = \sigma_{\mathrm{ATM}} + \sigma_{\mathrm{BF}} + \tfrac12\sigma_{\mathrm{RR}}$ and $\sigma_p = \sigma_{\mathrm{ATM}} + \sigma_{\mathrm{BF}} - \tfrac12\sigma_{\mathrm{RR}}$.
2. ATM strikes: forward ATM means $K = F$; an unadjusted delta-neutral straddle gives $K = F\exp(a^2/2)$; its premium-adjusted counterpart gives $K = F\exp(-a^2/2)$ under these assumptions.

**Limitations and cautions:** A market-strangle premium quote is a different definition of butterfly and need not satisfy this direct split.

**Double check:** $\sigma_c - \sigma_p = \sigma_{\mathrm{RR}}$ and $(\sigma_c + \sigma_p)/2 - \sigma_{\mathrm{ATM}} = \sigma_{\mathrm{BF}}$.

## Topic 5: Premium and Greek units

**Purpose:** Report premium, Gamma and Vega in the right units and currencies.

**When to use:** Premium amounts, premium conversions or Greeks are requested per notional.

**Constraints:**
- $V$ of Topic 1 is in terms currency per unit of base notional (terms pips before any point multiplier). The same premium in base currency per unit of base notional is $V/S$; a base-percent premium is $100\,V/S$.
- Pips and percentage premium are not interchangeable.

**How to implement:**
1. Terms premium per unit base notional: $V$; times the pair's point multiplier when the task asks for points.
2. Base premium per unit base notional: $V/S$ (divide by spot, whatever multiplier the terms figure carries: base pips $=$ terms pips $/ S$).
3. For base notional $Q_f$: domestic premium $Q_f V$, present foreign equivalent $Q_f V/S$. A price per domestic notional uses its explicitly specified denominator.
4. Spot Gamma and Vega per foreign notional at fixed strike and curves: $\Gamma_s = D_f n(d_1)/(S\sigma\sqrt{T_e})$ and $\mathrm{Vega} = D_d F n(d_1)\sqrt{T_e}$, Vega per unit decimal volatility (per percentage point: $0.01$ times this).

**Limitations and cautions:** Sticky-strike and sticky-delta smile sensitivities are different: smile movement can add chain-rule terms.

**Double check:** Each unit (decimal versus percentage point, base versus terms currency) matches the field name, and for every row base premium times $S$ equals terms premium.

References: Garman and Kohlhagen (1983), Foreign currency option values, Journal of International Money and Finance 2(3); Reiswich and Wystup (2010), A guide to FX options quoting conventions, Journal of Derivatives 18(2); Clark (2011), Foreign Exchange Option Pricing: A Practitioner's Guide, Wiley.
