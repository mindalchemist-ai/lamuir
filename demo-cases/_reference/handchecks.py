"""Hand-computable checks of the reference implementation (Claude Code). Usage: python demo-cases/_reference/handchecks.py"""
import csv
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import reference as ref  # noqa: E402

ok = lambda a, b, tol: abs(a - b) <= tol


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        check.failed = True


check.failed = False

# 1. Spread on three dates, read straight from the raw lines (10 Yr is field 11, 2 Yr field 7 in the 2023 file).
lines = {l.split(",")[0]: l.split(",") for l in (ref.data("yield-curve-inversion", "treasury_par_yield_curve_2023.csv")).read_text().splitlines()[1:]}
daily = dict(ref.yield_curve()["_daily"])
for us, iso in [("07/03/2023", "2023-07-03"), ("01/03/2023", "2023-01-03"), ("12/29/2023", "2023-12-29")]:
    hand = (float(lines[us][11]) - float(lines[us][7])) * 100
    check(f"yield spread {iso} = {hand:.2f} bp", ok(daily[iso], hand, 1e-9))

# 2. Black-Scholes textbook value (S=K=100, T=1, r=5%, sigma=20%, q=0: call 10.4506); Merton with lambda=0 equals BS.
check("BS textbook call 10.4506", ok(ref.bs(100, 100, 1, 0.05, 0, 0.2, "call"), 10.4506, 5e-5))
m0, _ = ref.merton(100, 90, 0.5, 0.04, 0.01, 0.15, 0.0, -0.1, 0.15, "put")
check("Merton(lambda=0) = BS", ok(m0, ref.bs(100, 90, 0.5, 0.04, 0.01, 0.15, "put"), 1e-12))
j = ref.jump_prices()
check("put-call parity in both models", j["max_parity_error"] < 1e-10)
check("matched variance sigma_BS", ok(j["sigma_bs"], math.sqrt(0.15 ** 2 + 0.5 * (0.01 + 0.0225)), 1e-15))

# 3. Backtest toy (the reference function itself): prices 10, 11, 12, 11, 10, 12, 13, 14 with 2/3-day averages and a
#    0.1% cost. Signals t2..t7 = 1,1,0,0,1,1; D = 3. E3 = 0.999; E4 = 0.999*10/11; E5 = E4*1.2*0.999 (exit);
#    E6 = E5; E7 = E6*0.999 (re-entry on the last day, executed as the rule says) = 1.0876396...
s, eq, bh, pos, trades, _ = ref.sma_backtest([10, 11, 12, 11, 10, 12, 13, 14], fast=2, slow=3, fee=0.001)
hand = 0.999 * (10 / 11) * 1.2 * 0.999 * 0.999
check("backtest toy start day 3", s == 3)
check("backtest toy trades on days 3, 5, 7 (last day included)", [t[0] for t in trades] == [3, 5, 7])
check(f"backtest toy final equity {hand:.7f}", ok(eq[7], hand, 1e-12))
check("backtest toy buy-and-hold", ok(bh[7], 0.999 * 14 / 11, 1e-12))
st = ref.stats(eq, s, 8, 252)
rets = [eq[4] / eq[3] - 1, eq[5] / eq[4] - 1, eq[6] / eq[5] - 1, eq[7] / eq[6] - 1]
check("backtest toy max drawdown = 1 - E4/E3", ok(st["max_drawdown"], 1 - eq[4] / eq[3], 1e-15))

# 4. Rolling and EWMA toy (the reference function itself): log returns 0.01, 0.02, -0.01, 0; window 2, lambda 0.5, A = 1.
#    t=2: rolling sd sqrt(5e-5), EWMA seed (0.0001+0.0004)/2 = 2.5e-4; t=3: rolling sqrt(4.5e-4), EWMA 1.75e-4;
#    t=4: rolling sqrt(5e-5), EWMA 8.75e-5. Values are x100.
prices = [1, math.exp(0.01), math.exp(0.03), math.exp(0.02), math.exp(0.02)]
got = ref.ewma_rolling(prices, W=2, lam=0.5, A=1)
want = [(2, 100 * math.sqrt(5e-5), 100 * math.sqrt(2.5e-4)), (3, 100 * math.sqrt(4.5e-4), 100 * math.sqrt(1.75e-4)),
        (4, 100 * math.sqrt(5e-5), 100 * math.sqrt(8.75e-5))]
check("rolling/EWMA toy, three days", all(g[0] == w[0] and ok(g[1], w[1], 1e-9) and ok(g[2], w[2], 1e-9) for g, w in zip(got, want)))
check("constant price gives zero volatility", all(x[1] == 0 and x[2] == 0 for x in ref.ewma_rolling([1.1] * 70)))
check("EWMA series starts on day 60", ref.eurusd_ewma()["_daily"][0][0] == ref.eurusd("eurusd-ewma-volatility")[0][60])

# 5. Triangle consistency and direction: EUR_USD is the ECB USD rate itself.
c = ref.cross_rates()
first = next(r for r in csv.DictReader(open(ref.data("usd-cross-rates", "ecb_reference_rates_2025.csv")))
             if r["CURRENCY"] == "USD" and r["TIME_PERIOD"] == c["first_date"])
check("EUR_USD equals the ECB USD quote", ok(c["_daily"][0][1]["EUR"], float(first["OBS_VALUE"]), 0))
check("triangle error < 1e-12", c["max_triangle_error"] < 1e-12)

# 6. Bond: a bond priced at its own coupon rate is at par (price 100); a 1-year zero-coupon-like bond (one payment of 104)
#    has Macaulay duration exactly 1; and the 10-year annual-pay par bond at 4% has modified duration 8.1109 (textbook value).
check("bond at par when yield = coupon", ok(ref.bond_measures(0.04)[0], 100.0, 1e-9))
check("one-payment bond duration 1", ok(ref.bond_measures(0.05, n=1)[1], 1.0, 1e-12))
check("10y 4% par bond modified duration 8.1109", ok(ref.bond_measures(0.04)[2], 8.1109, 5e-5))
sys.exit(1 if check.failed else 0)
