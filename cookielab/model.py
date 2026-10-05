"""Pure, conditional checks over already admitted synthetic stored metadata."""

import re

from .contracts import validate

LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", re.ASCII)
PATH = re.compile(r"/[A-Za-z0-9/._~-]*", re.ASCII)
ASSUMPTIONS = (
    "Synthetic declarations only; stored admission and retention are assumed.",
    "Supported hosts and paths are canonical supplied context, not parsed URLs.",
    "Secure transport and whole-second time are supplied, never measured.",
    "Browser delivery, storage acceptance, session lifetime and authentication are unverified.",
)
DECISIONS = ("ELIGIBLE_UNDER_ASSUMPTIONS", "NOT_ELIGIBLE", "UNRESOLVED")


def _host(value):
    if value is None or not 1 <= len(value) <= 253:
        return False
    labels = value.split(".")
    return (len(labels) >= 2 and labels[-1] == "test"
            and all(LABEL.fullmatch(label) and not label.startswith("xn--") for label in labels))


def _path(value):
    return (value is not None and bool(PATH.fullmatch(value))
            and not any(segment in (".", "..") for segment in value.split("/")))


def _gate(name, state):
    suffix = {"PASS": "LIVE" if name == "expiry" else "MATCH",
              "FAIL": "EXPIRED" if name == "expiry" else "MISMATCH",
              "UNKNOWN": "CONTEXT"}[state]
    return {"state": state, "reason": name.upper() + "_" + suffix}


def _domain(cookie, request):
    domain, host = cookie["domain"], request["host"]
    if not _host(domain) or not _host(host) or cookie["host_only"] is None:
        return "UNKNOWN"
    if cookie["host_only"]:
        matched = host == domain
    else:
        matched = host == domain or host.endswith("." + domain)
    return "PASS" if matched else "FAIL"


def _path_scope(cookie, request):
    stored, current = cookie["path"], request["path"]
    if not _path(stored) or not _path(current):
        return "UNKNOWN"
    matched = (stored == current or (current.startswith(stored)
               and (stored.endswith("/") or current[len(stored):len(stored) + 1] == "/")))
    return "PASS" if matched else "FAIL"


def _transport(cookie, request):
    secure, transport = cookie["secure"], request["secure_transport"]
    if secure is False:
        return "PASS"
    if secure is None or transport is None:
        return "UNKNOWN"
    return "PASS" if transport else "FAIL"


def _expiry(cookie, request):
    if cookie["lifetime"] == "session":
        return "PASS"
    if cookie["lifetime"] == "unknown" or cookie["expires_at"] is None or request["now"] is None:
        return "UNKNOWN"
    return "FAIL" if cookie["expires_at"] <= request["now"] else "PASS"


def evaluate(document):
    """Validate bounded built-in metadata; return detached conditional results.

    Null/unsupported context never grants eligibility. A known failure remains
    visible even if another independent check cannot complete. No external effects.
    """
    validate(document)
    results = []
    statistics = {f"{s}:{d}": 0 for s in ("SUPPORTED", "UNSUPPORTED") for d in DECISIONS}
    for case in document["cases"]:
        cookie, request = case["cookie"], case["request"]
        gates = {name: _gate(name, func(cookie, request)) for name, func in (
            ("domain", _domain), ("path", _path_scope),
            ("transport", _transport), ("expiry", _expiry),
        )}
        unsupported = [gate["reason"] for gate in gates.values() if gate["state"] == "UNKNOWN"]
        unsupported += ["FEATURE:" + feature for feature in case["unsupported_features"]]
        status = "UNSUPPORTED" if unsupported else "SUPPORTED"
        failed = any(gate["state"] == "FAIL" for gate in gates.values())
        decision = "NOT_ELIGIBLE" if failed else "UNRESOLVED" if unsupported else "ELIGIBLE_UNDER_ASSUMPTIONS"
        statistics[f"{status}:{decision}"] += 1
        results.append({"id": case["id"], "cookie": dict(cookie), "request": dict(request),
                        "gates": gates, "unsupported_contexts": unsupported,
                        "profile_status": status, "scope_decision": decision})
    return {"version": 1, "profile": "stored-cookie-scope/1", "results": results,
            "statistics": statistics, "assumptions": list(ASSUMPTIONS)}
