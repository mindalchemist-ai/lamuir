#!/usr/bin/env python3
"""Run the verified quant agent on QF-Bench tasks and grade each one with QF-Bench's own tests.

The agent's model is an NVIDIA Nemotron model called through Nebius Token Factory. For every task
this script builds the task image from the task's own environment/Dockerfile on top of the agent
layer, runs the agent with only the task statement and environment visible, then runs the task's
official tests/test.sh against the written outputs and reads the reward it records.

Example:
    export NEBIUS_API_KEY=...
    python scripts/run_qfbench.py --qfbench ~/QuantitativeFinance-Bench --tasks <task-name> --jobs 4
"""
import argparse
import concurrent.futures
import contextlib
import glob
import datetime
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import threading
import time
import tomllib

REPO = pathlib.Path(__file__).resolve().parents[1]
PROVIDER = "Nebius Token Factory"
DEFAULT_ENDPOINT = "https://api.studio.nebius.com"
DEFAULT_MODEL = "nvidia/nemotron-3-super-120b-a12b"
MODEL_LABELS = {
    "nvidia/nemotron-3-super-120b-a12b": "NVIDIA Nemotron 3 Super 120B",
    "nvidia/Nemotron-3_5-Lightning": "NVIDIA Nemotron 3.5 Lightning",
    "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B": "NVIDIA Nemotron 3 Nano 30B",
    "nvidia/Nemotron-3-Ultra-550b-a55b": "NVIDIA Nemotron 3 Ultra 550B",
}
SANDBOX_NAMES = ("finance-bench-sandbox:latest", "quantitative-finance-bench-sandbox:latest")
PRINT_LOCK = threading.Lock()


def log(msg):
    with PRINT_LOCK:
        print(f"[{datetime.datetime.now():%H:%M:%S}] {msg}", flush=True)


def banner(args):
    label = MODEL_LABELS.get(args.model, args.model)
    host = re.sub(r"^https?://", "", args.endpoint).split("/")[0]
    lines = [f"Model    : {label} ({args.model})",
             f"Provider : {PROVIDER} ({host})",
             f"Agent    : Lamuir",
             f"Benchmark: QF-Bench, graded by each task's own tests/test.sh"]
    width = max(len(x) for x in lines)
    print("=" * (width + 4))
    for line in lines:
        print(f"| {line.ljust(width)} |")
    print("=" * (width + 4), flush=True)


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def build(tag, dockerfile, context, build_args=None, log_path=None):
    cmd = ["docker", "build", "-t", tag, "-f", str(dockerfile)]
    for k, v in (build_args or {}).items():
        cmd += ["--build-arg", f"{k}={v}"]
    p = run(cmd + [str(context)])
    if log_path:
        pathlib.Path(log_path).write_text(p.stdout + p.stderr)
    if p.returncode != 0:
        raise RuntimeError(f"docker build {tag} failed:\n{p.stderr[-2000:]}")


def list_tasks(qfbench, wanted, excluded):
    tasks = sorted(d.name for d in (qfbench / "tasks").iterdir() if (d / "instruction.md").is_file())
    if wanted and wanted != "all":
        names = [t.strip() for t in wanted.split(",") if t.strip()]
        missing = [t for t in names if t not in tasks]
        if missing:
            sys.exit(f"unknown task(s): {', '.join(missing)}")
        tasks = names
    tasks = [t for t in tasks if t not in set(excluded)]
    # Longest tasks first (by their longest earlier run), so slow tasks do not start last and stretch the run.
    seconds = {}
    for f in glob.glob(str(REPO / "runs" / "*" / "*" / "result.json")):
        with contextlib.suppress(Exception):
            r = json.load(open(f))
            t = pathlib.Path(f).parent.name
            seconds[t] = max(seconds.get(t, 0), float(r.get("seconds") or 0))
    return sorted(tasks, key=lambda t: -seconds.get(t, 0))


def task_settings(task_dir):
    cfg = tomllib.loads((task_dir / "task.toml").read_text())
    agent = cfg.get("agent", {})
    env = cfg.get("environment", {})
    verifier = cfg.get("verifier", {})
    return {"agent_timeout": float(agent.get("timeout_sec", 1800)),
            "verifier_timeout": float(verifier.get("timeout_sec", 600)),
            "cpus": env.get("cpus"), "memory": env.get("memory")}


