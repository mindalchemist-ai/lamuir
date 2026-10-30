# Historical-simulation VaR / ES and the expanding-window VaR backtest
The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input or convention, follow the task description.

Historical-simulation (HS) VaR at confidence $c$ is an order statistic of the empirical loss distribution, and ES is the mean of the losses at or beyond that order statistic. Write one function with one order-statistic rule and reuse it for the full sample, ES and every backtest window.

1. Inputs: the portfolio return series $r_1, \dots, r_n$, the confidence $c$ and the tail $\alpha = 1 - c$.
2. Losses: $L_i = -r_i$, positive for a loss.
3. Choose one order-statistic rule; the task's definition wins. Common choices:
   1. Sort the losses in descending order and take $k = \lceil n\alpha \rceil$ (at least 1): VaR is the $k$-th largest loss and ES the mean of the $k$ largest losses.
   2. The interpolated quantile `numpy.quantile(L, c, method=...)`, with ES the mean of the losses at or above the VaR.
   3. As choice 1 with $k = \lfloor n\alpha \rfloor$.
   If the task does not say, pick one and state it in the output. An ascending sort changes which element is the $k$-th; check that the VaR is a large loss.
4. ES uses the same $k$, or the same threshold, as the VaR from the same sorted losses.
5. Write steps 2-4 once, as one function of a return window and $c$, and use it for the full sample and for every backtest window.
6. Expanding-window backtest: for each test day $t$, the window is the returns strictly before $t$; the day is an exceedance when $L_t$ exceeds that window's VaR (or reaches it, if the task says so). Count the exceedances $x$ over the $T$ test days.
7. Kupiec proportion of failures with $p = \alpha$ and $\hat{p} = x/T$: $\mathrm{LR} = -2\left[(T - x)\ln(1-p) + x \ln p - (T - x)\ln(1 - \hat{p}) - x \ln \hat{p}\right]$, p-value from the chi-square survival function with one degree of freedom; when $x = 0$ drop the $x \ln \hat{p}$ term.
8. Apply unit scaling (returns or currency) once, at output time; every summary statistic taken from a per-method table uses the units of that table.

Checks:
- $\mathrm{ES}_c \ge \mathrm{VaR}_c > 0$ for each confidence, and the full-sample HS VaR equals `hs_var_es` applied to all data.
- Backtest exceedance rate is near $\alpha$ (same order of magnitude); a rate near $1-\alpha$ or near 0.5 means the sort direction or k is inverted.
- Summary ranges / min / max match the per-method table they summarise (same units).
