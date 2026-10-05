"""Real subprocess bytes plus trusted-stream seams; no network targets."""

import io
import json
from pathlib import Path
import subprocess  # nosec B404: trusted local CLI verification, no input commands
import sys
import tempfile
import unittest
from unittest.mock import patch

from cookielab import Invalid
from cookielab import __main__ as cli
from cookielab import report

ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args, optimized=False):
    command = [sys.executable, "-B"] + (["-O"] if optimized else []) + ["-m", "cookielab", *args]
    return subprocess.run(command, cwd=ROOT, capture_output=True, timeout=15)  # nosec B603: fixed interpreter/module, literal test arguments


class CliTests(unittest.TestCase):
    def test_full_bytes_normal_and_optimized(self):
        for optimized in (False, True):
            for fmt, name in (("json", "expected.json"), ("markdown", "expected.md")):
                result = run_cli("fixtures/cases.json", "--format", fmt, optimized=optimized)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stderr, b"")
                self.assertEqual(result.stdout, (ROOT / "fixtures" / name).read_bytes())

    def test_diagnostics_and_argument_help(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "invalid.json"
            for row in json.loads((ROOT / "fixtures/diagnostics.json").read_bytes()):
                path.write_bytes(row["raw"].encode())
                result = run_cli(str(path))
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, b"")
                self.assertEqual(result.stderr, ("cookielab: " + row["code"] + "\n").encode())
        self.assertEqual(run_cli().returncode, 1)
        self.assertEqual(run_cli("--help").returncode, 0)

    def test_fresh_file_alias_existing_and_supported_exit(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            source, output = Path(directory) / "source.json", Path(directory) / "output.json"
            document = json.loads((ROOT / "fixtures/cases.json").read_bytes())
            document["cases"] = document["cases"][:1]
            source.write_text(json.dumps(document), encoding="utf-8")
            result = run_cli(str(source), "--output", str(output))
            self.assertEqual(result.returncode, 0)
            before = output.read_bytes()
            self.assertEqual(run_cli(str(source), "--output", str(output)).returncode, 1)
            self.assertEqual(output.read_bytes(), before)
            alias = run_cli(str(source), "--output", str(source))
            self.assertEqual(alias.stderr, b"cookielab: OUTPUT_EQUALS_INPUT\n")
            self.assertEqual(alias.returncode, 1)

    def test_stdout_counts_flush_and_closed(self):
        class Stream:
            def __init__(self, count=None, failure=False):
                self.buffer = self
                self.count, self.failure = count, failure

            def write(self, payload):
                return self.count

            def flush(self):
                if self.failure:
                    raise OSError("synthetic flush")

        for count in (0, None, True, 3.0):
            with patch.object(cli.sys, "stdout", Stream(count)), patch.object(cli, "_silence_failed_stream", return_value=True):
                with self.assertRaises(OSError):
                    cli._stdout(b"abc")
        with patch.object(cli.sys, "stdout", Stream(3, True)), patch.object(cli, "_silence_failed_stream", return_value=True):
            with self.assertRaises(OSError):
                cli._stdout(b"abc")
        closed = io.TextIOWrapper(io.BytesIO())
        closed.close()
        with patch.object(cli.sys, "stdout", closed), patch.object(cli, "_silence_failed_stream", return_value=False):
            with self.assertRaisesRegex(Invalid, "STDOUT_WRITE_AND_SILENCE_FAILED"):
                cli._stdout(b"abc")

    def test_file_short_write_cleanup_and_cleanup_failure(self):
        class Stream:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def write(self, payload):
                return False

            def flush(self):
                return None

        with patch("builtins.open", return_value=Stream()), patch.object(report.os, "unlink") as unlink:
            with self.assertRaises(OSError):
                report.write_fresh("owned-output", b"abc")
            unlink.assert_called_once_with("owned-output")
        with patch("builtins.open", return_value=Stream()), patch.object(report.os, "unlink", side_effect=OSError):
            with self.assertRaisesRegex(Invalid, "OUTPUT_WRITE_AND_CLEANUP_FAILED"):
                report.write_fresh("owned-output", b"abc")


if __name__ == "__main__":
    unittest.main()
