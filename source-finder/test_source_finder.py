"""Offline tests of the source finder (Claude Code): Tavily, Nemotron and downloads are replaced by fakes, so no
network call and no key is needed. Usage: python source-finder/test_source_finder.py"""
import json
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import source_finder as sf  # noqa: E402

failed = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        failed.append(name)


def refused(plan):
    try:
        sf.validate(plan)
    except sf.Refused:
        return True
    return False


# validation: only registered sources and sane parameters get through
check("treasury years accepted", sf.validate({"source": "treasury_par_yield", "params": {"years": [2023, 2022, 2023]}})["params"] == {"years": [2022, 2023]})
check("unknown source refused", refused({"source": "bloomberg", "params": {}}))
check("null source refused", refused({"source": None, "params": {}, "reason": "no source"}))
check("future year refused", refused({"source": "treasury_par_yield", "params": {"years": [2099]}}))
check("too many years refused", refused({"source": "treasury_par_yield", "params": {"years": list(range(2000, 2015))}}))
check("ECB currencies upper-cased", sf.validate({"source": "ecb_fx_reference", "params": {"currencies": ["usd", "gbp"], "start": "2025-01-01", "end": "2025-12-31"}})["params"]["currencies"] == ["GBP", "USD"])
check("ECB unknown currency refused", refused({"source": "ecb_fx_reference", "params": {"currencies": ["BTC"], "start": "2025-01-01", "end": "2025-12-31"}}))
check("ECB reversed dates refused", refused({"source": "ecb_fx_reference", "params": {"currencies": ["USD"], "start": "2025-12-31", "end": "2025-01-01"}}))
check("SEC ticker with a path refused", refused({"source": "sec_companyfacts", "params": {"tickers": ["../../etc"]}}))
check("SEC more than 5 tickers refused", refused({"source": "sec_companyfacts", "params": {"tickers": ["A", "B", "C", "D", "E", "F"]}}))

# fetch refuses a host outside the allowlist, even if asked
try:
    sf.fetch("https://example.com/data.csv", pathlib.Path(tempfile.mkdtemp()) / "x")
    check("fetch refuses a non-official host", False)
except AssertionError:
    check("fetch refuses a non-official host", True)

# search keeps only allowlisted hosts even if the provider returns others
orig = sf.curl
sf.curl = lambda *a, **k: json.dumps({"results": [
    {"title": "Treasury rates", "url": "https://home.treasury.gov/resource-center/data-chart-center/interest-rates", "content": "x"},
    {"title": "lookalike", "url": "https://treasury.gov.example.com/x", "content": "y"},
    {"title": "blog", "url": "https://someblog.com/yield-curve", "content": "z"}]}).encode()
sf.os.environ.setdefault("TAVILY_API_KEY", "test-not-a-key")
res = sf.tavily_search("yield curve inversion")
sf.curl = orig
check("search drops non-official and lookalike hosts", [r["url"] for r in res] == ["https://home.treasury.gov/resource-center/data-chart-center/interest-rates"])

# end to end with fakes: the record and the instruction are written
out = pathlib.Path(tempfile.mkdtemp())
fake_files = lambda plan, d: (d.mkdir(parents=True, exist_ok=True), (d / "treasury_par_yield_curve_2022.csv").write_text("Date\n"),
                              [{"file": "treasury_par_yield_curve_2022.csv", "url": "https://home.treasury.gov/x", "sha256": "0", "bytes": 5}])[2]
rec = sf.build("How many days was the curve inverted in 2022?", out,
               search=lambda q: [{"title": "t", "url": "https://home.treasury.gov/a", "content": ""}],
               plan=lambda q, r: sf.validate({"source": "treasury_par_yield", "params": {"years": [2022]}, "reason": "Treasury publishes par yields"}),
               fetcher=fake_files)
check("sources.json written with search, plan and files", json.loads((out / "sources.json").read_text())["plan"]["source"] == "treasury_par_yield"
      and rec["search"]["provider"] == "Tavily")
check("instruction.md names the question and the file", "inverted in 2022" in (out / "instruction.md").read_text()
      and "treasury_par_yield_curve_<year>.csv" in (out / "instruction.md").read_text())

# the model's reply is parsed strictly
sf.curl = lambda *a, **k: json.dumps({"choices": [{"message": {"content": 'Sure: {"source": "ecb_fx_reference", "params": {"currencies": ["USD"], "start": "2025-01-02", "end": "2025-12-31"}, "reason": "ECB"}'}}]}).encode()
sf.os.environ.setdefault("MODEL_API_KEY", "test-not-a-key")
check("plan parsed from a model reply", sf.plan_with_nemotron("q", [])["source"] == "ecb_fx_reference")
sf.curl = lambda *a, **k: json.dumps({"choices": [{"message": {"content": "I cannot help"}}]}).encode()
try:
    sf.plan_with_nemotron("q", [])
    check("a reply without JSON is refused", False)
except sf.Refused:
    check("a reply without JSON is refused", True)
sf.curl = orig

# keys never reach the command line
calls = []
sf.subprocess.run = lambda cmd, input=None, capture_output=None: (calls.append((cmd, input)), type("P", (), {"returncode": 0, "stdout": b"{}", "stderr": b""})())[1]
sf.os.environ["TAVILY_API_KEY"] = "secret-value-123"
sf.tavily_search("q")
check("key passed on stdin, not in argv", "secret-value-123" not in " ".join(calls[-1][0]) and b"secret-value-123" in calls[-1][1])
sys.exit(1 if failed else 0)
