"""Reproduce full reports, freeze identities, mutants and physical pipe failures.

Usage: python tools/verify.py --output reports/<fresh-directory>. No network. Mutation
copies stay within a test-owned temporary directory; the actual model is never edited.
"""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess  # nosec B404: fixed local verification commands only
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cookielab import parse, render


def run(command, cwd=ROOT):
    return subprocess.run(command, cwd=cwd, capture_output=True, timeout=60)  # nosec B603: trusted interpreter/tool commands, never input-controlled code


def tests(output, name, cwd=ROOT, optimized=False):
    command = [sys.executable, "-B"] + (["-O"] if optimized else [])
    completed = run(command + ["-m", "unittest", "discover", "-s", "tests", "-v"], cwd)
    (output / (name + ".stdout")).write_bytes(completed.stdout)
    (output / (name + ".stderr")).write_bytes(completed.stderr)
    return completed


def pipe_boundary(mode):
    # Parent waits for READY, closes the selected physical pipe, then releases child.
    source = (
        "import sys; from cookielab.__main__ import main; "
        "sys.stdout.buffer.write(b'READY\\n'); sys.stdout.buffer.flush(); "
        "sys.stdin.buffer.readline(); "
        + ("raise SystemExit(main([]))" if mode == "stderr" else
           "raise SystemExit(main(['fixtures/cases.json']))")
    )
    child = subprocess.Popen([sys.executable, "-B", "-c", source], cwd=ROOT,  # nosec B603: fixed trusted barrier test child
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        if child.stdout.readline() != b"READY\n":
            raise RuntimeError("PIPE_BARRIER_NOT_READY")
        if mode == "stdout":
            child.stdout.close()
            child.stdout = None
        if mode == "stderr":
            child.stderr.close()
            child.stderr = None
        child.stdin.write(b"GO\n")
        child.stdin.flush()
        child.stdin.close()
        child.stdin = None
        stdout, stderr = child.communicate(timeout=15)
        expected = 2 if mode == "control" else 1
        good = child.returncode == expected
        if mode == "control":
            good = good and stdout == (ROOT / "fixtures/expected.json").read_bytes() and stderr == b""
        return {"mode": mode, "barrier": True, "returncode": child.returncode, "passed": good,
                "stdout_bytes": len(stdout or b""), "stderr_bytes": len(stderr or b"")}
    finally:
        if child.poll() is None:
            child.kill()
            child.wait()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="Fresh report directory")
    args = parser.parse_args()
    output = Path(args.output).resolve()
    # A verifier output is trusted operator input, but keep all mutation/temp files in ROOT.
    if not output.is_relative_to(ROOT) or output == ROOT:
        parser.error("Output must be a fresh descendant of the project")
    output.mkdir(parents=True, exist_ok=False)
    receipt = {"python": sys.version, "normal": None, "optimized": None, "mutants": [], "pipes": []}
    for name, optimized in (("normal", False), ("optimized", True)):
        completed = tests(output, name, optimized=optimized)
        receipt[name] = {"exit": completed.returncode, "passed": completed.returncode == 0}
    original = (ROOT / "cookielab/model.py").read_bytes()
    edits = [
        ("host-only", 'if cookie["host_only"]:', 'if False:'),
        ("domain-dot", 'host.endswith("." + domain)', 'host.endswith(domain)'),
        ("path-boundary", 'stored.endswith("/") or current[len(stored):len(stored) + 1] == "/"', 'True'),
        ("expiry-equality", 'cookie["expires_at"] <= request["now"]', 'cookie["expires_at"] < request["now"]'),
        ("unknown-pass", 'return "UNKNOWN"', 'return "PASS"'),
    ]
    for name, before, after in edits:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            sandbox = Path(directory)
            for folder in ("cookielab", "tests", "fixtures", "docs"):
                shutil.copytree(ROOT / folder, sandbox / folder, ignore=shutil.ignore_patterns("__pycache__"))
            source = original.decode("utf-8")
            if before not in source:
                raise RuntimeError("MUTATION_ANCHOR_MISSING")
            (sandbox / "cookielab/model.py").write_text(source.replace(before, after, 1), encoding="utf-8", newline="\n")
            # Model tests isolate semantic failures from the CLI wrapper and harness.
            completed = run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_model.py", "-v"], sandbox)
            (output / ("mutant-" + name + ".stderr")).write_bytes(completed.stderr)
            failures = completed.stderr.count(b"\nFAIL:")
            errors = completed.stderr.count(b"\nERROR:")
            receipt["mutants"].append({"name": name, "exit": completed.returncode, "failures": failures,
                                       "errors": errors, "passed": completed.returncode != 0 and failures > 0 and errors == 0})
    receipt["original_unchanged"] = (ROOT / "cookielab/model.py").read_bytes() == original
    restored = tests(output, "restored")
    receipt["restored"] = {"exit": restored.returncode, "passed": restored.returncode == 0}
    for mode in ("control", "stdout", "stderr"):
        receipt["pipes"].append(pipe_boundary(mode))
    doc = parse((ROOT / "fixtures/cases.json").read_bytes())
    stress = {"version": 1, "cases": []}
    for i in range(40):
        case = copy.deepcopy(doc["cases"][0])
        case["id"] = str(i) + "x" * 62
        case["cookie"].update(domain="a." * 123 + "test", path="/" + "x" * 255)
        case["request"].update(host="a." * 123 + "test", path="/" + "x" * 255)
        case["unsupported_features"] = ["f" + str(n) + "x" * 30 for n in range(8)]
        stress["cases"].append(case)
    receipt["stress"] = {"input": len(json.dumps(stress, separators=(",", ":")).encode()),
                         "json": len(render(stress)), "markdown": len(render(stress, "markdown")),
                         "natural_overflow": False, "hard_resource_proof": False}
    scanner = run([sys.executable, "-m", "bandit", "-r", "cookielab", "tests", "tools", "-f", "json"])
    (output / "bandit.json").write_bytes(scanner.stdout)
    (output / "bandit.stderr").write_bytes(scanner.stderr)
    scan = json.loads(scanner.stdout)
    receipt["bandit"] = {"exit": scanner.returncode, "findings": len(scan["results"]),
                         "errors": len(scan["errors"]), "passed": scanner.returncode == 0 and not scan["errors"]}
    receipt["hashes"] = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                         for folder in ("cookielab", "tests", "tools", "fixtures", "docs")
                         for path in sorted((ROOT / folder).glob("*")) if path.is_file()}
    receipt["passed"] = (all(receipt[key]["passed"] for key in ("normal", "optimized", "restored", "bandit"))
                         and receipt["original_unchanged"]
                         and all(row["passed"] for row in receipt["mutants"] + receipt["pipes"]))
    (output / "results.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt))
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
