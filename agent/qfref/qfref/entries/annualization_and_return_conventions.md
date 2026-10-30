# Annualization and return conventions

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input, setting or convention, follow the task description.

Use this when a task turns prices into returns, aggregates returns over time, or reports annualized returns or volatilities. A number or formula the task states always wins; the rows below say what to use when it does not.

## Decisions

| Decision | Options | How the task text selects | When the text is silent |
|---|---|---|---|
| Periods per year A | a stated annualization factor; 252; 365 or 365.25; 52; 12 | A given factor or "periods per year" is used as is. "Trading days" or daily exchange data usually means 252; calendar-day accrual, assets that trade every day, or "calendar days" mean 365 (or 365.25 if written); weekly 52; monthly 12. | Count the observations per year in the data's date column and use the conventional value that matches its frequency, then state it. |
| Volatility scaling | sqrt(A) * sd of period returns; a method the task gives for dependent returns | sqrt(A) assumes uncorrelated period returns; the same rule gives sqrt(h) for an h-period horizon. | sqrt(A), stated as an i.i.d. approximation. |
| Annual return | arithmetic: A * mean(r); geometric: (1 + R_total) ** (A / n) - 1 | "Arithmetic", a formula of mean times A, or a Sharpe-ratio numerator usually means arithmetic; "compound", "CAGR", "geometric" or a formula with a power means geometric. The years elapsed can be n / A or the calendar span in days / 365 (or 365.25). | Report what the field name says (a "CAGR" field is geometric); otherwise arithmetic for ratios built from means, geometric for growth of wealth, and say which. |
| Return definition | log: ln(P[t] / P[t-1]); simple: P[t] / P[t-1] - 1 | "log", "ln", "continuously compounded" mean log; "percentage change", "pct_change", "simple", "arithmetic return" mean simple. | Simple returns for portfolios and wealth, log returns for models written in logs; state the choice. |
| Aggregating over time and across assets | log returns add over time; simple returns compound over time; portfolio returns weight simple returns | A portfolio's return is the weighted sum of simple returns; weighting log returns is only an approximation. | — |

Use one definition for every quantity derived from the same series: a Sharpe ratio, a volatility and a drawdown reported together come from the same returns and the same A.

## Check

1. Simple and log returns are linked exactly: $\ln(1 + r^{s}_t) = r^{\ell}_t$; compound simple returns, add log returns, and both give the same total return.
2. Periods per year $A$ come from the data: count the rows per calendar year (about 252 for weekday data, 12 monthly, 52 weekly, 365 calendar daily).
3. Arithmetic annualized return: $A \cdot \bar{r}$.
4. Geometric annualized return over $n$ periods: $\prod_t (1 + r_t)^{A/n} - 1$, which equals $\exp(A \cdot \overline{r^{\ell}}) - 1$.
5. Annualized volatility: $\sqrt{A} \cdot s_r$, with the sample standard deviation (divisor $n-1$).
6. The geometric return is below the arithmetic one whenever the volatility is positive; if it is not, the compounding or the period count is wrong.
