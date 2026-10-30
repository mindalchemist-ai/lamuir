"""Independent reference answers for the six demo cases (written by Claude Code; plain Python only,
no code shared with the agent). Usage: python demo-cases/_reference/reference.py
Writes _reference/expected/<case>.json. Keep this folder out of anything the agent can read."""
import csv
import datetime as dt
import json
import math
import pathlib

CASES = pathlib.Path(__file__).resolve().parents[1]
OUT = pathlib.Path(__file__).resolve().parent / "expected"


def data(case, name):
    return CASES / case / "environment" / "data" / name


# 1. yield-curve-inversion
def yield_curve():
    rows = []
    for y in (2022, 2023, 2024, 2025):
        for r in csv.DictReader(open(data("yield-curve-inversion", f"treasury_par_yield_curve_{y}.csv"))):
            if r["2 Yr"].strip() and r["10 Yr"].strip():
                rows.append((dt.datetime.strptime(r["Date"], "%m/%d/%Y").date(), float(r["2 Yr"]), float(r["10 Yr"])))
    rows.sort()
    spread = [(d, (y10 - y2) * 100.0) for d, y2, y10 in rows]
    yields = {d.isoformat(): (y2, y10) for d, y2, y10 in rows}
    inv = [d for d, s in spread if s < 0]
    best, cur, prev = 0, 0, None
    for d, s in spread:
        cur = cur + 1 if s < 0 else 0
        best = max(best, cur)
    low = min(spread, key=lambda x: x[1])
    return {"n_days": len(spread), "mean_spread_bp": math.fsum(s for _, s in spread) / len(spread),
            "min_spread_bp": low[1], "min_spread_date": low[0].isoformat(), "n_inverted_days": len(inv),
            "first_inverted_date": inv[0].isoformat(), "last_inverted_date": inv[-1].isoformat(),
            "longest_inverted_streak_days": best,
            "_daily": [(d.isoformat(), s) for d, s in spread], "_yields": yields}


# 2. jump-option-prices
P2 = dict(S=100.0, T=0.5, r=0.04, q=0.01, sigma=0.15, lam=0.5, mu_j=-0.10, delta=0.15)
STRIKES = [70.0 + 5 * i for i in range(13)]


def ncdf(x):
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def bs(S, K, T, r, q, v, kind):
    d1 = (math.log(S / K) + (r - q + 0.5 * v * v) * T) / (v * math.sqrt(T))
    d2 = d1 - v * math.sqrt(T)
    if kind == "call":
        return S * math.exp(-q * T) * ncdf(d1) - K * math.exp(-r * T) * ncdf(d2)
    return K * math.exp(-r * T) * ncdf(-d2) - S * math.exp(-q * T) * ncdf(-d1)


def merton(S, K, T, r, q, sigma, lam, mu_j, delta, kind, N=20):
    k = math.exp(mu_j + 0.5 * delta * delta) - 1.0
    lp = lam * (1.0 + k)
    total = 0.0
    for n in range(N + 1):
        w = math.exp(-lp * T) * (lp * T) ** n / math.factorial(n)
        rn = r - lam * k + n * math.log(1.0 + k) / T
        vn = math.sqrt(sigma * sigma + n * delta * delta / T)
        total += w * bs(S, K, T, rn, q, vn, kind)
    return total, N + 1


def jump_prices():
    p = P2
    v_bs = math.sqrt(p["sigma"] ** 2 + p["lam"] * (p["mu_j"] ** 2 + p["delta"] ** 2))
    rows = []
    for K in STRIKES:
        mc, n_terms = merton(p["S"], K, p["T"], p["r"], p["q"], p["sigma"], p["lam"], p["mu_j"], p["delta"], "call")
        mp, _ = merton(p["S"], K, p["T"], p["r"], p["q"], p["sigma"], p["lam"], p["mu_j"], p["delta"], "put")
        bc, bp = bs(p["S"], K, p["T"], p["r"], p["q"], v_bs, "call"), bs(p["S"], K, p["T"], p["r"], p["q"], v_bs, "put")
        rows.append({"strike": K, "bs_call": bc, "merton_call": mc, "call_diff": mc - bc,
                     "bs_put": bp, "merton_put": mp, "put_diff": mp - bp, "n_terms": n_terms})
    atm = next(r for r in rows if r["strike"] == 100.0)
    par = lambda c, pt, K: abs(c - pt - (p["S"] * math.exp(-p["q"] * p["T"]) - K * math.exp(-p["r"] * p["T"])))
    perr = max(max(par(r["bs_call"], r["bs_put"], r["strike"]), par(r["merton_call"], r["merton_put"], r["strike"])) for r in rows)
    return {"sigma_bs": v_bs, "max_parity_error": perr, "n_terms": rows[0]["n_terms"], "atm_call_diff": atm["call_diff"],
            "atm_put_diff": atm["put_diff"],
            "largest_put_diff_strike": max(rows, key=lambda r: r["put_diff"])["strike"], "_rows": rows}


