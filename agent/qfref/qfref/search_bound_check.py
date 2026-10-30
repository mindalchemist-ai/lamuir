import csv, glob, json, math, os, re

NUMBER = r"(?:-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?|10\^\{?-?\d+\}?)"
BRACKET = re.compile(r"\[\s*\$?\s*(" + NUMBER + r")\s*,\s*(" + NUMBER + r")\s*\$?\s*\]")
SEARCH_WORDS = re.compile(r"\b(?:search|bracket|root|solve|solver|brentq|bisect)", re.I)


def _num(text):
    m = re.fullmatch(r"10\^\{?(-?\d+)\}?", text)
    return 10.0 ** int(m.group(1)) if m else float(text)


def search_bounds(statement):
    bounds = set()
    for sent in re.split(r"(?<=[.;])\s+|\n", (statement or "").replace("$", "")):
        if SEARCH_WORDS.search(sent) and not re.search(r"integrat", sent, re.I):
            for a, b in BRACKET.findall(sent):
                bounds |= {_num(a), _num(b)}
    return bounds


def _cells(path):
    if path.endswith(".json"):
        try:
            data = json.load(open(path))
        except (OSError, ValueError):
            return
        stack = [("", data)]
        while stack:
            key, node = stack.pop()
            if isinstance(node, dict):
                stack += [(k, v) for k, v in node.items()]
            elif isinstance(node, list):
                stack += [(key, v) for v in node]
            elif isinstance(node, (int, float)) and not isinstance(node, bool):
                yield key, float(node)
    else:
        try:
            with open(path, newline="") as f:
                rows = list(csv.reader(f))
        except (OSError, csv.Error):
            return
        header = rows[0] if rows else []
        for r in rows[1:]:
            for j, c in enumerate(r):
                try:
                    yield (header[j] if j < len(header) else str(j)), float(c)
                except ValueError:
                    pass


def search_bound_notes(out_dir, statement=""):
    # A solver result sitting exactly on the search interval's end means no root was found inside it.
    bounds = search_bounds(statement)
    if not bounds:
        return []
    notes = []
    for path in sorted(glob.glob(f"{out_dir}/**/*.csv", recursive=True) + glob.glob(f"{out_dir}/**/*.json", recursive=True)):
        hits = {}
        for key, v in _cells(path):
            for b in bounds:
                if b != 0 and math.isfinite(v) and abs(v - b) <= 1e-12 * max(1.0, abs(b)):
                    hits.setdefault((key, b), 0)
                    hits[(key, b)] += 1
        for (key, b), n in sorted(hits.items()):
            notes.append(
                f"Output note: {n} value(s) of '{key}' in {os.path.basename(path)} equal {b:g}, an end of the search interval the "
                f"task gives. A root search that returns the end of its interval found no root inside it, so those points were "
                f"not solved. Check the input to the solver at those points (for example a price below its no-arbitrage bound, "
                f"or a tolerance that skips very small prices) and solve them inside the interval.")
    return notes
