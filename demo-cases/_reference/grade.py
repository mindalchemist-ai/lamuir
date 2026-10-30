"""Grade one demo-case output folder against the reference (Claude Code).
Usage: python demo-cases/_reference/grade.py <case> <output_dir>
Checks that every deliverable exists; that results.json matches the reference value by value; that analysis.csv has
the stated columns and every row complete, with each cell matching the reference; and, where the task asks for them,
that trades.csv and price_curve.csv hold exactly the reference records (compared as sets, since no order is stated) and
agree with analysis.csv. Prints every failed check; exit code 0 only when all pass. Chart and explanation are reviewed
by hand."""
import csv
import json
import math
import pathlib
import sys

REF = pathlib.Path(__file__).resolve().parent / "expected"
FILES = ["results.json", "analysis.csv", "chart.png", "explanation.md"]
EXTRA = {"eurusd-sma-costs": "trades.csv", "bond-rate-sensitivity": "price_curve.csv"}
COLUMNS = {
    "yield-curve-inversion": "date,yield_2y,yield_10y,spread_bp,inverted",
    "jump-option-prices": "strike,bs_call,merton_call,call_diff,bs_put,merton_put,put_diff,n_terms",
    "eurusd-sma-costs": "date,price,signal,position,cost,strategy_equity,buy_hold_equity",
    "eurusd-ewma-volatility": "date,rolling_vol_pct,ewma_vol_pct",
    "usd-cross-rates": "date,EUR_USD,GBP_USD,JPY_USD,CHF_USD,GBP_JPY",
    "bond-rate-sensitivity": "t,cashflow,pv",
}
EXTRA_COLUMNS = {"price_curve.csv": "yield_change_bp,exact_price,duration_approx,duration_convexity_approx",
                 "trades.csv": "date,new_position,cost"}
# absolute tolerance, relative tolerance (a value passes if it is within either)
TOL = {"yield-curve-inversion": (1e-9, 0), "jump-option-prices": (1e-12, 1e-8),
       "eurusd-sma-costs": (1e-9, 1e-9), "eurusd-ewma-volatility": (1e-10, 1e-10),
       "usd-cross-rates": (1e-12, 1e-12), "bond-rate-sensitivity": (1e-9, 1e-10)}
BOUNDS = {"max_parity_error": 1e-10, "max_triangle_error": 1e-12}  # reported diagnostics: checked against a bound

TRUTH = {"true": True, "false": False, "1": True, "0": False, "1.0": True, "0.0": False, "yes": True, "no": False}
problems = []


def close(a, b, tol):
    return abs(a - b) <= tol[0] or abs(a - b) <= tol[1] * abs(b)


def number(x):
    try:
        v = float(x)
    except OverflowError:
        raise ValueError
    if isinstance(x, bool):
        raise ValueError
    if not math.isfinite(v):
        raise ValueError
    return v


def same(got, exp, tol, where):
    if isinstance(exp, dict):
        if not isinstance(got, dict):
            problems.append(f"{where}: expected an object")
            return
        for k, v in exp.items():
            if k.startswith("_"):
                continue
            if k not in got:
                problems.append(f"{where}.{k}: missing")
            elif k in BOUNDS:
                if isinstance(got[k], bool) or not isinstance(got[k], (int, float)) or not abs(got[k]) <= BOUNDS[k]:
                    problems.append(f"{where}.{k} = {got[k]!r}, bound {BOUNDS[k]}")
            else:
                same(got[k], v, tol, f"{where}.{k}")
    elif isinstance(exp, bool):
        if TRUTH.get(str(got).strip().lower()) is not exp:
            problems.append(f"{where} = {got!r}, expected {exp!r}")
    elif isinstance(exp, str):
        if str(got).strip() != exp:
            problems.append(f"{where} = {got!r}, expected {exp!r}")
    elif isinstance(exp, (int, float)):
        try:
            v = number(got)
            ok = close(v, float(exp), tol) and (not isinstance(exp, int) or v == exp)
        except (TypeError, ValueError):
            ok = False
        if not ok:
            problems.append(f"{where} = {got!r}, expected {exp!r}")


def expected_rows(case, ref):
    cols = COLUMNS[case].split(",")
    if case == "yield-curve-inversion":
        return [[d, *ref["_yields"][d], s, s < 0] for d, s in ref["_daily"]]
    if case == "jump-option-prices":
        return [[r[c] for c in cols] for r in ref["_rows"]]
    if case == "bond-rate-sensitivity":
        return [list(r) for r in ref["_rows"]]
    if case in ("eurusd-sma-costs", "eurusd-ewma-volatility"):
        return [list(r) for r in ref["_daily"]]
    if case == "usd-cross-rates":
        return [[d, u["EUR"], u["GBP"], u["JPY"], u["CHF"], g] for d, u, g in ref["_daily"]]
    raise KeyError(case)


def read_csv(path, header):
    try:
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
    except (OSError, UnicodeDecodeError, csv.Error) as e:
        problems.append(f"{path.name}: cannot be read ({type(e).__name__})")
        return None
    if not rows or [c.strip() for c in rows[0]] != header.split(","):
        problems.append(f"{path.name}: columns {rows[0] if rows else []}, expected {header}")
        return None
    width = len(header.split(","))
    for i, r in enumerate(rows[1:], 1):
        if len(r) != width or any(c.strip() == "" for c in r):
            problems.append(f"{path.name} row {i}: {len(r)} cells or an empty cell, expected {width} filled cells")
    return rows[1:]


