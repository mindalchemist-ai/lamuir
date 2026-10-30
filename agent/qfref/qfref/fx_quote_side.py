import glob, json, os, re, sys
from pathlib import Path

RAW = Path("runs")


def list_runs():
    batches = [b for b in sorted(os.listdir(RAW)) if b.startswith("rag13") and re.search(r"full|final", b)]
    runs = {}
    for b in batches:
        base = b.replace("-r429", "")
        for t in sorted(os.listdir(RAW / b)):
            p = RAW / b / t
            if not t.startswith("t1-") or not (p / "trace" / "mini.traj.json").exists():
                continue
            if (base, t) in runs and "-r429" not in b:
                continue
            runs[(base, t)] = p
    return runs


def verdict(run):
    g = run / "grader_output.txt"
    lines = g.read_text(errors="ignore").strip().splitlines() if g.exists() else []
    last = lines[-1] if lines else ""
    return "PASS" if ("passed" in last and "failed" not in last and "error" not in last) else "FAIL"


def steps(run):
    msgs = json.loads((run / "trace" / "mini.traj.json").read_text())["messages"]
    out = []
    for i, m in enumerate(msgs):
        if m["role"] != "assistant":
            continue
        code, rc, tout = "", None, ""
        for tc in m.get("tool_calls") or []:
            try:
                a = json.loads(tc["function"]["arguments"])
                code = a.get("code") or a.get("command") or ""
            except Exception:
                code = tc["function"].get("arguments", "")
        if i + 1 < len(msgs) and msgs[i + 1]["role"] == "tool":
            c = msgs[i + 1]["content"]
            try:
                j = json.loads(c)
                rc, tout = j.get("returncode"), str(j.get("output", ""))
            except Exception:
                tout = str(c)
        out.append({"req": len(out) + 1, "msg": i, "code": code, "rc": rc, "out": tout})
    return out


_SIDE_LIT = r"""['"](?:buy|sell|long|short|b|s|bought|sold)\w*['"]"""
_SIGN_ASSIGN = re.compile(r"^[ \t]*(?P<lhs>[A-Za-z_][\w.]*(?:\[['\"][^'\"]+['\"]\])?)\s*=\s*(?P<rhs>[^\n]*)$", re.M)
_NOTIONAL = re.compile(r"(?i)\b(?:\w*notional\w*|n|qty|quantity|units|face|face_value|position_size)\b|\[['\"]\w*notional\w*['\"]\]")
_DIFF = re.compile(r"\(\s*[^()\n]*?[\w\])]\s*-\s*[\w(][^()\n]*?\)")


def _sign_token(lhs):
    m = re.search(r"\[['\"]([^'\"]+)['\"]\]$", lhs)
    return m.group(1) if m else lhs.split(".")[-1]


def side_sign_hits(code):
    signs = []
    for m in _SIGN_ASSIGN.finditer(code):
        rhs = m.group("rhs")
        if re.search(_SIDE_LIT, rhs, re.I) and re.search(r"-\s*1(?:\.0*)?\b", rhs):
            signs.append((m.start(), _sign_token(m.group("lhs"))))
    if not signs:
        return []
    start = min(p for p, _ in signs)
    toks = {t for _, t in signs}
    body = re.sub(r"#[^\n]*", "", code[start:])
    with_sign, without = [], []
    for m in _SIGN_ASSIGN.finditer(body):
        lhs, rhs = m.group("lhs"), m.group("rhs")
        if _sign_token(lhs) in toks or "*" not in rhs or not _NOTIONAL.search(rhs):
            continue
        uses = any(re.search(r"(?<![\w'\"])%s(?![\w'\"])|['\"]%s['\"]" % (re.escape(t), re.escape(t)), rhs) for t in toks)
        if uses or re.search(_SIDE_LIT, rhs, re.I) or "abs(" in rhs:
            with_sign.append(m.group(0).strip())
        elif _DIFF.search(rhs):
            without.append(m.group(0).strip())
    if with_sign and without:
        return [{"sign": sorted(toks), "unsigned": without, "signed": with_sign}]
    return []


