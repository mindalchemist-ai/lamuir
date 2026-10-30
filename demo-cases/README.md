# Lamuir demo cases

Six quantitative-finance questions on public data, written for Lamuir. Each case asks one question and comes with a fixed snapshot of the input data, an independent reference solution and a grader. None is taken from QF-Bench.

| Case | Question | Data source |
|---|---|---|
| `yield-curve-inversion` | How many days was the 10-year minus 2-year U.S. Treasury yield spread negative in 2022–2025? | U.S. Treasury Daily Par Yield Curve Rates |
| `bond-rate-sensitivity` | How much would a 10-year, 4%-coupon bond's price fall if its yield rose 100 bp from the end-2024 10-year Treasury yield? | U.S. Treasury Daily Par Yield Curve Rates (2024) |
| `jump-option-prices` | How do Merton jump-diffusion option prices differ from Black-Scholes prices with the same total variance? | Parameters in the statement (assumed) |
| `eurusd-sma-costs` | Does a 50/200-day moving-average crossover on EUR/USD beat buy-and-hold after 2 bp trading costs, 2015–2025? | ECB euro reference rate against the U.S. dollar (ECB Data Portal) |
| `eurusd-ewma-volatility` | How do EWMA (λ = 0.94) and 60-day rolling volatility estimates of EUR/USD compare over 2015–2025? | Same as above |
| `usd-cross-rates` | What was the 2025 percent change of the euro, pound, yen and Swiss franc against the U.S. dollar? | ECB euro foreign exchange reference rates (ECB Data Portal) |

## Layout

- `<case>/instruction.md`: the full task statement, exactly as the agent receives it;
- `<case>/card.toml`: the time limit (900 s);
- `<case>/environment/Dockerfile` and `<case>/environment/data/`: the input folder.

Only `instruction.md` and `environment/` are given to the agent. `scripts/run_demo.py` builds the images, runs the agent on a case and grades its outputs.

## Data

`fetch_data.py` downloads the raw files into `_raw/` and builds every `environment/data/` folder; `python demo-cases/fetch_data.py --build-only` rebuilds the inputs from `_raw/` without downloading.

- Each download is recorded in `_raw/<source>/provenance.json` with its URL, UTC time and SHA-256.
- The build step only selects files and date ranges. It does not clean, deduplicate, fill or sort; the tasks leave that to the agent.

| Source | Terms | In this repository |
|---|---|---|
| U.S. Treasury | Work of the U.S. government; public domain | Included |
| ECB Data Portal | Free reuse with attribution; statistics must not be misrepresented | Included. Values such as cross rates, changes, strategy results and volatilities are computed by Lamuir from ECB data |

## Reference solution and grader

`_reference/` holds the independent reference implementation. It is never mounted into the agent's container.

- `reference.py` uses plain Python only, shares no code with the agent, and writes `expected/<case>.json`.
- `handchecks.py` runs 20 hand-computable checks on the reference functions: a textbook Black-Scholes value, Merton with λ = 0, an 8-day backtest worked by hand, a 3-day rolling and EWMA sample, a par bond's duration, and others.
- `grade.py <case> <output_dir>` grades one output folder within tolerances of 1e-8 to 1e-12. It checks that every file is present, `results.json` value by value, `analysis.csv` row by row and cell by cell, and the extra tables `trades.csv` and `price_curve.csv` record by record (any order, each record exactly once). Unreadable numbers and files fail the check rather than crashing it.
- `selftest_grade.py <scratch_dir>` builds a correct output for every case, equivalent spellings that must also pass, and many broken outputs that must all fail.

## Reference results

| Case | Key results |
|---|---|
| yield-curve-inversion | 998 days; 541 inverted, first 2022-04-01, last 2024-09-05; longest streak 537 days; deepest −108 bp on 2023-07-03 |
| bond-rate-sensitivity | 10-year yield 4.58% on 2024-12-31; price 95.43, modified duration 8.02, convexity 79.3; after +100 bp the price is 88.14 (−7.64%), and duration plus convexity gives 88.15 |
| jump-option-prices | σ_BS = 0.19685; 21 series terms (fixed); at the money the jump model is 0.343 cheaper for both call and put; the largest put premium is at K = 80 |
| eurusd-sma-costs | 2,816 rates; trading from 2015-10-14; 21 trades, costs 0.40%; strategy final equity 0.933 (Sharpe −0.11, max drawdown 16.5%) vs buy-and-hold 1.030 (Sharpe 0.08, max drawdown 23.4%) |
| eurusd-ewma-volatility | 2,756 days from 2015-03-27; means 7.58% (rolling) and 7.49% (EWMA); peaks 14.43% on 2022-11-29 (rolling) and 18.51% on 2022-11-11 (EWMA): the EWMA peak came 18 days earlier and was higher |
| usd-cross-rates | 255 days; against the USD in 2025: CHF +14.5%, EUR +13.8%, GBP +8.4%, JPY +0.2% |

## Independence from QF-Bench

Checked against the 86 QF-Bench statements:

- **Statement overlap:** no statement shares more than 1.2% of its six-word runs with a QF-Bench statement. The shared runs are standard formula notation, such as "a Poisson process with intensity lambda" and the log-return formula.
- **Task names:** none is identical to a QF-Bench task name.
- **Data:** no data file is byte-identical to a QF-Bench data file.