def compare_rows(name, body, exp, tol, cols):
    if len(body) != len(exp):
        problems.append(f"{name} has {len(body)} rows, expected {len(exp)}")
    for i, (g, e) in enumerate(zip(body, exp), 1):
        for j, ev in enumerate(e):
            same(g[j] if j < len(g) else None, ev, tol, f"{name} row {i} {cols[j]}")
        if len(problems) > 40:
            return


def records(rows, numeric, name, width):
    """Parse rows into tuples (numbers as floats, so 0, 0.0, -0.0 and 1e-4 compare by value); unreadable rows fail
    (rows of the wrong width were already reported by read_csv and are skipped here)."""
    out = []
    for i, r in enumerate(rows, 1):
        if len(r) != width:
            continue
        try:
            out.append(tuple(number(c) if j in numeric else c.strip() for j, c in enumerate(r)))
        except (ValueError, TypeError):
            problems.append(f"{name} row {i}: unreadable number in {r}")
    return out


def position(x):
    v = number(x)
    if v not in (0.0, 1.0):
        raise ValueError
    return int(v)


def main(case, out):
    out = pathlib.Path(out)
    for f in FILES + ([EXTRA[case]] if case in EXTRA else []):
        if not (out / f).is_file() or (out / f).stat().st_size == 0:
            problems.append(f"{f}: missing or empty")
    ref = json.loads((REF / f"{case}.json").read_text())
    tol = TOL[case]
    try:
        same(json.loads((out / "results.json").read_text()), ref, tol, "results")
    except (OSError, ValueError, RecursionError) as e:
        problems.append(f"results.json unreadable: {type(e).__name__}")
    cols = COLUMNS[case].split(",")
    body = read_csv(out / "analysis.csv", COLUMNS[case])
    if body is not None:
        compare_rows("analysis.csv", body, expected_rows(case, ref), tol, cols)
        if case == "yield-curve-inversion":
            for i, r in enumerate(body, 1):
                try:
                    if abs(100 * (number(r[2]) - number(r[1])) - number(r[3])) > 1e-9:
                        problems.append(f"analysis.csv row {i}: spread_bp is not 100*(yield_10y - yield_2y)")
                except (ValueError, IndexError):
                    pass
    if case == "eurusd-sma-costs":
        trades = read_csv(out / "trades.csv", EXTRA_COLUMNS["trades.csv"])
        if trades is not None:
            got = records(trades, {1, 2}, "trades.csv", 3)
            dates = [d for d, _, _ in got]
            if len(set(dates)) != len(dates):
                problems.append("trades.csv: a date appears more than once")
            if len(trades) != len(ref["_trades"]):
                problems.append(f"trades.csv has {len(trades)} rows, expected {len(ref['_trades'])} (one per position change)")
            want = {d: (p, c) for d, p, c in ref["_trades"]}
            for d, p, c in got:
                if d not in want:
                    problems.append(f"trades.csv {d}: no position change on this date in the reference")
                elif p != want[d][0] or not close(c, want[d][1], tol):
                    problems.append(f"trades.csv {d}: new_position {p}, cost {c}; expected {want[d][0]}, {want[d][1]}")
            missing = set(want) - set(dates)
            if missing:
                problems.append(f"trades.csv: {len(missing)} reference trades missing, e.g. {sorted(missing)[0]}")
            if body is not None:
                try:
                    pos = [position(r[3]) for r in body]
                    changes = [(body[i][0].strip(), p) for i, p in enumerate(pos) if p != (pos[i - 1] if i else 0)]
                    if sorted(changes) != sorted((d, int(p)) for d, p, _ in got):
                        problems.append("trades.csv does not match the position changes in analysis.csv")
                except (ValueError, IndexError):
                    problems.append("analysis.csv: position must be 0 or 1 on every row")
    if case == "jump-option-prices" and body is not None:
        # put-call parity is checked from the submitted prices, not taken from the reported max_parity_error
        S, T, r, q = 100.0, 0.5, 0.04, 0.01
        for i, row in enumerate(body, 1):
            try:
                k, bc, mc, bp, mp = (number(row[j]) for j in (0, 1, 2, 4, 5))
            except (ValueError, IndexError):
                continue
            fwd = S * math.exp(-q * T) - k * math.exp(-r * T)
            if max(abs(bc - bp - fwd), abs(mc - mp - fwd)) > BOUNDS["max_parity_error"]:
                problems.append(f"analysis.csv row {i}: submitted prices break put-call parity")
    if case == "usd-cross-rates" and body is not None:
        # the cross rate is checked against the submitted dollar values, not taken from the reported max_triangle_error
        for i, row in enumerate(body, 1):
            try:
                gbp, jpy, gbpjpy = number(row[2]), number(row[3]), number(row[5])
            except (ValueError, IndexError):
                continue
            if abs(gbp / jpy - gbpjpy) > BOUNDS["max_triangle_error"] * max(1.0, abs(gbpjpy)):
                problems.append(f"analysis.csv row {i}: GBP_JPY is not GBP_USD / JPY_USD")
    if case == "bond-rate-sensitivity":
        curve = read_csv(out / "price_curve.csv", EXTRA_COLUMNS["price_curve.csv"])
        if curve is not None:
            compare_rows("price_curve.csv", curve, [list(r) for r in ref["_grid"]], tol, EXTRA_COLUMNS["price_curve.csv"].split(","))
    for p in problems[:40]:
        print("FAIL", p)
    print(f"{case}: {'PASS' if not problems else f'FAIL ({len(problems)} problems)'}")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