def side_sign_note(h):
    s = h["sign"][0]
    lines = "; ".join(f"`{x}`" for x in h["unsigned"][:3])
    return (f"Code note: this cell builds the side multiplier `{s}` from the buy/sell field and uses it in "
            f"`{h['signed'][0]}`, but {lines} multiply the notional by a price change without it, so every sell-side "
            f"record gets the buyer's sign. If these amounts are meant from the position holder's side, multiply each "
            f"of them by `{s}`, and check that a sell record and the same record as a buy give opposite values.")


def _input_id_sets(run):
    sets = {}
    for f in glob.glob(str(run / "staged" / "environment" / "data" / "**" / "*.csv"), recursive=True):
        try:
            import pandas as pd
            df = pd.read_csv(f, nrows=5000)
        except Exception:
            continue
        for c in df.columns:
            if re.search(r"(?i)(^|_)id$|_id$", str(c)) and not pd.api.types.is_numeric_dtype(df[c]):
                v = df[c].dropna().astype(str)
                if len(v) >= 2 and v.is_unique:
                    sets[f"{Path(f).name}:{c}"] = set(v)
    return sets


def _id_maps(obj, path=""):
    if isinstance(obj, dict):
        yield path, set(map(str, obj.keys()))
        for k, v in obj.items():
            yield from _id_maps(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _id_maps(v, f"{path}[{i}]")
        ids = [str(x.get(k)) for x in obj if isinstance(x, dict) for k in x if re.search(r"(?i)(^|_)id$", str(k))]
        if ids:
            yield path + "[*].id", set(ids)


def count_hits(run, sibling_required):
    ids = _input_id_sets(run)
    if not ids:
        return []
    hits = []
    for f in glob.glob(str(run / "output" / "**" / "*.json"), recursive=True):
        try:
            obj = json.load(open(f))
        except Exception:
            continue
        maps = list(_id_maps(obj))
        for name, s in ids.items():
            full = [p for p, k in maps if k == s]
            for p, k in maps:
                if len(k) >= 1 and k < s and len(k) / len(s) >= 0.0:
                    if sibling_required and not full:
                        continue
                    hits.append({"file": Path(f).name, "path": p, "have": len(k), "input": len(s), "src": name,
                                 "missing": sorted(s - k)[:5], "sibling_full": full[:2]})
    return hits


_FILL = re.compile(r"^[ \t]+(?P<d>[A-Za-z_]\w*)\[[^\]\n]+\]\s*=", re.M)
_WRITE = re.compile(r"save_json\(|json\.dump\(|\.to_csv\(|\.to_json\(|open\([^)\n]*['\"]w")


def loop_rerun_hits(st):
    hits = []
    for i, s in enumerate(st):
        if s["rc"] in (0, None) or "Traceback" not in s["out"] or not re.search(r"^\s*for\b", s["code"], re.M):
            continue
        filled = set(_FILL.findall(s["code"]))
        if not filled:
            continue
        for d in filled:
            rerun, wrote = False, None
            for j in range(i + 1, len(st)):
                c = st[j]["code"]
                ok = st[j]["rc"] == 0
                if ok and (re.search(r"^[ \t]+%s\[[^\]\n]+\]\s*=" % re.escape(d), c, re.M) or
                           re.search(r"^[ \t]*%s\s*=\s*\{[^}\n]*\bfor\b" % re.escape(d), c, re.M) or
                           re.search(r"^[ \t]*%s\s*=\s*[A-Za-z_]\w*\(" % re.escape(d), c, re.M)):
                    rerun = True
                    break
                if ok and _WRITE.search(c) and re.search(r"\b%s\b" % re.escape(d), c):
                    wrote = st[j]["req"]
                    break
            if wrote and not rerun:
                hits.append({"err_req": s["req"], "map": d, "write_req": wrote})
    return hits
