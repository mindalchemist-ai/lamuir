"""Lamuir source finder: turn a question into an input folder built from official public data.

Usage: python source-finder/source_finder.py "How many days was the US yield curve inverted in 2022-2025?" --out <dir>

Steps (the agent itself never goes online):
1. Search: Tavily web search, restricted to official domains, finds pages that answer "where is this data published".
2. Plan: Nemotron on Nebius Token Factory picks one registered source and its parameters, as strict JSON,
   from the question and the search results. Anything outside the registry is refused.
3. Download: the registered adapter fetches the data from that source's own official endpoint (never from a URL
   taken from a search result) and writes it unchanged.
4. Record: <out>/sources.json holds the question, the search results, the plan, and for every file its URL, UTC time
   and SHA-256. <out>/instruction.md is the question plus a description of the files, ready for the agent.

Keys come from the environment only: TAVILY_API_KEY, and MODEL_API_KEY (or NEBIUS_API_KEY) with MODEL_ENDPOINT.
Keys are passed to curl on stdin, so they never appear in a process list or a log.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import subprocess
import urllib.parse

ALLOWED_DOMAINS = ["home.treasury.gov", "treasury.gov", "ecb.europa.eu", "data.ecb.europa.eu", "sec.gov"]
MODEL = os.environ.get("NEBIUS_MODEL", "nvidia/nemotron-3-super-120b-a12b")
DEFAULT_ENDPOINT = "https://api.studio.nebius.com/v1"
CURRENCIES = {"USD", "GBP", "JPY", "CHF", "CNY", "CAD", "AUD", "SEK", "NOK", "DKK", "PLN", "CZK", "HUF", "KRW", "INR"}


class Refused(Exception):
    """The question cannot be served from a registered official source."""


def curl(url, *, headers=None, data=None, out=None, user_agent=None):
    # Secrets go in a curl config read from stdin, never on the command line.
    config = "".join(f'header = "{h}"\n' for h in (headers or []))
    if user_agent:
        config += f'user-agent = "{user_agent}"\n'
    cmd = ["curl", "-sS", "--fail-with-body", "--max-time", "120", "-K", "-", url]
    if data is not None:
        cmd += ["--data", data]  # request bodies hold no secrets
    if out:
        cmd += ["-o", str(out)]
    p = subprocess.run(cmd, input=config.encode(), capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(f"download failed ({p.returncode}) for {urllib.parse.urlsplit(url).netloc}: "
                           f"{p.stdout[:200].decode(errors='replace')} {p.stderr[:200].decode(errors='replace')}")
    return p.stdout


def need(name, *alts):
    for n in (name, *alts):
        if os.environ.get(n, "").strip():
            return os.environ[n].strip()
    raise SystemExit(f"set {name} in the environment")


# 1. search
def tavily_search(question):
    body = json.dumps({"query": f"official data source: {question}", "search_depth": "basic", "max_results": 5,
                       "include_domains": ALLOWED_DOMAINS})
    raw = curl("https://api.tavily.com/search", headers=["Content-Type: application/json",
                                                         f"Authorization: Bearer {need('TAVILY_API_KEY')}"], data=body)
    results = json.loads(raw).get("results", [])
    # include_domains is a request, not a guarantee: keep only results whose host is on the allowlist
    keep = []
    for r in results:
        host = urllib.parse.urlsplit(r.get("url", "")).hostname or ""
        if any(host == d or host.endswith("." + d) for d in ALLOWED_DOMAINS):
            keep.append({"title": r.get("title", ""), "url": r["url"], "content": (r.get("content") or "")[:500]})
    return keep


# 2. plan
SOURCES = {
    "treasury_par_yield": {
        "describe": "U.S. Treasury Daily Par Yield Curve Rates, one CSV per calendar year (1990 onward).",
        "params": {"years": "list of calendar years, e.g. [2022, 2023]"},
    },
    "ecb_fx_reference": {
        "describe": "ECB euro foreign exchange reference rates, daily, units of currency per 1 EUR (1999 onward).",
        "params": {"currencies": "list of ISO codes other than EUR", "start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},
    },
    "sec_companyfacts": {
        "describe": "SEC EDGAR XBRL company facts for listed U.S. companies (all reported values of every tag).",
        "params": {"tickers": "list of U.S. stock tickers, at most 5"},
    },
}


def plan_with_nemotron(question, results):
    system = ("You map a finance question to exactly one registered official data source. Reply with JSON only: "
              '{"source": <one of the registry keys or null>, "params": {...}, "reason": "<one sentence>"}. '
              "Use null when no registered source holds the data the question needs. Registry: " + json.dumps(SOURCES))
    user = json.dumps({"question": question, "search_results": [{"title": r["title"], "url": r["url"]} for r in results]})
    endpoint = os.environ.get("MODEL_ENDPOINT", DEFAULT_ENDPOINT).rstrip("/")
    body = json.dumps({"model": MODEL, "temperature": 0, "max_tokens": 2000,
                       "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]})
    raw = curl(endpoint + "/chat/completions", headers=["Content-Type: application/json",
                                                       f"Authorization: Bearer {need('MODEL_API_KEY', 'NEBIUS_API_KEY')}"],
               data=body)
    text = json.loads(raw)["choices"][0]["message"]["content"] or ""
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise Refused("the model did not return a plan")
    return validate(json.loads(m.group(0)))


def validate(plan):
    source, params = plan.get("source"), plan.get("params") or {}
    if source not in SOURCES:
        raise Refused(plan.get("reason") or "no registered official source holds this data")
    if source == "treasury_par_yield":
        years = sorted({int(y) for y in params.get("years", [])})
        if not years or years[0] < 1990 or years[-1] > dt.date.today().year or len(years) > 10:
            raise Refused(f"years out of range: {params.get('years')}")
        params = {"years": years}
    elif source == "ecb_fx_reference":
        cur = sorted({str(c).upper() for c in params.get("currencies", [])})
        start, end = dt.date.fromisoformat(params["start"]), dt.date.fromisoformat(params["end"])
        if not cur or not set(cur) <= CURRENCIES or start < dt.date(1999, 1, 4) or end < start:
            raise Refused(f"unsupported currencies or dates: {params}")
        params = {"currencies": cur, "start": start.isoformat(), "end": end.isoformat()}
    elif source == "sec_companyfacts":
        tickers = sorted({str(t).upper() for t in params.get("tickers", []) if re.fullmatch(r"[A-Za-z.\-]{1,6}", str(t))})
        if not tickers or len(tickers) > 5:
            raise Refused(f"unsupported tickers: {params.get('tickers')}")
        params = {"tickers": tickers}
    return {"source": source, "params": params, "reason": plan.get("reason", "")}


# 3. download (each adapter builds its own official URL from validated parameters)
def sec_agent():
    return f"MindAlchemist Lamuir {need('DEMO_DATA_CONTACT_EMAIL')}"


def download(plan, data_dir):
    data_dir.mkdir(parents=True, exist_ok=True)
    files, p = [], plan["params"]
    if plan["source"] == "treasury_par_yield":
        for y in p["years"]:
            url = ("https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/"
                   f"{y}/all?type=daily_treasury_yield_curve&field_tdr_date_value={y}&page&_format=csv")
            files.append(fetch(url, data_dir / f"treasury_par_yield_curve_{y}.csv"))
    elif plan["source"] == "ecb_fx_reference":
        url = (f"https://data-api.ecb.europa.eu/service/data/EXR/D.{'+'.join(p['currencies'])}.EUR.SP00.A"
               f"?startPeriod={p['start']}&endPeriod={p['end']}&format=csvdata")
        files.append(fetch(url, data_dir / "ecb_reference_rates.csv"))
    elif plan["source"] == "sec_companyfacts":
        tickers = json.loads(curl("https://www.sec.gov/files/company_tickers.json", user_agent=sec_agent()))
        cik = {v["ticker"].upper(): int(v["cik_str"]) for v in tickers.values()}
        for t in p["tickers"]:
            if t not in cik:
                raise Refused(f"ticker {t} not found in SEC's list")
            url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik[t]:010d}.json"
            files.append(fetch(url, data_dir / f"companyfacts_{t}.json", user_agent=sec_agent()))
    return files


def fetch(url, path, user_agent=None):
    host = urllib.parse.urlsplit(url).hostname or ""
    assert any(host == d or host.endswith("." + d) for d in ALLOWED_DOMAINS), host
    curl(url, out=path, user_agent=user_agent)
    return {"file": path.name, "url": url, "downloaded_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}


# 4. record
FILE_NOTES = {
    "treasury_par_yield": "`treasury_par_yield_curve_<year>.csv`: the U.S. Treasury's Daily Treasury Par Yield Curve Rates "
                          "for each year, as published. `Date` is MM/DD/YYYY; the other columns are par yields in percent "
                          "by tenor; rows are in the Treasury's order and the tenor columns differ between years.",
    "ecb_fx_reference": "`ecb_reference_rates.csv`: the ECB Data Portal's CSV export of the euro foreign exchange "
                        "reference rates, as delivered: one row per currency and date (`CURRENCY`, `TIME_PERIOD`, "
                        "`OBS_VALUE`). Every rate is units of that currency per 1 EUR.",
    "sec_companyfacts": "`companyfacts_<ticker>.json`: the SEC EDGAR XBRL companyfacts JSON for each company, as "
                        "delivered. Facts are under `facts` -> taxonomy -> tag -> `units`; the same period appears in "
                        "several filings, so values are not deduplicated.",
}


def build(question, out, search=tavily_search, plan=plan_with_nemotron, fetcher=download):
    out = pathlib.Path(out)
    results = search(question)
    chosen = plan(question, results)
    files = fetcher(chosen, out / "environment" / "data")
    record = {"question": question, "search": {"provider": "Tavily", "allowed_domains": ALLOWED_DOMAINS, "results": results},
              "plan": {"model": MODEL, "provider": "Nebius Token Factory", **chosen}, "files": files}
    (out / "sources.json").write_text(json.dumps(record, indent=1))
    (out / "instruction.md").write_text(
        f"# {question}\n\n## Data\n\nThe files in `/app/data/` were downloaded from official public sources "
        f"(see `sources.json` beside this task for the URLs, download times and SHA-256):\n\n- {FILE_NOTES[chosen['source']]}\n\n"
        "## Output\n\nWrite to `/app/output/`: `results.json` with the key numbers that answer the question, "
        "`analysis.csv` with the table behind them, `chart.png`, and `explanation.md`, a short plain-English answer "
        "that states the data source, the method and its limits.\n")
    return record


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    try:
        r = build(a.question, a.out)
        print(json.dumps({"source": r["plan"]["source"], "params": r["plan"]["params"],
                          "files": [f["file"] for f in r["files"]]}, indent=1))
    except Refused as e:
        raise SystemExit(f"not served: {e}")