def task_image(task, task_dir, agent_image, run_dir):
    # The task's own Dockerfile, with its sandbox base replaced by the agent layer.
    src = (task_dir / "environment" / "Dockerfile").read_text()
    lines = []
    for line in src.splitlines():
        m = re.match(r"\s*FROM\s+(\S+)(.*)$", line, re.I)
        # some tasks pin the sandbox by digest (name:tag@sha256:...); the name before the digest decides
        if m and m.group(1).split("@")[0] in SANDBOX_NAMES:
            line = f"FROM {agent_image}{m.group(2)}"
        lines.append(line)
    dockerfile = run_dir / task / "task.Dockerfile"
    dockerfile.write_text("\n".join(lines) + "\n")
    tag = f"lamuir-task-{task}:{agent_image.split(':')[-1]}"
    build(tag, dockerfile, task_dir / "environment", log_path=run_dir / task / "build.log")
    return tag


def count_requests(trace_dir):
    traj = trace_dir / "mini.traj.json"
    if not traj.is_file():
        return None
    try:
        msgs = json.loads(traj.read_text()).get("messages", [])
    except (OSError, ValueError):
        return None
    return sum(1 for m in msgs if m.get("role") == "assistant")


def grade_counts(logs_dir):
    ctrf = logs_dir / "ctrf.json"
    if ctrf.is_file():
        try:
            summary = json.loads(ctrf.read_text())["results"]["summary"]
            return summary.get("passed"), summary.get("tests")
        except (OSError, ValueError, KeyError):
            pass
    # tasks whose test.sh runs test_outputs.py as a script print one PASS/FAIL line per check
    log = logs_dir.parent / "grader.log"
    if log.is_file():
        lines = log.read_text(errors="ignore").splitlines()
        passed = sum(1 for l in lines if l.startswith("PASS "))
        failed = sum(1 for l in lines if l.startswith("FAIL "))
        if passed + failed:
            return passed, passed + failed
    return None, None


def apply_reward(result, logs_dir):
    # test.sh writes 1/0; tasks graded by verifier.py write the fraction of checks passed (e.g. 1.0, 0.5833).
    # A task passes only with a reward of exactly 1.
    reward_file = logs_dir / "reward.txt"
    raw = reward_file.read_text().strip() if reward_file.is_file() else ""
    try:
        value = float(raw)
    except ValueError:
        value = None
    result["reward"] = value
    result["passed"] = value is not None and value >= 1.0 - 1e-9  # some verifiers score a perfect result above 1 (1.033333)
    result["tests_passed"], result["tests_total"] = grade_counts(logs_dir)


def regrade(run_dir, args):
    # Re-read every task's reward without rerunning anything, then rewrite the summaries.
    results = []
    for f in sorted(run_dir.glob("*/result.json")):
        r = json.loads(f.read_text())
        if not r.get("error"):
            apply_reward(r, f.parent / "verifier")
        f.write_text(json.dumps(r, indent=2))
        results.append(r)
    meta = json.loads((run_dir / "results.json").read_text())["run"] if (run_dir / "results.json").is_file() else {}
    passed = write_summary(run_dir, args, results, meta)
    print(f"regraded {len(results)} tasks in {run_dir.name}: passed {passed}")


def stop(name):
    run(["docker", "rm", "-f", name])


