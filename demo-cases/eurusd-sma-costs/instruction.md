# Does a 50/200-day moving-average crossover on EUR/USD beat buy-and-hold after 2 bp trading costs, 2015–2025?

## Data

`/app/data/ecb_eurusd_2015_2025.csv` is the ECB Data Portal's CSV export of the daily euro reference rate against the U.S. dollar, from 2015-01-02 to 2025-12-31, unchanged. `TIME_PERIOD` is the date and `OBS_VALUE` the rate, in **U.S. dollars per 1 euro**. Treat it as the EUR/USD price. There is one row per ECB business day; days without a rate are simply absent.

## Task

1. Sort by date and use `OBS_VALUE` as the price; call the rows days $0, 1, \dots, n-1$. Do not fill missing days: consecutive rows are consecutive observations.
2. **Signal.** On day $t \ge 199$, $s_t = 1$ if the 50-day simple moving average (days $t-49..t$) is strictly above the 200-day one (days $t-199..t$), otherwise $s_t = 0$. Days 0-198 are warm-up: no signal and no trading. The strategy is long EUR (1) or flat (0).
3. **Execution.** The signal from day $t$ is traded at the price of day $t+1$. The position held after day $d$ is $p_d = s_{d-1}$, and it earns the next day's return.
4. **Start.** Both the strategy and buy-and-hold start on day $D = 200$, the first execution day, with capital 1. Buy-and-hold buys on day $D$ and pays the same entry cost.
5. **Costs.** 2 bp per side, charged on the equity after that day's return: $\text{cost}_d = 0.0002 \times |p_d - p_{d-1}| \times E_{d-1}(1 + p_{d-1} r_d)$ (on day $D$, $0.0002 \times |p_D - 0| \times 1$). The position before day $D$ is 0. Trades on every day are executed as the rule says, the last day included. There is no extra closing trade at the end, and the last day is marked at its price.
6. **Equity.** $E_D = 1 - \text{cost}_D$; for $d > D$, $E_d = E_{d-1}(1 + p_{d-1} r_d) - \text{cost}_d$, with $r_d = P_d/P_{d-1} - 1$.
7. **Statistics** for each equity series over days $D..n-1$:
   - daily returns $E_d/E_{d-1} - 1$ for $d > D$ only: day $D$ itself has no return (its entry cost is already in $E_D$), so there are $n-1-D$ daily returns;
   - Sharpe ratio $\bar{x}/s_x\cdot\sqrt{252}$ of those $n-1-D$ daily returns (annualized with 252 observations per year), with sample standard deviation (ddof = 1) and no risk-free rate;
   - maximum drawdown $\max_d(1 - E_d/\max_{u\le d}E_u)$, as a positive fraction.

## Output

Write to `/app/output/`:

- `analysis.csv`, one row per day $D..n-1$, columns `date,price,signal,position,cost,strategy_equity,buy_hold_equity`. Here `date` is ISO; `signal` is $s_d$; `position` is $p_d$; `cost` is the cost charged that day.
- `trades.csv`, one row per position change, columns `date,new_position,cost`.
- `results.json` with these keys:
  - `start_date` and `end_date`;
  - `n_trades`;
  - `total_costs`;
  - `strategy` and `buy_and_hold`, each an object with `final_equity`, `sharpe` and `max_drawdown`.
  
  Values are unrounded decimals.
- `chart.png`: both equity curves, with the strategy's drawdown in a panel below.
- `explanation.md`: start with one or two sentences that answer the question in the title directly, using the numbers you computed. Then give a short plain-English explanation of the result and of what the costs took away. It should state that the ECB rate is a daily reference rate rather than a traded price, and that this is a historical test, not a forecast.
