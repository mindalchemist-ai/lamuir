# Characteristic-function option prices: choosing and checking a numerical integration

The task description inside <task_instructions> takes priority over this card: where it gives a different formula or a rule, follow the task description.

## Concepts

Semi-analytic prices such as $C = S e^{-qT} P_1 - K e^{-rT} P_2$ with $P_j = \tfrac12 + \tfrac1\pi \int_0^\infty \mathrm{Re}\left[\frac{e^{-i\eta \ln K} g_j(\eta)}{i\eta}\right] d\eta$ have an oscillating integrand. Integration error appears first where the price is small: short maturities and deep out-of-the-money strikes.

## Algorithm: judge integration methods against a high-accuracy reference

1. Price the comparison grid with every candidate method exactly as the task specifies it.
2. Compute reference prices from a much more accurate integration: `scipy.integrate.quad` with `epsabs` and `epsrel` of $10^{-12}$, a larger `limit` (for example 1000) and an upper bound well beyond where the integrand has decayed; doubling the bound must not change the price.
3. The error of each method is the maximum over the grid of the absolute difference from the reference; print all of them.
4. Test every price against the no-arbitrage bounds $\max(S e^{-qT} - K e^{-rT}, 0) \le C \le S e^{-qT}$, with $C$ decreasing and convex in $K$; a method that gives a price below its lower bound (for example a negative call) is inaccurate there.
5. Two methods agreeing or disagreeing with each other does not show which one is accurate. The difference between two methods is the same number for both of them, so a rule that ranks the methods by that difference (or by each method's distance from their mean) always ties and decides nothing. When the task's selection rule compares the methods, decide with the errors from step 3 and the bounds from step 4, apply the rule, and state the numbers that decided it.
   Check before saving the choice: `assert (chosen_prices >= lower_bound - 1e-8).all()` on the comparison grid; if it fails, the other method is the more accurate one there.
6. Use the chosen method, with the task's settings, for all later prices.

## Implied volatility from these prices

- Before root-finding, check the price against the same bounds. A price at or below the lower bound has no implied volatility above zero; a solver bracket such as $[10^{-4}, 5]$ then returns its lower end.
- An implied volatility equal to the lower end of the search interval is a diagnosis of the price, not a result: check the integration at that strike and maturity.
- Deep out-of-the-money short-dated prices can be smaller than the absolute tolerance of the integrator; tighten `epsabs`/`epsrel`, raise the upper integration limit, or use the method with the smaller error in steps 3 and 4.
