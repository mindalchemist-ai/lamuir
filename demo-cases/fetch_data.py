"""Download the public source files for the demo cases and build each case's input folder.

Usage: python demo-cases/fetch_data.py [--build-only]
Raw downloads go to demo-cases/_raw/<source>/ with a provenance.json (URL, time, SHA-256). Each case's
environment/data/ is then built from those raw files by selection and format conversion only: choosing
fields and date ranges. No row is cleaned, deduplicated,
filled or sorted here; that is the agent's job.
"""
import argparse
import datetime as dt
import hashlib
import json
import pathlib
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parent
RAW = ROOT / "_raw"
TREASURY = ("https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/"
            "{y}/all?type=daily_treasury_yield_curve&field_tdr_date_value={y}&page&_format=csv")
ECB_EURUSD = ("https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A"
              "?startPeriod=2015-01-01&endPeriod=2025-12-31&format=csvdata")
ECB = ("https://data-api.ecb.europa.eu/service/data/EXR/D.USD+GBP+JPY+CHF.EUR.SP00.A"
       "?startPeriod=2025-01-01&endPeriod=2025-12-31&format=csvdata")



def user_agent():
    return "MindAlchemist Lamuir demo data"


def download(url, path, provenance):
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["curl", "-sSf", "-A", user_agent(), "-o", str(path), url], check=True)
    provenance.append({"file": path.name, "url": url, "downloaded_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                       "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size})
    time.sleep(0.5)


def fetch():
    for name, jobs in {
        "treasury": [(TREASURY.format(y=y), f"par_yield_{y}.csv") for y in (2022, 2023, 2024, 2025)],
        "ecb": [(ECB, "ecb_exr_2025.csv"), (ECB_EURUSD, "ecb_eurusd_2015_2025.csv")],
    }.items():
        provenance = []
        for url, fname in jobs:
            download(url, RAW / name / fname, provenance)
        (RAW / name / "provenance.json").write_text(json.dumps(provenance, indent=1))


def data_dir(case):
    d = ROOT / case / "environment" / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d


def build():
    # yield-curve-inversion. Treasury: the four yearly files as published (their tenor columns differ by year, so they are not merged).
    for y in (2022, 2023, 2024, 2025):
        (data_dir("yield-curve-inversion") / f"treasury_par_yield_curve_{y}.csv").write_bytes(
            (RAW / "treasury" / f"par_yield_{y}.csv").read_bytes())
    # bond-rate-sensitivity uses the 2024 Treasury file, as published.
    (data_dir("bond-rate-sensitivity") / "treasury_par_yield_curve_2024.csv").write_bytes(
        (RAW / "treasury" / "par_yield_2024.csv").read_bytes())
    # eurusd-sma-costs and eurusd-ewma-volatility. ECB EUR/USD reference rate: the CSV as delivered by the ECB data API.
    for case in ("eurusd-sma-costs", "eurusd-ewma-volatility"):
        (data_dir(case) / "ecb_eurusd_2015_2025.csv").write_bytes((RAW / "ecb" / "ecb_eurusd_2015_2025.csv").read_bytes())
    # usd-cross-rates. ECB: the CSV as delivered by the ECB data API.
    (data_dir("usd-cross-rates") / "ecb_reference_rates_2025.csv").write_bytes((RAW / "ecb" / "ecb_exr_2025.csv").read_bytes())



if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--build-only", action="store_true")
    if not ap.parse_args().build_only:
        fetch()
    build()