def run_task(task, args, agent_image, run_dir, env_file):
    task_dir = args.qfbench / "tasks" / task
    work = run_dir / task
    out, trace, logs = work / "output", work / "trace", work / "verifier"
    for d in (out, trace, logs):
        d.mkdir(parents=True, exist_ok=True)
        d.chmod(0o777)
    s = task_settings(task_dir)
    if args.time_limit:
        s["agent_timeout"] = args.time_limit
    card = work / "card.toml"
    # QF-Bench sets a time limit per task and no request limit; max_requests = 0 says so to the agent.
    card.write_text(f"[agent]\ntimeout_sec = {s['agent_timeout']}\nmax_requests = 0\n")
    result = {"task": task, "model": args.model, "provider": PROVIDER}
    t0 = time.time()
    try:
        image = task_image(task, task_dir, agent_image, run_dir)
        res = []
        if s["cpus"]:
            res += ["--cpus", str(s["cpus"])]
        if s["memory"]:
            res += ["--memory", str(s["memory"]).replace("G", "g")]
        name = f"lamuir-{run_dir.name}-{task}"[:120]
        # Only the statement and the environment are visible to the agent: tests/ and solution/ stay out.
        agent_cmd = ["docker", "run", "--rm", "--name", name, *res, "--env-file", str(env_file),
                     "-e", "OUTPUT_DIR=/app/output",
                     "-v", f"{task_dir / 'instruction.md'}:/input/instruction.md:ro",
                     "-v", f"{task_dir / 'environment'}:/input/environment:ro",
                     "-v", f"{card}:/input/card.toml:ro",
                     # Some tasks default OUTPUT_DIR to /output, most to /app/output: both are the same folder.
                     "-v", f"{out}:/app/output", "-v", f"{out}:/output", "-v", f"{trace}:/tmp/trace",
                     "--entrypoint", "python", image, "/opt/solve.py", "solve",
                     "--task-dir", "/input", "--out", "/app/output"]
        log(f"start {task}")
        try:
            p = run(agent_cmd, timeout=s["agent_timeout"] + args.grace)
            (work / "agent.log").write_text(p.stdout + p.stderr)
            result["agent_exit"] = p.returncode
        except subprocess.TimeoutExpired as e:
            stop(name)
            (work / "agent.log").write_text((e.stdout or "") + (e.stderr or ""))
            result["agent_exit"] = "timeout"
        result["agent_seconds"] = round(time.time() - t0, 1)
        result["requests"] = count_requests(trace)
        # QF-Bench's own verifier, unchanged: it installs its pinned pytest stack, so it needs network.
        grade_cmd = ["docker", "run", "--rm", "--name", f"{name}-grade",
                     "-v", f"{task_dir / 'tests'}:/tests:ro", "-v", f"{out}:/app/output", "-v", f"{out}:/output",
                     "-v", f"{logs}:/logs/verifier", "-v", "qfb-grader-uv-cache:/root/.cache/uv",  # pinned test stack, downloaded once
                     "--entrypoint", "bash", image, "/tests/test.sh"]
        try:
            g = run(grade_cmd, timeout=s["verifier_timeout"] + args.grace)
            (work / "grader.log").write_text(g.stdout + g.stderr)
        except subprocess.TimeoutExpired:
            stop(f"{name}-grade")
        apply_reward(result, logs)
    except Exception as exc:  # noqa: BLE001
        result["passed"] = False
        result["error"] = f"{type(exc).__name__}: {exc}"[:2000]
    result["seconds"] = round(time.time() - t0, 1)
    (work / "result.json").write_text(json.dumps(result, indent=2))
    tests = f"{result.get('tests_passed')}/{result.get('tests_total')}" if result.get("tests_total") else "-"
    log(f"{'PASS' if result['passed'] else 'FAIL'} {task}  tests {tests}  requests {result.get('requests')}  "
        f"{result['seconds']:.0f}s" + (f"  error: {result['error'][:120]}" if result.get("error") else ""))
    return result


