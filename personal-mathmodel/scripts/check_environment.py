#!/usr/bin/env python3
"""Check only tools declared for a task; never install or run a model/compiler job."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

if sys.version_info < (3, 9):
    print("This helper requires Python 3.9 or newer; use the existing compatible project interpreter.", file=sys.stderr)
    raise SystemExit(2)

TASKS = ("md", "compute", "plot", "latex", "pdf-view", "diagram")
MODULE = re.compile(r"^[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*$")
PROBE = r'''
import importlib, json, sys
items = []
for name in json.loads(sys.argv[1]):
    try:
        module = importlib.import_module(name)
        version = getattr(module, "__version__", None)
        items.append({"module": name, "importable": True,
                      "version": str(version)[:100] if version is not None else None})
    except Exception as exc:
        items.append({"module": name, "importable": False,
                      "reason": type(exc).__name__ + ": " + str(exc)[:240]})
print("ENV_CHECK_JSON=" + json.dumps({"python": sys.version.split()[0],
      "executable": sys.executable, "modules": items}))
'''


def resolve(command: str) -> str | None:
    if os.sep in command or (os.altsep and os.altsep in command):
        # Preserve the venv's symlink spelling: resolving it can select base Python.
        path = Path(command).expanduser().absolute()
        return str(path) if path.is_file() and os.access(path, os.X_OK) else None
    return shutil.which(command)


def run(command: list[str], timeout: float, folder: Path) -> dict:
    """Bound elapsed time and retained output; do not use a shell or project cwd."""
    env = os.environ.copy()
    env.update(PYTHONDONTWRITEBYTECODE="1", MPLCONFIGDIR=str(folder / "mpl"))
    try:
        # Files avoid keeping a noisy tool's unbounded output in memory.
        with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
            proc = subprocess.Popen(command, cwd=folder, env=env, stdout=out, stderr=err,
                                    start_new_session=(os.name != "nt"))
            try:
                returncode = proc.wait(timeout=timeout)
                timed_out = False
            except subprocess.TimeoutExpired:
                if os.name != "nt":
                    import signal
                    os.killpg(proc.pid, signal.SIGKILL)
                else:
                    proc.kill()
                proc.wait()
                returncode, timed_out = None, True
            out.seek(0); err.seek(0)
            stdout = out.read(16_384).decode("utf-8", errors="replace")
            stderr = err.read(4_096).decode("utf-8", errors="replace")
        return {"returncode": returncode, "timed_out": timed_out,
                "stdout": stdout, "stderr": stderr}
    except OSError as exc:
        return {"returncode": None, "timed_out": False, "launch_error": str(exc)[:300],
                "stdout": "", "stderr": ""}


def item(name: str, status: str, evidence: str, **extra) -> dict:
    return dict(name=name, status=status, evidence=evidence, **extra)


def check_python(args, modules: list[str], folder: Path) -> list[dict]:
    executable = resolve(args.python)
    if not executable:
        return [item("python", "missing", "Selected Python executable was not found.",
                     requested=args.python, action="Use the existing project interpreter, or select its actual path.")]
    result = run([executable, "-I", "-B", "-c", PROBE, json.dumps(modules)], args.timeout, folder)
    if result["timed_out"] or result.get("launch_error"):
        return [item("python-probe", "unverified", "The selected-interpreter probe did not complete.",
                     executable=executable, reason="timeout" if result["timed_out"] else result["launch_error"])]
    rows = [line[len("ENV_CHECK_JSON="):] for line in result["stdout"].splitlines()
            if line.startswith("ENV_CHECK_JSON=")]
    if result["returncode"] != 0 or not rows:
        return [item("python-probe", "unverified", "No successful structured response from the selected interpreter.",
                     executable=executable, returncode=result["returncode"],
                     detail=(result["stderr"] or result["stdout"])[-400:])]
    try:
        data = json.loads(rows[-1])
        if not isinstance(data.get("modules"), list):
            raise ValueError("module results not a list")
        if [r["module"] for r in data["modules"]] != modules:
            raise ValueError("module result set differs from request")
        if not all(isinstance(r.get("importable"), bool) for r in data["modules"]):
            raise ValueError("module import state is missing or invalid")
    except (ValueError, TypeError, KeyError) as exc:
        return [item("python-probe", "unverified", "Malformed structured probe result.", reason=str(exc)[:200])]
    checks = [item("python", "checked", "Selected interpreter responded to an isolated probe.",
                   executable=data.get("executable", executable), version=data.get("python"))]
    for row in data["modules"]:
        checks.append(item("module:" + row["module"], "checked" if row["importable"] else "missing",
                           "Imported in the selected interpreter." if row["importable"] else "Import failed in the selected interpreter.",
                           version=row.get("version"), detail=row.get("reason"),
                           action=None if row["importable"] else "Check this project's dependency/version requirements; no installation was attempted."))
    return checks


def check_tool(name: str, requested: str, flag: str, args, folder: Path) -> dict:
    executable = resolve(requested)
    if not executable:
        return item(name, "missing", "Requested executable was not found or is not executable.",
                    requested=requested, action="Select an existing compatible tool, or arrange only this missing dependency.")
    result = run([executable, flag], args.timeout, folder)
    if result["timed_out"] or result.get("launch_error"):
        return item(name, "unverified", "Version probe did not complete.", executable=executable,
                    reason="timeout" if result["timed_out"] else result["launch_error"])
    text = (result["stdout"].strip() or result["stderr"].strip())[:350]
    if result["returncode"] != 0 or not text:
        return item(name, "unverified", "Executable exists, but a successful version response was not obtained.",
                    executable=executable, returncode=result["returncode"], detail=text)
    return item(name, "checked", "Executable returned version/help text; no document or image was processed.",
                executable=executable, version_response=text)


def examine(args) -> dict:
    tasks = list(dict.fromkeys(args.task))
    checks, limits = [], [
        "Only explicitly requested task checks are reported; absent unrelated tools do not block them.",
        "A tool version or Python import is not a numerical test, rendering test, paper compilation or scientific validation.",
        "No project data, credential inventory, environment-variable dump, network request or installation is performed.",
        "Requested third-party imports execute their initialization in a short-lived subprocess; request only trusted project dependencies.",
    ]
    modules = list(dict.fromkeys(args.require_module or [])) if {"compute", "plot"}.intersection(tasks) else []
    if "plot" in tasks:
        modules = list(dict.fromkeys(modules + [args.plot_library]))
    for module in modules:
        if not MODULE.fullmatch(module):
            raise ValueError("Use import module names such as numpy or sklearn, not pip requirements or shell text.")
    with tempfile.TemporaryDirectory(prefix="mathmodel-task-env-") as temporary:
        folder = Path(temporary)
        if "md" in tasks:
            checks.append(item("md", "checked", "Plain Markdown editing has no compiler or scientific-package prerequisite in this check."))
        if {"compute", "plot"}.intersection(tasks):
            checks += check_python(args, modules, folder)
            if "compute" in tasks and not args.require_module:
                checks.append(item("compute-dependencies", "unverified", "No computational dependencies were declared; only Python was checked.",
                                   action="Infer the needed imports from the agreed plan/script before claiming implementation readiness."))
            if "plot" in tasks:
                limits.append("Plot-library import only: fonts, export formats and actual plot readability are not checked.")
        if "latex" in tasks:
            engine = args.engine
            if engine is None and args.compiler:
                base = Path(args.compiler).name.lower().removesuffix(".exe")
                engine = base if base in {"xelatex", "tectonic", "pdflatex", "lualatex"} else None
            if engine is None:
                checks.append(item("latex-engine", "unverified", "No selected engine; multiple compilers were not probed.",
                                   action="Reuse the paper/project's chosen engine and its actual executable path."))
            else:
                checks.append(check_tool("latex:" + engine, args.compiler or engine, "--version", args, folder))
            limits.append("LaTeX packages, class compatibility, CJK fonts and this paper's actual compilation remain unchecked.")
        if "pdf-view" in tasks:
            renderer = args.renderer
            if renderer is None:
                renderer = next((name for name in ("pdftoppm", "mutool", "magick") if resolve(name)), None)
            if renderer is None:
                checks.append(item("pdf-renderer", "missing", "No supported PDF rasterizer was found.",
                                   action="Use one existing renderer; installing all alternatives is unnecessary."))
            else:
                base = Path(renderer).name.lower().removesuffix(".exe")
                flag = "-v" if base in {"pdftoppm", "mutool"} else "-version" if base == "magick" else "--version"
                checks.append(check_tool("pdf-renderer", renderer, flag, args, folder))
            limits.append("No PDF was rendered or visually inspected by this environment check.")
        if "diagram" in tasks:
            drawio = args.diagram_tool or next((name for name in ("drawio", "draw.io") if resolve(name)), "drawio")
            checks.append(check_tool("diagram-export", drawio, "--version", args, folder))
            limits.append("No GUI session, diagram layout or diagram export was tested.")
    statuses = {row["status"] for row in checks}
    exit_code = 1 if "missing" in statuses else 3 if "unverified" in statuses else 0
    return dict(recorded_at_utc=datetime.now(timezone.utc).isoformat(), tasks=tasks,
                checker_python=sys.executable, checks=checks,
                status="current_task_missing_dependency" if exit_code == 1 else "needs_details_or_verification" if exit_code == 3 else "requested_checks_ready",
                exit_code=exit_code, limits=limits)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=TASKS, action="append", required=True,
                        help="Repeat for a combination; do not select irrelevant tasks")
    parser.add_argument("--python", default=sys.executable, help="Existing project interpreter, used only for compute/plot")
    parser.add_argument("--require-module", action="append", help="Trusted import name actually required by compute/plot; repeat as needed")
    parser.add_argument("--plot-library", default="matplotlib", help="Plot import name; default matplotlib (import probe only)")
    parser.add_argument("--engine", choices=("xelatex", "tectonic", "pdflatex", "lualatex"))
    parser.add_argument("--compiler", help="Existing compiler path; never installed or used to compile a paper here")
    parser.add_argument("--renderer", help="Existing PDF rasterizer; only used with --task pdf-view")
    parser.add_argument("--diagram-tool", help="Existing diagram exporter; only used with --task diagram")
    parser.add_argument("--timeout", type=float, default=10, help="Seconds per probe; must be positive and at most 60")
    parser.add_argument("--json", type=Path, help="Optional explicit JSON report; no other lasting files are written")
    args = parser.parse_args()
    try:
        if not 0 < args.timeout <= 60:
            raise ValueError("timeout must be greater than zero and at most 60 seconds")
        report = examine(args)
        if args.json:
            target = args.json.expanduser().resolve()
            if target.suffix.lower() != ".json" or target == Path(__file__).resolve():
                raise ValueError("Report must be an explicitly selected .json file")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(report["status"] + " | tasks: " + ", ".join(report["tasks"]))
        for row in report["checks"]:
            print(f"{row['status'].upper()} {row['name']}: {row['evidence']}")
            if row.get("action"):
                print("  Next: " + row["action"])
        print("Task-scoped environment checks only; no model or paper has been validated.")
        return report["exit_code"]
    except (OSError, ValueError) as exc:
        print("Environment check did not complete: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
