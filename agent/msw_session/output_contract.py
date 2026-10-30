'output_contract for the Python session: the output requirements read from the task statement (files, keys, columns, key templates and their stated value forms, units, decimals, date formats, order) and writers that apply only what the statement states.'
import json
import os
import re

from session_io import save_json, to_builtin

SPEC_PATH = os.environ.get("MSW_OUTPUT_SPEC", "/tmp/msw_output_spec.json")


def defaults():
    """The output defaults for whatever the task statement leaves open (location, file types, names, numbers, dates, a
    conventions record); a requirement the statement states always wins."""
    return {k: v for k, v in spec().get("_defaults", {}).items() if k != "files_without_requirements"}


def spec(name=None):
    """The output contract read from the task statement: {file: {...}} or the entry of one file (by name or basename).
    Each requirement carries the statement text it comes from; a requirement the statement does not state is absent."""
    try:
        with open(SPEC_PATH) as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {}
    if name is None:
        return data
    if name == "_defaults":
        return data.get("_defaults", {})
    base = os.path.basename(name)
    return data.get(name) or next((v for k, v in data.items() if k != "_defaults" and os.path.basename(k) == base), {})


def _value_forms(entry):
    return [(float(x), y) for x, y in entry.get("value_forms", []) if re.fullmatch(r"-?\d*\.?\d+", str(x))]


RULES = [
    ("as written", lambda x: _plain(x)),
    ("leading 0. dropped", lambda x: _plain(x)[2:] if _plain(x).startswith("0.") else None),
    ("times 100", lambda x: _plain(round(x * 100, 10))),
    ("point as underscore", lambda x: _plain(x).replace(".", "_")),
    ("point removed", lambda x: _plain(x).replace(".", "")),
]


def _plain(x):
    if isinstance(x, float) and x.is_integer():
        return str(int(x))
    return repr(x) if isinstance(x, float) else str(x)


def value_rule(name=None):
    """(rule name, function) that turns a number into its form inside keys, learned from the statement's own examples
    (such as "0.99 becomes 99"); the identity when the statement gives no example."""
    forms = []
    for entry in ([spec(name)] if name else [v for k, v in spec().items() if k != "_defaults"]):
        forms += _value_forms(entry)
    for rule, fn in RULES:
        if not forms or any(fn(x) is None for x, _ in forms):
            continue
        # the same prefix and suffix around the transformed number in every example ("p99", "q_995_x")
        affixes = set()
        for x, y in forms:
            core = fn(x)
            i = y.find(core) if core else -1
            affixes.add((y[:i], y[i + len(core):]) if i >= 0 else None)
        if len(affixes) == 1 and None not in affixes:
            pre, suf = affixes.pop()
            name = rule + (f", prefix {pre!r}" if pre else "") + (f", suffix {suf!r}" if suf else "")
            return name, (lambda v, fn=fn, pre=pre, suf=suf: None if fn(v) is None else f"{pre}{fn(v)}{suf}")
    return RULES[0]