def write_summary(run_dir, args, results, meta):
    passed = sum(1 for r in results if r.get("passed"))
    meta.update({"finished": datetime.datetime.now().isoformat(timespec="seconds"),
                 "tasks": len(results), "passed": passed,
                 "pass_rate": round(passed / len(results), 4) if results else None})
    (run_dir / "results.json").write_text(json.dumps({"run": meta, "results": results}, indent=2))
    label = MODEL_LABELS.get(args.model, args.model)
    md = [f"# QF-Bench run `{run_dir.name}`", "",
          f"**Model: {label} (`{args.model}`) on {PROVIDER}.** Agent: Lamuir.", "",
          f"Passed **{passed} / {len(results)}** ({100 * passed / max(len(results), 1):.1f}%), "
          f"graded by each task's own `tests/test.sh`.", "",
          "| Task | Result | Tests | Requests | Seconds |", "|---|---|---|---|---|"]
    for r in sorted(results, key=lambda r: r["task"]):
        tests = f"{r.get('tests_passed')}/{r.get('tests_total')}" if r.get("tests_total") else "-"
        md.append(f"| {r['task']} | {'PASS' if r.get('passed') else 'FAIL'} | {tests} | "
                  f"{r.get('requests') if r.get('requests') is not None else '-'} | {r.get('seconds', '-')} |")
    (run_dir / "summary.md").write_text("\n".join(md) + "\n")
    return passed


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--qfbench", required=True, type=pathlib.Path, help="path to a QuantitativeFinance-Bench checkout")
    ap.add_argument("--tasks", default="all", help="comma-separated task names, or 'all'")
    ap.add_argument("--exclude", default="", help="comma-separated task names to skip")
    ap.add_argument("--model", default=os.environ.get("NEBIUS_MODEL", DEFAULT_MODEL), help="NVIDIA model id on Nebius Token Factory")
    ap.add_argument("--endpoint", default=os.environ.get("NEBIUS_ENDPOINT", DEFAULT_ENDPOINT))
    ap.add_argument("--jobs", type=int, default=4, help="tasks run in parallel")
    ap.add_argument("--time-limit", type=float, default=None, help="override every task's agent time limit (seconds), for testing time-based behaviour only")
    ap.add_argument("--grace", type=int, default=120, help="seconds allowed past a task's time limit before the container is stopped")
    ap.add_argument("--runs-dir", type=pathlib.Path, default=REPO / "runs")
    ap.add_argument("--run-name", default=None)
    ap.add_argument("--regrade", action="store_true", help="only re-read the rewards of the existing run --run-name and rewrite its summary")
    args = ap.parse_args()
    if args.regrade:
        if not args.run_name:
            sys.exit("--regrade needs --run-name")
        regrade((args.runs_dir / args.run_name).resolve(), args)
        return
    args.qfbench = args.qfbench.expanduser().resolve()

    key = os.environ.get("NEBIUS_API_KEY") or os.environ.get("MODEL_API_KEY")
    if not key:
        sys.exit("set NEBIUS_API_KEY to a Nebius Token Factory API key")
    if not (REPO / "agent" / "solve.py").is_file():
        sys.exit("agent/solve.py is missing")
    if not (args.qfbench / "docker" / "sandbox.Dockerfile").is_file():
        sys.exit(f"{args.qfbench} does not look like a QF-Bench checkout")
    tasks = list_tasks(args.qfbench, args.tasks, [t.strip() for t in args.exclude.split(",") if t.strip()])

    banner(args)
    qfb_rev = run(["git", "-C", str(args.qfbench), "rev-parse", "--short", "HEAD"]).stdout.strip() or "unknown"
    name = args.run_name or f"{datetime.datetime.now():%Y%m%d-%H%M%S}-{args.model.split('/')[-1]}"
    run_dir = (args.runs_dir / name).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    for t in tasks:
        (run_dir / t).mkdir(exist_ok=True)

    # The key goes to the containers through an env file readable only by this user, never on a command line.
    secret = run_dir / ".secret"
    secret.mkdir(mode=0o700, exist_ok=True)
    env_file = secret / "model.env"
    env_file.write_text(f"MODEL_ENDPOINT={args.endpoint}\nMODEL_NAME={args.model}\nMODEL_API_KEY={key}\n")
    env_file.chmod(0o600)

    meta = {"benchmark": "QF-Bench", "qfbench_commit": qfb_rev, "agent": "Lamuir", "model": args.model,
            "model_label": MODEL_LABELS.get(args.model, args.model), "model_vendor": "NVIDIA",
            "provider": PROVIDER, "endpoint_host": re.sub(r"^https?://", "", args.endpoint).split("/")[0],
            "jobs": args.jobs, "started": datetime.datetime.now().isoformat(timespec="seconds")}
    results = []
    try:
        sandbox = f"qfbench-sandbox:{qfb_rev}"
        log(f"building QF-Bench sandbox {sandbox}")
        build(sandbox, args.qfbench / "docker" / "sandbox.Dockerfile", args.qfbench, log_path=run_dir / "sandbox-build.log")
        agent_image = f"lamuir-agent:qfbench-{qfb_rev}"
        log(f"building agent layer {agent_image}")
        build(agent_image, REPO / "docker" / "qfbench-agent.Dockerfile", REPO,
              {"BASE": sandbox}, log_path=run_dir / "agent-build.log")
        log(f"running {len(tasks)} task(s), {args.jobs} at a time")
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            futures = [pool.submit(run_task, t, args, agent_image, run_dir, env_file) for t in tasks]
            for f in concurrent.futures.as_completed(futures):
                results.append(f.result())
                write_summary(run_dir, args, results, dict(meta))
    finally:
        shutil.rmtree(secret, ignore_errors=True)
    passed = write_summary(run_dir, args, results, meta)
    print(f"\n{MODEL_LABELS.get(args.model, args.model)} on {PROVIDER}: passed {passed}/{len(results)} "
          f"QF-Bench tasks. Results: {run_dir / 'summary.md'}")


if __name__ == "__main__":
    main()
