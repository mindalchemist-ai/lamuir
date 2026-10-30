import csv, glob, json, math, os, re

ADDITIVE = re.compile(r"(?:^|_)(?:mean|expected|total|sum|el|pnl|contribution|dollars?|amount|exposure)(?:_|$)", re.I)
NON_ADDITIVE = re.compile(r"(?:^|_)(?:std|stdev|sd|vol|volatility|var|es|cvar|quantile|percentile|pct|percent|ratio|rate|prob|probability|share|weight|rank|n|count|z|t|tstat)(?:_|$)", re.I)


def _portfolio_values(out_dir):
    found = {}
    for path in glob.glob(f"{out_dir}/**/*.json", recursive=True):
        try:
            data = json.load(open(path))
        except (OSError, ValueError):
            continue
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and v != 0:
                    found.setdefault(k, (os.path.basename(path), float(v)))
    return found


def group_sum_notes(out_dir, statement=""):
    # A group breakdown of an additive figure should add up to the same-named portfolio figure.
    top = _portfolio_values(out_dir)
    notes = []
    for path in sorted(glob.glob(f"{out_dir}/**/*.csv", recursive=True)):
        try:
            with open(path, newline="") as f:
                rows = list(csv.DictReader(f))
        except (OSError, csv.Error):
            continue
        if not 2 <= len(rows) <= 200:
            continue
        label = next(iter(rows[0]))
        if any(re.fullmatch(r"-?[\d.eE+-]+", (r.get(label) or "").strip()) for r in rows):
            continue
        for name in rows[0]:
            if name not in top or not ADDITIVE.search(name) or NON_ADDITIVE.search(name):
                continue
            try:
                vals = [float(r[name]) for r in rows]
            except (TypeError, ValueError):
                continue
            total, (src, whole) = sum(vals), top[name]
            if abs(total - whole) <= 0.01 * abs(whole) or all(abs(v - whole) <= 0.01 * abs(whole) for v in vals):
                continue
            notes.append(
                f"Output note: column '{name}' in {os.path.basename(path)} adds up to {total:.6g} over its {len(rows)} rows, "
                f"while '{name}' in {src} is {whole:.6g}. When each row is a group's part of the portfolio figure, the rows add "
                f"up to it (a mean of a sum is the sum of the means); an average per member of the group does not. Check which "
                f"of the two the task's description of this column asks for, and keep the two files consistent with it.")
    return notes