def key(template, file=None, **values):
    """A key or column name from a template of the statement, e.g. key("var_{level}_{method}", level=0.99,
    method="historical"); numbers take the form the statement's examples show, other values are written as given."""
    rule = value_rule(file)[1]
    out = template
    for k, v in values.items():
        text = rule(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else str(v)
        out = out.replace("{" + k + "}", text if text is not None else _plain(v))
    if re.search(r"\{[A-Za-z_]+\}", out):
        raise ValueError(f"no value given for {re.findall(r'{([A-Za-z_]+)}', out)} in {template!r}")
    return out


def number_key(n, file=None):
    """An integer key (a day offset, a lag, a horizon) written the way the statement's examples for that file write it,
    e.g. "t-5", "t0", "t+5" when the examples carry a prefix and an explicit plus; str(n) when there are no such examples."""
    entries = [spec(file)] if file else [v for k, v in spec().items() if k != "_defaults"]
    pat = next((p for e in entries for p in e.get("number_keys", [])), None)
    n = int(n)
    if not pat:
        return str(n)
    body = f"+{n}" if pat.get("explicit_plus") and n > 0 else str(n)
    return f"{pat.get('prefix', '')}{body}{pat.get('suffix', '')}"


def _report(path, present, entry):
    expected = entry.get("keys") or entry.get("columns") or []
    missing = [k for k in expected if k not in present]
    extra = [k for k in present if expected and k not in expected and not _matches_template(k, entry)]
    if missing:
        print(f"output_contract: {os.path.basename(path)} lacks {len(missing)} name(s) the task states: {missing[:12]}")
    if extra and entry.get("type") == "csv":
        print(f"output_contract: {os.path.basename(path)} has column(s) the task does not list: {extra[:12]}")
    if not missing:
        print(f"output_contract: {os.path.basename(path)} holds every name the task states for it")


def _matches_template(name, entry):
    for t in entry.get("templates", []):
        rx = "".join(re.escape(p) if i % 2 == 0 else r"[A-Za-z0-9._-]+" for i, p in enumerate(re.split(r"(\{[A-Za-z_]+\})", t)))
        if re.fullmatch(rx, name):
            return True
    return False


def _json_names(data, out):
    if isinstance(data, dict):
        for k, v in data.items():
            out.add(k)
            _json_names(v, out)
    elif isinstance(data, list):
        for v in data:
            _json_names(v, out)
    return out


def _int_like_keys(data):
    # keys "5.0" -> "5" in every object whose keys are all integer-like floats
    if isinstance(data, dict):
        keys = list(data)
        fix = len(keys) >= 1 and all(isinstance(k, str) and re.fullmatch(r"-?\d+\.0", k) for k in keys)
        return {(k[:-2] if fix else k): _int_like_keys(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_int_like_keys(v) for v in data]
    return data


def write_json(path, data, *, indent=2):
    """save_json plus what the statement states for this file: integer-like float keys ("5.0") become integers unless the
    statement shows the ".0" form; then reports names the statement lists for this file that the data lacks."""
    entry = spec(path)
    data = to_builtin(data)
    if not entry.get("float_keys_shown"):
        data = _int_like_keys(data)
    save_json(path, data, indent=indent)
    if entry:
        _report(path, _json_names(data, set()), entry)
    return path


def write_csv(path, frame, **kwargs):
    """DataFrame.to_csv with index=False and what the statement states for this file: its listed column order (when the
    frame holds every listed column), its date format for datetime columns, and its stated number of decimals."""
    import pandas as pd
    entry = spec(path)
    out = frame.copy()
    cols = entry.get("columns") or []
    if cols and all(c in out.columns for c in cols):
        out = out[cols + [c for c in out.columns if c not in cols]]
    fmt = entry.get("date_format")
    if fmt and fmt != "iso8601":
        for c in out.columns:
            if pd.api.types.is_datetime64_any_dtype(out[c]):
                out[c] = out[c].dt.strftime(fmt)
    kwargs.setdefault("index", False)
    if entry.get("decimals") is not None and "float_format" not in kwargs:
        kwargs["float_format"] = f"%.{int(entry['decimals'])}f"
    out.to_csv(path, **kwargs)
    if entry:
        _report(path, list(out.columns), entry)
    return path


def describe(name=None):
    """Prints the contract, one file per block, with the statement text each requirement comes from."""
    data = spec() if name is None else {name: spec(name)}
    if "_defaults" in data and name is None:
        print("defaults for what the statement leaves open:")
        for k, v in defaults().items():
            print(f"  {k}: {v}")
        data = {k: v for k, v in data.items() if k != "_defaults"}
    for f, entry in data.items():
        print(f"{f} ({entry.get('type', '?')})")
        for k, v in entry.items():
            if k not in ("type",) and v not in (None, [], {}, ""):
                print(f"  {k}: {v}")
