"""One-shot hand-assigned oracle composition, run BEFORE the implementation.

No semantic matching functions: every expected gate row below is literal. Preserved
for provenance, never run by verification to overwrite frozen expected outputs.
"""

import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = {
    "id": "baseline",
    "cookie": {"domain": "example.test", "host_only": False, "path": "/app",
               "secure": True, "lifetime": "persistent", "expires_at": 101},
    "request": {"host": "example.test", "path": "/app/x",
                "secure_transport": True, "now": 100},
    "unsupported_features": [],
}
ASSUMPTIONS = [
    "Synthetic declarations only; stored admission and retention are assumed.",
    "Supported hosts and paths are canonical supplied context, not parsed URLs.",
    "Secure transport and whole-second time are supplied, never measured.",
    "Browser delivery, storage acceptance, session lifetime and authentication are unverified.",
]
# (id, nested changes, domain/path/transport/expiry states, optional features)
ROWS = [
    ("baseline", {}, "PPPP"),
    ("domain-subdomain", {"request.host": "shop.example.test"}, "PPPP"),
    ("domain-lookalike", {"request.host": "badexample.test"}, "FPPP"),
    ("domain-other", {"request.host": "other.test"}, "FPPP"),
    ("hostonly-equal", {"cookie.host_only": True}, "PPPP"),
    ("hostonly-child", {"cookie.host_only": True, "request.host": "shop.example.test"}, "FPPP"),
    ("nested-domain", {"cookie.domain": "shop.example.test", "request.host": "a.shop.example.test"}, "PPPP"),
    ("nested-lookalike", {"cookie.domain": "shop.example.test", "request.host": "badshop.example.test"}, "FPPP"),
    ("domain-null", {"cookie.domain": None}, "UPPP"),
    ("host-null", {"request.host": None}, "UPPP"),
    ("hostonly-null", {"cookie.host_only": None}, "UPPP"),
    ("host-uppercase", {"request.host": "Example.test"}, "UPPP"),
    ("domain-leading-dot", {"cookie.domain": ".example.test"}, "UPPP"),
    ("path-equal", {"request.path": "/app"}, "PPPP"),
    ("path-lookalike", {"request.path": "/apple"}, "PFPP"),
    ("path-root", {"cookie.path": "/"}, "PPPP"),
    ("path-trailing-ok", {"cookie.path": "/app/"}, "PPPP"),
    ("path-trailing-short", {"cookie.path": "/app/", "request.path": "/app"}, "PFPP"),
    ("path-case", {"request.path": "/APP/x"}, "PFPP"),
    ("path-double-slash", {"cookie.path": "/app//", "request.path": "/app//x"}, "PPPP"),
    ("path-percent", {"request.path": "/app/%78"}, "PUPP"),
    ("path-null", {"cookie.path": None}, "PUPP"),
    ("transport-plain", {"request.secure_transport": False}, "PPFP"),
    ("secure-false", {"cookie.secure": False, "request.secure_transport": False}, "PPPP"),
    ("transport-null", {"request.secure_transport": None}, "PPUP"),
    ("secure-false-null", {"cookie.secure": False, "request.secure_transport": None}, "PPPP"),
    ("secure-null", {"cookie.secure": None}, "PPUP"),
    ("expiry-before", {"cookie.expires_at": 99}, "PPPF"),
    ("expiry-equal", {"cookie.expires_at": 100}, "PPPF"),
    ("expiry-after", {"cookie.expires_at": 102}, "PPPP"),
    ("session", {"cookie.lifetime": "session", "cookie.expires_at": None, "request.now": None}, "PPPP"),
    ("clock-null", {"request.now": None}, "PPPU"),
    ("expiry-null", {"cookie.expires_at": None}, "PPPU"),
    ("lifetime-unknown", {"cookie.lifetime": "unknown", "cookie.expires_at": None}, "PPPU"),
    ("fail-and-unknown", {"request.host": "other.test", "request.now": None}, "FPPU"),
    ("samesite-excluded", {}, "PPPP", ["samesite"]),
    ("feature-and-fail", {"request.host": "other.test"}, "FPPP", ["partitioned"]),
    ("host-ip", {"request.host": "127.0.0.1"}, "UPPP"),
    ("domain-idna", {"cookie.domain": "xn--demo.test"}, "UPPP"),
    ("path-dot-segment", {"request.path": "/app/../x"}, "PUPP"),
]
DECISIONS = ("ELIGIBLE_UNDER_ASSUMPTIONS", "NOT_ELIGIBLE", "UNRESOLVED")
stats = {f"{s}:{d}": 0 for s in ("SUPPORTED", "UNSUPPORTED") for d in DECISIONS}
cases, results = [], []
for row in ROWS:
    identifier, edits, states = row[:3]
    case = copy.deepcopy(BASE)
    case["id"] = identifier
    for name, value in edits.items():
        parent, field = name.split(".")
        case[parent][field] = value
    if len(row) == 4:
        case["unsupported_features"] = row[3]
    gates, unsupported = {}, []
    for name, letter, good, bad in zip(
        ("domain", "path", "transport", "expiry"), states,
        ("MATCH", "MATCH", "MATCH", "LIVE"),
        ("MISMATCH", "MISMATCH", "MISMATCH", "EXPIRED"),
    ):
        state = {"P": "PASS", "F": "FAIL", "U": "UNKNOWN"}[letter]
        reason = name.upper() + "_" + {"P": good, "F": bad, "U": "CONTEXT"}[letter]
        gates[name] = {"state": state, "reason": reason}
        if letter == "U":
            unsupported.append(reason)
    unsupported += ["FEATURE:" + f for f in case["unsupported_features"]]
    status = "UNSUPPORTED" if unsupported else "SUPPORTED"
    decision = "NOT_ELIGIBLE" if "F" in states else "UNRESOLVED" if unsupported else "ELIGIBLE_UNDER_ASSUMPTIONS"
    stats[f"{status}:{decision}"] += 1
    cases.append(case)
    results.append({"id": identifier, "cookie": case["cookie"], "request": case["request"],
                    "gates": gates, "unsupported_contexts": unsupported,
                    "profile_status": status, "scope_decision": decision})
