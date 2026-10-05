# Verification — 2026-10-05

Windows Python 3.13.7, final local verifier receipt: reports/final/results.json
(retained locally; reports are ignored). Run `python -B tools/verify.py --output
reports/fresh-run` to reproduce without regenerating fixtures.

- 21 unittest methods pass normally, under -O and after mutation checks.
- All 40 full reports and both exact rendered oracle byte streams agree.
- Five frozen artifacts retain their recorded SHA256 identities.
- Host-only/domain-dot/path-boundary/expiry-equality/unknown-pass mutants fail
  3/2/3/1/1 assertions respectively, zero harness errors. Original model unchanged.
- Three live pipe-barrier cases pass: control exits 2 with 37016 JSON bytes;
  closed stdout and closed stderr error paths exit 1.
- Admitted stress: input 62533 bytes, JSON 94155, Markdown 414792.
  No natural output overflow was observed. Reduced-cap seam tests enforce refusal;
  this is not a hard process RSS/time proof.
- Bandit 1.9.4 scans application, tests and tools: zero findings, zero errors.
  Narrow subprocess exceptions are documented on trusted harness calls only.

Earlier Windows TEMP and overly broad AST compile-check failures were corrected;
failed raw receipts remain locally. Only the final passing run is cited here.
Published on GitHub; hosted Linux/Windows CI and CodeQL are queued.
All five frozen artifact byte/SHA256 identities match the published Git blobs. Finite checks and SAST do not
establish universal browser conformance, production safety or independent audit.