# 3 and 4. ECB EUR/USD
def eurusd(case):
    rows = sorted((r["TIME_PERIOD"], float(r["OBS_VALUE"])) for r in csv.DictReader(open(data(case, "ecb_eurusd_2015_2025.csv"))))
    return [d for d, _ in rows], [p for _, p in rows]


def sma_backtest(close, fast=50, slow=200, fee=0.001):
    n = len(close)
    signal = [None] * n
    for t in range(slow - 1, n):
        signal[t] = 1 if sum(close[t - fast + 1:t + 1]) / fast > sum(close[t - slow + 1:t + 1]) / slow else 0
    s = slow  # first execution: the close after the first valid signal
    pos = {s - 1: 0}
    eq, bh = {}, {}
    trades = []
    for d in range(s, n):
        prev_eq = 1.0 if d == s else eq[d - 1] * (1 + pos[d - 1] * (close[d] / close[d - 1] - 1))
        pos[d] = signal[d - 1]
        cost = fee * abs(pos[d] - pos[d - 1]) * prev_eq
        if pos[d] != pos[d - 1]:
            trades.append((d, pos[d], cost))
        eq[d] = prev_eq - cost
        bh[d] = (1 - fee) if d == s else bh[d - 1] * close[d] / close[d - 1]
    return s, eq, bh, pos, trades, signal


def stats(series, s, n, A):
    rets = [series[d] / series[d - 1] - 1 for d in range(s + 1, n)]
    m = math.fsum(rets) / len(rets)
    sd = math.sqrt(math.fsum((x - m) ** 2 for x in rets) / (len(rets) - 1))
    peak, mdd = -1.0, 0.0
    for d in range(s, n):
        peak = max(peak, series[d])
        mdd = max(mdd, 1 - series[d] / peak)
    return {"final_equity": series[n - 1], "sharpe": m / sd * math.sqrt(A), "max_drawdown": mdd}


def eurusd_sma():
    dates, price = eurusd("eurusd-sma-costs")
    s, eq, bh, pos, trades, signal = sma_backtest(price, fee=0.0002)
    costs = {d: cost for d, _, cost in trades}
    daily = [(dates[d], price[d], signal[d], pos[d], costs.get(d, 0.0), eq[d], bh[d]) for d in range(s, len(price))]
    return {"_daily": daily, "start_date": dates[s], "end_date": dates[-1], "n_trades": len(trades),
            "total_costs": math.fsum(t[2] for t in trades), "strategy": stats(eq, s, len(price), 252),
            "buy_and_hold": stats(bh, s, len(price), 252),
            "_trades": [(dates[d], p, cost) for d, p, cost in trades]}


def ewma_rolling(price, W=60, lam=0.94, A=252):
    r = [None] + [math.log(price[t] / price[t - 1]) for t in range(1, len(price))]
    out, v = [], None
    for t in range(W, len(price)):
        win = r[t - W + 1:t + 1]
        m = math.fsum(win) / W
        roll = 100 * math.sqrt(A * math.fsum((x - m) ** 2 for x in win) / (W - 1))
        v = math.fsum(x * x for x in r[1:W + 1]) / W if t == W else lam * v + (1 - lam) * r[t] ** 2
        out.append((t, roll, 100 * math.sqrt(A * v)))
    return out


def eurusd_ewma():
    dates, price = eurusd("eurusd-ewma-volatility")
    out = [(dates[t], a, b) for t, a, b in ewma_rolling(price)]
    mr = max(out, key=lambda x: x[1])
    me = max(out, key=lambda x: x[2])
    return {"first_date": out[0][0], "last_date": out[-1][0], "n_days": len(out),
            "mean_rolling_vol_pct": math.fsum(x[1] for x in out) / len(out), "mean_ewma_vol_pct": math.fsum(x[2] for x in out) / len(out),
            "max_rolling_vol_pct": mr[1], "max_rolling_vol_date": mr[0], "max_ewma_vol_pct": me[2], "max_ewma_vol_date": me[0],
            "days_ewma_above_rolling": sum(1 for x in out if x[2] > x[1]), "_daily": out}


