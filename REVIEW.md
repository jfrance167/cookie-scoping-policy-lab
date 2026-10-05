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
approval is disabled. Hosted Windows/Ubuntu tests and Bandit, plus CodeQL, passed at commit
600e935ba0f7a13f052cbb109445c7979267f632; existing credentials cannot read
secret-scanning alerts. Open CodeQL and Dependabot alert counts read back as zero
on 2026-10-05. Main requires strict checks bound to GitHub Actions app 15368 and
blocks force pushes/deletion.

Publication correction: quoted the pip command after GitHub rejected its YAML
syntax; all three workflow/configuration YAML files now parse locally. Hosted
checks are required to establish runtime compatibility.

Documentation closeout self-review: reconciled the exact hosted commit/run results
and alert-readback limits against GitHub. Application/test/tool/frozen source hashes
remain unchanged. No runtime test rerun is needed for these factual Markdown edits;
PR checks will verify the documentation branch. Manual merge authorization remains.