report = {"version": 1, "profile": "stored-cookie-scope/1", "results": results,
          "statistics": stats, "assumptions": ASSUMPTIONS}


def entities(value):
    return "".join(f"&#{ord(c)};" for c in value)


lines = ["# Offline stored-cookie scope", "", "Supplied metadata only; no cookie is built or sent.", ""]
for result in results:
    lines.extend(["## " + entities(result["id"]), "", "| Field | Value |", "|---|---|"])
    for key, value in result.items():
        if key == "id":
            continue
        rendered = json.dumps(value, ensure_ascii=True) if type(value) is dict or type(value) is list else str(value)
        lines.append("| " + key + " | " + entities(rendered) + " |")
    lines.append("")
lines.extend(["Assumptions:", ""] + ["- " + entities(s) for s in ASSUMPTIONS])
diagnostics = [
    {"raw": "{\"version\":1,\"version\":1,\"cases\":[]}", "code": "DUPLICATE_KEY"},
    {"raw": "{\"version\":1.0,\"cases\":[]}", "code": "NONINTEGER_JSON"},
    {"raw": "{\"version\":NaN,\"cases\":[]}", "code": "NONINTEGER_JSON"},
    {"raw": "{\"version\":10000000000,\"cases\":[]}", "code": "INTEGER_TOKEN_BOUND"},
    {"raw": "{}", "code": "SCHEMA"},
    {"raw": "{\"version\":true,\"cases\":[]}", "code": "VERSION"},
    {"raw": "{\"version\":1,\"cases\":[]}", "code": "CASE_COUNT"},
    {"raw": "[", "code": "INVALID_JSON"},
]
payloads = {
    "fixtures/cases.json": json.dumps({"version": 1, "cases": cases}, indent=2) + "\n",
    "fixtures/expected.json": json.dumps(report, ensure_ascii=True, indent=2) + "\n",
    "fixtures/expected.md": "\n".join(lines) + "\n",
    "fixtures/diagnostics.json": json.dumps(diagnostics, indent=2) + "\n",
}
for relative, source in payloads.items():
    path = ROOT / relative
    path.parent.mkdir(exist_ok=True)
    with path.open("xb") as stream:
        stream.write(source.encode("utf-8"))
names = ("docs/CONTRACT.md", *payloads)
receipt = {name: {"bytes": (ROOT / name).stat().st_size,
                  "sha256": hashlib.sha256((ROOT / name).read_bytes()).hexdigest()} for name in names}
with (ROOT / "fixtures/freeze.json").open("x", encoding="utf-8") as stream:
    json.dump(receipt, stream, indent=2)
print(json.dumps({"rows": len(results), "statistics": stats, "frozen_files": len(receipt)}))
