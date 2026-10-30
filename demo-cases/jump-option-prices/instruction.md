# How do Merton jump-diffusion option prices differ from Black-Scholes prices with the same total variance?

This is a pricing example under assumed parameters, not a market quote.

## Parameters

Spot $S_0=100$, maturity $T=0.5$ years, continuously compounded risk-free rate $r=0.04$, continuous dividend yield $q=0.01$, diffusion volatility $\sigma_D=0.15$. Jumps arrive as a Poisson process with intensity $\lambda=0.5$ per year; each jump multiplies the price by $J$ with $\ln J \sim N(\mu_J, \delta^2)$, $\mu_J=-0.10$, $\delta=0.15$. Strikes $K = 70, 75, \dots, 130$ (13 strikes). European options.

## Task

1. **Merton (1976) jump-diffusion price**, for calls and puts. Let $k = e^{\mu_J+\delta^2/2}-1$ and $\lambda' = \lambda(1+k)$. Then
   $$V = \sum_{n=0}^{N} \frac{e^{-\lambda' T}(\lambda' T)^n}{n!}\, V_{BS}(S_0, K, T, r_n, q, \sigma_n),$$
   where $r_n = r - \lambda k + n\ln(1+k)/T$, $\sigma_n^2 = \sigma_D^2 + n\delta^2/T$, and $V_{BS}$ is the Black-Scholes-Merton price with dividend yield $q$. Use exactly $N = 20$, so the sum has 21 terms ($n = 0, 1, \dots, 20$); the terms after that are below $10^{-20}$.
2. **Black-Scholes price with the same total variance.** Price the Black-Scholes columns `bs_call` and `bs_put` with the single volatility $\sigma_{BS} = \sqrt{\sigma_D^2 + \lambda(\mu_J^2+\delta^2)} = 0.196850196850$, **not** with $\sigma_D = 0.15$. As a check, `bs_put` at strike 70 is about 0.0134; with $\sigma_D$ it would be about 0.0005. Then both models give log returns the same variance per year, and any difference comes from the shape of the distribution.
3. For each strike compute $\text{diff} = V_{Merton} - V_{BS}$ for calls and for puts.
4. Check put-call parity, $C - P = S_0e^{-qT} - Ke^{-rT}$, for both models.

## Output

Write to `/app/output/`:

- `analysis.csv`, one row per strike in ascending order, columns `strike,bs_call,merton_call,call_diff,bs_put,merton_put,put_diff,n_terms`.
- `results.json` with these keys:
  - `sigma_bs`;
  - `n_terms` (integer, the number of series terms: 21);
  - `atm_call_diff` and `atm_put_diff` (strike 100);
  - `largest_put_diff_strike` (the strike with the largest `put_diff`);
  - `max_parity_error` (the largest absolute put-call parity error over both models and all strikes).
  
  Prices are unrounded.
- `chart.png`: the price difference (Merton minus Black-Scholes) against strike as a single line. By put-call parity `call_diff` and `put_diff` are the same number at every strike, so plot it once and label it "call and put (equal by parity)".
- `explanation.md`: start with one or two sentences that answer the question in the title directly, using the numbers you computed. Then give a short plain-English explanation, by strike, of where the jump model prices higher or lower than Black-Scholes and why, stating that the parameters are assumed. By put-call parity, `call_diff` equals `put_diff` at every strike, so describe the difference per strike rather than contrasting calls with puts.
