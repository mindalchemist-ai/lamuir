"""Data-quality facts about the task's tabular inputs, printed before the model's first reply.

Usage: python profile_data.py <input_dir>
States facts only (missing cells, non-numeric tokens in numeric columns, duplicates, date order, extreme values,
constant columns); how to treat them is the task's decision. Runs in the task's own interpreter.
"""
import pathlib
import sys

import numpy as np
import pandas as pd

MAX_FILES = 8
MAX_COLS = 12
MISSING_TOKENS = {"", "na", "n/a", "nan", "null", "none", "-", "--", "#n/a", "nat"}


def read_table(path):
    suffix = path.suffix.lower()
    if suffix in (".csv", ".tsv", ".txt"):
        sep = "\t" if suffix == ".tsv" else None
        return pd.read_csv(path, sep=sep, engine="python", dtype=str, keep_default_na=False)
    if suffix in (".parquet", ".pqt"):
        return pd.read_parquet(path).astype(str).replace({"nan": "", "None": "", "NaT": ""})
    return None


def numeric_part(col):
    stripped = col.str.strip()
    missing = stripped.str.lower().isin(MISSING_TOKENS)
    values = pd.to_numeric(stripped.where(~missing), errors="coerce")
    bad = (~missing) & values.isna()
    return values, missing, bad


def date_part(name, col):
    if not any(k in name.lower() for k in ("date", "time", "period", "day", "month")):
        return None
    parsed = pd.to_datetime(col.str.strip(), errors="coerce", format="mixed")
    return parsed if parsed.notna().mean() > 0.8 else None


def profile(path):
    try:
        df = read_table(path)
    except Exception as exc:
        return [f"  could not be read as a table ({type(exc).__name__})"]
    if df is None or df.empty:
        return []
    lines = [f"  {len(df)} rows x {df.shape[1]} columns; fully duplicated rows: {int(df.duplicated().sum())}"]
    numeric_cols, notes = [], []
    for name in df.columns[:200]:
        col = df[name].astype(str)
        dates = date_part(str(name), col)
        values, missing, bad = numeric_part(col)
        n_missing = int(missing.sum())
        if dates is not None:
            d = dates.dropna()
            dup = int(d.duplicated().sum())
            order = "increasing" if d.is_monotonic_increasing else ("decreasing" if d.is_monotonic_decreasing else "not sorted")
            notes.append(f"  date column `{name}`: {d.min().date()} to {d.max().date()}, {order}, duplicate dates {dup}, "
                         f"unparseable or missing {len(col) - len(d)}")
            continue
        if values.notna().mean() >= 0.8 and len(values.dropna()) > 0:
            numeric_cols.append(name)
            v = values.dropna()
            med = float(v.median())
            mad = float((v - med).abs().median())
            extreme = int(((v - med).abs() > 20 * mad).sum()) if mad > 0 else 0
            flags = []
            if n_missing:
                flags.append(f"missing {n_missing}")
            if int(bad.sum()):
                examples = sorted(set(col[bad].str.strip()))[:3]
                flags.append(f"non-numeric {int(bad.sum())} (e.g. {', '.join(repr(e) for e in examples)})")
            if extreme:
                flags.append(f"beyond 20 MAD from the median {extreme} (max |x| {float(v.abs().max()):.4g})")
            if v.nunique() == 1:
                flags.append("constant")
            if flags:
                notes.append(f"  numeric column `{name}`: " + "; ".join(flags))
        elif n_missing:
            notes.append(f"  text column `{name}`: missing {n_missing}")
    if numeric_cols:
        lines.append(f"  numeric columns: {len(numeric_cols)}; total missing cells in them: "
                     f"{int(sum(numeric_part(df[c].astype(str))[1].sum() for c in numeric_cols))}")
    lines += notes[:MAX_COLS]
    if len(notes) > MAX_COLS:
        lines.append(f"  ... {len(notes) - MAX_COLS} more columns with findings")
    return lines


def main(root):
    paths = sorted(p for p in pathlib.Path(root).rglob("*")
                   if p.is_file() and p.suffix.lower() in (".csv", ".tsv", ".parquet", ".pqt"))
    if not paths:
        return
    out = []
    for path in paths[:MAX_FILES]:
        body = profile(path)
        if body:
            out.append(f"== {path}")
            out += body
    if len(paths) > MAX_FILES:
        out.append(f"({len(paths) - MAX_FILES} more tabular files not profiled)")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/input")
