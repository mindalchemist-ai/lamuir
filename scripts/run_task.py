#!/usr/bin/env python3
"""Run Lamuir on a task of your own: a folder with instruction.md and, optionally, data/ (or environment/data/).

The model is NVIDIA Nemotron 3 Super 120B called through Nebius Token Factory. The agent sees only the statement and
the data. Unless the statement already asks for explanation.md or limits the output files, one sentence is added at
its end asking for a short explanation, so every run ends with a plain-English summary of its own results.

Example:
    export NEBIUS_API_KEY=...
    python scripts/run_task.py my-task/            # my-task/instruction.md, my-task/data/*.csv
Outputs and the full trajectory go to runs/<run>/task/.
"""
import argparse
import datetime
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import run_demo  # noqa: E402  (shared image build and model settings)

EXPLAIN = ("\n\nAlso write `/app/output/explanation.md`: a short plain-English summary of what you computed and what the "
           "results mean, using the values you computed, and the main limits of the analysis.\n")
# a statement that names its only deliverables is left as written
LIMITS_OUTPUT = re.compile(r"\b(only|exactly|no other|nothing else)\b[^.\n]{0,60}\b(file|files|output|outputs)\b|"
                           r"\b(write|create|produce)\s+only\b", re.I)


def with_explanation(statement):
    if "explanation.md" in statement or LIMITS_OUTPUT.search(statement):
        return statement, False
    return statement.rstrip() + EXPLAIN, True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task", type=pathlib.Path, help="folder with instruction.md and optional data/")
    ap.add_argument("--time-limit", type=float, default=900.0, help="seconds")
    ap.add_argument("--run-name", default=None)
    ap.add_argument("--runs-dir", type=pathlib.Path, default=REPO / "runs")
    a = ap.parse_args()
    key = os.environ.get("NEBIUS_API_KEY", "").strip()
    if not key:
        sys.exit("set NEBIUS_API_KEY (a Nebius Token Factory key)")
    src = a.task.resolve()
    if not (src / "instruction.md").is_file():
        sys.exit(f"{src} has no instruction.md")
    run_dir = a.runs_dir / (a.run_name or f"task-{datetime.datetime.now():%Y%m%d-%H%M%S}")
    work = run_dir / "task"
    stage = work / "input"
    data = next((d for d in (src / "environment" / "data", src / "data") if d.is_dir()), None)
    (stage / "environment" / "data").mkdir(parents=True, exist_ok=True)
    if data:
        shutil.copytree(data, stage / "environment" / "data", dirs_exist_ok=True)
    statement, added = with_explanation((src / "instruction.md").read_text())
    (stage / "instruction.md").write_text(statement)
    (stage / "card.toml").write_text(f"[agent]\ntimeout_sec = {a.time_limit}\nmax_requests = 0\n")
    files = sorted(p.name for p in (stage / "environment" / "data").iterdir() if p.is_file())
    (stage / "environment" / "Dockerfile").write_text("FROM lamuir-sandbox:latest\nWORKDIR /app\nRUN mkdir -p /app/data /app/output\n"
                                                      + "".join(f"COPY data/{f} /app/data/{f}\n" for f in files))
    out, trace = work / "output", work / "trace"
    for d in (out, trace):
        d.mkdir(parents=True, exist_ok=True)
        d.chmod(0o777)
    env_file = run_dir / ".env"
    env_file.write_text(f"MODEL_ENDPOINT={run_demo.ENDPOINT}\nMODEL_NAME={run_demo.MODEL}\nMODEL_API_KEY={key}\n")
    env_file.chmod(0o600)
    print(f"Lamuir · NVIDIA Nemotron 3 Super 120B on Nebius Token Factory · explanation request "
          f"{'added' if added else 'not added (the statement covers its outputs)'}", flush=True)
    try:
        run_demo.build("lamuir-sandbox:latest", REPO / "docker" / "sandbox.Dockerfile", REPO / "docker", log=run_dir / "sandbox-build.log")
        agent_image = "lamuir-agent:latest"
        run_demo.build(agent_image, REPO / "docker" / "qfbench-agent.Dockerfile", REPO,
                       {"BASE": "lamuir-sandbox:latest"}, log=run_dir / "agent-build.log")
        (work / "Dockerfile").write_text((stage / "environment" / "Dockerfile").read_text().replace("lamuir-sandbox:latest", agent_image, 1))
        image = f"lamuir-task:{run_dir.name}"[:128].lower()
        run_demo.build(image, work / "Dockerfile", stage / "environment", log=work / "image-build.log")
        name = f"lamuir-{run_dir.name}"[:120]
        cmd = ["docker", "run", "--rm", "--name", name, "--env-file", str(env_file), "-e", "OUTPUT_DIR=/app/output",
               "-v", f"{stage / 'instruction.md'}:/input/instruction.md:ro", "-v", f"{stage / 'environment'}:/input/environment:ro",
               "-v", f"{stage / 'card.toml'}:/input/card.toml:ro", "-v", f"{out}:/app/output", "-v", f"{trace}:/tmp/trace",
               "--entrypoint", "python", image, "/opt/solve.py", "solve", "--task-dir", "/input", "--out", "/app/output"]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=a.time_limit + 120)
            (work / "agent.log").write_text(p.stdout + p.stderr)
        except subprocess.TimeoutExpired:
            subprocess.run(["docker", "rm", "-f", name], capture_output=True)
    finally:
        env_file.unlink(missing_ok=True)
    written = sorted(p.name for p in out.iterdir() if p.is_file())
    (work / "result.json").write_text(json.dumps({"explanation_request_added": added, "outputs": written,
                                                  "requests": run_demo.requests_in(trace)}, indent=2))
    print("outputs:", ", ".join(written) or "none")
    print(f"run folder: {work}")


if __name__ == "__main__":
    main()