# 5. usd-cross-rates
def cross_rates():
    q = {}
    for r in csv.DictReader(open(data("usd-cross-rates", "ecb_reference_rates_2025.csv"))):
        q.setdefault(r["TIME_PERIOD"], {})[r["CURRENCY"]] = float(r["OBS_VALUE"])
    days = sorted(d for d, v in q.items() if len(v) == 4)
    usd = {d: {"EUR": q[d]["USD"], "GBP": q[d]["USD"] / q[d]["GBP"], "JPY": q[d]["USD"] / q[d]["JPY"],
               "CHF": q[d]["USD"] / q[d]["CHF"]} for d in days}
    chg = {c: (usd[days[-1]][c] / usd[days[0]][c] - 1) * 100 for c in ("EUR", "GBP", "JPY", "CHF")}
    gbpjpy = {d: q[d]["JPY"] / q[d]["GBP"] for d in days}
    tri = max(abs(usd[d]["GBP"] / usd[d]["JPY"] - gbpjpy[d]) for d in days)
    return {"max_triangle_error": tri,"first_date": days[0], "last_date": days[-1], "n_days": len(days), "change_pct": chg,
            "strongest": max(chg, key=chg.get), "weakest": min(chg, key=chg.get),
            "gbp_jpy_change_pct": (gbpjpy[days[-1]] / gbpjpy[days[0]] - 1) * 100,
            "_daily": [(d, usd[d], gbpjpy[d]) for d in days]}


# 6. bond-rate-sensitivity
def bond_measures(y, coupon=4.0, face=100.0, n=10):
    cf = [coupon + (face if t == n else 0.0) for t in range(1, n + 1)]
    pv = [c / (1 + y) ** t for t, c in zip(range(1, n + 1), cf)]
    price = math.fsum(pv)
    mac = math.fsum(t * v for t, v in zip(range(1, n + 1), pv)) / price
    mod = mac / (1 + y)
    conv = math.fsum(t * (t + 1) * v for t, v in zip(range(1, n + 1), pv)) / (price * (1 + y) ** 2)
    return price, mac, mod, conv, cf, pv


def bond_rate():
    rows = list(csv.DictReader(open(data("bond-rate-sensitivity", "treasury_par_yield_curve_2024.csv"))))
    last = max(rows, key=lambda r: dt.datetime.strptime(r["Date"], "%m/%d/%Y"))
    y = float(last["10 Yr"]) / 100
    price, mac, mod, conv, cf, pv = bond_measures(y)
    up = bond_measures(y + 0.01)[0]
    approx = price * (1 - mod * 0.01 + 0.5 * conv * 0.01 ** 2)
    grid = []
    for i in range(25):
        dy = round(-0.03 + 0.0025 * i, 4)
        grid.append([dy * 1e4, bond_measures(y + dy)[0], price * (1 - mod * dy), price * (1 - mod * dy + 0.5 * conv * dy * dy)])
    return {"yield_date": dt.datetime.strptime(last["Date"], "%m/%d/%Y").date().isoformat(), "yield": y, "price": price,
            "macaulay_duration": mac, "modified_duration": mod, "convexity": conv, "price_up_100bp": up,
            "price_change_pct": (up / price - 1) * 100, "approx_price_up_100bp": approx, "approximation_error": approx - up,
            "_rows": [[t, c, v] for t, c, v in zip(range(1, 11), cf, pv)], "_grid": grid}

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for name, fn in [("yield-curve-inversion", yield_curve), ("jump-option-prices", jump_prices),
                     ("eurusd-sma-costs", eurusd_sma), ("eurusd-ewma-volatility", eurusd_ewma), ("usd-cross-rates", cross_rates),
                     ("bond-rate-sensitivity", bond_rate)]:
        res = fn()
        (OUT / f"{name}.json").write_text(json.dumps(res, indent=1, default=str))
        print(name, json.dumps({k: v for k, v in res.items() if not k.startswith("_")}, default=str)[:600])
