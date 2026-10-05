# ECC self-review — 2026-10-05

Implementing agent reviewed all five application modules, public callers, both
test files, verifier, one-shot oracle author, frozen contract and publication
configuration with the pinned ECC reviewer checklist. This is a self-review.

Checked exact type identity before callbacks, whole-schema admission, unknown/fail
preservation, dot/slash boundaries, expiry equality, detached output, inert rendering,
size limits, fresh-file cleanup and exact delivery counts. Tests exercise these
boundaries and literal expectations; mutation checks catch five semantic regressions.

Corrected harness defects: temporary directories now stay in the owned workspace;
the capability AST check distinguishes fixed re.compile from builtin code compile.
Removed an unused verifier import. Application oracles were never regenerated.

Remaining actionable runtime defects found: zero (critical/high/medium/low: 0).
Local final verification passes; see VERIFICATION.md. No independent audit or merge
approval is claimed. Residual filesystem races, caller dishonesty, excluded browser
policies and hard process resources remain documented limits.

All three action references resolve to full commits (checkout v6, setup-python v6,
CodeQL v4); least permissions and checkout credential persistence disabled.
Optional scanner dependencies are exact-version pins; metadata transport failures
prevented a complete hash lock. Published with secret scanning, push protection and Dependabot alerts/security
updates enabled. Default workflow permissions are read-only and Actions PR
approval is disabled. Hosted checks are pending; existing credentials cannot read
secret-scanning alerts.

Publication correction: quoted the pip command after GitHub rejected its YAML
syntax; all three workflow/configuration YAML files now parse locally. Hosted
checks are required to establish runtime compatibility.
