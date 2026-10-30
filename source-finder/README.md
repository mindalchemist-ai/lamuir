# Source finder (Tavily)

Written by Claude Code, 2026-10-29. It turns a question asked without data into an input folder built from official public data, for Lamuir to solve. This is the part of the solution that makes a runtime call to the Tavily API.

```bash
python source-finder/source_finder.py "How many days was the U.S. Treasury yield curve inverted in 2022-2025?" --out /tmp/lamuir-task
```

## Steps

The agent itself never goes online.

1. **Search (Tavily).** Tavily web search runs with `include_domains` set to official sites: treasury.gov, ecb.europa.eu and sec.gov. Results from any other host are dropped again locally, because `include_domains` is only a request to the provider.
2. **Plan (Nemotron on Nebius Token Factory).** The model maps the question and the search results to one registered source and its parameters, as strict JSON. The plan is validated: only registered sources, years in range, ISO currency codes, at most 5 tickers. Anything else is refused with a reason.
3. **Download.** The adapter for that source builds the URL from the validated parameters, on that source's own official endpoint. A URL found in a search result is never downloaded. `fetch` also refuses any host outside the allowlist.
4. **Record.** `sources.json` holds the question, the Tavily results, the plan, and for every file its URL, UTC download time and SHA-256. `instruction.md` is the question plus a description of the files, ready for the agent. The agent then runs in its sandbox without network, as usual.

## Registered sources

| Key | Source | Parameters |
|---|---|---|
| `treasury_par_yield` | U.S. Treasury Daily Par Yield Curve Rates | years |
| `ecb_fx_reference` | ECB euro foreign exchange reference rates | currencies, start, end |
| `sec_companyfacts` | SEC EDGAR XBRL company facts | tickers |

## Keys

Keys are read from the environment only:
- `TAVILY_API_KEY`;
- `MODEL_API_KEY` (or `NEBIUS_API_KEY`), with an optional `MODEL_ENDPOINT`;
- `DEMO_DATA_CONTACT_EMAIL`, which SEC's fair-access policy requires in the User-Agent.

Keys are passed to `curl` through a config on stdin, so they never appear in the process list or in logs. The offline test checks this.

## Tests

`python -B source-finder/test_source_finder.py` runs 17 offline checks. Tavily, the model and the downloads are replaced by fakes, so no network and no key is needed. The checks cover:
- validation and refusals;
- dropping non-official and look-alike hosts;
- refusing a non-official download;
- parsing the model's reply;
- the files written;
- keys staying off the command line.

## Limitations

- **Instructions:** the generated `instruction.md` describes the files but not a method, so the agent decides the method from the question. For recorded demos, a reviewed task statement is still preferable.
