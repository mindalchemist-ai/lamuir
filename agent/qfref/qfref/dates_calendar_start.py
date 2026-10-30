import glob, json, math, os, re, sys
import pandas as pd

CAL_RE = re.compile(r"(?:after|following|beyond)\s+(?:the\s+)?(?:first\s+)?(\d+)(?:st|nd|rd|th)?\s+calendar\s+(month|day|week|quarter|year)s?", re.I)
FREQ = {"month": "M", "day": "D", "week": "W", "quarter": "Q", "year": "Y"}
DATE_COL_RE = re.compile(r"(^|_)(date|month|period|dt)($|_)", re.I)


def input_grid(data_dir, unit):
    vals = set()
    for p in sorted(glob.glob(os.path.join(data_dir, "**", "*"), recursive=True)):
        try:
            if p.endswith((".pqt", ".parquet")):
                df = pd.read_parquet(p)
            elif p.endswith(".csv"):
                df = pd.read_csv(p, nrows=2_000_000)
            else:
                continue
        except Exception:
            continue
        for c in df.columns:
            if not DATE_COL_RE.search(str(c)):
                continue
            s = pd.to_datetime(df[c], errors="coerce").dropna()
            if len(s):
                vals.update(s.dt.to_period(FREQ[unit]).unique())
    return sorted(vals)


def output_date_frames(out_dir):
    for p in sorted(glob.glob(os.path.join(out_dir, "*.csv"))):
        try:
            df = pd.read_csv(p)
        except Exception:
            continue
        cols = [c for c in df.columns if DATE_COL_RE.search(str(c))]
        if not cols:
            continue
        d = pd.to_datetime(df[cols[0]], errors="coerce")
        if d.notna().any():
            yield os.path.basename(p), df.assign(_d=d)


def check_calendar_offset(instruction, data_dir, out_dir):
    m = CAL_RE.search(instruction)
    if not m:
        return []
    n, unit = int(m.group(1)), m.group(2).lower()
    grid = input_grid(data_dir, unit)
    if len(grid) <= n:
        return []
    pos = {g: i for i, g in enumerate(grid)}
    frames = list(output_date_frames(out_dir))
    present = set()
    for _, df in frames:
        present.update(df["_d"].dropna().dt.to_period(FREQ[unit]).unique())
    notes = []
    for name, df in frames:
        first = df["_d"].min().to_period(FREQ[unit])
        p = pos.get(first)
        if p is None or p == 0:
            continue
        if p < n:
            continue
        expected = next((g for g in grid[n:] if g in present), None)
        if expected is not None and first != expected:
            notes.append(
                f"{name}: earliest row is {first} = position {p} (0-based) of the {len(grid)} distinct calendar {unit}s in the input data. "
                f"A start rule counted in calendar {unit}s with n = {n} uses that full grid (index {n} = {grid[n]}), "
                f"not the list of periods that survived your filters. Recheck which date list you skip the first {n} entries of."
            )
    return notes


def json_leaves(obj, path=""):
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        if isinstance(obj, float) and math.isfinite(obj) and obj != 0:
            yield path, float(obj)
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from json_leaves(v, f"{path}.{k}" if path else str(k))


def column_means(out_dir):
    means = []
    for p in sorted(glob.glob(os.path.join(out_dir, "*.csv"))):
        try:
            df = pd.read_csv(p)
        except Exception:
            continue
        if len(df) > 500_000:
            continue
        num = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and df[c].notna().sum() > 1]
        cats = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c]) and 1 < df[c].nunique() <= 20]
        for c in num:
            means.append((os.path.basename(p), c, "all", df[c].mean()))
            for g in cats:
                for val, sub in df.groupby(g)[c]:
                    if sub.notna().sum() > 1:
                        means.append((os.path.basename(p), c, f"{g}={val}", sub.mean()))
    return means


def close(a, b, rel=1e-9):
    return abs(a - b) <= rel * max(abs(a), abs(b))


def check_key_column_alignment(out_dir):
    means = column_means(out_dir)
    if not means:
        return []
    cols = {c for _, c, _, _ in means}
    notes = []
    for p in sorted(glob.glob(os.path.join(out_dir, "*.json"))):
        try:
            leaves = list(json_leaves(json.load(open(p))))
        except Exception:
            continue
        for key, v in leaves:
            named = [c for c in cols if len(str(c)) >= 4 and str(key).endswith(str(c))]
            if not named:
                continue
            named_c = max(named, key=lambda c: len(str(c)))
            if any(c == named_c and close(v, mu) for _, c, _, mu in means):
                continue
            files = {f for f, c, _, _ in means if c == named_c}
            other = [(f, c, g) for f, c, g, mu in means if f in files and c != named_c and not str(named_c).endswith(str(c)) and close(v, mu)]
            if other:
                f, c, g = other[0]
                notes.append(f"{os.path.basename(p)}: '{key}' equals the mean of column '{c}' ({g}) in {f}, not of column '{named_c}'. Check the order in which coefficients are mapped to names.")
    return notes


