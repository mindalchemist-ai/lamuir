"""Self-test of grade.py (Claude Code): a correct output built from the reference must pass, and each broken variant must
fail. Usage: python demo-cases/_reference/selftest_grade.py <scratch_dir>"""
import csv
import json
import pathlib
import re
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import grade  # noqa: E402


def write_correct(case, o):
    ref = json.loads((grade.REF / f"{case}.json").read_text())
    o.mkdir(parents=True, exist_ok=True)
    (o / "results.json").write_text(json.dumps({k: v for k, v in ref.items() if not k.startswith("_")}))
    (o / "chart.png").write_bytes(b"png")
    (o / "explanation.md").write_text("text")
    with open(o / "analysis.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(grade.COLUMNS[case].split(","))
        w.writerows([[str(c).lower() if isinstance(c, bool) else c for c in r] for r in grade.expected_rows(case, ref)])
    if case == "eurusd-sma-costs":
        with open(o / "trades.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(grade.EXTRA_COLUMNS["trades.csv"].split(","))
            w.writerows(reversed(ref["_trades"]))  # any order is accepted
    if case == "bond-rate-sensitivity":
        with open(o / "price_curve.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(grade.EXTRA_COLUMNS["price_curve.csv"].split(","))
            w.writerows(ref["_grid"])


def edit_csv(path, fn):
    rows = list(csv.reader(open(path, newline="")))
    rows = fn(rows)
    with open(path, "w", newline="") as f:
        csv.writer(f).writerows(rows)


# equivalent spellings that must still pass
EQUIVALENT = {
    "eurusd-sma-costs": [("positions as -0.0/1.0 and costs in scientific notation", "analysis.csv",
                          lambda r: [r[0]] + [[*x[:3], "-0.0" if float(x[3]) == 0 else "1.0", f"{float(x[4]):e}", *x[5:]] for x in r[1:]]),
                         ("trades with -0.0 and 1.0", "trades.csv", lambda r: [r[0]] + [[x[0], "-0.0" if float(x[1]) == 0 else "1.0", x[2]] for x in r[1:]])],
}
BROKEN = {
    "yield-curve-inversion": [("yields replaced by 999/888", "analysis.csv", lambda r: [r[0]] + [[x[0], "999", "888", *x[3:]] for x in r[1:]]),
                              ("rows cut to the date only", "analysis.csv", lambda r: [r[0]] + [[x[0]] for x in r[1:]]),
                              ("one inverted flag flipped", "analysis.csv", lambda r: [r[0], [*r[1][:4], "true" if r[1][4] == "false" else "false"]] + r[2:])],
    "eurusd-sma-costs": [("trades.csv replaced by text", "trades.csv", lambda r: [["anything"]]),
                         ("one trade dropped", "trades.csv", lambda r: r[:-1]),
                         ("every trade listed twice", "trades.csv", lambda r: [r[0]] + r[1:] + r[1:]),
                         ("a cost written as nan", "trades.csv", lambda r: [r[0], [r[1][0], r[1][1], "nan"]] + r[2:]),
                         ("a cost written as text", "trades.csv", lambda r: [r[0], [r[1][0], r[1][1], "abc"]] + r[2:]),
                         ("a trades row with a missing cell", "trades.csv", lambda r: [r[0], r[1][:2]] + r[2:]),
                         ("a position of 2", "analysis.csv", lambda r: [r[0], [*r[1][:3], "2", *r[1][4:]]] + r[2:]),
                         ("position one row late", "analysis.csv", lambda r: [r[0]] + [[*x[:3], y[3], *x[4:]] for x, y in zip(r[1:], [r[1]] + r[1:-1])])],
    "bond-rate-sensitivity": [("price curve one row short", "price_curve.csv", lambda r: r[:-1]),
                              ("approximation columns swapped", "price_curve.csv", lambda r: [r[0]] + [[x[0], x[1], x[3], x[2]] for x in r[1:]])],
    "usd-cross-rates": [("GBP_JPY off by 1e-9 relative", "analysis.csv",
                         lambda r: [r[0], [*r[1][:5], repr(float(r[1][5]) * (1 + 1e-9))]] + r[2:])],
    "jump-option-prices": [("merton_call at K=70 off by 2e-8, reported parity error unchanged", "analysis.csv",
                            lambda r: [r[0], [r[1][0], r[1][1], repr(float(r[1][2]) + 2e-8), *r[1][3:]]] + r[2:]),
                           ("an empty cell", "analysis.csv", lambda r: [r[0], [*r[1][:-1], ""]] + r[2:]),
                           ("a CSV field longer than the csv module's limit", "analysis.csv", lambda r: [r[0], [*r[1][:-1], "9" * 200000]] + r[2:])],
}
# broken in other ways than a CSV edit: (case, name, function of the output folder)
OTHER = [
    ("jump-option-prices", "results.json number 10**400", lambda o: (o / "results.json").write_text(
        re.sub(r'"n_terms": \d+', '"n_terms": 1' + "0" * 400, (o / "results.json").read_text()))),
    ("eurusd-ewma-volatility", "analysis.csv unreadable", lambda o: (o / "analysis.csv").chmod(0)),
    ("eurusd-sma-costs", "trades.csv unreadable", lambda o: (o / "trades.csv").chmod(0)),
    ("usd-cross-rates", "analysis.csv not UTF-8", lambda o: (o / "analysis.csv").write_bytes(b"\xff\xfe" + (o / "analysis.csv").read_bytes())),
]


def run(case, o):
    p = subprocess.run([sys.executable, str(HERE / "grade.py"), case, str(o)], capture_output=True, text=True)
    if p.returncode not in (0, 1) or not p.stdout.strip():
        return False, "grader crashed: " + (p.stderr.strip().splitlines() or ["no output"])[-1]
    return p.returncode == 0, p.stdout.strip().splitlines()[-1]


if __name__ == "__main__":
    base = pathlib.Path(sys.argv[1])
    bad = 0
    for case in grade.COLUMNS:
        o = base / case / "correct"
        write_correct(case, o)
        passed, line = run(case, o)
        print(("ok   " if passed else "BAD  ") + f"correct output: {line}")
        bad += not passed
        for name, fname, fn in EQUIVALENT.get(case, []):
            b = base / case / ("eq_" + name.replace(" ", "_").replace("/", "_"))
            shutil.copytree(o, b, dirs_exist_ok=True)
            edit_csv(b / fname, fn)
            passed, line = run(case, b)
            print(("ok   " if passed else "BAD  ") + f"{case} equivalent ({name}): {line}")
            bad += not passed
        for name, fname, fn in BROKEN.get(case, []):
            b = base / case / name.replace(" ", "_").replace("/", "_")
            shutil.copytree(o, b, dirs_exist_ok=True)
            edit_csv(b / fname, fn)
            passed, line = run(case, b)
            crashed = line.startswith("grader crashed")
            print(("BAD  " if passed or crashed else "ok   ") + f"{case} broken ({name}): {line}")
            bad += passed or crashed
    for case, name, fn in OTHER:
        b = base / case / name.replace(" ", "_").replace("*", "")
        shutil.copytree(base / case / "correct", b, dirs_exist_ok=True)
        fn(b)
        passed, line = run(case, b)
        crashed = line.startswith("grader crashed")
        print(("BAD  " if passed or crashed else "ok   ") + f"{case} broken ({name}): {line}")
        bad += passed or crashed
    n_eq = sum(len(v) for v in EQUIVALENT.values())
    n_broken = sum(len(v) for v in BROKEN.values()) + len(OTHER)
    print(f"{len(grade.COLUMNS)} correct, {n_eq} equivalent, {n_broken} broken outputs tested")
    print("self-test", "passed" if not bad else f"FAILED ({bad})")
    sys.exit(1 if bad else 0)
