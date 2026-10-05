"""Independent frozen reports and strict public-boundary tests."""

import copy
import ast
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from cookielab import Invalid, evaluate, parse, render
from cookielab import contracts

ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = json.loads((ROOT / "fixtures/cases.json").read_text(encoding="utf-8"))


def sample():
    return {"version": 1, "cases": [copy.deepcopy(DOCUMENT["cases"][0])]}


class ModelTests(unittest.TestCase):
    def reject(self, document, code):
        with self.assertRaisesRegex(Invalid, "^" + code + "$"):
            evaluate(document)

    def test_frozen_artifacts(self):
        entries = json.loads((ROOT / "fixtures/freeze.json").read_text())
        for name, receipt in entries.items():
            raw = (ROOT / name).read_bytes()
            self.assertEqual(len(raw), receipt["bytes"], name)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), receipt["sha256"], name)

    def test_application_capability_surface(self):
        allowed = {"json", "re", "os", "argparse", "sys"}
        forbidden_calls = {"eval", "exec", "compile", "__import__", "system", "popen"}
        for path in (ROOT / "cookielab").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertIn(alias.name, allowed, path.name)
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    self.assertIn(node.module, allowed, path.name)
                elif isinstance(node, ast.Call):
                    name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ""
                    # re.compile builds a fixed regex, not executable Python source.
                    if (name == "compile" and isinstance(node.func, ast.Attribute)
                            and isinstance(node.func.value, ast.Name) and node.func.value.id == "re"):
                        continue
                    self.assertNotIn(name, forbidden_calls, path.name)

    def test_full_report_and_bytes(self):
        expected = json.loads((ROOT / "fixtures/expected.json").read_bytes())
        self.assertEqual(evaluate(DOCUMENT), expected)
        for format_name, filename in (("json", "expected.json"), ("markdown", "expected.md")):
            self.assertEqual(render(DOCUMENT, format_name), (ROOT / "fixtures" / filename).read_bytes())

    def test_frozen_diagnostics(self):
        for row in json.loads((ROOT / "fixtures/diagnostics.json").read_bytes()):
            with self.subTest(code=row["code"]):
                with self.assertRaisesRegex(Invalid, "^" + row["code"] + "$"):
                    evaluate(parse(row["raw"].encode()))

    def test_finite_domain_table(self):
        # Expected host-only and domain-scope truths are literal, not formula copies.
        table = [("example.test", True, True), ("shop.example.test", False, True),
                 ("a.shop.example.test", False, True), ("badexample.test", False, False),
                 ("example.test.other.test", False, False), ("other.test", False, False)]
        for host, host_only_match, domain_match in table:
            for host_only, expected in ((True, host_only_match), (False, domain_match)):
                doc = sample()
                doc["cases"][0]["cookie"]["host_only"] = host_only
                doc["cases"][0]["request"]["host"] = host
                with self.subTest(host=host, host_only=host_only):
                    self.assertEqual(evaluate(doc)["results"][0]["gates"]["domain"]["state"],
                                     "PASS" if expected else "FAIL")

    def test_finite_path_table(self):
        table = [("/", "/", True), ("/", "/x", True), ("/app", "/app", True),
                 ("/app", "/app/x", True), ("/app", "/apple", False),
                 ("/app/", "/app", False), ("/app/", "/app/x", True),
                 ("/app", "/APP", False), ("/app//", "/app//x", True),
                 ("/app/x", "/app/xy", False)]
        for stored, current, expected in table:
            doc = sample()
            doc["cases"][0]["cookie"]["path"] = stored
            doc["cases"][0]["request"]["path"] = current
            with self.subTest(stored=stored, current=current):
                self.assertEqual(evaluate(doc)["results"][0]["gates"]["path"]["state"],
                                 "PASS" if expected else "FAIL")

    def test_independent_unknown_and_exclusion(self):
        doc = sample()
        doc["cases"][0]["request"].update(host="other.test", now=None)
        row = evaluate(doc)["results"][0]
        self.assertEqual(row["scope_decision"], "NOT_ELIGIBLE")
        self.assertEqual(row["profile_status"], "UNSUPPORTED")
        self.assertEqual(row["gates"]["domain"]["state"], "FAIL")
        self.assertEqual(row["gates"]["expiry"]["state"], "UNKNOWN")
        doc = sample()
        doc["cases"][0]["unsupported_features"] = ["future-policy"]
        self.assertEqual(evaluate(doc)["results"][0]["scope_decision"], "UNRESOLVED")

    def test_whole_schema_before_negative_shortcut(self):
        doc = sample()
        doc["cases"][0]["request"]["host"] = "other.test"
        later = copy.deepcopy(doc["cases"][0])
        later["id"] = "later"
        later["cookie"]["value"] = "not-admitted"
        doc["cases"].append(later)
        self.reject(doc, "SCHEMA")

    def test_native_objects_no_callbacks(self):
        events = []

        class Meta(type):
            def __eq__(cls, other):
                events.append("metaclass equality")
                return False

        class Trap(metaclass=Meta):
            def __iter__(self):
                events.append("iterate")
                return iter(())

            def __str__(self):
                events.append("string")
                return "trap"

        for value in (Trap(), iter(()), (1,), b"raw", 1.0, object()):
            doc = sample()
            doc["cases"][0]["cookie"]["domain"] = value
            self.reject(doc, "TREE_TYPE")
        self.assertEqual(events, [])

    def test_subclasses_rejected(self):
        for base, value in ((str, "x"), (int, 1), (list, []), (dict, {}), (bytes, b"x")):
            derived = type("Derived", (base,), {})
            doc = sample()
            doc["cases"][0]["request"]["host"] = derived(value)
            self.reject(doc, "TREE_TYPE")
        with self.assertRaisesRegex(Invalid, "INPUT_LIMIT"):
            parse(type("Bytes", (bytes,), {})(b"{}"))

    def test_cycle_alias_detachment_and_no_mutation(self):
        cycle = []
        cycle.append(cycle)
        self.reject(cycle, "TREE_CYCLE")
        doc = sample()
        doc["cases"].append(copy.deepcopy(doc["cases"][0]))
        doc["cases"][1]["id"] = "second"
        doc["cases"][1]["cookie"] = doc["cases"][0]["cookie"]
        before = copy.deepcopy(doc)
        result = evaluate(doc)
        self.assertEqual(doc, before)
        result["results"][0]["cookie"]["domain"] = "other.test"
        self.assertEqual(doc, before)
        self.assertEqual(result["results"][1]["cookie"]["domain"], "example.test")

    def test_schema_types_and_expiry_shape(self):
        for name, value, code in (("host_only", 1, "BOOL_TYPE"), ("expires_at", True, "TIME"),
                                  ("domain", False, "NULL_TEXT_TYPE"), ("lifetime", "forever", "LIFETIME"),
                                  ("expires_at", -1, "TIME")):
            doc = sample()
            doc["cases"][0]["cookie"][name] = value
            self.reject(doc, code)
        doc = sample()
        doc["cases"][0]["cookie"]["lifetime"] = "session"
        self.reject(doc, "EXPIRY_SHAPE")

    def test_bounds_and_bad_text(self):
        for value, code in (("x" * 257, "TEXT_TYPE_OR_LIMIT"), ("x\n", "TEXT_CONTROL"),
                            ("\ud800", "INVALID_UNICODE")):
            doc = sample()
            doc["cases"][0]["request"]["host"] = value
            self.reject(doc, code)
        for raw, code in ((b" " * 65537, "INPUT_LIMIT"), (b"\xff", "INVALID_JSON"),
                          (b"[" * 9 + b"]" * 9, "JSON_DEPTH")):
            with self.assertRaisesRegex(Invalid, code):
                parse(raw)
        deep = []
        for _ in range(8):
            deep = [deep]
        self.reject(deep, "TREE_DEPTH")
        self.reject([0] * 101, "CONTAINER_LIMIT")
        self.reject([["x"] * 100 for _ in range(51)], "NODE_LIMIT")
        self.reject(10 ** 10, "INTEGER_TOKEN_BOUND")

    def test_duplicate_ids_and_features(self):
        doc = sample()
        doc["cases"] *= 2
        self.reject(doc, "DUPLICATE_CASE_ID")
        for features, code in ((["same", "same"], "FEATURE_DUPLICATE"), (["Bad"], "FEATURE_FORMAT"),
                               (["same"] * 9, "FEATURE_LIST")):
            doc = sample()
            doc["cases"][0]["unsupported_features"] = features
            self.reject(doc, code)

    def test_output_caps_and_inert_rendering(self):
        doc = sample()
        doc["cases"][0]["request"]["host"] = '<a href="example">'
        payload = render(doc, "markdown")
        self.assertNotIn(b"<a", payload)
        self.assertIn(b"&#60;", payload)
        with patch("cookielab.report.OUTPUT_BYTES", 1):
            with self.assertRaisesRegex(Invalid, "OUTPUT_LIMIT"):
                render(doc)
        with self.assertRaisesRegex(Invalid, "REPORT_FORMAT"):
            render(doc, "html")
        with self.assertRaisesRegex(Invalid, "REPORT_FORMAT"):
            render(doc, object())

    def test_admitted_stress_and_api_serialized_cap(self):
        doc = sample()
        original = doc["cases"][0]
        original["cookie"].update(domain="x" * 250 + ".test", path="/" + "x" * 255)
        original["request"].update(host="x" * 250 + ".test", path="/" + "x" * 255)
        original["unsupported_features"] = ["feature" + "x" * i for i in range(8)]
        doc["cases"] = []
        for i in range(40):
            row = copy.deepcopy(original)
            row["id"] = str(i) + "x" * 62
            doc["cases"].append(row)
        self.assertLess(len(json.dumps(doc, separators=(",", ":")).encode()), contracts.INPUT_BYTES)
        for fmt in ("json", "markdown"):
            self.assertLess(len(render(doc, fmt)), contracts.OUTPUT_BYTES)
        with patch("cookielab.contracts.INPUT_BYTES", 1):
            self.reject(doc, "INPUT_LIMIT")


if __name__ == "__main__":
    unittest.main()
