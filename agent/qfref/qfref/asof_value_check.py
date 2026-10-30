import csv, glob, json, math, os, re

VALUATION = re.compile(r"(?:valuation|pricing|as[- ]of|analysis) date[^0-9\n]{0,40}?(\d{4}-\d{2}-\d{2})|as of (\d{4}-\d{2}-\d{2})", re.I)
DATE_COL = re.compile(r"^(?:date|datetime|timestamp|trade_date|asof|as_of)$", re.I)
PRICE_COL = re.compile(r"^(?:close|adj[ _]?close|price|last|spot|settle|settlement)$", re.I)


def _numbers(path):
    try:
        data = json.load(open(path))
    except (OSError, ValueError):
        return []
    out, stack = [], [("", data)]
    while stack:
        key, node = stack.pop()
        if isinstance(node, dict):
            stack += list(node.items())
        elif isinstance(node, list):
            stack += [(key, v) for v in node]
        elif isinstance(node, (int, float)) and not isinstance(node, bool) and math.isfinite(node):
            out.append((key, float(node)))
    return out


def asof_notes(out_dir, statement, data_dirs):
    # A value reported "at the valuation date" that equals the last row of a price series running past that date.
    dates = {a or b for a, b in VALUATION.findall(statement or "")}
    if len(dates) != 1:
        return []
    val = dates.pop()
    reported = [(os.path.basename(p), k, v) for p in glob.glob(f"{out_dir}/**/*.json", recursive=True) for k, v in _numbers(p)]
    notes = []
    for d in data_dirs:
        for path in sorted(glob.glob(os.path.join(d, "**", "*.csv"), recursive=True)):
            try:
                with open(path, newline="") as f:
                    rows = list(csv.DictReader(f))
            except (OSError, csv.Error, UnicodeDecodeError):
                continue
            if not rows:
                continue
            dcol = next((c for c in rows[0] if c and DATE_COL.match(c.strip())), None)
            if not dcol:
                continue
            rows = sorted((r for r in rows if r.get(dcol)), key=lambda r: r[dcol][:10])
            before = [r for r in rows if r[dcol][:10] <= val]
            if not before or rows[-1][dcol][:10] <= val:
                continue
            for pcol in (c for c in rows[0] if c and PRICE_COL.match(c.strip())):
                try:
                    last, asof = float(rows[-1][pcol]), float(before[-1][pcol])
                except (TypeError, ValueError):
                    continue
                if last == asof:
                    continue
                for fname, key, v in reported:
                    if abs(v - last) <= 1e-9 * max(1.0, abs(last)):
                        notes.append(
                            f"Output note: '{key}' in {fname} is {v:g}, the {pcol} on the last row of {os.path.basename(path)} "
                            f"({rows[-1][dcol][:10]}), which is after the valuation date {val} the task gives. Data after "
                            f"the valuation date is not known at valuation; the {pcol} on or before {val} is {asof:g} "
                            f"({before[-1][dcol][:10]}). Use the value as of the valuation date unless the task says otherwise.")
    return notes
