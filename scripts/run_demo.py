#!/usr/bin/env python3
"""Run Lamuir on the demo cases and grade each result against its independent reference.

The model is NVIDIA Nemotron 3 Super 120B called through Nebius Token Factory. For each case this script builds the
case image from demo-cases/<case>/environment on the Lamuir sandbox plus the agent layer, runs the agent with only
the task statement and the input data visible, then grades the outputs with demo-cases/_reference/grade.py.

Example:
    export NEBIUS_API_KEY=...
    python scripts/run_demo.py --cases yield-curve-inversion
"""
import argparse
import concurrent.futures
import datetime
import json
import os
import pathlib
import re
import subprocess
import sys
import time

REPO = pathlib.Path(__file__).resolve().parents[1]
CASES = REPO / "demo-cases"
MODEL = os.environ.get("NEBIUS_MODEL", "nvidia/nemotron-3-super-120b-a12b")  # any NVIDIA Nemotron model id on Nebius Token Factory
ENDPOINT = "https://api.studio.nebius.com"


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def build(tag, dockerfile, context, args=None, log=None):
    cmd = ["docker", "build", "-t", tag, "-f", str(dockerfile)]
    for k, v in (args or {}).items():
        cmd += ["--build-arg", f"{k}={v}"]
    p = run(cmd + [str(context)])
    if log:
        log.write_text(p.stdout + p.stderr)
    if p.returncode:
        sys.exit(f"docker build failed for {tag}; see {log}")


def requests_in(trace):
    for f in trace.rglob("*.traj.json"):
        try:
            return sum(1 for m in json.loads(f.read_text()).get("messages", []) if m.get("role") == "assistant")
        except (OSError, ValueError):
            pass
    return None


def run_case(case, agent_image, run_dir, env_file):
    src, work = CASES / case, run_dir / case
    out, trace = work / "output", work / "trace"
    for d in (out, trace):
        d.mkdir(parents=True, exist_ok=True)
        d.chmod(0o777)
    dockerfile = re.sub(r"^\s*FROM\s+\S+", f"FROM {agent_image}", (src / "environment" / "Dockerfile").read_text(), count=1, flags=re.M)
    (work / "Dockerfile").write_text(dockerfile)
    image = f"lamuir-case:{case}-{run_dir.name}"[:128].lower()
    build(image, work / "Dockerfile", src / "environment", log=work / "image-build.log")
    t0 = time.time()
    name = f"lamuir-{run_dir.name}-{case}"[:120]
    agent = ["docker", "run", "--rm", "--name", name, "--env-file", str(env_file),
             "-e", "OUTPUT_DIR=/app/output",
             "-v", f"{src / 'instruction.md'}:/input/instruction.md:ro",
             "-v", f"{src / 'environment'}:/input/environment:ro",
             "-v", f"{src / 'card.toml'}:/input/card.toml:ro",
             "-v", f"{out}:/app/output", "-v", f"{trace}:/tmp/trace",
             "--entrypoint", "python", image, "/opt/solve.py", "solve", "--task-dir", "/input", "--out", "/app/output"]
    limit = 900 + 120
    try:
        p = run(agent, timeout=limit)
        (work / "agent.log").write_text(p.stdout + p.stderr)
        exit_code = p.returncode
    except subprocess.TimeoutExpired as e:
        run(["docker", "rm", "-f", name])
        (work / "agent.log").write_text(str(e.stdout or "") + str(e.stderr or ""))
        exit_code = "timeout"
    g = run([sys.executable, str(CASES / "_reference" / "grade.py"), case, str(out)])
    (work / "grader.log").write_text(g.stdout + g.stderr)
    result = {"case": case, "passed": g.returncode == 0, "agent_exit": exit_code, "seconds": round(time.time() - t0, 1),
              "requests": requests_in(trace), "model": MODEL, "provider": "Nebius Token Factory"}
    (work / "result.json").write_text(json.dumps(result, indent=2))
    print(f"{'PASS' if result['passed'] else 'FAIL'} {case}  requests {result['requests']}  seconds {result['seconds']}", flush=True)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default="all", help="comma-separated case names, or 'all'")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--run-name", default=None)
    ap.add_argument("--runs-dir", type=pathlib.Path, default=REPO / "runs")
    args = ap.parse_args()
    key = os.environ.get("NEBIUS_API_KEY", "").strip()
    if not key:
        sys.exit("set NEBIUS_API_KEY (a Nebius Token Factory key)")
    cases = sorted(d.name for d in CASES.iterdir() if (d / "instruction.md").is_file()) if args.cases == "all" else args.cases.split(",")
    run_dir = args.runs_dir / (args.run_name or f"demo-{datetime.datetime.now():%Y%m%d-%H%M%S}")
    run_dir.mkdir(parents=True, exist_ok=True)
    env_file = run_dir / ".env"
    env_file.write_text(f"MODEL_ENDPOINT={ENDPOINT}\nMODEL_NAME={MODEL}\nMODEL_API_KEY={key}\n")
    env_file.chmod(0o600)
    print(f"Lamuir · {MODEL} on Nebius Token Factory · {len(cases)} case(s)", flush=True)
    try:
        build("lamuir-sandbox:latest", REPO / "docker" / "sandbox.Dockerfile", REPO / "docker", log=run_dir / "sandbox-build.log")
        agent_image = "lamuir-agent:latest"
        build(agent_image, REPO / "docker" / "qfbench-agent.Dockerfile", REPO,
              {"BASE": "lamuir-sandbox:latest"}, log=run_dir / "agent-build.log")
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            results = list(pool.map(lambda c: run_case(c, agent_image, run_dir, env_file), cases))
    finally:
        env_file.unlink(missing_ok=True)
    (run_dir / "results.json").write_text(json.dumps({"model": MODEL, "results": results}, indent=2))
    print(f"passed {sum(r['passed'] for r in results)} / {len(results)}  ({run_dir})")


if __name__ == "__main__":
    main()
