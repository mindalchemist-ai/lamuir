# Lamuir

Lamuir is an AI coding agent for quantitative finance. Given a question in plain English and the relevant data, or a request to retrieve it from official sources, Lamuir profiles the data, writes and executes Python in a sandbox, validates the results against financial identities and the requested output format, and corrects the errors it detects. It delivers the code, result files, tables, plots and a short written explanation.

Lamuir runs on **NVIDIA Nemotron 3 Super 120B** (`nvidia/nemotron-3-super-120b-a12b`), an open-weight model with 120B total and 12B active parameters, served on **Nebius Token Factory**. It uses **Tavily** to locate official data sources.

On [QF-Bench](https://github.com/QF-Bench/QuantitativeFinance-Bench), a public quantitative finance coding benchmark, Lamuir reaches **75.6% pass@1** (65 of 86 tasks, one run each). For reference, the top entry on the [official QF-Bench leaderboard](https://qfbench.com/) is 61.7% (GPT-5.5 with Codex CLI). QF-Bench was our development benchmark; we also tested Lamuir on a separate set of held-out questions (see [Demo cases](#demo-cases)).

To make its analysis and code more reliable, Lamuir provides the model with structured finance knowledge, algorithmic guidance, and API references that match the installed library versions. It is designed to be extended: new data sources can be registered with the source finder, new methods and conventions added to the knowledge cards, and references added for new versions of pandas, NumPy, SciPy, arch and other quantitative finance libraries.

### Powered by NVIDIA Nemotron, Nebius Token Factory and Tavily

| | Role in Lamuir | What you need |
|---|---|---|
| **NVIDIA Nemotron** | Performs all reasoning and writes all code. Default: **Nemotron 3 Super 120B**; any Nemotron model on Token Factory can be selected with `NEBIUS_MODEL` | Nothing extra: Nemotron is served by Nebius Token Factory |
| **Nebius Token Factory** | Serves Nemotron through an OpenAI-compatible API (`https://api.studio.nebius.com/v1`) | An API key from [tokenfactory.nebius.com](https://tokenfactory.nebius.com/), set as `NEBIUS_API_KEY` |
| **Tavily** | Web search restricted to official data sites, used by the source finder to locate the data for a question | An API key from [app.tavily.com](https://app.tavily.com/), set as `TAVILY_API_KEY` |

## How Lamuir uses Nemotron and Nebius Token Factory

- **Reasoning and code.** All reasoning and generated code come from Nemotron 3 Super through the Token Factory OpenAI-compatible endpoint, at temperature 0 with reasoning enabled. A typical question takes 5–40 model requests.
- **Model choice.** Another Nemotron model on Token Factory can be selected with `NEBIUS_MODEL` (see [Choosing a Nemotron model](#run-lamuir-yourself)). We compared three NVIDIA models with the same agent on 20 benchmark tasks (one run each); Nemotron 3 Super solved the most, 16 of 20.
- **Data source selection.** In the source finder, Nemotron reads the question together with the web-search results and selects one registered official data source, returning strict JSON.
- **Provenance.** Every result file records the model and provider used.

## Architecture

```text
               Question
                  |
                  v
  +------------------------------+
  |        Source finder         |
  |                              |
  |    Tavily: official sites    |
  |    Nemotron: pick source     |
  |      Download + SHA-256      |
  +------------------------------+
                  |
                  v
           Question + data
                  |
                  v
  +------------------------------+
  |    Lamuir agent (Docker)     |
  |                              |
  |       1. Data profile        |
  |      2. Knowledge cards      |      +--------------------+
  |    3. Output requirements    |      |  Nemotron 3 Super  |
  |     4. Run Python cells <-+  |<---->|    Nebius Token    |
  |               |           |  |      |      Factory       |
  |               v violation |  |      +--------------------+
  |       5. Result checks ---+  |
  |               |              |
  |               | pass         |
  +---------------|--------------+
                  v
        Code, results, plots,
       explanation, run log
```

## How it works

Lamuir takes a question in plain English, which may also specify the expected output, and the data needed to answer it. If no data is provided, the [source finder](#source-finder) first retrieves it from official public sources. The agent then works in five steps:

1. **Data profile.** Before the first model request, Lamuir reads up to eight CSV, TSV and parquet files in full and reports facts only: row counts, duplicated rows, missing or non-numeric cells, extreme values, date ranges and duplicate dates. How to handle them is left to the question.
2. **Finance, algorithm and coding knowledge cards.** More than 200 reference cards cover financial methods, market conventions and library APIs. They are indexed as 948 retrievable chunks, and the cards relevant to the question are added to the model's context through retrieval-augmented generation (RAG): method and convention cards are matched to the question's terms, library reference cards are ranked with BM25, and a second retrieval pass adds library usage notes, prioritizing the functions named in the question and the selected cards, within a fixed context budget. Each method card describes the method's purpose, when to use it, how to implement it, its limitations, and a computable cross-check. Library references are adapted to the versions installed in the sandbox, and references to libraries that are not installed are left out. In addition, 45 API cards contain the official docstrings of the installed pandas, NumPy, SciPy and arch functions (signature, summary and parameters, unmodified); they are attached together with the method cards that use those functions.
3. **Output requirements.** Lamuir reads the expected output from the question: files, keys and columns, units, date formats, decimal places, and any examples given. Helper functions write files that follow these requirements. Where the question does not specify a format, documented defaults apply.
4. **Execution.** The model writes and executes Python one cell at a time in a persistent sandboxed session and inspects every result. When a call fails with a known library-version error, such as an argument removed in the installed pandas, a one-line note with the correct usage is appended to the error message (62 rules).
5. **Result checks.** Before results are accepted, Lamuir verifies:
   - that all required files and fields are present;
   - that the output format matches the specification: date format, decimal versus percent scale, integer keys, numbers inside keys;
   - that values satisfy financial invariants: non-negative option values, probabilities within [0, 1], non-negative volatilities and integer counts.

   A definite violation is returned to the model with the field and value, and must be fixed before the run completes.

### Source finder

`source-finder/` builds a dataset from official public data for a question that comes without data:

1. **Search.** Tavily web search, restricted to official domains: treasury.gov, ecb.europa.eu and sec.gov.
2. **Plan.** Nemotron selects one registered source and its parameters, and the plan is validated.
3. **Download.** The source's own adapter downloads the data from its official endpoint.
4. **Record.** Every file is recorded with its URL, download time and SHA-256 hash.

The agent itself has no web-browsing tool; data reaches it only through the files you provide or through the source finder.

## Run Lamuir yourself

Lamuir runs on your own machine. It requires Docker, Python 3.11 or later and a Nebius Token Factory API key; the source finder also requires a Tavily API key.

**1. Get API keys**

- **Nebius Token Factory:** sign in at [Nebius Token Factory](https://tokenfactory.nebius.com/) and create an API key. Lamuir calls the OpenAI-compatible endpoint `https://api.studio.nebius.com/v1` with the model `nvidia/nemotron-3-super-120b-a12b` (NVIDIA Nemotron 3 Super 120B).
- **Tavily** (source finder only): sign in at [app.tavily.com](https://app.tavily.com/) and copy the API key (it starts with `tvly-`).

**2. Set the keys** (they are read from environment variables and never written to files in the repository)

```bash
git clone https://github.com/mindalchemist-ai/lamuir.git && cd lamuir
export NEBIUS_API_KEY=...          # Nebius Token Factory key
export TAVILY_API_KEY=tvly-...     # source finder only
```

**Choosing a Nemotron model.** Lamuir uses NVIDIA Nemotron 3 Super 120B by default; all results in this README were measured with it. To use another NVIDIA Nemotron model served on Nebius Token Factory, set its model ID as shown in the Token Factory model list:

```bash
export NEBIUS_MODEL=nvidia/nemotron-3-super-120b-a12b   # default; replace with another Nemotron model ID
```

`NEBIUS_MODEL` applies to `scripts/run_demo.py`, `scripts/run_task.py`, `scripts/run_qfbench.py` (also `--model`) and the source finder.

**3. Run a demo case**

```bash
python scripts/run_demo.py --cases yield-curve-inversion
```

The script builds the Docker images (cached after the first build). The agent sees only the question and its data, and its results are compared with the case's independent reference solution. Results and the full run log are written to `runs/<run>/<case>/`. Use `--cases all` to run all six cases.

**4. Analyze your own question**

Create a folder with the question in `instruction.md` and any data files in `data/`, then run:

```bash
python scripts/run_task.py my-question/
```

Unless the question already asks for `explanation.md` or limits the output files, Lamuir asks the model for a short written summary of the results, so every run ends with an explanation based on the computed values.

**5. Retrieve official data automatically (Nebius + Nemotron + Tavily)**

```bash
python source-finder/source_finder.py "How many days was the U.S. Treasury yield curve inverted in 2022-2025?" --out my-question
python scripts/run_task.py my-question/
```

The first command searches official sites with Tavily, uses Nemotron to select a registered source, and downloads the data from its official endpoint; `my-question/sources.json` records each file's URL, download time and SHA-256 hash. The second command answers the question with that data.

## Demo cases

Six questions on public data, written for Lamuir and independent of QF-Bench. Each case includes the question, a fixed snapshot of the input data, an independent reference solution and a grader; see `demo-cases/README.md`.

| Case | Question |
|---|---|
| yield-curve-inversion | How many days was the 10-year minus 2-year U.S. Treasury yield spread negative in 2022–2025? |
| bond-rate-sensitivity | How much would a 10-year, 4%-coupon bond's price fall if its yield rose 100 bp from the end-2024 10-year Treasury yield? |
| jump-option-prices | How do Merton jump-diffusion option prices differ from Black-Scholes prices with the same total variance? |
| eurusd-sma-costs | Does a 50/200-day moving-average crossover on EUR/USD beat buy-and-hold after 2 bp trading costs, 2015–2025? |
| eurusd-ewma-volatility | How do EWMA (λ = 0.94) and 60-day rolling volatility estimates of EUR/USD compare over 2015–2025? |
| usd-cross-rates | What was the 2025 percent change of the euro, pound, yen and Swiss franc against the U.S. dollar? |

All six can be replayed on the [project page](https://mindalchemist-ai.github.io/lamuir-demo/), where each question is answered with the values the run produced: its metrics, chart and result files. Every case matched its reference solution in each of its recorded runs.

## Evaluation on QF-Bench

We evaluated Lamuir on the 86 public tasks of [QF-Bench](https://github.com/QF-Bench/QuantitativeFinance-Bench). Each task is graded by its own unmodified tests. QF-Bench is licensed under CC BY-NC 4.0, and none of its content is included in this repository.

Lamuir solved **65 of the 86 tasks (75.6%)**, with one run per task. Across all tasks it passed 93.7% of the individual tests in the tasks' graders; most remaining failures were small details such as units, formats or key names, rather than wrong methods.

To reproduce it, clone QF-Bench and run all tasks:

```bash
git clone https://github.com/QF-Bench/QuantitativeFinance-Bench.git ../QuantitativeFinance-Bench
python scripts/run_qfbench.py --qfbench ../QuantitativeFinance-Bench --tasks all
```

## Repository layout

| Path | Contents |
|---|---|
| `agent/` | The agent. The entry point is `solve.py`; the main module is `solver_agent.py`; `mini_driver.py` handles model requests. `qfref/` contains the knowledge cards and checks, and `msw_session/` the session helpers |
| `docker/` | Sandbox image and agent layer |
| `scripts/run_demo.py` | Runs and checks the demo cases |
| `scripts/run_task.py` | Runs Lamuir on your own question |
| `scripts/run_qfbench.py` | Runs and grades QF-Bench tasks (requires a separate QF-Bench copy) |
| `source-finder/` | Tavily-based source finder |
| `demo-cases/` | The six demo cases, with the data download script, reference solutions and grader |

## Known limitations

- **Run-to-run variation.** Model outputs at temperature 0 are not fully deterministic, so a question may be answered correctly in one run and not in another. All reported pass rates are from single runs.
- **No web browsing.** By design, the agent runs without internet access. It receives data only through the files you provide or through the source finder, which uses Tavily search to locate official data and downloads it before the agent starts.
- **Not investment advice.** Lamuir is a coding and analysis tool.

## License

Apache License 2.0; see `LICENSE`.
